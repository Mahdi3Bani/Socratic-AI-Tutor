# 📚 Socratic AI Tutor – Project Overview

A **local-first Socratic-style tutor** powered by **GPT** and **DSPy**. This project simulates a patient AI tutor that guides students through questions with thoughtful prompting rather than just delivering answers.

---

## 🧠 Purpose

This project is an educational demo to explore **DSPy**, a library for modular and declarative LLM apps. It emphasizes real-world use cases like personalized tutoring.  
It is designed to work **locally** with **Docker** and **FastAPI**, and will eventually include a **Next.js frontend** for user interaction.

---

## 🎯 Goals

✅ Build an AI that responds to student questions with helpful, Socratic-style guidance.  
✅ Use DSPy modules to compose, evaluate, and improve LLM responses.  
✅ Provide context-aware answers based on difficulty level and domain (math, science, etc.).  
✅ Serve the model with a FastAPI backend.  
✅ Create a beautiful frontend in Next.js (WIP).  
✅ Run everything locally using Docker.

---

## 🏗️ Architecture

**Frontend:**  
- Next.js (with TailwindCSS)  
- Students type in questions and receive guided answers.

**Backend:**  
- FastAPI app handling requests to DSPy modules.

**LLM:**  
- OpenAI GPT-3.5/4 via DSPy Predictors.

**DSPy Modules:**  
- Handle reasoning, tutoring format, and feedback loops.

**Evaluator:**  
- Scores responses by clarity, helpfulness, or alignment with a rubric.

**Docker:**  
- Containerized local environment with a single `run.sh` script to set up and run everything.

---

## 📥 Input Format

Each student prompt is wrapped into an `Example` object like this:

```python
dspy.Example(
    question="Why is the sky blue?",
    subject="physics",
    level="beginner"
).with_inputs("question", "subject", "level")
```

---

## 📤 Output Format

The model returns a structured response:

```json
{
  "clarifying_question": "What do you know about how light behaves when it hits the atmosphere?",
  "concept_hint": "Think about how sunlight contains different colors, and how shorter wavelengths scatter more easily.",
  "feedback": "Great start! You're asking the right kind of question."
}
```

---

## 🧩 DSPy Signature

```python
class SocraticTutor(dspy.Signature):
    """Respond to students with a clarifying question and helpful hints."""

    question: str = dspy.InputField()
    subject: Literal["math", "physics", "biology", "history", "chemistry"] = dspy.InputField()
    level: Literal["beginner", "intermediate", "advanced"] = dspy.InputField()

    clarifying_question: str = dspy.OutputField()
    concept_hint: str = dspy.OutputField()
    feedback: str = dspy.OutputField()
```

---

## 🧪 Example Prompts

### Beginner Example

**Input:**

```json
{
  "question": "Why do we need oxygen?",
  "subject": "biology",
  "level": "beginner"
}
```

**Expected Output:**

```json
{
  "clarifying_question": "What role do you think oxygen plays in your body's energy?",
  "concept_hint": "Oxygen is crucial in a process called cellular respiration.",
  "feedback": "You're thinking like a scientist already!"
}
```

---

## 🔬 Evaluation Ideas

Use evaluators to test whether the model is:

- Asking meaningful clarifying questions.
- Giving domain-correct conceptual hints.
- Matching explanations to the correct student level.

Implement **feedback loops** to automatically revise poor answers using **DSPy's compile-time tuning**.

---

## 🐳 Local Dev via Docker

Use the included `run.sh` script to set up the virtual environment and launch the app in Docker:

```bash
./run.sh
```

This will:

- Create a Python venv.  
- Build and run a Docker container with FastAPI + DSPy.  
- Start the server on `localhost:8000`.

---

## 🖼️ Frontend UX (Next.js)

### Layout

- 📘 **Left panel**: subject selector and difficulty level dropdown.  
- 💬 **Center panel**: text input box for the student's question.  
- 🤖 **Right panel**: AI Tutor's Socratic-style response.

### Features

