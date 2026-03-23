"""MCP Gateway tool sync — discovers tools from the gateway and upserts them in the DB."""

from loguru import logger
from sqlalchemy import select

from app.config import get_settings
from app.database import async_session
from app.models.tool import Tool
from app.services.mcp_client import MCPClient

MCP_GATEWAY_CATEGORY = "mcp-gateway"
MCP_GATEWAY_SERVER_NAME = "MCP Gateway"


async def sync_mcp_gateway_tools() -> None:
    """Connect to the MCP Gateway, discover tools, and upsert Tool records.

    Called during app startup. Non-fatal — logs and returns on any failure.
    """
    settings = get_settings()
    gateway_url = settings.MCP_GATEWAY_URL
    if not gateway_url:
        return

    logger.info(f"[MCP Gateway] Syncing tools from {gateway_url}...")

    # Discover tools from gateway
    try:
        client = MCPClient(gateway_url)
        discovered = await client.list_tools()
    except Exception as e:
        logger.warning(f"[MCP Gateway] Could not connect to gateway: {e}")
        return

    if not discovered:
        logger.info("[MCP Gateway] No tools discovered from gateway")
        return

    logger.info(f"[MCP Gateway] Discovered {len(discovered)} tools")

    async with async_session() as db:
        discovered_names = set()

        for mcp_tool in discovered:
            raw_name = mcp_tool.get("name", "")
            if not raw_name:
                continue

            tool_name = f"mcp_gateway_{raw_name}"
            tool_display = f"Gateway: {raw_name}"
            tool_desc = mcp_tool.get("description", "")[:500]
            tool_schema = mcp_tool.get("inputSchema", {"type": "object", "properties": {}})
            discovered_names.add(tool_name)

            existing_r = await db.execute(select(Tool).where(Tool.name == tool_name))
            existing_tool = existing_r.scalar_one_or_none()

            if existing_tool:
                # Update in case schema/description changed
                existing_tool.display_name = tool_display
                existing_tool.description = tool_desc
                existing_tool.parameters_schema = tool_schema
                existing_tool.mcp_server_url = gateway_url
                existing_tool.mcp_server_name = MCP_GATEWAY_SERVER_NAME
                existing_tool.mcp_tool_name = raw_name
                existing_tool.enabled = True
            else:
                tool = Tool(
                    name=tool_name,
                    display_name=tool_display,
                    description=tool_desc,
                    type="mcp",
                    category=MCP_GATEWAY_CATEGORY,
                    icon="🌐",
                    parameters_schema=tool_schema,
                    mcp_server_url=gateway_url,
                    mcp_server_name=MCP_GATEWAY_SERVER_NAME,
                    mcp_tool_name=raw_name,
                    enabled=True,
                    is_default=False,
                )
                db.add(tool)

        # Disable stale gateway tools (no longer on the gateway)
        stale_query = select(Tool).where(
            Tool.category == MCP_GATEWAY_CATEGORY,
            Tool.enabled == True,
        )
        if discovered_names:
            stale_query = stale_query.where(~Tool.name.in_(discovered_names))
        stale_r = await db.execute(stale_query)
        for stale_tool in stale_r.scalars().all():
            stale_tool.enabled = False
            logger.info(f"[MCP Gateway] Disabled stale tool: {stale_tool.name}")

        await db.commit()

    logger.info(f"[MCP Gateway] Synced {len(discovered_names)} tools")
