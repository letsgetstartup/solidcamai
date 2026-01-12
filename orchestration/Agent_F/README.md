# Agent F: Interaction Manager (Human-AI Cognitive Hub)

## 🎯 Overview & Mission
Agent F is the **Cognitive Interface** of the SIMCO AI ecosystem. It transforms abstract BigQuery telemetry into actionable intelligence through high-performance dashboards, real-time alerts, and an LLM-powered AI Investigator.

## 🏗️ Technical Architecture
### Deployment & Stack
- **Frontend**: Single Page Application (SPA) / Progressive Web App (PWA) served via Firebase Hosting.
- **Backend**: Python-based Firebase Cloud Functions (Gen 2).
- **Core AI**: **Retrieval-Augmented Generation (RAG)** using the BigQuery data as context.

### Data Flow
1.  **Retrieve**: Queries Agent D (Data Architect) for filtered telemetry.
2.  **Display**: Streams KPIs to the production shop floor dashboards.
3.  **Investigate**: Facilitates natural language chat about machine anomalies.

## 🚀 Production Best Practices
- **UX Excellence**: Implements Industrial Dark Mode with glassmorphism to reduce screen glare on shop floor monitors.
- **AI Guardrails**: Enforces deterministic grounding for the AI Investigator to prevent hallucinations regarding machine status.
- **Real-time Accuracy**: Uses Firebase real-time listeners for high-priority alerts (e.g., Tool Breakage).

## 🛡️ Security & Compliance
- **Access Control**: Role-Based Access Control (RBAC). Only "Shop Floor Managers" can access the Full Investigator.
- **Data Privacy**: The Investigator only shows scrubbed data as provided by Agent E.
- **Session Security**: Enforces 24-hour token expiry for dashboard access points.

## 🔄 Orchestration & Lifecycle
- **Input**: BigQuery Views (Agent D).
- **Endpoint**: `https://[PROJECT].web.app` (Landing) & `ai_investigator` (API).
- **Interface**: Omni-channel (Web, Mobile, Industrial Kiosks).
- **Failure Recovery**: Fallback to "Static Mode" (cached data) if the BigQuery API exceeds latency thresholds.

## 📊 Observability (SLIs)
- **Dashboard Load Time**: Time from URL request to first meaningful paint (FMP).
- **AI Query Latency**: Time from user question to LLM response.
- **Interaction Breadth**: % of shop floor staff actively using the "Investigator" for maintenance.

## 🏁 Operational Status
- **Current Status**: 🟢 **OPERATIONAL**
- **Last Sync**: Production Homepage deployed to Firebase Hosting.
- **Next Job Execution**: Push Aggregate KPI Alert (Spindle Load Anomaly) to Live Dashboard.
