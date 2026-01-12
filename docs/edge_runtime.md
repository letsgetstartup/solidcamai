# SIMCO AI | Edge Runtime & Reliability

The Edge Agent uses a specialized execution model to ensure that machine communication never compromises system stability.

## Worker Sandbox Model
Each machine driver is executed in an **isolated worker process**. 
- **Isolation**: Memory leaks or segmentation faults in a driver (especially those using binary C-libraries like FOCAS) are contained within the worker.
- **IPC**: Communication uses standard `multiprocessing.Queue` for telemetry payloads.

## Reliability Policies

### 1. Timeouts
- **Default Timeout**: 5 seconds per poll.
- **Behavior**: If a driver hangs (network lag, busy controller), the worker is terminated (`SIGTERM/SIGKILL`), and the main agent proceeds to the next cycle.

### 2. Exponential Backoff with Jitter
When a machine fails to respond:
- **Wait Time**: `2^consecutive_failures + rand(0,1)` seconds.
- **Max Delay**: 300 seconds (5 minutes).
This prevents "retry storms" on the network.

### 3. Circuit Breaker
- **Threshold**: 5 consecutive failures.
- **State**: After 5 failures, the machine is logged as **CRITICAL** and placed into a long-cooldown state.

## Store-and-Forward Buffer (SQLite)
The agent uses a durable SQLite database (`buffer.db`) to ensure telemetry is never lost during network outages.
- **Idempotency**: Every record is assigned a deterministic SHA-256 ID based on `machine_id`, `timestamp`, and core metrics. The cloud ingestor uses this ID to drop duplicates (Effectively Once semantics).
- **Persistence**: Records are kept in the `telemetry_buffer` table until successfully acknowledged by the cloud.

## Reliable Uplink
- **Batching**: Uploads are performed in batches (default: 100) to optimize network throughput.
- **Resilience**:
    - **Backoff**: If the cloud is unreachable (5xx/Timeouts), the worker uses exponential backoff with jitter (max 5 minutes).
    - **In-flight Safety**: Records being sent are marked as `in_flight`. On startup, any stale `in_flight` records are automatically returned to the `queued` state.
