import os
import requests
import asyncio
import chainlit as cl
from rapidfuzz import fuzz
from datetime import datetime

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


# ------------------ Generate Animation ------------------
async def generate_new_animation(user_input: str):
    loading_msg = await cl.Message(content="⏳ Generating animation...").send()
    stop_event = asyncio.Event()
    asyncio.create_task(animate_loading(loading_msg, "⏳ Working", stop_event))

    try:
        resp = requests.post(
            f"{BACKEND_URL}/generate_manim", json={"text": user_input}, timeout=6000
        )
        data = resp.json()

        stop_event.set()
        await asyncio.sleep(0.7)

        if resp.status_code != 200 or "error" in data or "video_url" not in data:
            loading_msg.content = f"⚠️ Error: {data.get('error', resp.text)}"
            await loading_msg.update()
            return

        video_url = f"{BACKEND_URL}{data['video_url']}"
        video_name = os.path.basename(data["video_url"])
        task_id = data["task_id"]
        question = data["question"]
        answer = data.get("answer", "🤔 (not provided)")  # store internally only

        loading_msg.content = "✅ Animation ready!"
        await loading_msg.update()

        # Show video
        await cl.Message(
            content=f"Here is your animation 🎥 ({video_name})",
            elements=[cl.Video(name=video_name, url=video_url)]
        ).send()

        # Show question (❌ no answer revealed)
        await cl.Message(
            content=f"📝 **Quiz Time!**\n{question}\n\n👉 Reply with your answer."
        ).send()

        # Track pending task
        pending_tasks[task_id] = {
            "question": question,
            "answer": answer,   # stored, but not shown
            "video_url": video_url,
            "awaiting_answer": True,
            "concept": user_input,
        }

        # Add to history
        history_cache.append({
            "text": user_input,
            "video_url": video_url,
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        })
        if len(history_cache) > 10:
            history_cache.pop(0)

    except Exception as e:
        stop_event.set()
        loading_msg.content = f"⚠️ Exception: {e}"
        await loading_msg.update()


async def check_user_answer(task_id: str, user_answer: str):
    task = pending_tasks.get(task_id)
    if not task:
        await cl.Message(content="⚠️ Task not found. Try again.").send()
        return

    correct_answer = str(task["answer"]).strip()
    user_answer_clean = user_answer.strip().lower()
    similarity = fuzz.partial_ratio(user_answer_clean, correct_answer.lower())

    if similarity >= 70:
        # ✅ Correct
        await cl.Message(content="✅ Correct! Well done!").send()
        pending_tasks.pop(task_id, None)
    else:
        # ❌ Wrong → resend the same quiz question to backend as new input
        await cl.Message(content="❌ That’s not correct. Let’s try again with a new video...").send()

        try:
            resp = requests.post(
                f"{BACKEND_URL}/generate_manim",
                json={"text": task["question"]},  # send quiz question itself
                timeout=6000
            )
            data = resp.json()

            if "error" in data or "video_url" not in data:
                await cl.Message(content=f"⚠️ Error: {data.get('error', resp.text)}").send()
                return

            # Show new video using path, not url
            video_name = os.path.basename(data["video_url"])
            video_path = os.path.join("media", "videos", "latest", "480p15", video_name)

            new_task_id = data["task_id"]
            question = data["question"]
            answer = data.get("answer", "🤔 (not provided)")

            # Wait until video file exists
            for _ in range(30):  # wait max 30*0.5 = 15 sec
                if os.path.exists(video_path):
                    break
                await asyncio.sleep(0.5)

            await cl.Message(
                content=f"Here’s your new video 🎥 ({video_name})",
                elements=[cl.Video(name=video_name, path=video_path)]
            ).send()

            # Ask the new quiz question
            await cl.Message(
                content=f"📝 **Quiz Time!**\n{question}\n\n👉 Reply with your answer."
            ).send()

            # Track pending task
            pending_tasks[new_task_id] = {
                "question": question,
                "answer": answer,
                "video_url": video_path,
                "awaiting_answer": True,
                "concept": task["question"],  # original quiz question is concept
            }

            # Remove old task
            pending_tasks.pop(task_id, None)

        except Exception as e:
            await cl.Message(content=f"⚠️ Error generating new video: {e}").send()

