import os
import requests
import asyncio
import chainlit as cl
from rapidfuzz import fuzz
from datetime import datetime
from typing import Optional

BACKEND_URL = "http://localhost:8000"
history_cache = []
pending_tasks = {}  # task_id -> {"question": str, "answer": str, "video_url": str}

# ------------------ Chat Start ------------------
@cl.on_chat_start
async def start_chat():
    await cl.Message(
        content=(
            "👋 Hi! Send me a math concept or question and I'll generate a Manim animation.\n\n"
            "➡️ After the animation, I'll also quiz you.\n"
            "Type `history` anytime to see recent animations."
        )
    ).send()


# ------------------ Loading Animation ------------------
async def animate_loading(message: cl.Message, base_text: str, stop_event: asyncio.Event):
    dots = ["", ".", "..", "..."]
    i = 0
    while not stop_event.is_set():
        message.content = f"{base_text}{dots[i % len(dots)]}"
        await message.update()
        await asyncio.sleep(0.6)
        i += 1


# ------------------ Display Polished History ------------------
async def display_history():
    if not history_cache:
        await cl.Message(content="📭 History is empty.").send()
        return

    await cl.Message(content="🕹 **Recent Animations:**").send()

    for idx, entry in enumerate(reversed(history_cache[-5:]), 1):
        content = (
            f"**#{idx}**\n"
            f"💬 **Prompt:** {entry['text']}\n"
            f"🕒 **Time:** {entry['timestamp']}\n"
            f"🎥 **Video URL:** {entry['video_url']}"
        )
        await cl.Message(content=content).send()


# ------------------ Message Handler ------------------
@cl.on_message
async def handle_message(message: cl.Message):
    user_input = message.content.strip()

    # 1) Show history
    if user_input.lower() == "history":
        await display_history()
        return

    # 2) If user is answering a pending question
    for task_id, task in list(pending_tasks.items()):
        if task.get("awaiting_answer"):
            await check_user_answer(task_id, user_input)
            return

    # 3) Otherwise treat as new animation request
    await generate_new_animation(user_input)


# ------------------ Helpers: Range-get based availability check ------------------
async def _range_get_url_async(url: str, timeout: int = 5) -> Optional[int]:
    """
    Issue a lightweight GET with Range: bytes=0-0 to check availability.
    Runs in a thread to avoid blocking the event loop.
    Returns HTTP status code (e.g., 200, 206) or None on exception.
    """
    def _req():
        try:
            # request only first byte; many servers will respond 206 Partial Content
            resp = requests.get(url, headers={"Range": "bytes=0-0"}, stream=True, timeout=timeout)
            status = resp.status_code
            # ensure response content is consumed/closed
            try:
                # read a tiny chunk to allow connection reuse then close
                _ = next(resp.iter_content(chunk_size=1), b"")
            except Exception:
                pass
            resp.close()
            return status
        except Exception:
            return None

    return await asyncio.to_thread(_req)


async def wait_for_video_url(video_url: str, total_wait: float = 30.0, interval: float = 0.5) -> bool:
    """
    Poll the backend URL (via Range GET) until it returns 200 or 206, or until timeout.
    Returns True if available, False if timed out.
    """
    elapsed = 0.0
    while elapsed < total_wait:
        status = await _range_get_url_async(video_url)
        # 200 OK or 206 Partial Content both indicate the resource is available
        if status in (200, 206):
            return True
        await asyncio.sleep(interval)
        elapsed += interval
    return False


