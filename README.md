# MAM - Mathematical Animations using Manim

An AI-powered web application that generates interactive mathematical and scientific animations using Manim. Students input concepts or questions and receive dynamically generated animated explanations with an adaptive learning quiz system.

## 🚀 Demo

**Live Demo**: [https://mam.mithil.hackclub.app/](https://mam.mithil.hackclub.app/)

---

## 🎯 Problem Statement

Our application addresses three critical challenges in mathematics education:

1. **Visual Learning Gap**: Students struggle to understand mathematical concepts from text alone
2. **Scalability Issues**: Individual explanation to every student is difficult in traditional education systems  
3. **Resource Intensive**: Teachers spend excessive time creating visual teaching materials and aids

---

## ✨ Features

- 🎯 **AI-Powered Animation Generation**: Uses GPT-4 to create custom Manim scripts
- 🎥 **Real-time Video Rendering**: Dynamic mathematical animation creation
- 🧠 **Interactive Quiz System**: Adaptive learning with immediate feedback
- 🔄 **Smart Learning Loop**: Generates explanatory videos for incorrect answers
- 💬 **Chat Interface**: User-friendly conversation-based interaction
- 📚 **Animation History**: Track and revisit previous animations
- ⚡ **Fast API Backend**: High-performance server with automatic retries

---

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   AI Services   │
│   (Chainlit)    │◄──►│   (FastAPI)     │◄──►│    (GPT-4)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Chat Interface  │    │ Video Processing│    │ Code Generation │
│ History Tracking│    │ Session Mgmt    │    │ Quiz Generation │
│ Fuzzy Matching  │    │ File Management │    │ Answer Validation│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Application Flow

1. **User Input**: Mathematical concept or question submission
2. **AI Processing**: GPT-4 generates custom Manim animation code
3. **Video Rendering**: Manim engine creates mathematical animation
4. **Interactive Assessment**: System generates contextual quiz questions
5. **Adaptive Learning**: 
   - ✅ Correct answers → Success feedback
   - ❌ Wrong answers → Simplified explanatory video + retry loop

### Technology Stack

- **AI Model**: OpenAI GPT-4 (Code generation, quiz creation)
- **Animation Engine**: Manim Community Edition v0.16+
- **Backend**: FastAPI (Python)
- **Frontend**: Chainlit (Chat interface)
- **Answer Matching**: RapidFuzz (Fuzzy string matching)
- **Video Processing**: FFmpeg (via Manim)

---

## 📋 Prerequisites

- **Python 3.9+**
- **Manim Community Edition v0.16+**
- **OpenAI API key** with GPT-4 access
- **System Requirements**:
  - 4GB+ RAM (8GB+ recommended)
  - 2GB+ free disk space
  - Stable internet connection

---

## 🛠️ Setup Instructions

### 1. Repository Setup
```bash
git clone https://github.com/MithilSaiReddy/TTM
cd TTM
```

### 2. Environment Configuration
```bash
# Create virtual environment
python3 -m venv venv

# Activate environment
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows
```

### 3. Dependencies Installation
```bash
pip install -r requirements.txt
```

### 4. API Key Configuration
Create a `.env` file in the project root:
```bash
OPENAI_API_KEY="your-openai-api-key-here"
```

### 5. Backend Server Launch
```bash
uvicorn app:app --reload
```

### 6. Frontend Interface Launch
Open a new terminal and run:
```bash
chainlit run frontend.py
```

### 7. Access Application
Navigate to the Chainlit interface (typically `http://localhost:8000`)

---

## 🎯 Usage Guide

### Getting Started
1. Open the chat interface in your browser
2. Enter a mathematical concept or question
3. Watch the AI-generated animation
4. Complete the interactive quiz
5. Receive adaptive feedback and explanations

### Example Inputs
```
"Pythagorean theorem"
"Show me quadratic equations"
"Explain the area of rectangle length 5m breadth is 2m"
"Demonstrate calculus derivatives"
```

### Special Commands
- `history` - View recent animation history

---

## 🔌 API Endpoints

| Endpoint | Method | Description | Parameters |
|----------|--------|-------------|------------|
| `/generate_manim` | POST | Generate animation from user input | `{"user_input": "concept"}` |
| `/check_answer` | POST | Validate quiz answers | `{"answer": "response", "question": "quiz"}` |
| `/video/{filename}` | GET | Serve generated video files | `filename` (path parameter) |

---

## 📁 Project Structure

```
TTM/
├── app.py                 # FastAPI backend server
├── frontend.py            # Chainlit chat interface
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── .env                  # Environment variables (create)
├── media/
│   └── videos/
│       └── latest/
│           └── 480p15/   # Generated video files
└── queries/
    └── latest.py         # Temporary Manim scripts
```

---

## 📊 Models & Data Used

### AI Models
- **Primary Model**: OpenAI GPT-4
  - **License**: Commercial API (requires subscription)
  - **Usage**: Manim code generation, quiz question creation, answer validation
  - **Rate Limits**: Subject to OpenAI API limitations

### Animation Framework
- **Manim Community Edition**
  - **License**: MIT License
  - **Version**: v0.16+
  - **Usage**: Mathematical animation rendering and video generation

### Supporting Libraries
- **FastAPI**: MIT License
- **Chainlit**: Apache 2.0 License  
- **RapidFuzz**: MIT License
- **Python Standard Library**: Python Software Foundation License

### Data Processing
- **No persistent data storage**: All sessions are temporary
- **Video files**: Automatically generated and managed locally
- **User inputs**: Processed in real-time, not stored permanently

---

## ⚠️ Known Limitations & Risks

### Technical Limitations
- **CORS Configuration**: Currently allows all origins (⚠️ requires restriction for production)
- **Complex Animations**: May require extended generation times (30+ seconds)
- **Device Compatibility**: Optimized for desktop browsers; limited mobile support
- **Answer Recognition**: Fuzzy matching may occasionally produce false positives/negatives
- **Resource Intensive**: CPU-intensive video rendering may affect system performance

### Operational Risks
- **API Dependency**: Requires stable internet connection for OpenAI API calls
- **Rate Limiting**: Subject to OpenAI API usage limits and costs
- **Storage Growth**: Video files accumulate over time (automatic cleanup recommended)
- **Concurrent Users**: Limited by server resources and API quotas

### Security Considerations
- **API Key Protection**: Ensure secure storage of OpenAI API keys
- **Input Validation**: User inputs are processed by AI (potential for unexpected outputs)
- **File Management**: Temporary files require proper cleanup mechanisms

### Educational Limitations
- **Content Accuracy**: AI-generated explanations should be verified for mathematical correctness
- **Learning Assessment**: Quiz system provides basic evaluation (not comprehensive assessment)
- **Language Support**: Currently optimized for English mathematical terminology

---

## 💼 Value Proposition

### For Educational Institutions
- **Automated Content Creation**: Reduces teacher workload in material preparation
- **Interactive Learning**: Enhances student engagement through visual explanations
- **Adaptive Assessment**: Provides personalized learning experiences
- **Scalable Solution**: Handles multiple students simultaneously

### Go-to-Market Strategy
- **Target Customers**: Schools, colleges, online learning platforms, educational apps
- **Revenue Model**: B2B subscription/licensing for integration into existing ecosystems
- **Distribution**: Direct sales and partnerships with educational institutions
- **Integration**: API-based integration into existing school/learning applications

---

## 🛣️ Future Roadmap

1. **Agentic Approach**: Enhanced AI decision-making capabilities
2. **API Expansion**: Comprehensive API for third-party integrations  
3. **Fine-Tuned LLM**: Custom-trained models for mathematical content
4. **Audio Integration**: Voice explanations and audio-visual learning
5. **Advanced Analytics**: Student performance tracking and insights
6. **Multi-language Support**: Localization for global education markets

---

## 🔧 Troubleshooting

### Common Issues

**API Key Errors**
```bash
export OPENAI_API_KEY="your-api-key-here"
# OR add to .env file
```

**Manim Installation Issues**
```bash
pip install manim
# OR for conda users:
conda install manim -c conda-forge
```

**Port Conflicts**
```bash
uvicorn app:app --port 8001  # Use alternative port
```

**Video Loading Problems**
- Verify backend server is running
- Check video files exist in `media/videos/latest/480p15/`
- Ensure stable internet connection
- Clear browser cache

**Quiz Recognition Issues**
- Use simpler mathematical terminology
- Check spelling and mathematical notation
- Try rephrasing answers
- Use standard mathematical expressions

---

## 🤝 Contributing

We welcome contributions to improve MAM! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines for Python code
- Include comprehensive docstrings and comments
- Test new features thoroughly before submission
- Update documentation for any new functionality

---

## 👥 Team & Contacts

### Core Development Team

**Mithil Sai** - Frontend & Backend Developer  
📧 [eaglebelt@proton.me](mailto:eaglebelt@proton.me)  
🔗 GitHub: [MithilSaiReddy](https://github.com/MithilSaiReddy)  
🎯 **Responsibilities**: User interface design, API development, system architecture

**Harshavardhan** - Backend Developer & AI Fine-tuner  
📧 [harsha19821983@gmail.com](mailto:harsha19821983@gmail.com)  
🎯 **Responsibilities**: AI model integration, backend optimization, machine learning pipeline

### Contact Information
- **Technical Support**: Create an issue on GitHub
- **Business Inquiries**: Contact team leads directly via email
- **Demo Requests**: Schedule via team contacts

---

## 📄 License

This project is released under the **MIT License**. See [LICENSE](LICENSE) file for details.

### Third-Party Licenses
- OpenAI GPT-4: Commercial API License
- Manim Community: MIT License  
- FastAPI: MIT License
- Chainlit: Apache 2.0 License

---

## 🙏 Acknowledgments

- **Manim Community** for the exceptional mathematical animation framework
- **OpenAI** for providing powerful GPT-4 API capabilities
- **FastAPI** and **Chainlit** teams for robust development frameworks
- **Educational Technology Community** for inspiration and feedback

---

## 📈 Project Status

**Current Version**: 1.0.0  
**Development Status**: Active  
**Last Updated**: August 2025  
**Demo Status**: Live at [mam.mithil.hackclub.app](https://mam.mithil.hackclub.app/)

---

**⭐ If this project helps your learning or teaching, please give it a star!**

**📊 README Views: Please increment by 1 - Current count: 2**

---

*Built with ❤️ for transforming mathematical education through AI and interactive visual learning*
