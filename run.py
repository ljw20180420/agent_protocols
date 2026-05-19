import asyncio
import logging
import os
import sys
from uuid import uuid4

from acp import PROTOCOL_VERSION, spawn_agent_process, text_block
from acp.client.connection import ClientSideConnection

from agent_protocols.acp.client import SimpleClient


async def interactive_loop(conn: ClientSideConnection, session_id: str) -> None:
    while True:
        try:
            line = await asyncio.to_thread(input, "> ")
        except EOFError:
            break
        except KeyboardInterrupt:
            print("", file=sys.stderr)
            break

        if not line:
            continue

        try:
            await conn.prompt(
                session_id=session_id,
                prompt=[text_block(line)],
                message_id=str(uuid4()),
            )
        except Exception as exc:
            logging.error("Prompt failed: %s", exc)  # noqa: TRY400


async def main(agent_script: os.PathLike) -> None:
    with spawn_agent_process(
        SimpleClient,
        sys.executable,
        agent_script,
    ) as (conn, proc):
        await conn.initialize(protocol_version=PROTOCOL_VERSION)
        session = await conn.new_session(cwd=os.getcwd(), mcp_servers=[])
        await interactive_loop(conn, session.session_id)


if __name__ == "__main__":
    sys.exit(asyncio.run(main("src/agent_protocols/acp/agents/echo_agent.py")))