# ------------------ Generate Animation with retry + wait ------------------
async def generate_new_animation(user_input: str, max_retries: int = 3, wait_for_file_secs: float = 30.0):
    loading_msg = await cl.Message(content="⏳ Generating animation...").send()
    stop_event = asyncio.Event()
    asyncio.create_task(animate_loading(loading_msg, "⏳ Working", stop_event))

    attempt = 0
    data = None
    while attempt < max_retries:
        attempt += 1
        try:
            resp = requests.post(
                f"{BACKEND_URL}/generate_manim",
                json={"text": user_input},
                timeout=6000
            )
            # Guard against non-JSON error text
            try:
                data = resp.json()
            except Exception:
                data = {"error": resp.text}

            if resp.status_code == 200 and "video_url" in data:
                # Verify backend is serving the video (use URL)
                video_url = f"{BACKEND_URL}{data['video_url']}"
                available = await wait_for_video_url(video_url, total_wait=wait_for_file_secs)
                if available:
                    break  # success
                else:
                    await cl.Message(content=f"⚠️ Attempt {attempt}: video not available yet, will retry.").send()
                    data = None
            else:
                await cl.Message(content=f"⚠️ Attempt {attempt} failed: {data.get('error', resp.text)}").send()

        except Exception as e:
            await cl.Message(content=f"⚠️ Attempt {attempt} exception: {e}").send()

        # exponential-ish backoff to reduce pressure on backend
        backoff = min(2 ** (attempt - 1), 8)
        await asyncio.sleep(backoff)

    stop_event.set()
    await asyncio.sleep(0.3)

    if not data or "video_url" not in data:
        loading_msg.content = f"❌ Failed to generate animation after {max_retries} attempts."
        await loading_msg.update()
        return

    # Normal flow when successful
    video_url = f"{BACKEND_URL}{data['video_url']}"
    video_name = os.path.basename(data["video_url"])
    task_id = data["task_id"]
    question = data["question"]
    answer = data.get("answer", "🤔 (not provided)")

    loading_msg.content = "✅ Animation ready!"
    await loading_msg.update()

    # Use URL-based video playback (robust)
    await cl.Message(
        content=f"Here is your animation 🎥 ({video_name})",
        elements=[cl.Video(name=video_name, url=video_url)]
    ).send()

    await cl.Message(
        content=f"📝 **Quiz Time!**\n{question}\n\n👉 Reply with your answer."
    ).send()

    pending_tasks[task_id] = {
        "question": question,
        "answer": answer,
        "video_url": video_url,
        "awaiting_answer": True,
        "concept": user_input,
    }

    history_cache.append({
        "text": user_input,
        "video_url": video_url,
        "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    })
    if len(history_cache) > 10:
        history_cache.pop(0)


# ------------------ Check Answer with Retry (uses URL & wait) ------------------
async def check_user_answer(task_id: str, user_answer: str, max_retries: int = 3, wait_for_file_secs: float = 30.0):
    task = pending_tasks.get(task_id)
    if not task:
        await cl.Message(content="⚠️ Task not found. Try again.").send()
        return

    correct_answer = str(task["answer"]).strip()
    user_answer_clean = user_answer.strip().lower()
    similarity = fuzz.partial_ratio(user_answer_clean, correct_answer.lower())

    if similarity >= 70:
        await cl.Message(content="✅ Correct! Well done!").send()
        pending_tasks.pop(task_id, None)
        return

    await cl.Message(content="❌ That’s not correct. Let’s try again with a new video...").send()

    attempt = 0
    data = None
    while attempt < max_retries:
        attempt += 1
        try:
            resp = requests.post(
                f"{BACKEND_URL}/generate_manim",
                json={"text": task["question"]},
                timeout=6000
            )
            try:
                data = resp.json()
            except Exception:
                data = {"error": resp.text}

            if resp.status_code == 200 and "video_url" in data:
                video_url = f"{BACKEND_URL}{data['video_url']}"
                available = await wait_for_video_url(video_url, total_wait=wait_for_file_secs)
                if available:
                    break
                else:
                    await cl.Message(content=f"⚠️ Retry {attempt}: new video not available yet, will retry.").send()
                    data = None
            else:
                await cl.Message(content=f"⚠️ Retry {attempt} failed: {data.get('error', resp.text)}").send()

        except Exception as e:
            await cl.Message(content=f"⚠️ Retry {attempt} exception: {e}").send()

        backoff = min(2 ** (attempt - 1), 8)
        await asyncio.sleep(backoff)

    if not data or "video_url" not in data:
        await cl.Message(content=f"❌ Failed to generate new video after {max_retries} retries.").send()
        return

    video_name = os.path.basename(data["video_url"])
    video_url = f"{BACKEND_URL}{data['video_url']}"
    new_task_id = data["task_id"]
    question = data["question"]
    answer = data.get("answer", "🤔 (not provided)")

    await cl.Message(
        content=f"Here’s your new video 🎥 ({video_name})",
        elements=[cl.Video(name=video_name, url=video_url)]
    ).send()

    await cl.Message(
        content=f"📝 **Quiz Time!**\n{question}\n\n👉 Reply with your answer."
    ).send()

    pending_tasks[new_task_id] = {
        "question": question,
        "answer": answer,
        "video_url": video_url,
        "awaiting_answer": True,
        "concept": task["question"],
    }
    pending_tasks.pop(task_id, None)
