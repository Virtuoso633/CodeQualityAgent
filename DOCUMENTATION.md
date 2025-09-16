
# Technical Documentation & Engineering Decisions

This document provides a deep dive into the architecture, component design, and data flows of the CodeIQ Intelligence Agent. It outlines the key engineering decisions made and explains the rationale behind them.

## 1. Core Architectural Philosophy: Agentic & Decoupled

The fundamental design choice for CodeIQ was to build a system that was both **intelligent** and **scalable**. This led to two core principles:

1.  **Agentic Design:** Instead of relying on a single, monolithic AI model to perform all tasks, we adopted an **agentic pattern**. The system is composed of multiple, specialized AI agents, each with a distinct role and expertise. This is analogous to a human software team where you have a security expert, a performance engineer, and a project manager. This separation of concerns leads to higher-quality, more focused outputs.

2.  **Decoupled Architecture:** The system is built as a modern client-server application. The **FastAPI backend** acts as the powerful, stateless "brain," while the **Streamlit frontend** serves as the interactive, stateful "face." This separation allows them to be developed, deployed, and scaled independently, which is a robust industry-standard practice.

---

## 2. Component Breakdown & Data Flow

Here is a detailed look at each major component, its purpose, and how it interacts with the rest of the system.

### The Analysis Flow (When a User Submits a Repository)

This is the primary data flow when a user clicks "Analyze Repository."

 <!-- **Action:** Create a simple diagram showing this flow -->

**Step 1: Frontend (`web/frontend/streamlit_app.py`)**
*   **What it does:** Captures the user's request (a GitHub URL or uploaded files) and sends it as an HTTPS POST request to the backend API.
*   **Importance:** Provides the user-friendly interface. It immediately gets an `analysis_id` back and begins polling the backend for status updates, creating a non-blocking, responsive user experience.

**Step 2: Backend API (`web/backend/main.py`)**
*   **What it does:** The FastAPI application receives the request. It immediately returns an `analysis_id` and spins up a background task to handle the long-running analysis.
*   **Framework:** **FastAPI** was chosen for its high performance, asynchronous capabilities (critical for handling long AI tasks without blocking), and automatic OpenAPI documentation.
*   **Importance:** Acts as the central nervous system, coordinating all backend operations.

**Step 3: The Conductor (`tools/analyzers/comprehensive_scanner.py`)**
*   **What it does:** This is the main orchestrator for the analysis. It clones the repo, collects all relevant source files, and then initiates multiple asynchronous calls to the specialized agents for each file.
*   **Importance:** This component is the "project manager" of the analysis, delegating tasks and collecting results.

**Step 4: The Specialists (`agents/specialized/`)**
This is the heart of the agentic pattern. The `ComprehensiveCodebaseScanner` calls upon these agents:
*   `security_agent.py`: Analyzes code *only* for security vulnerabilities. Its prompt is highly focused on OWASP Top 10 and CWEs.
*   `performance_agent.py`: Analyzes code *only* for performance bottlenecks, algorithmic complexity, and memory issues.
*   `architecture_agent.py`: Looks at the entire file structure and generates a high-level Mermaid diagram of the system's components.
*   **AST Analyzer (in `comprehensive_scanner.py`):** This is not an LLM-based agent but a traditional code parser. It uses Python's built-in `ast` library to parse the code's structure and find precise, non-debatable quality issues like overly complex functions or bad error handling.
*   **Importance:** This multi-agent approach provides a "defense in depth" analysis. The LLM-based agents are great at finding nuanced, contextual issues, while the AST analyzer is perfect for finding concrete, structural problems.

**Step 5: The Synthesizer (`flows/analysis/crew_coordinator.py`)**
*   **What it does:** After all the individual file analyses are complete, the raw JSON list of all security and performance issues is passed to this coordinator.
*   **Framework:** **CrewAI** was chosen to manage a multi-step reasoning process. It uses two agents:
    1.  A "Principal Engineer" agent to identify high-level themes from the raw data.
    2.  A "Product Manager" agent to translate those technical themes into a business-focused, non-technical executive summary.
*   **Importance:** This component transforms a long, noisy list of technical findings into a concise, actionable summary that a manager or team lead can immediately understand.

**Step 6: The RAG Preparer (`tools/analyzers/rag_analyzer.py`)**
*   **What it does:** In parallel with the other analyses, this component reads all the code, splits it into chunks, and uses **FAISS** (a vector library) and Google's embedding models to create a searchable vector index of the entire codebase.
*   **Importance:** This is a "Super Stretch" feature that prepares the system for the interactive Q&A. It creates the "memory" that the AI will use to answer deep questions about the code.

---

### The Interactive Q&A Flow

This flow is triggered when a user asks a question in the chat interface.

**1. Report Summary Q&A (`flows/interactive/qa_system.py`)**
*   **How it works:** When a user asks a high-level question, the backend constructs a rich "context summary" containing the overall scores and the CrewAI executive summary. This summary, along with the user's question, is sent to the Gemini LLM in a single prompt.
*   **Why this pattern?** It's fast, cheap, and efficient. It answers questions *about the report* without needing to re-read the entire codebase.

**2. Ask the Codebase (RAG) (`tools/analyzers/rag_analyzer.py`)**
*   **How it works:** This is a more complex, two-step process:
    1.  **Retrieval:** The user's question is converted into a vector. The system performs a similarity search on the pre-built FAISS index to find the most relevant chunks of *actual source code*.
    2.  **Augmented Generation:** A new prompt is constructed that includes both the user's original question and the retrieved code snippets. This "augmented" prompt is then sent to the Gemini LLM.
*   **Why this pattern?** This is the key to overcoming the context window limitations of LLMs. It allows the AI to reason about massive codebases by focusing only on the most relevant parts for any given question. It provides highly accurate, "grounded" answers that reference specific source files.

### Frameworks & Libraries: The "Why"

*   **FastAPI:** Chosen for its async capabilities, which are essential for I/O-bound tasks like making multiple, parallel calls to the Gemini API.
*   **Streamlit:** Chosen for its ability to rapidly create beautiful, interactive data applications with pure Python. It's the perfect tool for building the user-facing dashboard.
*   **Docker:** Chosen to solve the "it works on my machine" problem. Containerization ensures that the application runs consistently across development, testing, and production environments.
*   **CrewAI:** Chosen over a single-agent setup for its strength in orchestrating multi-step, role-based workflows. The "Engineer -> Manager" pipeline for the executive summary is a perfect use case.
*   **LangChain:** Used as the foundational library for interacting with LLMs, managing prompts, and, most importantly, for its robust RAG implementation tools (Text Splitters, Vector Stores, and Retrievers).
*   **FAISS:** Chosen as the vector store for its speed and efficiency. It runs entirely in memory on the CPU, making it perfect for a free-tier deployment without requiring a dedicated vector database service.