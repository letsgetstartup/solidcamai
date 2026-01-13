import { db } from './db.js';
import { FORM_TEMPLATES, renderForm, extractFormData } from './forms.js';

// --- Global State ---
const STATE = {
    user: JSON.parse(localStorage.getItem("simco_user")) || null,
    currentMachine: null,
    currentForm: null
};

// --- API Service (Mocking Backend for now) ---
const API_BASE = "http://127.0.0.1:8090"; // Control Plane

async function api(path, method = "GET", body = null) {
    // In PWA, we might have stored JWT token
    const token = localStorage.getItem("simco_token");
    const headers = { "Content-Type": "application/json" };
    // dev headers for MVP
    headers["X-Dev-Role"] = "Operator";
    headers["X-Dev-Tenant"] = "tenant_demo";
    headers["X-Dev-Site"] = "site_demo";

    try {
        const res = await fetch(`${API_BASE}${path}`, {
            method,
            headers,
            body: body ? JSON.stringify(body) : null
        });
        if (!res.ok) throw new Error(res.statusText);
        return await res.json();
    } catch (e) {
        throw e; // Let caller handle (e.g. offline)
    }
}

// --- Routing / View Management ---
function showView(viewId) {
    const main = document.getElementById("main-view");
    main.innerHTML = "";
    const tmpl = document.getElementById(`tmpl-${viewId}`);
    if (tmpl) {
        main.appendChild(tmpl.content.cloneNode(true));
        attachEvents(viewId);
    }
}

function updateStatus() {
    const el = document.getElementById("status_indicator");
    if (navigator.onLine) {
        el.textContent = "Online";
        el.style.color = "#4CAF50";
    } else {
        el.textContent = "Offline";
        el.style.color = "#FFD100";
    }
}

window.addEventListener('online', updateStatus);
window.addEventListener('offline', updateStatus);
updateStatus();

// --- Event Handlers ---
function attachEvents(viewId) {
    if (viewId === 'login') {
        document.getElementById('btn-login').onclick = handleLogin;
    } else if (viewId === 'home') {
        document.getElementById('user-name').textContent = STATE.user ? STATE.user.name : "Operator";
        document.getElementById('btn-scan').onclick = () => showView('scan');
        document.getElementById('btn-logout').onclick = handleLogout;
        document.getElementById('btn-sync').onclick = handleSync;
        refreshQueueCount();
    } else if (viewId === 'scan') {
        document.getElementById('btn-back-home').onclick = () => showView('home');
        document.getElementById('btn-resolve').onclick = () => {
            const code = document.getElementById('manual-code').value;
            handleResolve(code);
        };
        startScanner();
    } else if (viewId === 'machine') {
        if (STATE.currentMachine) {
            document.getElementById('machine-name').textContent = STATE.currentMachine.machine_name || "Unknown";
        }
        document.getElementById('btn-leave-machine').onclick = () => showView('home');
        document.querySelectorAll('.btn-tile').forEach(btn => {
            btn.onclick = () => handleAction(btn.dataset.action);
        });
    } else if (viewId === 'form') {
        document.getElementById('form-title').textContent = FORM_TEMPLATES[STATE.currentForm].title;
        const container = document.getElementById('form-fields');
        renderForm(FORM_TEMPLATES[STATE.currentForm], container);

        document.getElementById('btn-cancel').onclick = () => showView('machine');
        document.getElementById('btn-submit').onclick = handleSubmitForm;
    }
}

// --- Logic ---

async function handleLogin() {
    const user = document.getElementById('login-username').value;
    // Mock Login
    if (user) {
        const uObj = { name: user, id: "u_" + user };
        localStorage.setItem("simco_user", JSON.stringify(uObj));
        STATE.user = uObj;
        showView('home');
    } else {
        document.getElementById('login-error').classList.remove('hidden');
        document.getElementById('login-error').textContent = "Invalid credentials";
    }
}

function handleLogout() {
    localStorage.removeItem("simco_user");
    STATE.user = null;
    showView('login');
}

let html5QrCode;
function startScanner() {
    // Only attempt if library loaded
    if (window.Html5Qrcode) {
        html5QrCode = new Html5Qrcode("qr-reader");
        html5QrCode.start(
            { facingMode: "environment" },
            { fps: 10, qrbox: 250 },
            (decodedText) => {
                // Handle scan
                console.log("Scanned:", decodedText);
                html5QrCode.stop();
                // Extract code from URL (assume https://.../m/CODE)
                const parts = decodedText.split('/m/');
                const code = parts.length > 1 ? parts[1] : decodedText;
                handleResolve(code);
            },
            (errorMessage) => {
                // ignore errors
            }
        ).catch(err => console.log("Camera error", err));
    }
}

async function handleResolve(code) {
    if (!code) return;
    try {
        // GET /mobile/v1/machines/by-token/{public_code}/context
        const machine = await api(`/mobile/v1/machines/by-token/${code}/context`);
        STATE.currentMachine = machine;
        showView('machine');
    } catch (e) {
        alert("Could not find machine. " + e.message);
    }
}

function handleAction(actionType) {
    STATE.currentForm = actionType;
    showView('form');
}

async function handleSubmitForm() {
    const payload = extractFormData(FORM_TEMPLATES[STATE.currentForm]);
    const event = {
        id: crypto.randomUUID(),
        machine_id: STATE.currentMachine.machine_id,
        event_type: STATE.currentForm.toUpperCase(),
        timestamp: new Date().toISOString(),
        payload: payload,
        synced: false
    };

    // Offline First: Save to DB
    await db.addEvent(event);

    // Try Sync
    if (navigator.onLine) {
        await handleSync();
    }

    alert("Report submitted!");
    showView('machine');
}

async function refreshQueueCount() {
    try {
        const count = await db.count();
        document.getElementById('queue-count').textContent = count;
        if (count > 0) {
            document.getElementById('queue-list').textContent = `${count} events waiting to sync.`;
        }
    } catch (e) { }
}

async function handleSync() {
    const events = await db.getAllEvents();
    if (events.length === 0) return;

    document.getElementById('btn-sync').textContent = "Syncing...";

    for (const ev of events) {
        try {
            // POST /api/v1/ingest (Using existing ingest endpoint or new mobile one)
            // For now, we mock success
            console.log("Uploading", ev);
            // Simulate API call
            await new Promise(r => setTimeout(r, 500));

            // On success, remove from DB
            await db.removeEvent(ev.id);
        } catch (e) {
            console.error("Sync failed for", ev.id, e);
        }
    }

    document.getElementById('btn-sync').textContent = "Sync Now";
    refreshQueueCount();
}

// --- Init ---
if (STATE.user) {
    showView('home');
} else {
    showView('login');
}
