import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# from models.models import ChatRequest, Response
from utils.constants import MCP_PORT, MCP_TOOLS_PATH

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from langchain_openai import ChatOpenAI

from models.models import ChatRequest, Response

from utils.constants import OPENAI_API_KEY, OPENAI_MODEL

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

app = FastAPI()


origins = [
    # "http://localhost",
    # "http://localhost:8001",
    # Add more origins as needed
    '*'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def pretty_print_tool_response(response):
    print("\n=== Tool Invocation Summary ===\n")

    for message in response['messages']:
        # Check if it's an AIMessage with tool calls
        if hasattr(message, "additional_kwargs") and "tool_calls" in message.additional_kwargs:
            for call in message.additional_kwargs["tool_calls"]:
                tool_name = call["function"]["name"]
                args = call["function"]["arguments"]
                print(f"🔧 Tool Called: {tool_name}")
                print(f"📦 Arguments: {args}\n")

        # If it's a ToolMessage
        if hasattr(message, "name") and message.name:
            print(f"✅ Tool Response from '{message.name}':")
            print(f"📝 Content: {message.content}\n")

        # Final AI message
        if hasattr(message, "content") and message.content and not hasattr(message, "name"):
            print("💬 Final AI Response:")
            print(message.content)
            print("\n" + "="*40 + "\n")





async def setupAgent(inputMessage: str):
    model = ChatOpenAI(model="gpt-4o-mini")
    async with MultiServerMCPClient(
        {
            "mongodb": {
                "command": "npx",
                "args": [
                    "-y",
                    "mcp-mongo-server",
                    "mongodb://localhost:27017/email_database"
                ],
            },
            "dd_mcp_tools": {
                "command": "python",
                "args": [str(MCP_TOOLS_PATH)], # This is working
                # "args": ["./mcp_client/dd_mcp_tools.py"],
                "transport": "stdio"
            },

        }
    ) as client:
        print("got the client")
        agent = create_react_agent(model, client.get_tools())
        print("Agent created")
        print("Thinking...")
        response = await agent.ainvoke({"messages": inputMessage})
        pretty_print_tool_response(response)
        ans = response['messages'][-1].content
        # print("Created react agent")
        print("ANS: ", ans)
        return ans

@app.post("/chat", response_model=Response)
async def chat(request: ChatRequest):
    response = await setupAgent(request.message)
    return Response(response=response)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=MCP_PORT)
