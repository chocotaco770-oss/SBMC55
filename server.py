#!/usr/bin/env python3
import http.server
import json
import os
import hashlib
import secrets
import urllib.parse

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
DB_FILE = os.path.join(DATA_DIR, 'db.json')
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public')
PORT = 3000

ADMIN = {'username': 'MuntasirAlvee', 'password': 'Alvee@1971'}

# --- DB helpers ---
os.makedirs(DATA_DIR, exist_ok=True)

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'users': [], 'customMenus': [], 'uploadedFiles': [], 'loggedInUsers': [], 'sessions': {}}

def save_db(db):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

# --- In-memory sessions ---
sessions = {}  # token -> {username, isAdmin, name}

def gen_token():
    return secrets.token_hex(32)

def auth_from_header(handler):
    auth = handler.headers.get('Authorization', '')
    if auth and auth in sessions:
        return sessions[auth]
    return None

# --- Menu helpers ---
def find_menu(menus, menu_id):
    for m in menus:
        if m.get('id') == menu_id:
            return m
        if m.get('children'):
            found = find_menu(m['children'], menu_id)
            if found:
                return found
    return None

def delete_menu(menus, menu_id):
    for i, m in enumerate(menus):
        if m.get('id') == menu_id:
            menus.pop(i)
            return True
        if m.get('children') and delete_menu(m['children'], menu_id):
            return True
    return False

