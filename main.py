import os
import json
import asyncio
from typing import Annotated, List
from dotenv import load_dotenv

# --- NATIVE CLOUD SDKs ---
from gradient import Gradient

# --- LANGGRAPH CORE (Golden Path standard) ---
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition

# --- MCP & ADK ---
from langchain_mcp_adapters.client import MultiServerMCPClient
from gradient_adk import entrypoint

load_dotenv()

# --- 1. PERSISTENCE (Checkpointer) ---
# Managed conversation history that provides checkpointer-style persistence
shared_checkpointer = MemorySaver()

# --- 2. USER-DEFINED FUNCTION ---
# Combines with MCP server integration to satisfy the requirement
@tool
def calculate_cloud_cost(hours: int, instance_price_per_month: float) -> str:
    """Calculates the estimated cost of a cloud instance over a specific number of hours."""
    hourly_rate = instance_price_per_month / 730 # Approx hours in a month
    cost = hours * hourly_rate
    return f"Estimated cost for {hours} hours is ${cost:.2f}"

# --- 3. THE GOLDEN PATH AGENT ---
async def run_golden_agent(user_input: str, thread_id: str):
    # Connect to MCP with ALL DigitalOcean services enabled
    mcp_client = MultiServerMCPClient({
        "digitalocean": {
            "transport": "stdio",
            "command": "npx",
            "args": [
                "-y", 
                "@digitalocean/mcp", 
                "--services", 
                "accounts,apps,databases,doks,droplets,insights,marketplace,networking,spaces"
            ],
            "env": {**os.environ}
        }
    })
    
    inf_client = Gradient(model_access_key=os.environ.get("GRADIENT_MODEL_ACCESS_KEY"))

    try:
        # 🚨 THE FIX: The MultiServer client automatically converts MCP tools to LangChain tools!
        mcp_tools = await mcp_client.get_tools() 
        
        # Combine both sets of tools for the agent
        all_tools = mcp_tools + [calculate_cloud_cost]
        
        # Standardized tool execution telemetry aligned with LangGraph
        tool_node = ToolNode(all_tools)

        # NODE: THE BRAIN
        async def call_model(state: MessagesState):
            tool_list = ", ".join([t.name for t in all_tools])
            sys_msg = (
                f"You are a Cloud DevOps Agent. Available tools: {tool_list}\n"
                "To use a tool, reply ONLY in this exact format:\n"
                "CALL: [tool_name] {{\"arg1\": \"value1\"}}\n"
                "Otherwise, answer the user normally."
            )
            
            msgs = [{"role": "system", "content": sys_msg}]
            
            # Map LangGraph's standard messages to the format the Gradient SDK expects
            for m in state["messages"]:
                if isinstance(m, ToolMessage):
                    msgs.append({"role": "user", "content": f"Tool Result ({m.name}): {m.content}"})
                elif isinstance(m, AIMessage):
                    if m.tool_calls:
                        # Reconstruct the tool call so the model remembers its past actions
                        call_str = f"CALL: {m.tool_calls[0]['name']} {json.dumps(m.tool_calls[0]['args'])}"
                        msgs.append({"role": "assistant", "content": call_str})
                    else:
                        msgs.append({"role": "assistant", "content": str(m.content)})
                else:
                    msgs.append({"role": "user", "content": str(m.content)})

            # Call GPT-5.4 via Gradient SDK with a larger token window for the massive tool list
            resp = await asyncio.to_thread(
                inf_client.chat.completions.create,
                messages=msgs,
                model="openai-gpt-5.4",
                max_tokens=3000
            )
            
            content = resp.choices[0].message.content
            
            # GOLDEN PATH: Translate text to standard LangChain tool_calls
            if content and content.startswith("CALL:"):
                try:
                    parts = content.replace("CALL:", "").strip().split(" ", 1)
                    tool_name = parts[0]
                    args = json.loads(parts[1]) if len(parts) > 1 else {}
                    
                    # Returning AIMessage with tool_calls automatically routes to ToolNode
                    return {"messages": [AIMessage(content="", tool_calls=[{
                        "name": tool_name,
                        "args": args,
                        "id": f"call_{tool_name}"
                    }])]}
                except Exception as e:
                    print(f"DEBUG: Tool parsing failed: {e}")
                    return {"messages": [AIMessage(content="I encountered an error formatting the tool arguments.")]}
            
            # Normal conversational response
            return {"messages": [AIMessage(content=content)]}

        # --- GRAPH CONSTRUCTION ---
        workflow = StateGraph(MessagesState)
        
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", tool_node) 
        
        workflow.add_edge(START, "agent")
        
        # LangGraph's built-in router checks for tool_calls and routes appropriately
        workflow.add_conditional_edges("agent", tools_condition)
        workflow.add_edge("tools", "agent")

        # Compile with checkpointer for context persistence and time-travel workflows
        app = workflow.compile(checkpointer=shared_checkpointer)
        config = {"configurable": {"thread_id": thread_id}}

        # Process the input and return the final message
        final_state = await app.ainvoke({"messages": [HumanMessage(content=user_input)]}, config=config)
        return final_state["messages"][-1].content

    finally:
        if hasattr(mcp_client, "close"): 
            await mcp_client.close()

# --- ADK ENTRYPOINT ---
@entrypoint
async def main(data, context):
    user_prompt = data.get("prompt") or data.get("text") or "Hello"
    thread_id = data.get("thread_id", "default-session")
    
    try:
        response = await run_golden_agent(user_prompt, thread_id)
        return {"result": response}
    except Exception as e:
        print(f"CRITICAL ERROR: {str(e)}")
        return {"error": f"Agent encountered an issue: {str(e)}"}
