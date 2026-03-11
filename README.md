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
| **LLM Reasoning** | Powered by Serverless Inference, providing high-level DevOps intelligence without the need for local GPUs, with the flexibility to easily switch between any supported models by updating the model parameter in main.py. |
| **MCP Integration** | Leverages the official DigitalOcean MCP server via `npx` to dynamically execute real-world tools for Droplets, Apps, and Databases. |
| **LangGraph Orchestration** | Handles complex, multi-step reasoning—such as identifying a failing service and suggesting a fix—in a single turn. |
| **Managed Persistence** | Uses LangGraph `MemorySaver` to isolate user sessions via `thread_id`, remembering infrastructure context across prompts. |

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
Agent workspace name: Give it any name like `OceanSentry`.
Agent deployment name: Set this to `main`.

If you have already initialized but are still seeing the error, ensure your agent is configured locally:

```bash
gradient agent configure
```

When prompted:
Agent workspace name: Give it any name like `OceanSentry`.
Agent deployment name: Set this to `main`.
Entrypoint: main.py

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

## 🧠 Testing Context Memory & Thread Isolation

Use the following test cases in sequence to verify that the agent remembers previous interactions on the same thread, but isolates data from different threads.

| Test Case | Purpose | Terminal Command (`curl`) | Expected Behavior |
| :--- | :--- | :--- | :--- |
| **1. Establish Context** | Fetches initial data and saves it to a specific thread. | `curl -X POST http://localhost:8080/run -H "Content-Type: application/json" -d '{"prompt": "Can you list the names of any 5 DigitalOcean apps in my account?", "thread_id": "session-alpha"}'` | The agent triggers the MCP tool, retrieves your apps, and returns a list of 5 names. |
| **2. Test Memory** | Asks a follow-up question requiring exact recall of the previous turn. | `curl -X POST http://localhost:8080/run -H "Content-Type: application/json" -d '{"prompt": "What were the names of the first and last apps on that list?", "thread_id": "session-alpha"}'` | The agent answers immediately with the two specific names **without** running the list tool again, proving it remembers the context. |
| **3. Test Isolation** | Verifies that a new thread starts with a blank slate. | `curl -X POST http://localhost:8080/run -H "Content-Type: application/json" -d '{"prompt": "What were the names of the first and last apps on that list?", "thread_id": "session-beta"}'` | The agent gets confused or states it doesn't have a list to reference, proving that `session-beta` cannot see the data from `session-alpha`. |

---
---

## 🏗 Architecture: The Hybrid Runtime

1. **Gradient ADK Host:** Manages the local API server (/run), the LangGraph state machine, and persistent session memory via thread_id.
2. **Local Node.js Client:** Spawns a subprocess via MCP (stdio) using npx to securely interact with your live DigitalOcean infrastructure.
3. **Cloud Serverless Inference:** Offloads the complex, multi-step ReAct reasoning to the frontier OpenAI GPT-5.4 model, routed securely through DigitalOcean's native Gradient AI gateway.

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


