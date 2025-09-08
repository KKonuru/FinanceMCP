from contextlib import AsyncExitStack
from typing import Optional
import pytest
import uvicorn
from multiprocessing import Process
import time
from mcp.client.streamable_http import streamablehttp_client

from mcp import ClientSession
from mcp.client.sse import sse_client

class MCPClient:
    """MCP Client for interacting with an MCP Streamable HTTP server"""

    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    async def connect_to_streamable_http_server(
        self, server_url: str, headers: Optional[dict] = None
    ):
        """Connect to an MCP server running with HTTP Streamable transport"""
        self._streams_context = streamablehttp_client(  # pylint: disable=W0201
            url=server_url,
            headers=headers or {},
        )
        read_stream, write_stream, _ = await self._streams_context.__aenter__()  # pylint: disable=E1101

        self._session_context = ClientSession(read_stream, write_stream)  # pylint: disable=W0201
        self.session: ClientSession = await self._session_context.__aenter__()  # pylint: disable=C2801

        await self.session.initialize()

    async def process_tool_call(self,tool_call_name:str,tool_args:dict) -> str:

        #Test tool call for get-options-dates
        result = await self.session.call_tool(tool_call_name, tool_args)
        return result
        

    
    async def cleanup(self):
        """Properly clean up the session and streams"""
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
        if self._streams_context:  # pylint: disable=W0125
            await self._streams_context.__aexit__(None, None, None)  # pylint: disable=E1101

client = MCPClient()
async def startup():
    global client
    try:
        # Try to cleanup existing connection first
        if hasattr(client, '_session_context') or hasattr(client, '_streams_context'):
            await client.cleanup()
    except:
        pass
    
    # Create a fresh client for each test
    client = MCPClient()
    await client.connect_to_streamable_http_server(
        f"http://localhost:8000/mcp"
    )
    

@pytest.mark.asyncio
@pytest.mark.parametrize("tool_name, args", [
    ("get-stock-price-data",{"ticker":"AAPL"}),
    ("get-options-dates", {"ticker": "AAPL"}),
    ("get-stock-price-data", {"ticker": "AAPL","timeframe":"30d"}),
    ("get-dividend-history", {"ticker": "AAPL","years_back":"2"}),
    ("get-earnings-calendar", {"ticker": "AAPL"}),
])
async def test_tool_call( tool_name, args):
    # Always create a fresh connection for each test
    await startup()
    
    # Try without trailing slash first
    response = await client.process_tool_call(tool_name,args)
    assert response is not  None
    if tool_name=="get-options-dates":
        from datetime import datetime
        current_year = datetime.now().year
        assert str(current_year) in str(response)
    elif tool_name=="get-stock-price-data":
        assert "AAPL" in str(response)
    elif tool_name=="get-stock-price-data":
         assert "AAPL" in str(response)
         assert "30d" in str(response)
    elif tool_name=="get-dividend-history":
         assert "AAPL" in str(response)
         assert "dividend" in str(response).lower()
    elif tool_name=="get-earnings-calendar":
        assert "AAPL" in str(response)
        assert "earnings" in str(response).lower()

