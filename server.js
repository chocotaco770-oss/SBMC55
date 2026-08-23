const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const app = express();
const PORT = process.env.PORT || 3000;
const DATA_DIR = path.join(__dirname, 'data');
const DB_FILE = path.join(DATA_DIR, 'db.json');

// Ensure data directory exists
if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
}

// Initialize database
function loadDB() {
    if (fs.existsSync(DB_FILE)) {
        return JSON.parse(fs.readFileSync(DB_FILE, 'utf-8'));
    }
    return {
        users: [],
        customMenus: [],
        uploadedFiles: [],
        loggedInUsers: [],
        sessions: {}
    };
}

function saveDB(db) {
    fs.writeFileSync(DB_FILE, JSON.stringify(db, null, 2), 'utf-8');
}

// Middleware
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Serve static files
app.use(express.static(path.join(__dirname, 'public')));

// Admin credentials
const ADMIN = { username: 'MuntasirAlvee', password: 'Alvee@1971' };

// Generate session token
function generateToken() {
    return crypto.randomBytes(32).toString('hex');
}

// Auth middleware
function authMiddleware(req, res, next) {
    const token = req.headers['authorization'];
    if (!token) {
        return res.status(401).json({ error: 'No token provided' });
    }
    const db = loadDB();
    const session = db.sessions[token];
    if (!session) {
        return res.status(401).json({ error: 'Invalid token' });
    }
    req.user = session;
    next();
}

// Admin middleware
function adminMiddleware(req, res, next) {
    if (!req.user || !req.user.isAdmin) {
        return res.status(403).json({ error: 'Admin access required' });
    }
    next();
}

// ============ AUTH ROUTES ============

// Login
app.post('/api/login', (req, res) => {
    const { username, password } = req.body;
    const db = loadDB();

    // Check admin
    if (username === ADMIN.username && password === ADMIN.password) {
        const token = generateToken();
        db.sessions[token] = { username, isAdmin: true, name: 'Admin' };
        saveDB(db);
        
        // Track login
        db.loggedInUsers = db.loggedInUsers.filter(u => u.username !== username);
        db.loggedInUsers.push({ username, time: new Date().toISOString() });
        saveDB(db);
        
        return res.json({ 
            success: true, 
            token, 
            user: { name: 'Admin', username, isAdmin: true } 
        });
    }

    // Check regular user
    const user = db.users.find(u => u.username === username && u.password === password);
    if (user) {
        const token = generateToken();
        db.sessions[token] = { username, isAdmin: false, name: user.name };
        saveDB(db);
        
        // Track login
        db.loggedInUsers = db.loggedInUsers.filter(u => u.username !== username);
        db.loggedInUsers.push({ username, time: new Date().toISOString() });
        saveDB(db);
        
        return res.json({ 
            success: true, 
            token, 
            user: { name: user.name, username, isAdmin: false } 
        });
    }

    return res.status(401).json({ error: 'Invalid username or password' });
});

// Signup
app.post('/api/signup', (req, res) => {
    const { name, roll, group, username, password } = req.body;
    const db = loadDB();

    // Check if username is admin
    if (username === ADMIN.username) {
        return res.status(400).json({ error: 'This username is reserved' });
    }

    // Check if username exists
    if (db.users.find(u => u.username === username)) {
        return res.status(400).json({ error: 'Username already exists' });
    }

    // Create user
    db.users.push({ name, roll, group, username, password });
    saveDB(db);

    return res.json({ success: true, message: 'Registration successful' });
});

// Logout
app.post('/api/logout', authMiddleware, (req, res) => {
    const token = req.headers['authorization'];
    const db = loadDB();
    
    // Remove from logged in users
    db.loggedInUsers = db.loggedInUsers.filter(u => u.username !== req.user.username);
    
    // Remove session
    delete db.sessions[token];
    
    saveDB(db);
    return res.json({ success: true });
});

// ============ DATA ROUTES ============