- Type questions and get structured AI guidance.  
- "Coming Soon" tooltips for voice input and subject-specific UI features.  
- Stylish Tailwind components with light/dark mode.

---

## 🛠️ Future Improvements

- Add subject-specific context modules (e.g., physics laws or math formulas).  
- Enable voice input and TTS.  
- Let users rate AI feedback to improve the model via evaluators.  
- Add feedback loop to revise responses at compile time using DSPy.  
- Expand evaluator logic to dynamically score based on rubric.  
- Finalize frontend experience in Next.js.

---

## 🚀 Advanced DSPy Features to Implement

### 1. Chain of Thought Reasoning
Replace the basic `dspy.Predict` with `dspy.ChainOfThought` to enhance reasoning quality:

```python
# Enhanced reasoning with Chain of Thought
tutor = dspy.ChainOfThought(SocraticTutor)
```

This upgrade will help the tutor break down complex problems step-by-step, especially for advanced questions in subjects like physics and mathematics.

### 2. Prompt Optimization with BootstrapFewShot
Automatically improve prompts using a dataset of example Q&A pairs:

```python
# Example optimization code
def optimize_tutor(example_questions):
    # Define a quality metric
    def quality_metric(example, prediction):
        # Score based on clarity, helpfulness, etc.
        return score

    # Create and run the optimizer
    optimizer = dspy.BootstrapFewShot(metric=quality_metric)
    optimized_tutor = optimizer.compile(
        SocraticTutorModule(), 
        trainset=example_questions
    )
    return optimized_tutor
```

### 3. Subject-Specific Specialists
Create specialized modules for different domains:

```python
class MathTutor(dspy.Module):
    """Specialized tutor for mathematics."""
    def __init__(self):
        self.tutor = dspy.ProgramOfThought(SocraticTutor)  # Use code for math

class ScienceTutor(dspy.Module):
    """Specialized tutor for science subjects."""
    def __init__(self):
        self.tutor = dspy.ChainOfThought(SocraticTutor)  # Use reasoning chains

class HistoryTutor(dspy.Module):
    """Specialized tutor for history."""
    def __init__(self):
        self.tutor = dspy.Predict(SocraticTutor)  # Simple prediction is often sufficient
```

### 4. Response Caching
Improve performance by caching responses:

```python
# Enable caching when initializing the LM
lm = dspy.LM(
    model=settings.OPENAI_MODEL,
    api_key=api_key,
    cache=True  # Enable caching
)
```

### 5. Multiple Response Ensembling
Generate and select the best response from multiple candidates:

```python
class EnsembleTutor(dspy.Module):
    """Generate multiple responses and select the best one."""
    def __init__(self):
        self.tutor = dspy.Predict(SocraticTutor)
        
    def forward(self, question, subject, level):
        # Generate 3 different responses
        predictions = []
        for _ in range(3):
            # Vary temperature to get diverse responses
            predictions.append(self.tutor(question=question, subject=subject, level=level))
            
        # Select the best response based on some criteria
        best_prediction = self.select_best(predictions)
        return best_prediction
```

### 6. Enhanced Retrieval with RAG
Add domain-specific knowledge retrieval using DSPy's RAG capabilities:

```python
from dspy.retrieve import ColBERTv2

# First, create a retriever and index your domain knowledge
retriever = ColBERTv2(url="http://localhost:8000/api/retrieve")
retriever.index(domain_knowledge)

# Create a RAG signature
class KnowledgeAugmentedTutor(dspy.Signature):
    """Tutor that retrieves relevant knowledge before answering."""
    
    question: str = dspy.InputField()
    subject: str = dspy.InputField()
    level: str = dspy.InputField()
    
    retrieved_knowledge: str = dspy.OutputField()
    clarifying_question: str = dspy.OutputField()
    concept_hint: str = dspy.OutputField()
    feedback: str = dspy.OutputField()

# Implement the RAG module
class KnowledgeBasedTutor(dspy.Module):
    def __init__(self, retriever, num_passages=3):
        super().__init__()
        self.retriever = retriever
        self.num_passages = num_passages
        self.tutor = dspy.ChainOfThought(KnowledgeAugmentedTutor)
    
    def forward(self, question, subject, level):
        # Retrieve relevant knowledge
        retrieved_docs = self.retriever.search(
            f"Subject: {subject}. Level: {level}. Question: {question}", 
            k=self.num_passages
        )
        
        # Combine retrieved knowledge
        knowledge = "\n\n".join([doc.text for doc in retrieved_docs])
        
        # Generate response with retrieved knowledge
        prediction = self.tutor(
            question=question, 
            subject=subject, 
            level=level,
            retrieved_knowledge=knowledge
        )
        
        return prediction
```

