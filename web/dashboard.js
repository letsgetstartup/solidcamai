import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.1/firebase-app.js";
import { getAuth, onAuthStateChanged, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut } from "https://www.gstatic.com/firebasejs/9.22.1/firebase-auth.js";

// Firebase Configuration (from your project solidcamal)
const firebaseConfig = {
    apiKey: "AIzaSyCxONQZGuOsqUu85rfeh5YWlZjLonTn8e8",
    authDomain: "solidcamal.firebaseapp.com",
    projectId: "solidcamal",
    storageBucket: "solidcamal.firebasestorage.app",
    messagingSenderId: "165430767822",
    appId: "1:165430767822:web:944d131a648ecda071e09f",
    measurementId: "G-N1R51WW90Q"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

// DOM Elements
const authSection = document.getElementById('auth-section');
const dashboardSection = document.getElementById('dashboard-section');
const loginForm = document.getElementById('login-form');
const logoutBtn = document.getElementById('logout-btn');
const userEmailSpan = document.getElementById('user-email');
const authError = document.getElementById('auth-error');
const machineList = document.getElementById('machine-list');

// Auth State Monitor
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
function loadMachines() {
    const machines = [
        {
            model: "Fanuc RoboDrill B-Plus",
            id: "CNC-001-F",
            ip: "192.168.1.45",
            status: "Online / Ready",
            img: "assets/fanuc.png"
        },
        {
            model: "Siemens SINUMERIK 840D",
            id: "CNC-002-S",
            ip: "192.168.1.46",
            status: "Spindle Active",
            img: "assets/siemens.png"
        }
    ];

    machineList.innerHTML = machines.map(m => `
        <tr>
            <td><img src="${m.img}" class="machine-img"></td>
            <td><strong>${m.model}</strong></td>
            <td><code>${m.id}</code></td>
            <td>${m.ip}</td>
            <td>
                <div class="status-cell">
                    <div class="pulse"></div>
                    ${m.status}
                </div>
            </td>
            <td><button class="cta-button" style="padding: 5px 15px; font-size: 0.8rem;">Manage</button></td>
        </tr>
    `).join('');
}
