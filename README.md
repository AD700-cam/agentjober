# Python-Based AI Agent Architecture

Welcome to the **AI Agent Architecture** project. This project implements a modular, extensible, and robust framework for building autonomous AI agents capable of reasoning, utilizing tools, managing memory, and collaborating to solve complex tasks.

---

## 🏗️ System Architecture & Directory Structure

The project is structured to enforce a strict separation of concerns, making it easy to scale individual modules independently:

```text
ai-agent-roadmap/
├── agents/             # Agent definitions, orchestrators, and behavior logic
├── data/               # Static configurations, profiles, and runtime data
│   └── master_profile.json
├── docs/               # System architecture design, diagrams, and documentation
├── memory/             # Short-term (session) and long-term (vector) memory systems
├── prompts/            # System instructions, dynamic prompt templates, and few-shot examples
└── tools/              # Custom tool definitions, external API wrappers, and sandboxed executors
```

### Folder Breakdown

*   📁 **`agents/`**: Houses the core agent classes (e.g., `base_agent.py`, `orchestrator.py`) and specific sub-agent modules (e.g., `research_agent.py`, `code_agent.py`).
*   📁 **`data/`**: Stores agent configuration states, such as the [`master_profile.json`](file:///d:/temp/ai-agent-roadmap/data/master_profile.json), which defines identities, active capabilities, and LLM preferences.
*   📁 **`docs/`**: Holds architectural specifications, state diagrams, and API design files.
*   📁 **`memory/`**: Contains components responsible for agent memory, including interfaces to vector databases (long-term memory) and relational databases or Redis (short-term session memory).
*   📁 **`prompts/`**: Stores system prompt templates and dynamic builders to format context for LLM interaction.
*   📁 **`tools/`**: Contains files defining specific functions the agents can execute (e.g., file operations, API clients, calculation engines).

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Git

### Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd ai-agent-roadmap
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

3. Install requirements (once dependencies are defined):
   ```bash
   pip install -r requirements.txt
   ```

---

## 🛠️ Core Components Guide

### 1. Agent Configuration (`data/master_profile.json`)
The main config file controls the orchestrator's behavior:
- **Identity & Role**: Configures the persona and system instructions.
- **LLM Settings**: Specifies provider (e.g., Google Gemini, OpenAI), model version, and generation temperature.
- **Memory Integration**: Sets up short-term context window limits and vector database settings for retrieval-augmented generation (RAG).
- **Security & Safety**: Defines human-in-the-loop validation parameters for sensitive tools.

---

## 📄 License
This project is licensed under the MIT License.
