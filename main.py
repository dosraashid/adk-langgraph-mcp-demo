import os
import asyncio
from typing import Optional, TypedDict, Annotated
from dotenv import load_dotenv

# --- LANGCHAIN & LANGGRAPH IMPORTS ---
from langchain_gradient import ChatGradient
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages

# --- MCP & ADK IMPORTS ---
from langchain_mcp_adapters.client import MultiServerMCPClient
from gradient_adk import entrypoint

# Load API keys from the .env file
load_dotenv()

# --- 1. MANAGED PERSISTENCE (STATE SCHEMA) ---
# This class defines the "Memory" of the agent.
# Using add_messages ensures that the AI remembers the full conversation
# history instead of just the last message.
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

# --- 2. THE CORE AGENT LOGIC ---
async def run_mcp_agent(user_input: str, thread_id: str, checkpointer: MemorySaver):
    """
    The orchestrator function. It connects to the tools, hits the 
    Serverless LLM, and manages the LangGraph loop.
    """
    
    # --- HYBRID RUNTIME: CONNECTING TO MCP (NODE.JS) ---
    # We launch the Official DigitalOcean MCP server via 'stdio'.
    # This spawns a Node.js process that Python can talk to directly.
    client = MultiServerMCPClient({
        "digitalocean": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@digitalocean/mcp", "--services", "apps,droplets,databases"],
            "env": {
                **os.environ, 
                "DIGITALOCEAN_API_TOKEN": os.getenv("DIGITALOCEAN_API_TOKEN")
            }
        }
    })
    
    # We use an async context manager to ensure the connection is cleaned up
    async with client:
        # Load tools (like get_droplets) dynamically from the MCP server
        tools = await client.get_tools()
        
        # --- SERVERLESS INFERENCE: THE BRAIN ---
        # We hit the Llama 3.3 model hosted on DigitalOcean's managed GPUs.
        llm = ChatGradient(
            model="llama3.3-70b-instruct",
            api_key=os.getenv("GRADIENT_MODEL_ACCESS_KEY") or os.getenv("DIGITALOCEAN_INFERENCE_KEY"),
        )
        
        # We "bind" the tools so the LLM knows it has 'hands' to use
        llm_with_tools = llm.bind_tools(tools)

        # --- LANGGRAPH ORCHESTRATION ---
        # The Reasoning Node: Where the LLM decides what to do next
        def call_model(state: AgentState):
            response = llm_with_tools.invoke(state["messages"])
            return {"messages": [response]}

        # Define the Graph Flow
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", call_model)
        workflow.add_node("action", ToolNode(tools)) # Executes the MCP tools
        workflow.add_edge(START, "agent")
        
        # Routing Logic: Does the LLM want to use a tool or just talk?
        def should_continue(state: AgentState):
            last_message = state["messages"][-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "action"
            return END

        workflow.add_conditional_edges("agent", should_continue)
        workflow.add_edge("action", "agent")

        # Compile the agent with a "Checkpointer" for managed session persistence
        app = workflow.compile(checkpointer=checkpointer)

        # Execute for the specific thread_id (isolates user sessions)
        config = {"configurable": {"thread_id": thread_id}}
        input_state = {"messages": [HumanMessage(content=user_input)]}
        
        result = await app.ainvoke(input_state, config=config)
        return result["messages"][-1].content

# --- 3. THE CLI ENTRYPOINT ---
@entrypoint
async def main(body: dict):
    """Entrypoint for 'gradient agent run' usage."""
    user_input = body.get("prompt", "Hello")
    thread_id = body.get("thread_id", "cli-user-1")
    
    memory = MemorySaver()
    final_response = await run_mcp_agent(user_input, thread_id, memory)

    return {"response": final_response, "thread_id": thread_id}

# --- 4. INTERACTIVE DEMO MODE ---
async def interactive_chat():
    """Run a continuous, memory-aware chat in your terminal."""
    print("\n[CloudPilot DevOps Agent: Online]")
    print("Inference: Llama 3.3 (Serverless Inference)")
    print("Tools: Official DigitalOcean MCP (stdio)\n")
    
    # We initialize memory ONCE here so it persists between 'input' prompts
    memory = MemorySaver()
    session_id = "demo-session-123"

    while True:
        prompt = input("You: ")
        if prompt.lower() in ['exit', 'quit']:
            break
        
        try:
            # The agent will remember previous messages due to the persistent memory object
            response = await run_mcp_agent(prompt, session_id, memory)
            print(f"\nCloudPilot: {response}\n")
        except Exception as e:
            print(f"\n❌ Execution Error: {e}\n")

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore") # Keep the terminal output clean
    asyncio.run(interactive_chat())
