import os
import requests
import asyncio
import chainlit as cl
from datetime import datetime

BACKEND_URL = "http://localhost:8000/generate_manim"
history_cache = []


# ------------------ Chat Start ------------------
@cl.on_chat_start
async def start_chat():
    await cl.Message(
        content="👋 Hi! Send me a math question and I'll generate a Manim animation.\n\n"
                "Type `history` anytime to see recent animations in a neat format."
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
        # Nicely formatted card-like message
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

    # 1) Show history if user types 'history'
    if user_input.lower() == "history":
        await display_history()
        return

    # 2) Send initial loading message
    loading_msg = await cl.Message(content="⏳ Generating animation...").send()
    stop_event = asyncio.Event()
    asyncio.create_task(animate_loading(loading_msg, "⏳ Working", stop_event))

    try:
        resp = requests.post(BACKEND_URL, json={"text": user_input}, timeout=600)
        data = resp.json()

        stop_event.set()
        await asyncio.sleep(0.7)

        if resp.status_code != 200 or "error" in data or "video_url" not in data:
            loading_msg.content = f"⚠️ Error: {data.get('error', resp.text)}"
            await loading_msg.update()
            return

        video_url = f"http://localhost:8000{data['video_url']}"
        video_name = os.path.basename(data["video_url"])
        loading_msg.content = "✅ Animation ready!"
        await loading_msg.update()

        # Show video
        await cl.Message(
            content=f"Here is your animation 🎥 (`{video_name}`)",
            elements=[cl.Video(name=video_name, url=video_url)]
        ).send()

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
