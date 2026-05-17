import asyncio

from agent_protocols.acp.client import SimpleClient

asyncio.run(SimpleClient(config_file="config.yaml").main())
