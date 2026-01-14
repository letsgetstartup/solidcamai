import asyncio
import logging
from asyncua import Server, Client

logging.basicConfig(level=logging.DEBUG)

async def run():
    # Server
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://127.0.0.1:4844")
    async with server:
        print("Server started on 4844")
        
        # Client
        print("Client connecting...")
        async with Client(url="opc.tcp://127.0.0.1:4844") as client:
            print("Client connected!")
            # Read something
            node = client.get_node("i=84") # Root
            print(f"Root: {node}")
        print("Client disconnected")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(run())
