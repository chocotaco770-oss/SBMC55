// Initialize PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

// Admin credentials
const ADMIN = {
    username: 'MuntasirAlvee',
    password: 'Alvee@1971'
};

// Initialize users from localStorage or create empty array
let users = JSON.parse(localStorage.getItem('mbbs55_users')) || [];

// Current logged in user
let currentUser = null;

// PDF variables
let pdfDoc = null;
let pageNum = 1;
let pageRendering = false;
let pageNumPending = null;
let scale = 1.5;

// DOM Elements
const loginPage = document.getElementById('loginPage');
const signupPage = document.getElementById('signupPage');
const dashboardPage = document.getElementById('dashboardPage');

const loginForm = document.getElementById('loginForm');
const signupForm = document.getElementById('signupForm');

const showSignupLink = document.getElementById('showSignup');
const showLoginLink = document.getElementById('showLogin');

const welcomeUser = document.getElementById('welcomeUser');
const logoutBtn = document.getElementById('logoutBtn');

const pdfModal = document.getElementById('pdfModal');
const closeModal = document.querySelector('.close-modal');
const canvas = document.getElementById('pdfCanvas');
const ctx = canvas.getContext('2d');

// Page navigation elements
const prevPageBtn = document.getElementById('prevPage');
const nextPageBtn = document.getElementById('nextPage');
const pageInfo = document.getElementById('pageInfo');
const zoomInBtn = document.getElementById('zoomIn');
const zoomOutBtn = document.getElementById('zoomOut');

// Menu items
const menuItems = document.querySelectorAll('.menu-item');
const sections = document.querySelectorAll('.section');

// Event Listeners
showSignupLink.addEventListener('click', (e) => {
    e.preventDefault();
    showPage('signup');
});

showLoginLink.addEventListener('click', (e) => {
    e.preventDefault();
    showPage('login');
});

loginForm.addEventListener('submit', handleLogin);
signupForm.addEventListener('submit', handleSignup);

logoutBtn.addEventListener('click', handleLogout);

closeModal.addEventListener('click', () => {
    pdfModal.classList.remove('active');
});

window.addEventListener('click', (e) => {
    if (e.target === pdfModal) {
        pdfModal.classList.remove('active');
    }
});

prevPageBtn.addEventListener('click', onPrevPage);
nextPageBtn.addEventListener('click', onNextPage);
zoomInBtn.addEventListener('click', zoomIn);
zoomOutBtn.addEventListener('click', zoomOut);

// Menu navigation
menuItems.forEach(item => {
    item.addEventListener('click', () => {
        const menuName = item.getAttribute('data-menu');
        
        // Update active menu item
        menuItems.forEach(mi => mi.classList.remove('active'));
        item.classList.add('active');
        
        // Update active section
        sections.forEach(section => section.classList.remove('active'));
        document.getElementById(`${menuName}Section`).classList.add('active');
    });
});

// View PDF buttons
document.querySelectorAll('.view-pdf').forEach(btn => {
    btn.addEventListener('click', () => {
        openPDFModal();
    });
});

// Download PDF buttons
document.querySelectorAll('.download-pdf').forEach(btn => {
    btn.addEventListener('click', () => {
        downloadPDF();
    });
});

// Functions
function showPage(page) {
    loginPage.classList.remove('active');
    signupPage.classList.remove('active');
    dashboardPage.classList.remove('active');
    
    switch(page) {
        case 'login':
            loginPage.classList.add('active');
            break;
        case 'signup':
            signupPage.classList.add('active');
            break;
        case 'dashboard':
            dashboardPage.classList.add('active');
            break;
    }
}

function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    // Check admin login
    if (username === ADMIN.username && password === ADMIN.password) {
        currentUser = { username: 'Admin', role: 'admin' };
        welcomeUser.textContent = `Welcome, Admin`;
        showPage('dashboard');
        return;
    }
    
    // Check regular user login
    const user = users.find(u => u.username === username && u.password === password);
    
    if (user) {
        currentUser = user;
        welcomeUser.textContent = `Welcome, ${user.name}`;
        showPage('dashboard');
    } else {
        alert('Invalid username or password');
    }
}

function handleSignup(e) {
    e.preventDefault();
    
    const name = document.getElementById('signupName').value;
    const roll = document.getElementById('signupRoll').value;
    const group = document.getElementById('signupGroup').value;
    const username = document.getElementById('signupUsername').value;
    const password = document.getElementById('signupPassword').value;
    
    // Check if username already exists
    if (users.find(u => u.username === username)) {
        alert('Username already exists. Please choose another.');
        return;
    }
    
    // Check if it's the admin username
    if (username === ADMIN.username) {
        alert('This username is reserved. Please choose another.');
        return;
    }
    
    // Create new user
    const newUser = {
        name,
        roll,
        group,
        username,
        password
    };
    
    users.push(newUser);
    localStorage.setItem('mbbs55_users', JSON.stringify(users));
    
    alert('Registration successful! Please login.');
    showPage('login');
    signupForm.reset();
}

