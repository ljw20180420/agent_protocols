import asyncio
import os
import sys
from contextlib import AsyncExitStack
from typing import Any
from uuid import uuid4

import yaml
from acp import PROTOCOL_VERSION, spawn_agent_process, text_block
from acp.client.connection import ClientSideConnection
from acp.interfaces import Client
from acp.schema import NewSessionResponse


class SimpleClient(Client):
    def __init__(self, config_file: os.PathLike) -> None:
        with open(config_file, "r") as fd:
            self.config = yaml.safe_load(fd)
        self.agent_name = None
        self.agents = {}

    async def request_permission(self, options, session_id, tool_call, **kwargs: Any):
        return {"outcome": {"outcome": "cancelled"}}

    async def session_update(self, session_id, update, **kwargs):
        print("update:", session_id, update)

    async def initialize_and_new_session(
        self, conn: ClientSideConnection
    ) -> NewSessionResponse:
        await conn.initialize(protocol_version=PROTOCOL_VERSION)
        session = await conn.new_session(cwd=os.getcwd(), mcp_servers=[])
        return session

    async def select_agent(self) -> None:
        idx = await asyncio.to_thread(
            input,
            "".join(
                [
                    f"{i}: {agent_name}\n"
                    for i, agent_name in enumerate(self.agents.keys())
                ]
            ),
        )
        while self.agent_name is None:
            try:
                self.agent_name = list(self.agents.keys())[int(idx)]
            except Exception as e:
                print(e)

    async def main(self) -> None:
        async with AsyncExitStack() as stack:
            conn_procs = [
                await stack.enter_async_context(
                    spawn_agent_process(
                        self,
                        sys.executable,
                        agent_meta["script"],
                    )
                )
                for agent_name, agent_meta in self.config["agents"].items()
            ]
            sessions = await asyncio.gather(
                *[self.initialize_and_new_session(conn) for conn, proc in conn_procs]
            )
            for agent_name, (conn, proc), session in zip(
                self.config["agents"].keys(), conn_procs, sessions
            ):
                self.agents[agent_name] = {
                    "connection": conn,
                    "process": proc,
                    "session": session,
                }

            while True:
                if self.agent_name is None:
                    await self.select_agent()
                try:
                    prompt = await asyncio.to_thread(input, f"{self.agent_name}: ")
                except EOFError:
                    self.agent_name = None
                    continue
                await self.agents[self.agent_name]["connection"].prompt(
                    session_id=session.session_id,
                    prompt=[text_block(prompt)],
                    message_id=str(uuid4()),
                )
