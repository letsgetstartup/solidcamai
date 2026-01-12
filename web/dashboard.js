import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.1/firebase-app.js";
import { getAuth, onAuthStateChanged, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut } from "https://www.gstatic.com/firebasejs/9.22.1/firebase-auth.js";
import { firebaseConfig } from "./firebase-config.js";

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// Dev Mode Configuration (Moved to top)
const urlParams = new URLSearchParams(window.location.search);
const isDev = urlParams.get('dev') === '1';
const API_BASE = isDev ? "http://127.0.0.1:8081" : "https://us-central1-solidcamal.cloudfunctions.net";
const DEV_HEADERS = {
    "X-Dev-Role": "Manager",
    "X-Dev-Tenant": "tenant_demo",
    "X-Dev-Site": "site_demo"
};

// DOM Elements
const authSection = document.getElementById('auth-section');
const dashboardSection = document.getElementById('dashboard-section');
const loginForm = document.getElementById('login-form');
const logoutBtn = document.getElementById('logout-btn');
const userEmailSpan = document.getElementById('user-email');
const authError = document.getElementById('auth-error');
const machineList = document.getElementById('machine-list');

// Auth State Monitor
// Auth State Monitor
if (isDev) {
    console.log("Dev Mode: Bypassing Auth");
    authSection.style.display = 'none';
    dashboardSection.style.display = 'block';
    logoutBtn.style.display = 'none'; // No logout in dev
    userEmailSpan.textContent = "dev@local";
    loadMachines();
} else {
    onAuthStateChanged(auth, (user) => {
        if (user) {
            // User is signed in
            authSection.style.display = 'none';
            dashboardSection.style.display = 'block';
            logoutBtn.style.display = 'block';
            userEmailSpan.textContent = user.email;
            loadMachines();
        } else {
            // User is signed out
            authSection.style.display = 'block';
            dashboardSection.style.display = 'none';
            logoutBtn.style.display = 'none';
            userEmailSpan.textContent = '';
        }
    });
}

// Login Handlers
loginForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const email = loginForm.email.value;
    const password = loginForm.password.value;
    const action = e.submitter.id;

    if (action === 'login-submit') {
        signInWithEmailAndPassword(auth, email, password)
            .catch(err => authError.textContent = err.message);
    } else if (action === 'signup-submit') {
        createUserWithEmailAndPassword(auth, email, password)
            .catch(err => authError.textContent = err.message);
    }
});

// Logout Handler
logoutBtn.addEventListener('click', () => {
    signOut(auth);
});


// Mock Machine Data for Visual Discovery
async function loadMachines() {
    try {
        const url = `${API_BASE}/portal_api/v1/tenants/tenant_demo/sites/site_demo/machines`;
        const headers = isDev ? DEV_HEADERS : {};
        const res = await fetch(url, { headers });
        const machines = await res.json();

        machineList.innerHTML = machines.map(m => `
            <tr>
                <td><img src="assets/${m.machine_id.includes('fanuc') ? 'fanuc' : 'siemens'}.png" class="machine-img" onerror="this.src='assets/simco_ai_hero_logo.png'"></td>
                <td><strong>${m.machine_id}</strong></td>
                <td><code>${m.machine_id}</code></td>
                <td>${m.ip || '---'}</td>
                <td>
                    <div class="status-cell">
                        <div class="pulse ${m.status === 'ACTIVE' ? 'active' : ''}"></div>
                        ${m.status || 'UNKNOWN'}
                    </div>
                </td>
                <td><button class="cta-button" style="padding: 5px 15px; font-size: 0.8rem;" onclick="openManageModal('${m.machine_id}')">Manage</button></td>
            </tr>
        `).join('');

        if (machines.length === 0) {
            machineList.innerHTML = '<tr><td colspan="6" style="text-align:center; padding: 20px;">No machines discovered yet.</td></tr>';
        }
    } catch (err) {
        console.error("Failed to load machines:", err);
        machineList.innerHTML = `<tr><td colspan="6" style="text-align:center; color: red;">Error: ${err.message}</td></tr>`;
    }
}

// Global modal function
window.openManageModal = async (machineId) => {
    const modal = document.getElementById('manage-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalContent = document.getElementById('modal-content');

    modalTitle.textContent = `Managing ${machineId}`;
    modalContent.innerHTML = '<p>Loading latest state and events...</p>';
    modal.style.display = 'block';

    try {
        const headers = isDev ? DEV_HEADERS : {};
        // Fetch State
        const stateRes = await fetch(`${API_BASE}/portal_api/v1/tenants/tenant_demo/sites/site_demo/machines/${machineId}/state`, { headers });
        const state = await stateRes.json();

        // Fetch Events
        const eventsRes = await fetch(`${API_BASE}/portal_api/v1/tenants/tenant_demo/sites/site_demo/events`, { headers });
        const allEvents = await eventsRes.json();
        const machineEvents = allEvents.filter(e => e.machine_id === machineId).slice(0, 10);

        modalContent.innerHTML = `
            <div class="modal-grid">
                <div class="metrics-card">
                    <h3>Latest Metrics</h3>
                    <pre>${JSON.stringify(state.metrics, null, 2)}</pre>
                </div>
                <div class="events-card">
                    <h3>Recent Events</h3>
                    ${machineEvents.length > 0 ?
                `<ul>${machineEvents.map(e => `<li>[${e.severity}] ${e.event_type}: ${e.message}</li>`).join('')}</ul>` :
                '<p>No events recorded.</p>'}
                </div>
            </div>
        `;
    } catch (err) {
        modalContent.innerHTML = `<p style="color:red;">Error: ${err.message}</p>`;
    }
}

// Ensure the modal is in the HTML
if (!document.getElementById('manage-modal')) {
    const modalHtml = `
    <div id="manage-modal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="document.getElementById('manage-modal').style.display='none'">&times;</span>
            <h2 id="modal-title">Machine Manager</h2>
            <div id="modal-content"></div>
        </div>
    </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);
}
