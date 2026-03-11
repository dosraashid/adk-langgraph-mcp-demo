# 🤖 DigitalOcean ADK + LangGraph: DevOps Agent Demo

This repository is a production-ready, dual-purpose template demonstrating the "Golden Path" for building stateful, tool-enabled AI agents. It integrates **LangGraph** orchestration with **DigitalOcean Serverless Inference** and uses the **Gradient ADK** for seamless local testing and cloud deployment.

---

## 📂 Project Structure & File Guide

Here is a breakdown of how this agent is built and what each file does:

```text
adk-langgraph-demo/
├── .env                # (Local Only) Stores your private GRADIENT_MODEL_ACCESS_KEY.
├── .gradient/          
│   └── agent.yml       # The blueprint DigitalOcean reads when you run `deploy`.
├── main.py             # The core brain. Connects LangGraph, ADK, and the LLM together.
├── README.md           # This instruction manual.
├── requirements.txt    # The list of Python libraries needed to run the agent.
├── state.py            # Defines the memory structure so the agent remembers threads.
└── tools.py            # The "hands" of the AI (mock database and tool functions).
```

### Detailed File Breakdown
* **`main.py`**: The main entrypoint. It receives the web request, injects the `thread_id` into LangGraph's checkpointer, passes the prompt to DigitalOcean's Serverless Inference API, and returns the final response.
* **`tools.py`**: This is where your custom business logic lives. It contains the mock database (Users and Servers) and the `@tool` decorated functions the AI can call to look up data or perform actions.
* **`state.py`**: The schema for the agent's memory. It defines how standard conversation messages and custom shared memory (like user IDs) are appended and stored.
* **`.gradient/agent.yml`**: A required configuration file for the DigitalOcean Cloud Panel. It tells the cloud environment how to host and run your `main.py` file.

---

## 🌟 Key Capabilities
* **LangGraph Orchestration**: Handles multi-step reasoning (e.g., finding a user, then checking their assigned servers).
* **Managed Persistence**: Uses LangGraph Checkpointers to remember conversation history and isolate sessions via `thread_id`.
* **Standardized Tools**: Implements `ToolNode` with an interconnected mock database for User and Server management.
* **Serverless Intelligence**: Securely connects to DigitalOcean's hosted Llama 3.3 models—no local GPU required.

---

## 🛠️ Initial Setup (Python 3.12 Recommended)

1. **Environment Setup:**
   ```bash
   git clone https://github.com/dosraashid/adk-langgraph-demo
   cd adk-langgraph-demo
   python3.12 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Credentials (.env):**
   ```text
   GRADIENT_MODEL_ACCESS_KEY="your_model_key"
   DIGITALOCEAN_API_TOKEN="your_do_token"
   ```

---

## 🚀 Choose Your Path

This template is designed to work perfectly in two different environments without changing any code.

### Option 1: Run Locally (Fast Testing)
Keep the agent logic on your local machine while using DigitalOcean Serverless GPUs for the AI "brain."

**1. Start the server:**
```bash
gradient agent run
```

**2. Test the "Golden Path" (in a new terminal):**
*Step A: Multi-step reasoning (Find user -> Check servers)*
```bash
curl -X POST http://localhost:8080/run \
-H "Content-Type: application/json" \
-d '{"prompt": "Hi, I am alice@dev.com. Are any of my servers failing?", "thread_id": "demo-1"}'
```

*Step B: Action & Persistence (Fix the issue)*
```bash
curl -X POST http://localhost:8080/run \
-H "Content-Type: application/json" \
-d '{"prompt": "Please restart the failing one.", "thread_id": "demo-1"}'
```

### Option 2: Deploy to Cloud (Production)
Push your agent to the DigitalOcean Cloud Panel for 24/7 access, automatic scaling, and built-in observability.

**1. Export your Personal Access Token:**
*(This token requires Read/Write API permissions from your DO Dashboard)*
```bash
export DIGITALOCEAN_API_TOKEN="dop_v1_your_personal_token_here"
```

**2. Deploy the agent:**
```bash
gradient agent deploy
```

**3. Monitor & Manage:**
Once deployed, your agent will be live and accessible via a public endpoint. You can view logs, execution traces, and manage API keys in the **GenAI > Agents** section of your DigitalOcean Console.
