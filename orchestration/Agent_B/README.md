# Agent B: Edge Ingestor (High-Performance Industrial Gateway)

## 🎯 Overview & Mission
Agent B is the **Data Acquisition heartbeat** of the system. It is responsible for high-frequency polling, signal normalization, and real-time Edge AI anomaly detection to prevent tool breakage and costly shop-floor downtime.

## 🏗️ Technical Architecture
### Deployment & Stack
- **Protocols Supported**: MTConnect (HTTP), OPC-UA (TCP), Modbus/TCP.
- **Processing**: Weighted Moving Average (WMA) for signal smoothing.
- **Edge AI**: **LSTM-Autoencoder** running on TensorFlow Lite for real-time anomaly detection.

### Data Flow
1. **Poll**: Concurrent retrieval from CNC registry (Agent A).
2. **Normalize**: Signal unit standardization (e.g., Celsius, RPM, Load %).
3. **Analyze**: Edge AI inference for anomaly scoring.

## 🚀 Production Best Practices
- **Sampling Rate**: Optimized 10Hz sampling for high-load operations; downsampling during machine idle states to save storage.
- **Resource Constraints**: **Model Quantization** (INT8) used to allow AI inference on low-power industrial IPC hardware.
- **Data Quality**: Automated outlier rejection and sensor drift compensation.

## 🛡️ Security & Compliance
- **Data Perimeter**: Zero-trust polling. Only allows connections to IPs validated by Agent A.
- **Integrity**: Every telemetry packet is cryptographically signed at the source.
- **Privacy**: Local-only processing of operator interaction data; only machine physics are sent to the cloud.

## 🔄 Orchestration & Lifecycle
- **Input**: Machine Registry (Agent A).
- **Trigger**: Event-driven (New machine discovered) or Continuous Polling.
- **Consumer**: Agent C (Cloud Uplink) receives the normalized stream.
- **Failure Recovery**: Auto-checkpointing of ingestion offsets to prevent data gaps during service restarts.

## 📊 Observability (SLIs)
- **Ingestion Latency**: Time from sensor read to normalized JSON.
- **Anomaly Accuracy**: Precision/Recall score of tool-breakage predictions.
- **MTBF (Mean Time Between Failures)**: Availability of machine polling threads.

## 🏁 Operational Status
- **Current Status**: 🟢 **OPERATIONAL**
- **Last Sync**: Signal normalization complete for active machines.
- **Next Job Execution**: Edge AI Anomaly Vector Analysis in **10.0s**.
