import logging
import asyncio
from asyncua import Server, ua

logger = logging.getLogger(__name__)

class OPCUASimulator:
    def __init__(self, port: int = 4840):
        self.port = port
        self.server = Server()
        self.endpoint = f"opc.tcp://127.0.0.1:{port}"
        self.server.set_endpoint(self.endpoint)

    async def start(self):
        await self.server.init()
        self.server.set_server_name("SIMCO OPC UA Simulator")
        
        # Populate BuildInfo
        # asyncua fills standard nodes, but we can update them to simulate specific vendor
        # Implementation depends on asyncua version, but typically:
        
        # server properties are in self.server.nodes.server
        # We can write to nodes if needed
        # But simpler: asyncua server defaults should be enough for basic probe test
        # Let's try to set manufacturer name
        
        try:
             # asyncua.ua.NodeId(2263, 0) is ManufacturerName
            node = self.server.get_node(ua.NodeId(2263, 0))
            await node.write_value("Siemens")
            
            node_prod = self.server.get_node(ua.NodeId(2261, 0))
            await node_prod.write_value("Sinumerik 840D sl")
            
        except Exception as e:
            logger.warning(f"Failed to populate OPC UA simulator nodes: {e}")

        await self.server.start()
        logger.info(f"OPC UA Simulator started on {self.endpoint}")

    async def stop(self):
        await self.server.stop()
