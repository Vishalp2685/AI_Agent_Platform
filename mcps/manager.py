from jsonschema import validate
import sys
from pathlib import Path
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

# Add the parent directory to the module search path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from schemas import ToolRequest,ToolResponse,ToolDefintion


class Manager():
    def __init__(self):
        self.sessions = {} # this will store the sessions of 
        # different mcp servers like File system, git , postgrese etc
        self.tool_registery = {} # info of all tools are stored here
        self.client_contexts = {}
        self.session_contexts = {}


    async def register_server(self,name,session):
        self.sessions[name] = session

        tools = await session.list_tools()
        
        for tool in tools.tools:
            
            self.tool_registery[tool.name] = ToolDefintion(
                name = tool.name,
                title= tool.title,
                description= tool.description,
                input_schema= tool.inputSchema,
                output_schema=tool.outputSchema,
                server_name="filesystem"
            )

    async def initalize(self):
        server = StdioServerParameters(
            command="npx",
            args=[
                "-y",
                "@modelcontextprotocol/server-filesystem",
                "./workspace",
            ],
        )

        client_cm = stdio_client(server)
        read, write = await client_cm.__aenter__()

        session_cm = ClientSession(read, write)
        session = await session_cm.__aenter__()
        
        await session.initialize()

        self.client_contexts["filesystem"] = client_cm
        self.session_contexts["filesystem"] = session_cm
        
        await self.register_server('filesystem',session)

    async def list_tools(self):
        return self.tool_registery.values()

    async def call_tool(self, tool:ToolRequest):
        try:
            # compare the tool.arguments with the tool_regitery
            tool_defination = self.tool_registery.get(tool.tool_name)
            validate(instance=tool.arguments,
                     schema=tool_defination.input_schema)

            # comfigure this to get the srever name dynamically,
            session = self.sessions.get('filesystem')

            result =  await session.call_tool(tool.tool_name,tool.arguments)
            return ToolResponse(
                status=True,
                data=result
            )
        except Exception as e:
            print("****************************************")
            print(f"[Error](MCP, manager.py)-> {e}")
            print("****************************************")
            return ToolResponse(
                status=False,
                data=None,
                error=e
            )