### 7. Advanced Prompt Optimization with MIPROv2
Improve the quality of responses through DSPy's MIPROv2:

```python
# Define a quality metric
def socratic_quality_metric(example, prediction, trace=None):
    """
    Metric that evaluates how well the tutor follows Socratic principles.
    Returns a score between 0 and 1.
    """
    # Evaluate clarity of the clarifying question
    clarity_score = evaluate_clarity(prediction.clarifying_question)
    
    # Evaluate hint quality - should guide but not give away answers
    hint_score = evaluate_hint_quality(prediction.concept_hint)
    
    # Evaluate appropriateness for student level
    level_score = evaluate_level_match(example.level, prediction)
    
    # Compute weighted score
    total_score = 0.4 * clarity_score + 0.4 * hint_score + 0.2 * level_score
    
    # Store scores in trace if provided
    if trace is not None:
        trace["clarity"] = clarity_score
        trace["hint_quality"] = hint_score
        trace["level_match"] = level_score
    
    return total_score

# Create and use the MIPRO optimizer
def optimize_with_mipro(trainset):
    mipro = dspy.MIPROv2(metric=socratic_quality_metric)
    optimized_tutor = mipro.compile(
        SocraticTutorModule(),
        trainset=trainset,
        max_bootstrapped_demos=5,
        max_labeled_demos=10
    )
    return optimized_tutor
```

### 8. Multi-Step Reasoning with ReAct
Implement ReAct for complex subjects requiring multi-step reasoning:

```python
# Define a ReAct signature for multi-step reasoning
class ReActTutor(dspy.Signature):
    """Multi-step reasoning tutor that can solve complex problems."""
    
    question: str = dspy.InputField()
    subject: str = dspy.InputField()
    level: str = dspy.InputField()
    
    thoughts: str = dspy.OutputField(desc="Step-by-step reasoning about the problem")
    clarifying_question: str = dspy.OutputField()
    concept_hint: str = dspy.OutputField()
    feedback: str = dspy.OutputField()

# Implement ReAct for complex subjects
class ComplexProblemTutor(dspy.Module):
    def __init__(self):
        super().__init__()
        self.tutor = dspy.ReAct(ReActTutor)
    
    def forward(self, question, subject, level):
        prediction = self.tutor(
            question=question,
            subject=subject,
            level=level
        )
        return prediction
```

### 9. Comprehensive Evaluation Framework
Expand the evaluation framework with multiple metrics:

```python
class SocraticEvaluator:
    """Comprehensive evaluator for Socratic responses."""
    
    def __init__(self, lm=None):
        self.lm = lm or dspy.settings.lm
        
        # Define evaluation signatures
        self.clarity_evaluator = dspy.Predict(ClarityEvaluator)
        self.helpfulness_evaluator = dspy.Predict(HelpfulnessEvaluator)
        self.socratic_evaluator = dspy.Predict(SocraticPrinciplesEvaluator)
        
    def evaluate_response(self, question, subject, level, prediction):
        # Evaluate clarity
        clarity_result = self.clarity_evaluator(
            question=question,
            response=prediction.clarifying_question + "\n" + prediction.concept_hint
        )
        
        # Evaluate helpfulness
        helpfulness_result = self.helpfulness_evaluator(
            question=question,
            subject=subject,
            level=level,
            response=prediction.concept_hint
        )
        
        # Evaluate adherence to Socratic principles
        socratic_result = self.socratic_evaluator(
            question=question,
            clarifying_question=prediction.clarifying_question,
            concept_hint=prediction.concept_hint
        )
        
        # Combine scores
        return {
            "clarity": clarity_result.score,
            "helpfulness": helpfulness_result.score,
            "socratic_quality": socratic_result.score,
            "overall": (clarity_result.score + helpfulness_result.score + socratic_result.score) / 3,
            "feedback": socratic_result.improvement_suggestions
        }
```

