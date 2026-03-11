# 🤖 DigitalOcean ADK + MCP + LangGraph + Context: DevOps Agent Demo

This repository demonstrates the **"Golden Path"** for building an autonomous DevOps agent. It integrates **DigitalOcean Serverless Inference (Llama 3.3)** with the **Model Context Protocol (MCP)** and **LangGraph** to create a system that doesn't just answer questions—it manages infrastructure.

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
| **Llama 3.3 Reasoning** | Powered by Serverless Inference, providing high-level DevOps intelligence without the need for local GPUs, with the flexibility to easily switch between any supported models by updating the model parameter in main.py. |
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

## 🚀 Setup & Installation

### 1. Prerequisites
- Python **3.12** recommended
- **Node.js / NPM** (for `npx`)
- A **DigitalOcean API Token**
- A **Gradient AI Model Access Key**

### 2. Environment Setup

Install the required Python dependencies:

```bash
git clone https://github.com/dosraashid/adk-langgraph-demo
cd adk-langgraph-demo
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

### 4. Run

Start the agent in interactive mode:

```bash
python main.py
```

Once running, you can begin issuing prompts to the system.

---

## 🏗 Architecture: The Hybrid Runtime
1. **Local Python Host:** Manages the LangGraph state machine and conversation memory.
2. **Local Node.js Client:** Spawns via MCP (`stdio`) using `npx` to interact with DigitalOcean's infrastructure.
3. **Cloud Serverless Inference:** Offloads the massive Llama 3.3 70B computation to DigitalOcean's managed GPU clusters.

---

## 🛠️ Requirements & Troubleshooting

### Node.js Dependency
Because this agent uses the **Model Context Protocol (MCP)**, it requires **Node.js** to be installed on your local machine. The `main.py` script uses `npx` to fetch and run the official DigitalOcean tool server. 
* **Verify installation:** Run `node -v` in your terminal.

### Environment Secrets
Ensure your `.env` file is in the root directory. If you see a `401 Unauthorized` error, double-check that your **DigitalOcean API Token** has "Write" scopes for the services you want to manage (Droplets, Apps, etc.).

---

## 🤝 Contributing
This is a demo of the **Golden Path** for AI-driven DevOps. If you'd like to extend the agent's capabilities:
1. **Add new tools:** Update the `--services` flag in the `npx` command within `main.py`.
2. **Modify the Brain:** Switch the `model` parameter in `ChatGradient` to test different Llama variants.
3. **Enhance Memory:** Explore `PostgresSaver` in LangGraph for long-term database-backed persistence.

---


