from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import requests
import subprocess
import os
import logging
import uuid
import json
import re
from typing import Optional, Tuple

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

# ------------------ STATE ------------------
active_tasks = {}  # task_id -> {"question": str, "answer": str, "concept": str}

# ------------------ DATA MODELS ------------------
class Query(BaseModel):
    text: str

class Answer(BaseModel):
    task_id: str
    user_answer: str

# ------------------ HELPERS ------------------
def clean_code(text: str) -> str:
    """
    Remove surrounding markdown code fences (```json, ```python, etc.) and trim.
    Leaves inner content intact.
    """
    if not isinstance(text, str):
        return ""
    s = text.strip()

    # Remove a leading fence like ```json\n or ```\n or ```python\n
    s = re.sub(r'^\s*```[^\n]*\n', '', s, flags=re.DOTALL)
    # Remove a trailing fence like \n``` or ```\n
    s = re.sub(r'\n?```+\s*$', '', s, flags=re.DOTALL)

    # Also remove common inline fence tokens if present
    s = s.replace("```python", "").replace("```py", "").replace("```json", "").replace("```JSON", "")
    return s.strip()


def extract_first_json_object(s: str) -> Optional[str]:
    """
    Find and return the first balanced JSON object substring in s (including braces),
    ignoring braces that occur inside string literals. Returns None if not found.
    """
    if not isinstance(s, str):
        return None

    start = s.find('{')
    if start == -1:
        return None

    depth = 0
    in_str = False
    escape = False

    # iterate from first '{'
    for i, ch in enumerate(s[start:], start):
        if ch == '"' and not escape:
            in_str = not in_str
        # Handle escape char (so escaped quotes/braces are not treated specially)
        if ch == '\\' and not escape:
            escape = True
            continue
        else:
            escape = False

        if in_str:
            continue

        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                # return substring from first '{' to this '}'
                return s[start:i+1]

    # no balanced object found
    return None


def parse_mistral_response(raw_resp: str, user_input: str) -> Tuple[str, str]:
    """
    Robust parsing of model output:
    1) clean fences
    2) extract first {...} block
    3) try json.loads
    4) if that fails, try to repair stray backslashes
    5) if that fails, extract "question" and "answer" with regex + unicode-escape decode
    """
    logger.info("Raw Mistral response: %s", raw_resp)
    cleaned = clean_code(raw_resp)
    logger.info("After clean_code(): %s", cleaned[:400])

    json_sub = extract_first_json_object(cleaned)
    question = ""
    answer = ""

    if not json_sub:
        logger.warning("No JSON object found after cleaning.")
    else:
        logger.info("Extracted JSON substring (repr start): %s", repr(json_sub[:400]))

        # 1) try strict parse
        try:
            data = json.loads(json_sub)
            logger.info("Parsed JSON object (strict): %s", data)
            question = (data.get("question") or "").strip()
            answer = (data.get("answer") or "").strip()
        except json.JSONDecodeError as e:
            logger.warning("json.loads failed on extracted JSON: %s", e)

            # 2) Attempt to escape stray backslashes that are not part of valid JSON escapes.
            #    Valid escapes: " \\ \/ \b \f \n \r \t \u
            repaired = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', json_sub)
            logger.info("Attempting json.loads after backslash-repair (repr start): %s", repr(repaired[:400]))
            try:
                data = json.loads(repaired)
                logger.info("Parsed JSON object after backslash-repair: %s", data)
                question = (data.get("question") or "").strip()
                answer = (data.get("answer") or "").strip()
            except json.JSONDecodeError as e2:
                logger.warning("json.loads STILL failed after backslash repair: %s", e2)

                # 3) Last-resort: tolerant regex extraction for question & answer
                # This will capture string contents even when JSON is malformed.
                def _extract_field(s: str, name: str) -> str:
                    # capture minimal (non-greedy) content between quotes, allow escaped quotes
                    m = re.search(rf'"{re.escape(name)}"\s*:\s*"((?:\\.|[^"\\])*)"', s, flags=re.DOTALL)
                    if not m:
                        # try single-quoted (rare)
                        m = re.search(rf"'{re.escape(name)}'\s*:\s*'((?:\\.|[^'\\])*)'", s, flags=re.DOTALL)
                    if not m:
                        return ""
                    raw_val = m.group(1)
                    try:
                        # decode common escapes (\n, \t, \uXXXX, \\, \")
                        return bytes(raw_val, "utf-8").decode("unicode_escape")
                    except Exception:
                        # best-effort: replace escaped quotes and backslashes
                        return raw_val.replace(r'\"', '"').replace(r"\\", "\\")

                q_try = _extract_field(json_sub, "question")
                a_try = _extract_field(json_sub, "answer")
                if q_try or a_try:
                    logger.info("Regex-extracted fields -> question len:%d, answer len:%d", len(q_try), len(a_try))
                    question = q_try.strip()
                    answer = a_try.strip()
                else:
                    logger.error("Failed to extract question/answer by regex from JSON substring.")

    # Safety fallback if parsing produced empty question
    if not question:
        logger.info("Parsed question empty — using fallback based on user_input: %s", user_input)
        if "?" in user_input:
            question = "Can you solve a similar problem?"
            answer = "See original input"
        else:
            question = f"What is one key fact about {user_input}?"
            answer = user_input

    logger.info("Final question/answer -> Q: %r, A: %r", question, answer)
    return question, answer