### 10. Tracing and Debugging
Add tracing to understand the reasoning process:

```python
# Enable tracing for a tutor module
def create_traced_tutor():
    # Create the base tutor
    base_tutor = SocraticTutorModule()
    
    # Create a tracer
    tracer = dspy.Trace()
    
    # Enable tracing
    with tracer:
        # Run the module with tracing enabled
        prediction = base_tutor(
            question="Why does ice float on water?",
            subject="physics",
            level="intermediate"
        )
    
    # Analyze the trace
    print("Traced steps:")
    for i, step in enumerate(tracer.steps):
        print(f"Step {i+1}: {step['type']}")
        if "prompt" in step:
            print(f"Prompt: {step['prompt'][:100]}...")
        if "completion" in step:
            print(f"Completion: {step['completion'][:100]}...")
    
    return prediction, tracer
```

## 📝 Implementation Roadmap

To maximize our use of DSPy's capabilities, we'll implement these features in the following order:

1. **Basic Features (Already Implemented)**
   - Core module structure
   - Simple ChainOfThought reasoning
   - Response caching
   - Basic ensembling

2. **Phase 1: Enhanced Reasoning**
   - Subject-specific specialists (math, science, humanities)
   - ReAct implementation for complex problems
   - Advanced ensembling with better selection criteria

3. **Phase 2: Knowledge Integration**
   - RAG implementation with domain knowledge
   - Knowledge-grounded responses
   - Configurable knowledge sources

4. **Phase 3: Optimization**
   - MIPROv2 for prompt optimization
   - BootstrapFewShot for few-shot learning
   - Automatic improvement based on evaluation results

5. **Phase 4: Evaluation & Quality**
   - Comprehensive evaluation framework
   - Tracing and debugging tools
   - Automated quality improvement pipeline

This roadmap ensures we progressively enhance the system while maintaining a stable, functional application at each phase.

---

## 🔗 Technologies

- **DSPy**  
- **FastAPI**  
- **OpenAI** (via DSPy predictor)  
- **Next.js** (frontend, coming soon)  
- **Docker** (for local dev)

---

## 🔍 DSPy Alignment & Future Tasks

This project aligns with core DSPy features but can be enhanced by adopting advanced DSPy patterns demonstrated in [this breakdown notebook](https://github.com/ALucek/dspy-breakdown/blob/main/dspy_breakdown.ipynb).

### ✅ Implemented DSPy Concepts

- **DSPy Signature Definition**: Uses a custom `SocraticTutor` signature with well-defined input and output fields.
- **Structured Examples**: Wraps student prompts using `dspy.Example(...)` for clean modular inputs.
- **FastAPI Integration**: DSPy modules are served via FastAPI for efficient request handling.
- **Dockerized Local Setup**: A `run.sh` script and Docker configuration allow for consistent local development.

### 🔄 Not Yet Implemented (To-Do)

- **Evaluator Modules**  
  Develop and integrate `dspy.Evaluator` instances to measure clarity, accuracy, and helpfulness of responses.

- **Compile-Time Feedback Loops**  
  Add DSPy compile-time tuning to revise model behavior based on evaluation feedback.

- **Subject-Specific Context Modules**  
  Enhance guidance with context injectors for domain knowledge (e.g., formulas for math, laws for physics).

- **Voice Input and TTS**  
  Add voice input and text-to-speech features in the frontend for accessibility and ease of use.

- **Frontend Completion**  
  Complete the Next.js frontend UI to provide a polished user interaction layer.

---