// Get all data (users, menus, files)
app.get('/api/data', authMiddleware, (req, res) => {
    const db = loadDB();
    
    if (req.user.isAdmin) {
        // Admin gets everything
        return res.json({
            users: db.users,
            customMenus: db.customMenus,
            uploadedFiles: db.uploadedFiles,
            loggedInUsers: db.loggedInUsers
        });
    } else {
        // Regular user gets menus and files only
        return res.json({
            customMenus: db.customMenus,
            uploadedFiles: db.uploadedFiles
        });
    }
});

// ============ ADMIN ROUTES ============

// Create custom menu
app.post('/api/admin/menus', authMiddleware, adminMiddleware, (req, res) => {
    const { name, parentId } = req.body;
    const db = loadDB();
    
    const newId = 'menu_' + Date.now();
    const newMenu = {
        id: newId,
        name,
        parent: parentId || null,
        files: [],
        children: []
    };
    
    if (parentId) {
        // Find parent and add as child
        function addChild(menus) {
            for (let m of menus) {
                if (m.id === parentId) {
                    if (!m.children) m.children = [];
                    m.children.push(newMenu);
                    return true;
                }
                if (m.children && addChild(m.children)) return true;
            }
            return false;
        }
        addChild(db.customMenus);
    } else {
        db.customMenus.push(newMenu);
    }
    
    saveDB(db);
    return res.json({ success: true, menu: newMenu });
});

// Delete custom menu
app.delete('/api/admin/menus/:id', authMiddleware, adminMiddleware, (req, res) => {
    const { id } = req.params;
    const db = loadDB();
    
    function deleteMenu(menus) {
        for (let i = 0; i < menus.length; i++) {
            if (menus[i].id === id) {
                menus.splice(i, 1);
                return true;
            }
            if (menus[i].children && deleteMenu(menus[i].children)) return true;
        }
        return false;
    }
    
    deleteMenu(db.customMenus);
    saveDB(db);
    return res.json({ success: true });
});

// Upload files
app.post('/api/admin/upload', authMiddleware, adminMiddleware, (req, res) => {
    const { target, files } = req.body;
    const db = loadDB();
    
    if (target.startsWith('custom:')) {
        const menuId = target.substring(7);
        
        function findMenu(menus) {
            for (let m of menus) {
                if (m.id === menuId) return m;
                if (m.children) {
                    const found = findMenu(m.children);
                    if (found) return found;
                }
            }
            return null;
        }
        
        const menu = findMenu(db.customMenus);
        if (menu) {
            files.forEach(f => {
                menu.files.push({
                    name: f.name,
                    data: f.data,
                    time: new Date().toISOString()
                });
            });
        }
    } else {
        files.forEach(f => {
            db.uploadedFiles.push({
                target,
                file: {
                    name: f.name,
                    data: f.data,
                    time: new Date().toISOString()
                }
            });
        });
    }
    
    saveDB(db);
    return res.json({ success: true });
});

// Delete uploaded file
app.delete('/api/admin/files', authMiddleware, adminMiddleware, (req, res) => {
    const { target, fileName } = req.body;
    const db = loadDB();
    
    if (target.startsWith('custom:')) {
        const menuId = target.substring(7);
        function findMenu(menus) {
            for (let m of menus) {
                if (m.id === menuId) return m;
                if (m.children) {
                    const found = findMenu(m.children);
                    if (found) return found;
                }
            }
            return null;
        }
        const menu = findMenu(db.customMenus);
        if (menu) {
            menu.files = menu.files.filter(f => f.name !== fileName);
        }
    } else {
        db.uploadedFiles = db.uploadedFiles.filter(f => !(f.target === target && f.file.name === fileName));
    }
    
    saveDB(db);
    return res.json({ success: true });
});

// Get logged in users (for admin)
app.get('/api/admin/loggedin', authMiddleware, adminMiddleware, (req, res) => {
    const db = loadDB();
    return res.json({ loggedInUsers: db.loggedInUsers });
});

// Get registered users (for admin)
app.get('/api/admin/users', authMiddleware, adminMiddleware, (req, res) => {
    const db = loadDB();
    return res.json({ users: db.users });
});

// Serve index.html for all other routes
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
