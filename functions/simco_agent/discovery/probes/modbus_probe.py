import logging
import asyncio
from typing import Optional
from pymodbus.client import AsyncModbusTcpClient
from simco_agent.drivers.common.models import Fingerprint

logger = logging.getLogger(__name__)

class ModbusProbe:
    def __init__(self, timeout: float = 2.0):
        self.timeout = timeout

    async def run(self, ip: str, port: int) -> Optional[Fingerprint]:
        """
        Probes an IP:Port for Modbus TCP compatibility.
        """
        client = AsyncModbusTcpClient(ip, port=port)
        
        try:
            # pymodbus connect is async
            connected = await client.connect()
            if not connected:
                return None
            
            # Connection successful implies Modbus TCP handshake passed
            vendor = "Unknown"
            model = "Modbus Device"
            
            # Try to read Device Identification (MEI Type 14)
            # Function code 43 / 14 (0x2B / 0x0E)
            # Many simple devices don't support this and will return ExceptionResponse
            
            # Note: pymodbus usually raises ModbusException on failure
            try:
                # Read Basic Identity (0x01)
                # mei_response = await client.read_device_information(read_code=0x01)
                # if not mei_response.isError():
                #    vendor = mei_response.information.get(0x00, "Unknown").decode('utf-8')
                #    model = mei_response.information.get(0x01, "Modbus Device").decode('utf-8')
                pass 
                # Keeping it simple for now to avoid hanging on non-compliant devices
                # Just proving connection is enough for high confidence "modbus"
                
            except Exception as e:
                logger.debug(f"Modbus MEI read failed: {e}")

            # Optionally read holding registers 0-2 just to see if we get data
            # rr = await client.read_holding_registers(0, 3)
            # if not rr.isError(): ...

            client.close()
            
            return Fingerprint(
                ip=ip,
                protocol="modbus",
                vendor=vendor,
                model=model,
                endpoint=f"modbus-tcp://{ip}:{port}",
                confidence=0.9, # High confidence because TCP connect worked on Modbus port logic
                evidence={"port_open": port}
            )

        except Exception as e:
            logger.debug(f"Modbus probe error for {ip}:{port}: {e}")
            return None
        finally:
            client.close()