def generate_mistral_code(prompt: str) -> str:
    """Call the Mistral API."""
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
        subprocess.run([
            "manim",
            "-ql",
            "--media_dir", "media",
            file_path,
            "GeneratedScene"
        ], check=True)

        default_path = os.path.join("media", "videos", "latest", "480p15", "GeneratedScene.mp4")
        if not os.path.exists(default_path):
            logger.error("Manim did not produce expected file at %s", default_path)
            return ""

        unique_name = f"GeneratedScene_{task_id}.mp4"
        final_path = os.path.join(VIDEO_OUTPUT_DIR, unique_name)
        os.rename(default_path, final_path)
        return final_path

    except subprocess.CalledProcessError as e:
        logger.exception("Manim failed: %s", e)
        return ""


def generate_question_and_answer(user_input: str) -> Tuple[str, str]:
    """Generate a quiz question & answer depending on whether the user gave a concept or a question."""
    prompt = f"""
The student gave this input:
"{user_input}"

Decide:
1. If the input looks like a **concept** (e.g., "Pythagoras theorem", "Photosynthesis"),
   → Generate a specific quiz question testing that concept.
   Example: Input "Pythagoras theorem" → Question: "What is the formula relating the sides of a right triangle?"

2. If the input looks like a **question** (e.g., "What is 2+2?", "Why is the sky blue?"),
   → Generate a **similar type of question** (same topic or difficulty).
   Example: Input "What is 2+2?" → Question: "What is 3+5?"

Always provide:
- A clear **question**
- Its **correct short answer**

Respond ONLY in valid JSON:
{{
  "question": "string",
  "answer": "string"
}}
"""

    raw_resp = generate_mistral_code(prompt)
    # Parse robustly (handles fenced code + balanced braces + escaped characters)
    question, answer = parse_mistral_response(raw_resp, user_input)
    return question, answer


