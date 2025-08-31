# Mathematical Animations using Manim

An AI-powered web application that generates interactive mathematical and scientific animations using Manim. Users input concepts or questions, receive dynamically generated animated explanations, and participate in an adaptive learning quiz system.

---

## 🚀 Features

- 🎯 **AI-Powered Animation Generation**: Uses GPT-4 to create custom Manim scripts
- 🎥 **Real-time Video Rendering**: Dynamic mathematical animation creation
- 🧠 **Interactive Quiz System**: Adaptive learning with immediate feedback
- 🔄 **Smart Learning Loop**: Generates explanatory videos for wrong answers
- 💬 **Chat Interface**: User-friendly conversation-based interaction
- 📚 **Animation History**: Track and revisit previous animations
- ⚡ **Fast API Backend**: High-performance server with automatic retries

---

## 📋 Table of Contents

- [Application Flow](#application-flow)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Known Limitations](#known-limitations)
- [Contributing](#contributing)
- [Team](#team)

---

## 🔄 Application Flow

The application follows an intelligent adaptive learning loop:

1. **User Input**: User submits a mathematical concept or question
2. **AI Code Generation**: GPT-4 generates custom Manim animation code  
3. **Video Rendering**: Manim engine creates the mathematical animation
4. **Interactive Quiz**: System generates a related quiz question
5. **Adaptive Response**:
   - ✅ **Correct Answer**: Congratulates user and completes the cycle
   - ❌ **Wrong Answer**: Generates simplified explanatory video and loops back

---

## 📋 Prerequisites

- **Python 3.9+**
- **Manim Community Edition v0.16+**
- **OpenAI API key** with GPT-4 access
- **4GB+ RAM** (8GB+ recommended)
- **2GB+ free disk space**
- **Internet connection** for API calls

---

## 🛠 Installation

### 1. Clone the Repository
git clone https://github.com/MithilSaiReddy/TTM
cd TTM

### 2. Create Virtual Environment
python3 -m venv venv
source venv/bin/activate # Linux/macOS
OR
venv\Scripts\activate # Windows

### 3. Install Dependencies
pip install -r requirements.txt

### 4. Configure Environment Variables
Create a `.env` file or export directly:
export OPENAI_API_KEY="your-openai-api-key-here"


### 5. Start the Backend Server
uvicorn app:app --reload

### 6. Launch Frontend Chat Interface
In a new terminal:
chainlit run frontend.py

### 7. Access the Application
Open your browser to the Chainlit address (typically `http://localhost:8000`)

---

## 🎯 Usage

### Getting Started
1. Open the chat interface in your browser
2. Enter a mathematical concept or question
3. Watch the AI-generated animation
4. Answer the quiz question
5. Receive adaptive feedback

### Example Inputs
"Pythagorean theorem"
"Show me quadratic equations"
"Explain the area of rectanle length 5m bredth is 2 m

### Special Commands
- Type `history` to view recent animations

---

## 🏗 Architecture

### Backend (FastAPI)
- **API Endpoints**: RESTful services for animation generation
- **AI Integration**: GPT-4 powered Manim code generation
- **Video Processing**: Automatic Manim rendering and file management
- **Quiz Logic**: Dynamic question generation and validation
- **Session Management**: Handles concurrent users and retry mechanisms

### Frontend (Chainlit)
- **Chat Interface**: Conversational UI for seamless interaction
- **Real-time Updates**: Loading animations and progress indicators
- **Video Streaming**: Embedded animation viewing
- **History Tracking**: Session-based animation history
- **Fuzzy Matching**: Intelligent answer recognition

### Core Technologies
- **Manim**: Mathematical animation engine
- **OpenAI GPT-4**: AI code generation
- **FastAPI**: Web framework
- **Chainlit**: Chat interface
- **RapidFuzz**: Answer matching

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/generate_manim` | POST | Generate animation from user input |
| `/check_answer` | POST | Validate quiz answers |
| `/video/{filename}` | GET | Serve generated video files |

---

## 📁 Project Structure

TTM/
├── app.py # FastAPI backend
├── frontend.py # Chainlit chat interface
├── requirements.txt # Python dependencies
├── README.md # Project documentation
├── .env # Environment variables
├── media/
│ └── videos/
│ └── latest/
│ └── 480p15/ # Generated videos
└── queries/
└── latest.py # Temporary Manim scripts


---

## 🔧 Troubleshooting

### Common Issues

**"OpenAI API key not found"**
export OPENAI_API_KEY="your-api-key"

**"Manim command not found"**
pip install manim

**"Port already in use"**
uvicorn app:app --port 8001

**"Video not loading"**
- Check backend is running
- Verify video files in media folder
- Check internet connection

**"Quiz answers not recognized"**
- Try rephrasing your answer
- Use simpler terms
- Check for typos

---

## ⚠️ Known Limitations

- CORS currently allows all origins (restrict in production)
- Complex animations may require longer generation times
- Optimized for desktop browsers; limited mobile support
- Quiz matching may have occasional false positives/negatives
- Requires stable internet for OpenAI API calls
- CPU-intensive video rendering

---

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

For bug reports or feature requests, please open a GitHub issue.

---

## 👥 Team

- **Mithil** - Frontend & Backend Developer  
  📧 [eaglebelt@proton.me](mailto:eaglebelt@proton.me)

- **Harsha** - Backend Developer & AI Fine-tuner  
  📧 [harsha19821983@gmail.com](mailto:harsha19821983@gmail.com)

---

## 📄 License

This project is open source. MIT license.

---

## 🙏 Acknowledgments

- **Manim Community** for the amazing animation framework
- **OpenAI** for GPT-4 API
- **FastAPI** and **Chainlit** teams for excellent frameworks

---

**⭐ If you found this project helpful, please give it a star!**

**📊 Read Counter: Increase this number by 1 if you read this README - Current count: 1**

---

*Built with ❤️ for interactive mathematical learning*

