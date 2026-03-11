import os
import asyncio
from typing import Optional, TypedDict, Annotated
from dotenv import load_dotenv

# LangChain & LangGraph imports
from langchain_gradient import ChatGradient
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages

# MCP Adapter imports
from langchain_mcp_adapters.client import MultiServerMCPClient

# Gradient ADK imports
from gradient_adk import entrypoint

# Load variables from .env
load_dotenv()

# --- Define the AgentState inline ---
class AgentState(TypedDict):
    # add_messages ensures that new messages are appended to the list, 
    # rather than overwriting the existing messages.
    messages: Annotated[list, add_messages]

# 1. Define the Agent Logic
async def run_mcp_agent(user_input: str, thread_id: str):
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
    
    tools = await client.get_tools()
    
    # Using api_key parameter to bypass the environment lookup error
    llm = ChatGradient(
        model="llama3.3-70b-instruct",
        api_key=os.getenv("GRADIENT_MODEL_ACCESS_KEY") or os.getenv("DIGITALOCEAN_INFERENCE_KEY"),
    )
    
    llm_with_tools = llm.bind_tools(tools)

    def call_model(state: AgentState):
        response = llm_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("action", ToolNode(tools))
    workflow.add_edge(START, "agent")
    
    def should_continue(state: AgentState):
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "action"
        return END

    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("action", "agent")

    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)

    config = {"configurable": {"thread_id": thread_id}}
    input_state = {"messages": [HumanMessage(content=user_input)]}
    
    result = await app.ainvoke(input_state, config=config)
    return result["messages"][-1].content

# 2. The "Front Door" (Entrypoint)
@entrypoint
async def main(body: dict):
    user_input = body.get("prompt", "Hello")
    thread_id = body.get("thread_id", "mcp-demo-thread")

    final_response = await run_mcp_agent(user_input, thread_id)

    return {
        "response": final_response,
        "thread_id": thread_id
    }
