import os
import asyncio
import operator
from typing import TypedDict, Annotated, List
from dotenv import load_dotenv

# --- NATIVE CLOUD SDKs ---
# We use the native Gradient SDK to access GPT-5.4 on DigitalOcean
from gradient import Gradient

# --- AGENTIC ORCHESTRATION ---
# LangGraph manages the state (memory) and the "thinking vs acting" loop
from langchain_core.messages import HumanMessage, AIMessage, AnyMessage
from langchain_core.tools import StructuredTool
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# --- INFRASTRUCTURE ADAPTERS ---
# Connects our agent to DigitalOcean's Model Context Protocol (MCP) server
from langchain_mcp_adapters.client import MultiServerMCPClient

# --- GRADIENT AGENT FRAMEWORK ---
# The @entrypoint decorator registers this script with 'gradient agent run'
from gradient_adk import entrypoint

load_dotenv()

# --- 1. STATE DEFINITION ---
# This defines what the agent "carries" in its head. 
# operator.add tells LangGraph to append new data to existing history.
class AgentState(TypedDict):
    messages: Annotated[List[AnyMessage], operator.add]
    shared_memory: Annotated[List[str], operator.add]

# --- 2. THE MEMORY VAULT ---
# Initialized globally so it persists as long as the local server runs.
# It uses 'thread_id' to separate different user sessions.
shared_checkpointer = MemorySaver()

# --- 3. TOOL UTILITIES ---
def stringify_mcp_tools(tools):
    """
    Standardizes MCP tool outputs. 
    Our LLM expects strings, so we wrap the raw JSON/List outputs 
    from the MCP server into a single string format.
    """
    wrapped = []
    for tool in tools:
        def create_wrapper(t):
            # The async execution layer for the cloud tools
            async def wrapped_func(**kwargs):
                res = await t.ainvoke(kwargs) 
                if isinstance(res, list):
                    return "\n".join([str(b.get("text", b)) for b in res if isinstance(b, dict)])
                return str(res)
            return wrapped_func
        
        wrapped.append(StructuredTool.from_function(
            func=create_wrapper(tool),
            name=tool.name,
            description=tool.description,
            coroutine=create_wrapper(tool) # Links the async coroutine for execution
        ))
    return wrapped

# --- 4. CORE AGENT LOGIC ---
async def run_mcp_agent(user_input: str, thread_id: str):
    # Connect to the DigitalOcean MCP server via npx
    mcp_client = MultiServerMCPClient({
        "digitalocean": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@digitalocean/mcp", "--services", "apps,droplets"],
            "env": {**os.environ}
        }
    })
    
    # Initialize the high-performance Gradient inference client
    inf_client = Gradient(model_access_key=os.environ.get("GRADIENT_MODEL_ACCESS_KEY"))

    try:
        # Discover what tools our cloud environment currently supports
        raw_tools = await mcp_client.get_tools()
        tools = stringify_mcp_tools(raw_tools)

        # NODE: THE BRAIN (LLM)
        async def call_model(state: AgentState):
            tool_list = ", ".join([t.name for t in tools])
            # System message guiding the frontier model's ReAct loop format
            sys_msg = (
                f"You are a DigitalOcean Cloud Expert. Tools available: {tool_list}. "
                "1. If the answer is in the conversation history, use it. "
                "2. If you need cloud data, reply with ONLY: 'EXECUTE: [tool_name]'. "
                "3. Once you have data, summarize it naturally for the user."
            )
            
            msgs = [{"role": "system", "content": sys_msg}]
            for m in state["messages"]:
                role = "user" if isinstance(m, HumanMessage) else "assistant"
                msgs.append({"role": role, "content": str(m.content)})

            # GPT-5.4 call - using a thread to keep the event loop non-blocking
            resp = await asyncio.to_thread(
                inf_client.chat.completions.create,
                messages=msgs,
                model="openai-gpt-5.4",
                max_tokens=1000
            )
            return {"messages": [AIMessage(content=resp.choices[0].message.content)]}

        # NODE: THE ARMS (Tool Execution)
        async def tool_step(state: AgentState):
            last_msg = state["messages"][-1].content
            for t in tools:
                if t.name in last_msg:
                    print(f"DEBUG: Executing {t.name}...")
                    # Trigger the actual cloud API call (passing empty dict for schema validation)
                    obs = await t.ainvoke({}) 
                    return {"messages": [HumanMessage(content=f"Observation from {t.name}: {obs}")]}
            return state

        # --- 5. GRAPH CONSTRUCTION ---
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", call_model)
        workflow.add_node("action", tool_step)
        
        workflow.add_edge(START, "agent")
        
        # ROUTER: Decides if we need more data or if we are done
        def router(state: AgentState):
            content = state["messages"][-1].content
            # If the model wants to execute a tool and hasn't seen the results yet
            if "EXECUTE:" in content and "Observation from" not in content:
                return "action"
            return END

        workflow.add_conditional_edges("agent", router)
        workflow.add_edge("action", "agent")

        # Compile the graph with our persistent memory checkpointer
        app = workflow.compile(checkpointer=shared_checkpointer)
        config = {"configurable": {"thread_id": thread_id}}
        
        # Determine if this thread has history
        existing_state = app.get_state(config)
        initial_input = {"messages": [HumanMessage(content=user_input)]}
        if not existing_state.values:
            # First time for this thread, initialize shared_memory
            initial_input["shared_memory"] = []

        # Run the full cycle
        final_state = await app.ainvoke(initial_input, config=config)
        return final_state["messages"][-1].content

    finally:
        # Clean shutdown of the MCP connection
        if hasattr(mcp_client, "close"): 
            await mcp_client.close()

# --- 6. AGENT ENTRYPOINT ---
@entrypoint
async def main(data, context):
    """
    Standard entrypoint for the Gradient ADK.
    Takes incoming JSON data from the /run endpoint.
    """
    user_prompt = data.get("prompt") or data.get("text") or "Hello"
    thread_id = data.get("thread_id", "default-session")
    
    try:
        response = await run_mcp_agent(user_prompt, thread_id)
        return {"result": response}
    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        return {"error": f"Agent encountered an issue: {str(e)}"}