function handleLogout() {
    currentUser = null;
    showPage('login');
    loginForm.reset();
}

function openPDFModal() {
    pdfModal.classList.add('active');
    loadPDF();
}

async function loadPDF() {
    try {
        // For demo purposes, we'll show a placeholder message
        // In production, you would load the actual PDF file
        const loadingTask = pdfjsLib.getDocument('prep-ex21.pdf');
        
        loadingTask.promise.then(function(pdf) {
            pdfDoc = pdf;
            document.getElementById('pageInfo').textContent = `Page 1 of ${pdf.numPages}`;
            renderPage(pageNum);
        }).catch(function(error) {
            console.log('Error loading PDF:', error);
            // Show placeholder message
            ctx.fillStyle = '#333';
            ctx.font = '20px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('PDF Document: PREP EX 21', canvas.width / 2, 100);
            ctx.font = '16px Arial';
            ctx.fillText('Place your PDF file in the same directory as index.html', canvas.width / 2, 140);
            ctx.fillText('File name: prep-ex21.pdf', canvas.width / 2, 170);
            ctx.fillText('Total Pages: 2', canvas.width / 2, 200);
        });
    } catch (error) {
        console.log('Error:', error);
    }
}

function renderPage(num) {
    pageRendering = true;
    
    pdfDoc.getPage(num).then(function(page) {
        const viewport = page.getViewport({ scale: scale });
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        
        const renderContext = {
            canvasContext: ctx,
            viewport: viewport
        };
        
        page.render(renderContext).promise.then(function() {
            pageRendering = false;
            
            if (pageNumPending !== null) {
                renderPage(pageNumPending);
                pageNumPending = null;
            }
        });
    });
    
    document.getElementById('pageInfo').textContent = `Page ${num} of ${pdfDoc.numPages}`;
}

function onPrevPage() {
    if (pageNum <= 1) {
        return;
    }
    pageNum--;
    queueRenderPage(pageNum);
}

function onNextPage() {
    if (pageNum >= pdfDoc.numPages) {
        return;
    }
    pageNum++;
    queueRenderPage(pageNum);
}

function queueRenderPage(num) {
    if (pageRendering) {
        pageNumPending = num;
    } else {
        renderPage(num);
    }
}

function zoomIn() {
    scale += 0.25;
    if (pageNum) {
        queueRenderPage(pageNum);
    }
}

function zoomOut() {
    if (scale > 0.5) {
        scale -= 0.25;
        if (pageNum) {
            queueRenderPage(pageNum);
        }
    }
}

function downloadPDF() {
    // Create a link to download the PDF
    const link = document.createElement('a');
    link.href = 'prep-ex21.pdf';
    link.download = 'PREP_EX_21.pdf';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Check if user is already logged in
function checkSession() {
    const savedUser = localStorage.getItem('mbbs55_currentUser');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        welcomeUser.textContent = `Welcome, ${currentUser.name}`;
        showPage('dashboard');
    }
}

// Save session
function saveSession() {
    if (currentUser) {
        localStorage.setItem('mbbs55_currentUser', JSON.stringify(currentUser));
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Set canvas size
    canvas.width = 800;
    canvas.height = 600;
    
    // Draw initial message on canvas
    ctx.fillStyle = '#f5f5f5';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#1a5276';
    ctx.font = 'bold 24px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('PREP EX 21', canvas.width / 2, 150);
    ctx.font = '18px Arial';
    ctx.fillStyle = '#666';
    ctx.fillText('Previous Year Question Paper', canvas.width / 2, 190);
    ctx.fillText('MBBS 55 - Sher-E-Bangla Medical College', canvas.width / 2, 220);
    ctx.font = '14px Arial';
    ctx.fillText('Click "View PDF" to open the document', canvas.width / 2, 280);
    ctx.fillText('Make sure "prep-ex21.pdf" is in the same folder', canvas.width / 2, 310);
    
    // Add page navigation
    document.getElementById('pageInfo').textContent = 'Page 1 of 1';
});

// Keyboard shortcuts for PDF viewer
document.addEventListener('keydown', (e) => {
    if (!pdfModal.classList.contains('active')) return;
    
    switch(e.key) {
        case 'ArrowLeft':
            onPrevPage();
            break;
        case 'ArrowRight':
            onNextPage();
            break;
        case '+':
        case '=':
            zoomIn();
            break;
        case '-':
            zoomOut();
            break;
        case 'Escape':
            pdfModal.classList.remove('active');
            break;
    }
});
