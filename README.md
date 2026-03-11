# 🤖 DigitalOcean ADK + MCP + LangGraph + Context: DevOps Agent Demo

This repository demonstrates the **"Golden Path"** for building an autonomous DevOps agent. It integrates **DigitalOcean Serverless Inference (OpenAI GPT 5.4)** with the **Model Context Protocol (MCP)** and **LangGraph** to create a system that doesn't just answer questions—it manages infrastructure.

---

## 🏗️ Project Structure & File Guide

A clean, modular structure optimized for a Hybrid Runtime (Local Python + Local Node.js + Cloud LLM).

```text
/cloudpilot-agent
├── .env                  # 🔑 Local API keys (Never committed to Git)
├── .gitignore            # 🛡️ Security: Prevents sensitive keys from leaking
├── main.py               # 🧠 The Brain, Hands, and Memory (All-in-One Orchestrator)
├── requirements.txt      # 📦 Python dependency manifest
└── README.md             # 📝 Detailed Project Documentation
```

---

# 🔍 Detailed File Breakdown

## 1. `main.py`
The central orchestrator of the agent. This file handles three mission-critical roles:

**The Connector:**  
Establishes a live connection to the DigitalOcean MCP Server via a local `stdio` subprocess, allowing the agent to discover and use cloud tools dynamically.

**The Logic Engine:**  
Runs the LangGraph state machine, which coordinates the reasoning loop between the user's request and the model's response.

**The Memory:**  
Utilizes an inline `MemorySaver` to provide managed persistence, ensuring that conversation history is preserved across multiple turns.

## 2. `requirements.txt`
Defines the dependencies for the Hybrid Runtime.

It pulls in:
- `langchain-gradient` for inference
- `langgraph` for state management
- `mcp` adapters to bridge Python with the official DigitalOcean Node.js tool server

## 3. `.env` & `.gitignore`
Ensures **Security by Design**.

- The `.env` file stores your `DIGITALOCEAN_API_TOKEN` and `GRADIENT_MODEL_ACCESS_KEY` locally.
- The `.gitignore` prevents these secrets from ever being pushed to a public repository.

---

# ✨ Key Capabilities

| Capability | Description |
|---|---|
| **Managed Conversation History** | Supports "Checkpointer-style" persistence. The agent doesn't just remember text; it remembers tool execution states, enabling fault-tolerance and session resume. |
| **Full MCP Service Scope** | Out-of-the-box support for all DigitalOcean services, including `apps`, `droplets`, `databases`, `doks`, `networking`, `accounts`, `insights`, `marketplace`, and `spaces`. |
| **Thread Isolation** | Strict context handoff using `thread_id`. Information from `session-alpha` is never leaked to `session-beta`. |
| **Standardized Telemetry** | All tool interactions follow LangGraph `ToolNode` semantics, making it easy to integrate with observability tools in the future. |
| **Hybrid Tooling** | Demonstrates how to mix high-level Cloud APIs (via MCP) with local business logic (via `@tool` decorated Python functions). |

---

# 🚀 Recommended "Wow" Tests

Use these prompts to showcase the unique capabilities of the **MCP + LangGraph architecture**.

| Feature Highlight | Goal | Prompt Payload |
|---|---|---|
| **MCP Discovery** | Tool Awareness | What DigitalOcean tools do you have access to right now? |
| **Live Account Data** | Real-time Stats | List my active droplets and tell me which ones are in NYC3. |
| **Reasoning** | Infrastructure Audit | Check my account balance. Based on my usage, do I have any idle resources? |
| **LangGraph Orchestration** | Multi-step Debugging | Find my app named 'web-service', check its last deployment status, and if it failed, summarize the error logs. |
| **Managed Persistence** | Cross-Session Memory | Remember that 'web-service' is my high-priority app. Based on our last chat, is it healthy now? |
| **Hybrid Runtime** | Intelligence + Control | Analyze my account spending. Suggest which droplets I can resize or power down to save at least 10% this month. |

---

# 🚀 Setup & Installation

### 1. Prerequisites
- Python **3.12** recommended
- **Node.js / NPM** (for `npx`)
- A **DigitalOcean API Token**
- A **Gradient AI Model Access Key**

### 2. Environment Setup

Install the required Python dependencies:

```bash
git clone https://github.com/dosraashid/adk-langgraph-mcp-demo
cd adk-langgraph-mcp-demo
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Credentials

Update the .env file in the root directory and add your credentials:

```bash
GRADIENT_MODEL_ACCESS_KEY="your_model_access_key"
DIGITALOCEAN_API_TOKEN="your_DO_token"
```

Make sure .env is listed in your .gitignore to prevent accidental exposure of secrets.

### 4. Initialization

Before running the agent for the first time, you must initialize the Gradient configuration:

```bash
gradient agent init
```

When prompted:

* Agent workspace name: Give it any random name like `OceanSentry`.
* Agent deployment name: Set this to `main`.

### 5. Run

Start the agent server locally using the Gradient ADK:

```bash
gradient agent run
```

This will spin up a local Uvicorn server (typically on `http://localhost:8080`). Once it is running, you can issue prompts to the system in a separate terminal tab using `curl`. 

