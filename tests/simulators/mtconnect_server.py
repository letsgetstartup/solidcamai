import logging
import asyncio
from aiohttp import web

logger = logging.getLogger(__name__)

class MTConnectSimulator:
    def __init__(self, port: int = 7878):
        self.port = port
        self.app = web.Application()
        self.app.router.add_get('/probe', self.handle_probe)
        self.app.router.add_get('/current', self.handle_current)
        self.runner = None
        self.site = None

    async def start(self):
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, '127.0.0.1', self.port)
        await self.site.start()
        logger.info(f"MTConnect Simulator started on port {self.port}")

    async def stop(self):
        if self.runner:
            await self.runner.cleanup()

    async def handle_probe(self, request):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<MTConnectDevices xmlns:m="urn:mtconnect.org:MTConnectDevices:1.3" xmlns="urn:mtconnect.org:MTConnectDevices:1.3">
  <Header creationTime="2023-01-01T00:00:00Z" sender="SIMULATOR" instanceId="123" version="1.3" bufferSize="1000"/>
  <Devices>
    <Device id="d1" name="vmc-3axis" uuid="uuid-123">
      <Description>Vertical Machining Center</Description>
      <Manufacturer>Haas Automation</Manufacturer>
      <Model>VF-2</Model>
      <SerialNumber>123456</SerialNumber>
    </Device>
  </Devices>
</MTConnectDevices>
"""
        return web.Response(text=xml, content_type="text/xml")

    async def handle_current(self, request):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<MTConnectStreams xmlns:m="urn:mtconnect.org:MTConnectStreams:1.3" xmlns="urn:mtconnect.org:MTConnectStreams:1.3">
  <Header creationTime="2023-01-01T00:00:00Z"/>
  <Streams>
    <DeviceStream name="vmc-3axis" uuid="uuid-123">
      <ComponentStream component="Device" name="vmc-3axis" componentId="d1">
        <Events>
          <Availability sequence="1" timestamp="2023-01-01T12:00:00Z" dataItemId="avail" name="availability">AVAILABLE</Availability>
        </Events>
      </ComponentStream>
      <ComponentStream component="Controller" name="cnc" componentId="c1">
        <Events>
          <Execution sequence="2" timestamp="2023-01-01T12:00:01Z" dataItemId="exec" name="execution">ACTIVE</Execution>
          <ControllerMode sequence="3" timestamp="2023-01-01T12:00:01Z" dataItemId="mode" name="mode">AUTOMATIC</ControllerMode>
          <Program sequence="4" timestamp="2023-01-01T12:00:01Z" dataItemId="pgm" name="program">O1001.NC</Program>
          <PartCount sequence="5" timestamp="2023-01-01T12:00:01Z" dataItemId="pc" name="part_count">42</PartCount>
        </Events>
      </ComponentStream>
      <ComponentStream component="Rotary" name="spindle" componentId="s1">
        <Samples>
           <RotaryVelocity sequence="6" timestamp="2023-01-01T12:00:02Z" dataItemId="s1_speed" name="spindle_speed" subType="ACTUAL">1200.5</RotaryVelocity>
           <Load sequence="7" timestamp="2023-01-01T12:00:02Z" dataItemId="s1_load" name="spindle_load">15.2</Load>
        </Samples>
      </ComponentStream>
      <ComponentStream component="Linear" name="x" componentId="x1">
         <Samples>
            <PathFeedrate sequence="8" timestamp="2023-01-01T12:00:02Z" dataItemId="pfr" name="path_feedrate" subType="ACTUAL">500</PathFeedrate>
         </Samples>
      </ComponentStream>
    </DeviceStream>
  </Streams>
</MTConnectStreams>"""
        return web.Response(text=xml, content_type="text/xml")
