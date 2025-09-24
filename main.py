from collections.abc import AsyncIterator
import contextlib
from mcp.server.lowlevel import Server
import mcp.types as types
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Mount
from pydantic import AnyUrl
from starlette.types import Receive, Scope, Send
from eventstore import InMemoryEventStore, RedisEventStore
import uvicorn
from dotenv import load_dotenv
from Tools import market_data_tools,market_data_router,market_analysis_router,market_analysis_tools
# from options_analysis import tools as options_tools  # Commented out as the module is unresolved
load_dotenv()

app = Server("Finance MCP")

@app.call_tool()
async def call_tool(name: str, args:dict ) -> list[types.ContentBlock]:
    # have multiple routers and try each one until one works: market_data_router, market_analysis_router
    for router in [market_data_router, market_analysis_router]:
        try:
            return await router(name, args,app)
        except Exception as e:
            if not isinstance(e, ValueError):
                raise
            pass
    return [types.TextContent(type="text", text=f"Tool {name} not found. Main router")]

    
@app.list_tools()
async def list_tools() ->list[types.Tool]:
    initial_list = []
    if market_data_tools:
        initial_list.extend(market_data_tools)
    if market_analysis_tools:
        initial_list.extend(market_analysis_tools)
    return initial_list

event_store = RedisEventStore() #Reliability for streamable HTTP 

session_manager = StreamableHTTPSessionManager(
    app=app,
    event_store = event_store,
    json_response=False, #Disable JSON response for streamable HTTP
)
#ASGI handler 
async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
    await session_manager.handle_request(scope,receive,send)

@contextlib.asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    async with session_manager.run():
        try:
            yield
        finally:
            print("Lifespan shutdown")

starlette_app = Starlette(
    debug=True,
    routes=[
        Mount("/mcp",app=handle_streamable_http),

    ],
    lifespan = lifespan,
)


if __name__ == "__main__":
    uvicorn.run(starlette_app)
    