# --- Request handler ---
class APIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == '/api/data':
            self._handle_get_data()
        elif path == '/api/admin/users':
            self._handle_admin_users()
        elif path == '/api/admin/loggedin':
            self._handle_admin_loggedin()
        else:
            # Serve static files from public/
            if path == '/':
                self.path = '/index.html'
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_body()

        if path == '/api/login':
            self._handle_login(body)
        elif path == '/api/signup':
            self._handle_signup(body)
        elif path == '/api/logout':
            self._handle_logout()
        elif path == '/api/admin/menus':
            self._handle_create_menu(body)
        elif path == '/api/admin/upload':
            self._handle_upload(body)
        else:
            self._send_json(404, {'error': 'Not found'})

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_body()

        if path.startswith('/api/admin/menus/'):
            menu_id = path.split('/')[-1]
            self._handle_delete_menu(menu_id)
        elif path == '/api/admin/files':
            self._handle_delete_file(body)
        else:
            self._send_json(404, {'error': 'Not found'})

    def _read_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length)
        try:
            return json.loads(raw.decode('utf-8'))
        except:
            return {}

    def _send_json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    # --- Auth ---
    def _handle_login(self, body):
        username = body.get('username', '')
        password = body.get('password', '')
        db = load_db()

        if username == ADMIN['username'] and password == ADMIN['password']:
            token = gen_token()
            sessions[token] = {'username': username, 'isAdmin': True, 'name': 'Admin'}
            db['loggedInUsers'] = [u for u in db['loggedInUsers'] if u['username'] != username]
            db['loggedInUsers'].append({'username': username, 'time': __import__('datetime').datetime.utcnow().isoformat() + 'Z'})
            save_db(db)
            self._send_json(200, {'success': True, 'token': token, 'user': {'name': 'Admin', 'username': username, 'isAdmin': True}})
            return

        user = next((u for u in db['users'] if u['username'] == username and u['password'] == password), None)
        if user:
            token = gen_token()
            sessions[token] = {'username': username, 'isAdmin': False, 'name': user['name']}
            db['loggedInUsers'] = [u for u in db['loggedInUsers'] if u['username'] != username]
            db['loggedInUsers'].append({'username': username, 'time': __import__('datetime').datetime.utcnow().isoformat() + 'Z'})
            save_db(db)
            self._send_json(200, {'success': True, 'token': token, 'user': {'name': user['name'], 'username': username, 'isAdmin': False}})
            return

        self._send_json(401, {'error': 'Invalid username or password'})

    def _handle_signup(self, body):
        name = body.get('name', '')
        roll = body.get('roll', '')
        group = body.get('group', '')
        username = body.get('username', '')
        password = body.get('password', '')
        db = load_db()

        if username == ADMIN['username']:
            self._send_json(400, {'error': 'This username is reserved'})
            return
        if any(u['username'] == username for u in db['users']):
            self._send_json(400, {'error': 'Username already exists'})
            return

        db['users'].append({'name': name, 'roll': roll, 'group': group, 'username': username, 'password': password})
        save_db(db)
        self._send_json(200, {'success': True, 'message': 'Registration successful'})

    def _handle_logout(self):
        user = auth_from_header(self)
        if user:
            db = load_db()
            db['loggedInUsers'] = [u for u in db['loggedInUsers'] if u['username'] != user['username']]
            save_db(db)
            token = self.headers.get('Authorization', '')
            sessions.pop(token, None)
        self._send_json(200, {'success': True})

    # --- Data ---
    def _handle_get_data(self):
        user = auth_from_header(self)
        if not user:
            self._send_json(401, {'error': 'Unauthorized'})
            return
        db = load_db()
        if user.get('isAdmin'):
            self._send_json(200, {'users': db['users'], 'customMenus': db['customMenus'], 'uploadedFiles': db['uploadedFiles'], 'loggedInUsers': db['loggedInUsers']})
        else:
            self._send_json(200, {'customMenus': db['customMenus'], 'uploadedFiles': db['uploadedFiles']})

    # --- Admin ---
    def _handle_admin_users(self):
        user = auth_from_header(self)
        if not user or not user.get('isAdmin'):
            self._send_json(403, {'error': 'Admin access required'})
            return
        db = load_db()
        self._send_json(200, {'users': db['users']})

    def _handle_admin_loggedin(self):
        user = auth_from_header(self)
        if not user or not user.get('isAdmin'):
            self._send_json(403, {'error': 'Admin access required'})
            return
        db = load_db()
        self._send_json(200, {'loggedInUsers': db['loggedInUsers']})

    def _handle_create_menu(self, body):
        user = auth_from_header(self)
        if not user or not user.get('isAdmin'):
            self._send_json(403, {'error': 'Admin access required'})
            return

        name = body.get('name', '')
        parent_id = body.get('parentId')
        db = load_db()
        new_id = 'menu_' + str(int(__import__('time').time() * 1000))

        parent_val = body.get('parentVal', 'pharma')
        new_menu = {'id': new_id, 'name': name, 'parent': parent_val, 'files': [], 'children': []}

        if parent_id:
            parent = find_menu(db['customMenus'], parent_id)
            if parent:
                new_menu['parent'] = parent.get('parent') or parent_val
                if not parent.get('children'):
                    parent['children'] = []
                parent['children'].append(new_menu)
        else:
            db['customMenus'].append(new_menu)

        save_db(db)
        self._send_json(200, {'success': True, 'menu': new_menu})

    def _handle_delete_menu(self, menu_id):
        user = auth_from_header(self)
        if not user or not user.get('isAdmin'):
            self._send_json(403, {'error': 'Admin access required'})
            return
        db = load_db()
        delete_menu(db['customMenus'], menu_id)
        save_db(db)
        self._send_json(200, {'success': True})

    def _handle_upload(self, body):
        user = auth_from_header(self)
        if not user or not user.get('isAdmin'):
            self._send_json(403, {'error': 'Admin access required'})
            return

        target = body.get('target', '')
        files = body.get('files', [])
        db = load_db()

        if target.startswith('custom:'):
            menu_id = target[7:]
            menu = find_menu(db['customMenus'], menu_id)
            if menu:
                for f in files:
                    menu['files'].append({'name': f['name'], 'data': f['data'], 'time': __import__('datetime').datetime.utcnow().isoformat() + 'Z'})
        else:
            for f in files:
                db['uploadedFiles'].append({
                    'target': target,
                    'file': {'name': f['name'], 'data': f['data'], 'time': __import__('datetime').datetime.utcnow().isoformat() + 'Z'}
                })

        save_db(db)
        self._send_json(200, {'success': True})

    def _handle_delete_file(self, body):
        user = auth_from_header(self)
        if not user or not user.get('isAdmin'):
            self._send_json(403, {'error': 'Admin access required'})
            return
        target = body.get('target', '')
        file_name = body.get('fileName', '')
        db = load_db()
        if target.startswith('custom:'):
            menu_id = target[7:]
            menu = find_menu(db['customMenus'], menu_id)
            if menu:
                menu['files'] = [f for f in menu['files'] if f['name'] != file_name]
        else:
            db['uploadedFiles'] = [f for f in db['uploadedFiles'] if not (f['target'] == target and f['file']['name'] == file_name)]
        save_db(db)
        self._send_json(200, {'success': True})

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")

if __name__ == '__main__':
    print(f"Starting MBBS 55 Portal server on http://localhost:{PORT}")
    server = http.server.HTTPServer(('', PORT), APIHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()
