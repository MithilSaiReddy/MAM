from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import requests
import subprocess
import os
import logging
import uuid

logger = logging.getLogger("uvicorn.error")

app = FastAPI()

# ------------------ CORS ------------------
origins = ["*"]  # ⚠️ allow all for hackathon, restrict in prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ CONFIG ------------------
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "8MCQ1qpqvudUKeSWPzZr5HR7CV8e5IP5")
MISTRAL_MODEL_ID = "mistral-medium-latest"

QUERY_FOLDER = "queries"
SINGLE_FILE = os.path.join(QUERY_FOLDER, "latest.py")
os.makedirs(QUERY_FOLDER, exist_ok=True)

VIDEO_OUTPUT_DIR = os.path.join("media", "videos", "latest", "480p15")
os.makedirs(VIDEO_OUTPUT_DIR, exist_ok=True)

# ------------------ DATA MODEL ------------------
class Query(BaseModel):
    text: str

# ------------------ HELPERS ------------------
def clean_code(code: str) -> str:
    """Remove markdown fences and whitespace."""
    if not isinstance(code, str):
        return ""
    code = code.replace("```python", "").replace("```", "")
    code = code.replace("```py", "")
    return code.strip()

def generate_mistral_code(prompt: str) -> str:
    """Call the Mistral API to turn text into Manim code."""
    if not MISTRAL_API_KEY:
        raise RuntimeError("MISTRAL_API_KEY environment variable is not set")

    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": MISTRAL_MODEL_ID, "messages": [{"role": "user", "content": prompt}]}

    resp = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        json=payload,
        headers=headers,
        timeout=60,
    )
    if resp.status_code != 200:
        raise Exception(f"Mistral API error: {resp.status_code} {resp.text}")

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        return data.get("output", "") or str(data)

def auto_run_manim(file_path: str, task_id: str) -> str:
    """Run Manim and return output video path with a unique name."""
    try:
        # Force media_dir so output path is predictable
        subprocess.run([
            "manim",
            "-ql",
            "--media_dir", "media",
            file_path,
            "GeneratedScene"
        ], check=True)

        # Default manim output (known location)
        default_path = os.path.join("media", "videos", "latest", "480p15", "GeneratedScene.mp4")
        if not os.path.exists(default_path):
            logger.error("Manim did not produce expected file at %s", default_path)
            return ""

        # Move/rename to unique filename
        unique_name = f"GeneratedScene_{task_id}.mp4"
        final_path = os.path.join(VIDEO_OUTPUT_DIR, unique_name)
        os.rename(default_path, final_path)
        return final_path

    except subprocess.CalledProcessError as e:
        logger.exception("Manim failed: %s", e)
        return ""

# ------------------ API ROUTES ------------------
@app.post("/generate_manim")
def generate_manim(query: Query):
    """Generate a Manim script, run it, and return the video URL."""
    try:
        prompt = f"""
You are an expert Python programmer and Manim developer.
Convert the following theory or question into a complete, runnable Manim Community v0.16+ script.
- Include all necessary imports.
- Define a Scene class named GeneratedScene.
- Code must be directly runnable with `manim -ql <filename>.py`.
- Only provide code, no explanations.
- Do NOT include any markdown fences.
- Make animation visually appealing with smooth transitions
- Use contrasting colors for shapes
- Duration ~20-30 seconds
- Only provide runnable code
 - Include **smooth transitions** (Create, FadeIn, Transform, etc.).
Input:
{query.text}
"""

        # 1. Generate code from Mistral
        generated_code = clean_code(generate_mistral_code(prompt))
        if not generated_code:
            raise Exception("Mistral returned empty code.")

        # 2. Save script to disk
        with open(SINGLE_FILE, "w", encoding="utf-8") as f:
            f.write(generated_code)

        # 3. Generate unique ID for this run
        task_id = str(uuid.uuid4())[:8]

        # 4. Run Manim and get video path
        video_path = auto_run_manim(SINGLE_FILE, task_id)
        if not video_path or not os.path.exists(video_path):
            raise Exception("Manim did not produce a video.")

        # 5. Return URL to frontend
        video_url = f"/video/{os.path.basename(video_path)}"
        return {"saved_as": SINGLE_FILE, "video_url": video_url}

    except Exception as e:
        logger.exception("Error in /generate_manim: %s", e)
        return {"error": str(e)}

@app.get("/video/{filename}")
def get_video(filename: str):
    """Serve generated video file."""
    video_path = os.path.join(VIDEO_OUTPUT_DIR, filename)
    if not os.path.exists(video_path):
        logger.error(f"Video not found at: {video_path}")
        return {"error": "Video not found"}
    return FileResponse(video_path, media_type="video/mp4")