By passing a `thread_id` in your JSON payload, you tell the agent which "save slot" to use, allowing it to maintain conversational memory across multiple requests.

```bash
curl -X POST http://localhost:8080/run \
     -H "Content-Type: application/json" \
     -d '{
           "prompt": "List my DigitalOcean apps.",
           "thread_id": "my-dev-session-1"
         }'
```

---

## 🧪 Verification Commands & Test Cases

This agent uses **Thread-Scoped Persistence** via LangGraph Checkpointers. Run these test cases in sequence in your terminal to verify that memory is isolated between sessions, and that the agent can seamlessly route between cloud (MCP) and local tools.

| Test Case | Purpose | Terminal Command (`curl`) | Expected Behavior |
| :--- | :--- | :--- | :--- |
| **1. Establish Context (MCP)** | Fetch cloud data & save to Thread A. | `curl -X POST http://localhost:8080/run -H "Content-Type: application/json" -d '{"prompt": "List my DigitalOcean apps.", "thread_id": "alpha"}'` | Agent triggers the `apps-list` tool via the prebuilt LangGraph `ToolNode` and returns your apps. |
| **2. Test Local Tools** | Verify access to custom Python functions. | `curl -X POST http://localhost:8080/run -H "Content-Type: application/json" -d '{"prompt": "Calculate the cloud cost for running an instance for 100 hours if the monthly price is $20.", "thread_id": "alpha"}'` | Agent routes to the local `@tool` decorated `calculate_cloud_cost` function and returns the exact math. |
| **3. Verify Context Recall** | Test exact conversation history recall in same thread. | `curl -X POST http://localhost:8080/run -H "Content-Type: application/json" -d '{"prompt": "What was the very first question I asked you?", "thread_id": "alpha"}'` | Checkpointer retrieves `MessagesState`, and the agent accurately replies that you asked it to list your apps. |
| **4. Test Thread Isolation** | Prove memory is strictly scoped and isolated. | `curl -X POST http://localhost:8080/run -H "Content-Type: application/json" -d '{"prompt": "What was the very first question I asked you?", "thread_id": "beta"}'` | Agent looks at the isolated `beta` thread, sees it is empty, and replies that this is your first question. |

---

## 🏗 Architecture: The Hybrid Runtime

This agent implements the LangGraph Golden Path for DevOps automation, providing a standardized bridge between local infrastructure and cloud-hosted frontier models.

1. **Orchestration (LangGraph):** Uses a StateGraph with MessagesState to manage the reasoning loop. This satisfies the requirement for a standardized open-source framework for agentic flow.
2. **Standardized Tool Execution (ToolNode):** Employs the official LangGraph ToolNode to handle tool execution. This ensures telemetry is captured consistently, allowing tool calls to be recorded in history for replay or auditing.
3. **Managed Persistence (Checkpointers):** Employs MemorySaver to provide checkpointer-style persistence. This enables scoped memory per thread_id, allowing sessions to be resumed, replayed, or isolated.
4. **Hybrid MCP Runtime:** Bridges local User-Defined Functions (Python) with the DigitalOcean MCP Server (providing 9+ cloud services) via a secure stdio subprocess.
5. **Frontier Inference:** Routes complex ReAct reasoning to GPT-5.4 (or Llama 3.3) via the DigitalOcean Gradient AI gateway using the native Gradient SDK.

---

# 🛠️ Requirements & Troubleshooting

### Node.js Dependency

Because this agent uses the **Model Context Protocol (MCP)**, it requires **Node.js** to be installed on your local machine. The `main.py` script uses `npx` to fetch and run the official DigitalOcean tool server. 
* **Verify installation:** Run `node -v` in your terminal.

### Environment Secrets

Ensure your .env file is in the root directory and contains the following:

* **DIGITALOCEAN_API_TOKEN:** Must have `Write` scopes if you plan to manage/modify resources (Droplets, Apps, Databases).
* **GRADIENT_MODEL_ACCESS_KEY:** Required to authenticate your inference calls to the GPT-5.4 model on the Gradient platform.
  
### Common Errors

* **Connection Refused:** Ensure you are targeting the correct port in your curl command (usually 8080 or 8000). Check the gradient agent run startup logs to confirm.
* **401 Unauthorized:** Double-check that your API tokens are valid and correctly loaded in the .env file.

---

# 🤝 Contributing
This is a demo of the **Golden Path** for AI-driven DevOps. If you'd like to extend the agent's capabilities:
1. **Add new tools:** Update the `--services` flag in the `npx` command within `main.py`.
2. **Modify the Brain:** Switch the `model` parameter in `ChatGradient` to test different LLM variants.
3. **Enhance Memory:** Explore `PostgresSaver` in LangGraph for long-term database-backed persistence.

---