# ------------------ API ROUTES ------------------
@app.post("/generate_manim")
def generate_manim(query: Query):
    """Generate a Manim script, run it, return video + question."""
    try:
        # 1. Generate code
        generated_code = clean_code(generate_mistral_code(f"""
You are an expert senior Python programmer and senior Manim developer.
Convert the following theory or question into a complete, runnable Manim Community v0.16+ script
that can be understood evenn by a 5 years old.
- Use colorful colors and use simple shapes as graphics.
- Include all necessary imports.
- Define a Scene class named GeneratedScene.
- Code must be directly runnable with `manim -ql <filename>.py`.
- Only provide code, no explanations.
- Do NOT include any markdown fences.
- Make animation visually appealing with smooth transitions.
- Use contrasting colors for shapes.
- Duration ~20-30 seconds.
- Include smooth transitions (Create, FadeIn, Transform, etc.) when required.
- Donot include any images create all by your self if possible.
- Maintain aspect ration for 640x480 so keep all the things in that it self.
- Donot overlap over each other.
Input:
{query.text}
"""))
        if not generated_code:
            raise Exception("Mistral returned empty code.")

        with open(SINGLE_FILE, "w", encoding="utf-8") as f:
            f.write(generated_code)

        # 2. Run Manim
        task_id = str(uuid.uuid4())[:8]
        video_path = auto_run_manim(SINGLE_FILE, task_id)
        if not video_path or not os.path.exists(video_path):
            raise Exception("Manim did not produce a video.")

        # 3. Generate a question
        question, answer = generate_question_and_answer(query.text)

        # 4. Store task
        active_tasks[task_id] = {"question": question, "answer": answer, "concept": query.text}

        payload = {
            "task_id": task_id,
            "video_url": f"/video/{os.path.basename(video_path)}",
            "question": question,
            "answer": (answer or "").strip(),   # <-- return the answer explicitly
        }
        logger.info("Outgoing /generate_manim response: %s", payload)  # debug log
        return payload

    except Exception as e:
        logger.exception("Error in /generate_manim: %s", e)
        return {"error": str(e)}


@app.post("/check_answer")
def check_answer(ans: Answer):
    """
    Check user answer.
    - If correct → return success message.
    - If wrong → generate simplified "baby" animation using the same pipeline but lightweight.
    """
    task = active_tasks.get(ans.task_id)
    if not task:
        return {"error": "Task not found"}

    correct = task["answer"].strip().lower()
    user = ans.user_answer.strip().lower()

    if user == correct:
        # Correct answer → remove task
        active_tasks.pop(ans.task_id, None)
        return {"result": "✅ Correct! Well done!"}
    else:
        # Wrong answer → generate simplified animation
        concept = task["concept"]

        # Create simplified Manim prompt
        prompt = f"""
You are an expert Python programmer and Manim developer.
Create a simplified, fully runnable Manim Community v0.16+ animation that explains this concept for a beginner:

Concept: {concept}

Requirements:
- Duration ~10–15 seconds
- Only simple shapes (Circle, Square, etc.)
- Smooth but minimal transitions (Create, FadeIn)
- Bright colors, clear visuals
- No complex animations, images, or camera movement
- Class name: GeneratedScene
- Include all necessary imports
- Only provide runnable code, no markdown fences
"""

        try:
            # Generate simplified code from Mistral
            simplified_code = clean_code(generate_mistral_code(prompt))
            if not simplified_code:
                return {"result": "❌ Wrong! Failed to generate simplified animation."}

            # Save code to file
            with open(SINGLE_FILE, "w", encoding="utf-8") as f:
                f.write(simplified_code)

            # Generate unique task id for baby animation
            baby_id = str(uuid.uuid4())[:8]
            video_path = auto_run_manim(SINGLE_FILE, baby_id)

            if not video_path or not os.path.exists(video_path):
                return {"result": "❌ Wrong! AI-generated baby animation failed."}

            # Remove original task after generating baby animation
            active_tasks.pop(ans.task_id, None)

            return {
                "result": "❌ Wrong! Here’s a simpler animation explanation.",
                "video_url": f"/video/{os.path.basename(video_path)}"
            }

        except Exception as e:
            return {"result": f"❌ Error generating baby animation: {e}"}


@app.get("/video/{filename}")
def get_video(filename: str):
    """Serve generated video file."""
    video_path = os.path.join(VIDEO_OUTPUT_DIR, filename)
    if not os.path.exists(video_path):
        logger.error(f"Video not found at: {video_path}")
        return {"error": "Video not found"}
    return FileResponse(video_path, media_type="video/mp4")


