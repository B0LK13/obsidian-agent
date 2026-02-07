const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const PORT = process.env.PORT || 3000;
const API_KEY = process.env.API_KEY || crypto.randomBytes(32).toString('hex');
const DATA_DIR = process.env.DATA_DIR || '/app/data';
const ADMIN_USER = process.env.ADMIN_USER || 'admin';
const ADMIN_PASS = process.env.ADMIN_PASS || 'TBA-Moltbot@2026';

// Session store
const sessions = new Map();
const SESSION_DURATION = 24 * 60 * 60 * 1000; // 24 hours

// In-memory store (persisted to file)
let config = {
    name: 'Moltbot',
    version: '1.0.0',
    description: 'The Black Agency Bot Platform',
    features: [],
    settings: {}
};

// Load config from file
const configPath = path.join(DATA_DIR, 'config.json');
try {
    if (fs.existsSync(configPath)) {
        config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    }
} catch (e) {
    console.log('No existing config, using defaults');
}

// Save config to file
function saveConfig() {
    try {
        fs.mkdirSync(DATA_DIR, { recursive: true });
        fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
    } catch (e) {
        console.error('Failed to save config:', e.message);
    }
}

// Generate session token
function createSession(username) {
    const token = crypto.randomBytes(32).toString('hex');
    sessions.set(token, { username, created: Date.now() });
    return token;
}

// Validate session
function validateSession(token) {
    if (!token) return false;
    const session = sessions.get(token);
    if (!session) return false;
    if (Date.now() - session.created > SESSION_DURATION) {
        sessions.delete(token);
        return false;
    }
    return true;
}

// Get session from cookie
function getSessionFromCookie(req) {
    const cookies = req.headers.cookie || '';
    const match = cookies.match(/session=([^;]+)/);
    return match ? match[1] : null;
}

// Auth middleware for API
function checkAuth(req) {
    const authHeader = req.headers['authorization'];
    if (!authHeader) return false;
    const token = authHeader.replace('Bearer ', '');
    return token === API_KEY;
}

// Parse JSON body
function parseBody(req) {
    return new Promise((resolve, reject) => {
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', () => {
            try {
                resolve(body ? JSON.parse(body) : {});
            } catch (e) {
                reject(e);
            }
        });
    });
}

// Parse URL-encoded body
function parseFormBody(req) {
    return new Promise((resolve, reject) => {
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', () => {
            try {
                const params = new URLSearchParams(body);
                resolve(Object.fromEntries(params));
            } catch (e) {
                reject(e);
            }
        });
    });
}

// Login Page HTML
const loginHTML = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Moltbot - Login</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-gray-900 text-white min-h-screen flex items-center justify-center">
    <div class="w-full max-w-md">
        <div class="bg-gray-800 rounded-2xl shadow-2xl p-8 border border-gray-700">
            <div class="text-center mb-8">
                <div class="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-full mb-4">
                    <i class="fas fa-robot text-3xl"></i>
                </div>
                <h1 class="text-2xl font-bold">Moltbot</h1>
                <p class="text-gray-400 text-sm mt-1">The Black Agency Bot Platform</p>
            </div>
            
            <form id="loginForm" method="POST" action="/login" class="space-y-6">
                <div>
                    <label class="block text-sm font-medium text-gray-400 mb-2">Username</label>
                    <div class="relative">
                        <span class="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                            <i class="fas fa-user"></i>
                        </span>
                        <input type="text" name="username" required
                            class="w-full bg-gray-700 border border-gray-600 rounded-lg pl-10 pr-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                            placeholder="Enter username">
                    </div>
                </div>
                
                <div>
                    <label class="block text-sm font-medium text-gray-400 mb-2">Password</label>
                    <div class="relative">
                        <span class="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                            <i class="fas fa-lock"></i>
                        </span>
                        <input type="password" name="password" required
                            class="w-full bg-gray-700 border border-gray-600 rounded-lg pl-10 pr-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                            placeholder="Enter password">
                    </div>
                </div>

                <div id="error" class="hidden bg-red-900/50 border border-red-700 text-red-300 px-4 py-3 rounded-lg text-sm">
                    <i class="fas fa-exclamation-circle mr-2"></i>
                    <span id="errorMsg">Invalid credentials</span>
                </div>
                
                <button type="submit"
                    class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition duration-200 flex items-center justify-center gap-2">
                    <i class="fas fa-sign-in-alt"></i>
                    Sign In
                </button>
            </form>
            
            <div class="mt-6 pt-6 border-t border-gray-700">
                <p class="text-center text-gray-500 text-xs">
                    <i class="fas fa-shield-alt mr-1"></i>
                    Secured with session-based authentication
                </p>
            </div>
        </div>
        
        <p class="text-center text-gray-600 text-xs mt-6">
            &copy; 2026 The Black Agency
        </p>
    </div>

    <script>
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('error') === '1') {
            document.getElementById('error').classList.remove('hidden');
        }
    </script>
