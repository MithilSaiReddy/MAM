# Mathematical Animations using Manim

This project is a web application that generates interactive math and science animations using Manim, powered by AI-generated scripts via FastAPI backend and a chat-driven frontend interface. Users input concepts or questions, receive animated explanations, and are quizzed interactively.

---

## Table of Contents
- [Project Overview](#project-overview)
- [Setup Steps](#setup-steps)
- [Architecture Overview](#architecture-overview)
- [Core Components](#core-components)
- [Known Limitations](#known-limitations)
- [Team & Contact](#team--contact)

---

## Project Overview

This app converts user-submitted math or science concepts/questions into dynamic Manim animations, served by a FastAPI backend that generates code using LLMs (OpenAI GPT). The frontend—built with Chainlit—provides a chat interface with animation playback and quizzing capabilities.

---

## Setup Steps

### Prerequisites

- Python 3.9 or higher
- `manim` installed (Manim Community Edition v0.16+)
- [Optional] Virtual environment tool (recommended)

### Installation

1. Clone the repository:
    ```
    git clone https://github.com/MithilSaiReddy/TTM
    cd TTM
    ```

2. Create and activate a Python virtual environment:
    ```
    python3 -m venv venv
    source venv/bin/activate   # Linux/macOS
    venv\Scripts\activate      # Windows
    ```

3. Install backend and frontend dependencies:
    ```
    pip install -r requirements.txt
    ```

4. Set environment variables for API keys:
    - Create a `.env` file or export them directly:
    ```
    export OPENAI_API_KEY="your-openai-api-key"
    ```

5. Run the backend server:
    ```
    uvicorn app:app --reload
    ```

6. Start the frontend chat interface:
    ```
    chainlit run frontend.py
    ```

7. Open the chat UI in your browser (usually `http://localhost:8000` or the address printed by Chainlit).

---

## Architecture Overview

- **Backend:**  
  - FastAPI serves API endpoints  
  - Generates Manim code using OpenAI GPT-4  
  - Runs Manim to create video animations dynamically  
  - Manages active tasks and quiz question/answer logic  
  - Serves generated video files

- **Frontend:**  
  - Built with Chainlit (chat-driven UI framework)  
  - Accepts user input (concept or question)  
  - Shows loading animations, playback videos via URL  
  - Handles quiz answer submissions and feedback  
  - Displays recent animation history

- **Supporting tools:**  
  - `manim` (for generating math/science animations)  
  - `openai` GPT-4 model for AI code generation  
  - `rapidfuzz` for fuzzy matching user quiz answers

---

## Core Components

- **app.py**: Backend FastAPI application  
- **frontend.py**: Chat interface powered by Chainlit  
- **requirements.txt**: Required Python packages including FastAPI, Chainlit, Manim, OpenAI, etc.  
- **media/videos/latest/480p15/**: Storage for generated video files  
- **queries/latest.py**: Temporary storage for dynamically generated Manim scripts

---

## Known Limitations

- The app currently allows all CORS origins (`origins = ["*"]`), which should be restricted in production.  
- Manim rendering may slow on large or complex inputs; GPU acceleration can help.  
- UI primarily designed for desktop browsers; limited mobile support.  
- Quiz answer matching relies on fuzzy matching which may have false positives/negatives.  
- API keys must be kept secure and properly configured.  
- Simplified animations generated on wrong answers may not cover all cases well.  
- The system requires internet access to call OpenAI endpoints.

---

## Team & Contact

- **Mithil** - Frontend, Backend - [eaglebelt@proton.me](mailto:eaglebelt@proton.me)
- **Harsha** - Backend, AI finetuner - [harsha19821983@gmail.com](mailto:harsha19821983@gmail.com)

For questions, bug reports, or contribution requests, please open an issue or contact the team members above.

---

*Thank you for exploring the Mathematical Animations using Manim! Contributions and feedback are welcome.*

**📊 Read Counter: Increase this number by 1 to show how many people have read this README - Current count: 1**

