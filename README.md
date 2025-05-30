# 🧠 Socratic AI Tutor

A **local-first Socratic-style AI tutor** powered by **GPT** and **DSPy**. This project demonstrates how to build an educational AI that guides students through thoughtful questioning rather than just providing direct answers.

## 🎯 Features

- **Socratic Method**: AI asks clarifying questions and provides hints instead of direct answers
- **Subject-Aware**: Supports Math, Physics, Biology, History, and Chemistry
- **Level-Adaptive**: Adjusts responses for Beginner, Intermediate, and Advanced levels
- **Local-First**: Runs entirely on your machine with Docker
- **Modern Stack**: FastAPI backend with DSPy, Next.js frontend with TailwindCSS
- **Modular Design**: Built with DSPy for easy evaluation and improvement

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js       │    │   FastAPI       │    │   OpenAI GPT    │
│   Frontend      │◄──►│   Backend       │◄──►│   via DSPy      │
│   (Port 3000)   │    │   (Port 8000)   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

**Frontend**: Next.js with TailwindCSS - Three-panel layout for subject selection, question input, and AI responses

**Backend**: FastAPI serving DSPy modules with structured Socratic responses

**AI**: OpenAI GPT models accessed through DSPy's declarative interface

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key
- Git

### 1. Clone and Setup

```bash
git clone <repository-url>
cd Socratic-AI-Tutor
```

### 2. Configure Environment

```bash
# Copy environment template
cp env.example .env

# Edit .env and add your OpenAI API key
OPENAI_API_KEY=your_actual_api_key_here
OPENAI_MODEL=gpt-4
```

### 3. Run with Docker

```bash
# Make run script executable (Linux/Mac)
chmod +x run.sh

# Start the backend
./run.sh

# Or start with frontend (if available)
./run.sh --with-frontend
```

### 4. Test the API

```bash
curl -X POST "http://localhost:8000/api/v1/tutor" \
     -H "Content-Type: application/json" \
     -d '{"question":"Why is the sky blue?","subject":"physics","level":"beginner"}'
```

## 📡 API Endpoints

### Main Endpoints

- `POST /api/v1/tutor` - Get Socratic guidance for a question
- `GET /api/v1/health` - Health check
- `GET /api/v1/subjects` - List available subjects
- `GET /api/v1/levels` - List difficulty levels

### Example Request/Response

**Request:**
```json
{
  "question": "Why do we need oxygen?",
  "subject": "biology", 
  "level": "beginner"
}
```

**Response:**
```json
{
  "clarifying_question": "What role do you think oxygen plays in your body's energy?",
  "concept_hint": "Oxygen is crucial in a process called cellular respiration.",
  "feedback": "You're thinking like a scientist already!"
}
```

## 🧩 DSPy Implementation

### Core Signature

```python
class SocraticTutor(dspy.Signature):
    """Respond to students with a clarifying question and helpful hints."""
    
    question: str = dspy.InputField()
    subject: str = dspy.InputField() 
    level: str = dspy.InputField()
    
    clarifying_question: str = dspy.OutputField()
    concept_hint: str = dspy.OutputField()
    feedback: str = dspy.OutputField()
```

### Module Structure

- `SocraticTutorModule`: Main DSPy module using Predict
- `SocraticTutorService`: Service layer handling initialization and responses
- `evaluators.py`: Placeholder for future evaluation modules

## 🎨 Frontend Features

### Three-Panel Layout

1. **Left Panel**: Subject and difficulty level selection
2. **Center Panel**: Question input with real-time validation
3. **Right Panel**: Structured AI responses with visual indicators

### Response Types

- 🤔 **Clarifying Question**: Guides student thinking
- 💡 **Concept Hint**: Provides helpful context without answers
- 🌟 **Encouragement**: Supportive feedback

## 🛠️ Development

### Project Structure

```
Socratic-AI-Tutor/
├── app/                    # FastAPI backend
│   ├── api/               # API routes
│   ├── models.py          # Pydantic models
│   ├── dspy_modules.py    # DSPy signatures and modules
│   ├── config.py          # Configuration
│   ├── evaluators.py      # Future evaluators
│   └── main.py           # FastAPI app
├── frontend/              # Next.js frontend
│   ├── app/              # App router pages
│   ├── package.json      # Dependencies
│   └── tailwind.config.js # Styling
├── docker-compose.yml     # Container orchestration
├── Dockerfile            # Backend container
└── run.sh               # Setup script
```

### Running Locally (Development)

```bash
# Backend only
docker-compose up --build backend

# With frontend
docker-compose --profile frontend up --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🔮 Future Enhancements

### Planned DSPy Features

- **Evaluator Modules**: Assess response clarity, helpfulness, and accuracy
- **Compile-Time Tuning**: Automatic response improvement based on feedback
- **Subject-Specific Context**: Domain knowledge injection for better guidance
- **Multi-Turn Conversations**: Extended Socratic dialogues

### UI/UX Improvements

- **Voice Input/Output**: Speech-to-text and text-to-speech
- **Progress Tracking**: Student learning journey visualization
- **Personalization**: Adaptive difficulty and subject preferences
- **Mobile Responsive**: Optimized mobile experience

## 🧪 Testing

### Manual Testing

1. Start the application with `./run.sh`
2. Visit http://localhost:8000/docs for API documentation
3. Test with the provided curl command
4. Try different subjects and difficulty levels

### Example Questions

- **Physics (Beginner)**: "Why is the sky blue?"
- **Math (Intermediate)**: "How do I solve quadratic equations?"
- **Biology (Advanced)**: "What is the role of mitochondria in cellular respiration?"

## 📚 Technologies

- **Backend**: FastAPI, DSPy, OpenAI, Pydantic, Uvicorn
- **Frontend**: Next.js 14, React 18, TailwindCSS, TypeScript, Axios
- **Infrastructure**: Docker, Docker Compose
- **AI**: OpenAI GPT-3.5/4 via DSPy

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is for educational purposes. Please ensure you comply with OpenAI's usage policies when using their API.

## 🆘 Troubleshooting

### Common Issues

**Backend won't start**: Check your OpenAI API key in `.env`
**Docker issues**: Ensure Docker is running and you have sufficient permissions
**API errors**: Verify your OpenAI API key has sufficient credits

### Getting Help

- Check the logs: `docker-compose logs backend`
- Verify health: `curl http://localhost:8000/api/v1/health`
- Review the API docs: http://localhost:8000/docs

---

Built with ❤️ using DSPy for modular LLM applications