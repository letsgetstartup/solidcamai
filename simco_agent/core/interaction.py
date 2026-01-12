import logging
import json
import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from ..config import settings

logger = logging.getLogger("simco_agent.interaction")

class InteractionAgent:
    """Agent F: Omni-Channel Interaction & Reporting Engine."""
    
    def __init__(self):
        self.notification_queue = asyncio.Queue()
        self.active_screens: Dict[str, Dict[str, Any]] = {
            "ENTRANCE": {"id": "main_hq", "type": "big_screen", "last_update": None},
            "MACHINES": {} # Targeted machine touchscreens
        }
        logger.info("Agent F: Interaction Agent Initialized for Omni-Channel delivery.")

    async def run_services(self):
        """Starts background tasks for interactions."""
        await asyncio.gather(
            self._report_loop(),
            self._notification_worker(),
            self._ui_heartbeat()
        )

    # --- 1. Reporting Engine ---
    async def _report_loop(self):
        """Periodic report generation scheduler."""
        while True:
            # Logic for Daily Report at a specific time (e.g., midnight)
            # For demonstration, we simulate a run every 2 minutes
            await self.generate_and_dispatch_report("DAILY")
            await asyncio.sleep(120)

    async def generate_and_dispatch_report(self, frequency: str):
        """Generates a production report with HTML-like structure."""
        logger.info(f"Agent F: Generating {frequency} Production Report...")
        
        # Simulate data aggregation from buffer/registry
        stats = {
            "uptime_pct": 88.4,
            "alarm_count": 3,
            "top_machine": "FANUC-01",
            "anomalies_detected": 2
        }
        
        html_content = f"""
        <html>
            <body>
                <h1>SIMCO AI {frequency} Report - {datetime.now().strftime('%Y-%m-%d')}</h1>
                <p>Overall Shop Floor Performance: <b>{stats['uptime_pct']}%</b></p>
                <ul>
                    <li>Alarms Triggered: {stats['alarm_count']}</li>
                    <li>Critical Anomalies: {stats['anomalies_detected']}</li>
                    <li>Most Productive Asset: {stats['top_machine']}</li>
                </ul>
                <hr/>
                <p>SIMCO AI Security: Audit Chain Intact.</p>
            </body>
        </html>
        """
        
        logger.info(f"Agent F: {frequency} HTML Report generated. Dispatching to notifications.")
        await self.send_notification("EMAIL", {"subject": f"{frequency} Report", "body": html_content})

    # --- 2. Screen Routing & Multi-Target Display ---
    async def update_screen(self, screen_type: str, data: Dict[str, Any]):
        """Generic router for screen updates (Entrance vs Machine)."""
        if screen_type == "ENTRANCE":
            logger.info(f"Agent F: Routing HQ Update to Entrance Big Screen: {data}")
        else:
            await self.update_targeted_screen(screen_type, data)

    async def update_targeted_screen(self, machine_id: str, data: Dict[str, Any]):
        """Dispatches telemetry specifically to a machine touchscreen."""
        if machine_id not in self.active_screens["MACHINES"]:
            self.active_screens["MACHINES"][machine_id] = {"alerts": 0}
            logger.info(f"Agent F: Initialized machine touchscreen for {machine_id}")
        
        # Route to MQTT/Websocket (Mocked)
        logger.debug(f"Agent F: Routing update to touchscreen {machine_id}: {data}")

    async def _ui_heartbeat(self):
        """Periodic push of global state to the shop entrance big screen."""
        while True:
            entrance_data = {
                "fleet_status": "READY",
                "active_jobs": 5,
                "current_shift": "NIGHT"
            }
            # Simulate pushing to HQ Big Screen
            logger.info("Agent F: Pushing KPI sync to Entrance Big Screen.")
            await asyncio.sleep(10)

    # --- 3. AI Research Chatbot (Local RAG Logic) ---
    async def investigate_machine(self, machine_id: str, query: str) -> str:
        """Deep research into machine history for investigation."""
        logger.info(f"Agent F: AI Investigation started for {machine_id}: '{query}'")
        
        # Simulate searching buffer for machine_id
        # In production, this would index buffer.jsonl or query BigQuery
        if "load" in query.lower() or "overload" in query.lower():
            return (f"SIMCO AI Research: Machine {machine_id} showed a 94% spindle load spike at 14:30 today. "
                    "Correlation found with program 'O5001_ROUGHING'. Recommend checking tool wear.")
        
        return "I found no critical events for this machine in the last 24 hours."

    # --- 4. Notification System ---
    async def send_notification(self, channel: str, message: Any):
        """Adds a notification to the async dispatch queue."""
        await self.notification_queue.put({"channel": channel, "message": message})

    async def _notification_worker(self):
        """Background worker to handle delivery of emails and alerts."""
        while True:
            notif = await self.notification_queue.get()
            ch = notif["channel"]
            msg = notif["message"]
            
            logger.info(f"Agent F: [DISPATCH] Channel: {ch} | Target: Production_Manager@shop.com")
            # Simulation of SMTP / Push delivery
            await asyncio.sleep(0.5)
            self.notification_queue.task_done()