</body>
</html>`;

// HTML Dashboard
const dashboardHTML = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Moltbot Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-gray-900 text-white min-h-screen">
    <nav class="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div class="flex items-center justify-between max-w-6xl mx-auto">
            <div class="flex items-center gap-3">
                <i class="fas fa-robot text-2xl text-blue-400"></i>
                <span class="text-xl font-bold">Moltbot</span>
                <span class="text-xs bg-blue-600 px-2 py-1 rounded">v1.0.0</span>
            </div>
            <div class="flex items-center gap-4">
                <span id="status" class="flex items-center gap-2">
                    <span class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                    <span class="text-sm text-gray-400">Online</span>
                </span>
                <a href="/logout" class="text-gray-400 hover:text-white transition">
                    <i class="fas fa-sign-out-alt"></i>
                </a>
            </div>
        </div>
    </nav>
    
    <main class="max-w-6xl mx-auto p-6">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div class="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-gray-400 text-sm">Status</h3>
                    <i class="fas fa-heart text-green-400"></i>
                </div>
                <p class="text-2xl font-bold text-green-400">Healthy</p>
                <p class="text-xs text-gray-500 mt-1" id="uptime">Uptime: calculating...</p>
            </div>
            <div class="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-gray-400 text-sm">Features</h3>
                    <i class="fas fa-puzzle-piece text-blue-400"></i>
                </div>
                <p class="text-2xl font-bold" id="featureCount">0</p>
                <p class="text-xs text-gray-500 mt-1">Active modules</p>
            </div>
            <div class="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-gray-400 text-sm">API</h3>
                    <i class="fas fa-key text-yellow-400"></i>
                </div>
                <p class="text-2xl font-bold text-yellow-400">Secured</p>
                <p class="text-xs text-gray-500 mt-1">Bearer token required</p>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
                    <i class="fas fa-cog text-gray-400"></i>
                    Configuration
                </h2>
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">Bot Name</label>
                        <input type="text" id="botName" class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white" value="Moltbot">
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">Description</label>
                        <textarea id="botDesc" class="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white h-20">The Black Agency Bot Platform</textarea>
                    </div>
                    <button onclick="saveConfig()" class="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded text-sm font-medium transition">
                        <i class="fas fa-save mr-2"></i>Save Configuration
                    </button>
                </div>
            </div>

            <div class="bg-gray-800 rounded-lg p-6 border border-gray-700">
                <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
                    <i class="fas fa-terminal text-gray-400"></i>
                    API Endpoints
                </h2>
                <div class="space-y-3 text-sm font-mono">
                    <div class="flex items-center justify-between p-2 bg-gray-700 rounded">
                        <span class="text-green-400">GET</span>
                        <span class="text-gray-300">/health</span>
                        <span class="text-gray-500">Health check</span>
                    </div>
                    <div class="flex items-center justify-between p-2 bg-gray-700 rounded">
                        <span class="text-green-400">GET</span>
                        <span class="text-gray-300">/api/config</span>
                        <span class="text-gray-500">Get config</span>
                    </div>
                    <div class="flex items-center justify-between p-2 bg-gray-700 rounded">
                        <span class="text-yellow-400">POST</span>
                        <span class="text-gray-300">/api/config</span>
                        <span class="text-gray-500">Update config</span>
                    </div>
                    <div class="flex items-center justify-between p-2 bg-gray-700 rounded">
                        <span class="text-green-400">GET</span>
                        <span class="text-gray-300">/api/status</span>
                        <span class="text-gray-500">System status</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="mt-6 bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
                <i class="fas fa-shield-alt text-gray-400"></i>
                Security
            </h2>
            <div class="bg-gray-700 p-4 rounded">
                <p class="text-sm text-gray-400 mb-2">API Key (use in Authorization header)</p>
                <div class="flex items-center gap-2">
                    <code id="apiKey" class="flex-1 bg-gray-900 px-3 py-2 rounded text-green-400 text-sm overflow-x-auto">••••••••••••••••</code>
                    <button onclick="toggleApiKey()" class="bg-gray-600 hover:bg-gray-500 px-3 py-2 rounded text-sm">
                        <i class="fas fa-eye"></i>
                    </button>
                </div>
                <p class="text-xs text-gray-500 mt-2">Header: Authorization: Bearer &lt;api_key&gt;</p>
            </div>
        </div>
    </main>

    <footer class="text-center py-6 text-gray-500 text-sm">
        <p>Moltbot &copy; 2026 The Black Agency</p>
    </footer>

    <script>
        const startTime = Date.now();
        let apiKeyVisible = false;
        const apiKey = '${API_KEY}';

        function updateUptime() {
            const seconds = Math.floor((Date.now() - startTime) / 1000);
            const mins = Math.floor(seconds / 60);
            const hrs = Math.floor(mins / 60);
            document.getElementById('uptime').textContent = 'Session: ' + hrs + 'h ' + (mins % 60) + 'm ' + (seconds % 60) + 's';
        }
        setInterval(updateUptime, 1000);

        function toggleApiKey() {
            apiKeyVisible = !apiKeyVisible;
            document.getElementById('apiKey').textContent = apiKeyVisible ? apiKey : '••••••••••••••••';
        }

        async function saveConfig() {
            const name = document.getElementById('botName').value;
            const description = document.getElementById('botDesc').value;
            try {
                const res = await fetch('/api/config', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer ' + apiKey
                    },
                    body: JSON.stringify({ name, description })
                });
                if (res.ok) {
                    alert('Configuration saved!');
                } else {
                    alert('Failed to save configuration');
                }
            } catch (e) {
                alert('Error: ' + e.message);
            }
        }

        async function loadConfig() {
            try {
                const res = await fetch('/api/config', {
                    headers: { 'Authorization': 'Bearer ' + apiKey }
                });
                if (res.ok) {
                    const data = await res.json();
                    document.getElementById('botName').value = data.name || 'Moltbot';
                    document.getElementById('botDesc').value = data.description || '';
                    document.getElementById('featureCount').textContent = (data.features || []).length;
                }
            } catch (e) {
                console.error('Failed to load config:', e);
            }
        }
        loadConfig();
    </script>
</body>
</html>`;

