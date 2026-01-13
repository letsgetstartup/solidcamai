import logging
import asyncio
from typing import List, Dict, Any
from .rules import RuleEvaluator
from .notify import dispatcher
from simco_agent.observability.metrics import cloud_metrics

logger = logging.getLogger(__name__)

class StreamProcessor:
    """Orchestrates machine state updates and rule evaluation."""
    
    def __init__(self):
        self.evaluator = RuleEvaluator()
        # Simulated operational store: {machine_key: last_record}
        self.state_store: Dict[str, Dict[str, Any]] = {}
        # Simulated event store for idempotency check
        self.event_ids = set()
        # Persistence for retrieval via Portal API (Ring buffer: machine_key -> list[event])
        self.event_store: Dict[str, List[Dict[str, Any]]] = {}
        self.MAX_EVENTS_PER_MACHINE = 100

    async def process_batch(self, records: List[Dict[str, Any]]):
        """Handler for EventBus subscriptions."""
        for record in records:
            await self.process_record(record)

    async def process_record(self, record: Dict[str, Any]):
        machine_key = f"{record['tenant_id']}:{record['site_id']}:{record['machine_id']}"
        prev_state = self.state_store.get(machine_key)
        
        # 1. Evaluate Rules
        derived_events = self.evaluator.evaluate(record, prev_state)
        
        # 2. Handle Derived Events
        for event in derived_events:
            if event["event_id"] in self.event_ids:
                logger.debug(f"Processor: Skipping duplicate event {event['event_id']}")
                continue
            
            self.event_ids.add(event["event_id"])
            logger.info(f"Processor: NEW EVENT generated: {event['event_type']} for {record['machine_id']}")
            cloud_metrics.counter("cloud.processor.events_emitted_count", 1, labels={"event_type": event["event_type"]})

            # Write to operational event store
            machine_key = f"{record['tenant_id']}:{record['site_id']}:{record['machine_id']}"
            if machine_key not in self.event_store:
                self.event_store[machine_key] = []
            
            self.event_store[machine_key].append(event)
            # Keep only last N events
            if len(self.event_store[machine_key]) > self.MAX_EVENTS_PER_MACHINE:
                self.event_store[machine_key].pop(0)
            
            # 3. Dispatch Notifications
            await dispatcher.dispatch(event)

        # 4. Update Operational State
        self.state_store[machine_key] = record
        # In production, write to Firestore/Redis
        logger.debug(f"Processor: Updated operational state for {machine_key}")

# Singleton instance
processor = StreamProcessor()