// Server
const server = http.createServer(async (req, res) => {
    const url = new URL(req.url, `http://${req.headers.host}`);
    const pathname = url.pathname;

    // CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

    if (req.method === 'OPTIONS') {
        res.writeHead(204);
        return res.end();
    }

    // Public endpoints
    if (pathname === '/health') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({
            status: 'healthy',
            service: 'moltbot',
            version: config.version,
            timestamp: new Date().toISOString()
        }));
    }

    // Login page
    if (pathname === '/login' && req.method === 'GET') {
        const sessionToken = getSessionFromCookie(req);
        if (validateSession(sessionToken)) {
            res.writeHead(302, { 'Location': '/' });
            return res.end();
        }
        res.writeHead(200, { 'Content-Type': 'text/html' });
        return res.end(loginHTML);
    }

    // Login handler
    if (pathname === '/login' && req.method === 'POST') {
        try {
            const body = await parseFormBody(req);
            if (body.username === ADMIN_USER && body.password === ADMIN_PASS) {
                const sessionToken = createSession(body.username);
                res.writeHead(302, {
                    'Location': '/',
                    'Set-Cookie': `session=${sessionToken}; Path=/; HttpOnly; SameSite=Strict; Max-Age=${SESSION_DURATION / 1000}`
                });
                return res.end();
            } else {
                res.writeHead(302, { 'Location': '/login?error=1' });
                return res.end();
            }
        } catch (e) {
            res.writeHead(302, { 'Location': '/login?error=1' });
            return res.end();
        }
    }

    // Logout handler
    if (pathname === '/logout') {
        const sessionToken = getSessionFromCookie(req);
        if (sessionToken) {
            sessions.delete(sessionToken);
        }
        res.writeHead(302, {
            'Location': '/login',
            'Set-Cookie': 'session=; Path=/; HttpOnly; Max-Age=0'
        });
        return res.end();
    }

    // Protected dashboard - require login
    if (pathname === '/' && req.method === 'GET') {
        const sessionToken = getSessionFromCookie(req);
        if (!validateSession(sessionToken)) {
            res.writeHead(302, { 'Location': '/login' });
            return res.end();
        }
        res.writeHead(200, { 'Content-Type': 'text/html' });
        return res.end(dashboardHTML);
    }

    // Protected API endpoints
    if (pathname.startsWith('/api/')) {
        if (!checkAuth(req)) {
            res.writeHead(401, { 'Content-Type': 'application/json' });
            return res.end(JSON.stringify({ error: 'Unauthorized', message: 'Valid API key required' }));
        }

        if (pathname === '/api/config' && req.method === 'GET') {
            res.writeHead(200, { 'Content-Type': 'application/json' });
            return res.end(JSON.stringify(config));
        }

        if (pathname === '/api/config' && req.method === 'POST') {
            try {
                const body = await parseBody(req);
                config = { ...config, ...body, version: '1.0.0' };
                saveConfig();
                res.writeHead(200, { 'Content-Type': 'application/json' });
                return res.end(JSON.stringify({ success: true, config }));
            } catch (e) {
                res.writeHead(400, { 'Content-Type': 'application/json' });
                return res.end(JSON.stringify({ error: 'Invalid JSON' }));
            }
        }

        if (pathname === '/api/status' && req.method === 'GET') {
            res.writeHead(200, { 'Content-Type': 'application/json' });
            return res.end(JSON.stringify({
                status: 'running',
                uptime: process.uptime(),
                memory: process.memoryUsage(),
                node: process.version,
                config: config
            }));
        }
    }

    res.writeHead(404, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Not Found' }));
});

server.listen(PORT, () => {
    console.log(`Moltbot running on port ${PORT}`);
    console.log(`API Key: ${API_KEY}`);
    console.log(`Dashboard: http://localhost:${PORT}/`);
});
