import sqlite3
import json
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import uuid
import os
import math

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)

DB_FILE = 'service_finder.db'

def haversine(lat1, lon1, lat2, lon2):
    if not (lat1 and lon1 and lat2 and lon2): return 0
    R = 6371  # Earth radius in kilometers
    dlat = math.radians(float(lat2) - float(lat1))
    dlon = math.radians(float(lon2) - float(lon1))
    a = math.sin(dlat/2)**2 + math.cos(math.radians(float(lat1))) * math.cos(math.radians(float(lat2))) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

# Initial Services Seed Data
DEFAULT_SERVICES = [
    {'key': 'ac_service', 'displayName': 'AC Service', 'icon': '❄️', 'categories': json.dumps(['Repair', 'Installation', 'Cleaning'])},
    {'key': 'plumber', 'displayName': 'Plumbing', 'icon': '🚰', 'categories': json.dumps(['Tap Repair', 'Pipe Leak', 'Drainage'])},
    {'key': 'electrician', 'displayName': 'Electrician', 'icon': '⚡', 'categories': json.dumps(['Wiring', 'Appliance Repair', 'Lighting'])},
    {'key': 'cleaning', 'displayName': 'Cleaning', 'icon': '🧹', 'categories': json.dumps(['Home Deep Clean', 'Kitchen Clean', 'Bathroom Clean'])},
    {'key': 'painter', 'displayName': 'Painter', 'icon': '🎨', 'categories': json.dumps(['Interior Paint', 'Exterior Paint', 'Wall Decor'])},
    {'key': 'carpenter', 'displayName': 'Carpenter', 'icon': '🪑', 'categories': json.dumps(['Furniture Repair', 'Modular Kitchen', 'Door/Window'])},
    {'key': 'pest_control', 'displayName': 'Pest Control', 'icon': '🐜', 'categories': json.dumps(['General Pest', 'Termite', 'Cockroach'])},
    {'key': 'gardener', 'displayName': 'Gardener', 'icon': '🌳', 'categories': json.dumps(['Lawn Mow', 'Pruning', 'Planting'])},
    {'key': 'other', 'displayName': 'Others', 'icon': '🔧', 'categories': json.dumps(['Maintenance', 'Misc'])}
]

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Create Tables
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS services (
            key TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            icon TEXT,
            categories TEXT,
            is_custom INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS workers (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            service TEXT NOT NULL,
            cost REAL,
            lat REAL,
            lng REAL,
            bio TEXT,
            verified INTEGER DEFAULT 1,
            gender TEXT,
            experience INTEGER DEFAULT 0,
            rating REAL DEFAULT 0,
            total_reviews INTEGER DEFAULT 0,
            slots TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(service) REFERENCES services(key)
        );

        CREATE TABLE IF NOT EXISTS bookings (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            worker_id TEXT NOT NULL,
            service_key TEXT NOT NULL,
            slot TEXT,
            price REAL,
            status TEXT DEFAULT 'confirmed',
            address TEXT,
            lat REAL,
            lng REAL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(worker_id) REFERENCES workers(id)
        );
        
        CREATE TABLE IF NOT EXISTS reviews (
            id TEXT PRIMARY KEY,
            booking_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            worker_id TEXT NOT NULL,
            rating REAL,
            comments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(booking_id) REFERENCES bookings(id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(worker_id) REFERENCES workers(id)
        );
    ''')
    
    # Seed Services if empty
    c.execute('SELECT COUNT(*) FROM services')
    if c.fetchone()[0] == 0:
        c.executemany(
            'INSERT INTO services (key, display_name, icon, categories) VALUES (:key, :displayName, :icon, :categories)',
            DEFAULT_SERVICES
        )
    
    # Seed Admin User if not exists
    c.execute("SELECT COUNT(*) FROM users WHERE id = 'admin_1'")
    if c.fetchone()[0] == 0:
        c.execute('''
            INSERT INTO users (id, name, email, phone, password, role) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('admin_1', 'Admin', 'admin@smartlocal.com', '0000000000', 'Admin@123', 'admin'))
        
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

# Initialize the db on startup
init_db()

# --- ROUTES ---

@app.route('/')
def serve_index():
    return app.send_static_file('indexx.html')

@app.route('/api/services', methods=['GET'])
def get_services():
    conn = get_db_connection()
    services = conn.execute('SELECT * FROM services').fetchall()
    conn.close()
    
    result = []
    for s in services:
        result.append({
            'key': s['key'],
            'displayName': s['display_name'],
            'icon': s['icon'],
            'categories': json.loads(s['categories'] or '[]'),
            'isCustom': bool(s['is_custom'])
        })
    return jsonify(result)

@app.route('/api/admin/services', methods=['POST'])
def add_service():
    data = request.json
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO services (key, display_name, icon, categories, is_custom) 
            VALUES (?, ?, ?, ?, ?)
        ''', (data['name'], data['displayName'], data.get('icon', '🔧'), json.dumps(data.get('categories', [])), 1))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/auth/register', methods=['POST'])
def register_user():
    data = request.json
    user_id = 'user_' + str(uuid.uuid4().hex)
    
    conn = get_db_connection()
    try:
        # Check if user exists
        existing = conn.execute('SELECT id FROM users WHERE phone = ? OR email = ?', (data.get('phone'), data.get('email'))).fetchone()
        if existing:
            return jsonify({'error': 'User already exists with this phone or email.'}), 400
            
        conn.execute('''
            INSERT INTO users (id, name, email, phone, password, role)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, data['name'], data.get('email'), data.get('phone'), data['password'], data['role']))
        conn.commit()
        
        return jsonify({'success': True, 'user': {'id': user_id, 'name': data['name'], 'email': data.get('email'), 'role': data['role']}})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    role = data.get('role')
    password = data.get('password')
    email = data.get('email')
    phone = data.get('phone')
    name = data.get('name')
    
    conn = get_db_connection()
    try:
        # For Admin, strict check
        if role == 'admin':
            user = conn.execute('SELECT * FROM users WHERE role = ? AND password = ? AND LOWER(name) = LOWER(?)', 
                                (role, password, name)).fetchone()
            if not user:
                return jsonify({'error': 'Invalid admin credentials'}), 401
        else:
            # For Users/Workers, find by phone
            user = conn.execute('SELECT * FROM users WHERE role = ? AND phone = ?', (role, phone)).fetchone()
            
            # Auto-register if not exists (since we removed OTP/verification)
            if not user and name and phone:
                user_id = 'user_' + str(uuid.uuid4().hex)
                conn.execute('''
                    INSERT INTO users (id, name, email, phone, password, role)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_id, name, email, phone, password or 'Password@123', role))
                conn.commit()
                user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
            
            if not user:
                return jsonify({'error': 'User not found. Please register.'}), 404

        # Return user details
        user_res = {'id': user['id'], '_id': user['id'], 'name': user['name'], 'email': user['email'], 'role': user['role']}
        
        # If worker, attach workerId
        if role == 'worker':
            w = conn.execute('SELECT id FROM workers WHERE user_id = ?', (user['id'],)).fetchone()
            if w:
                user_res['workerId'] = w['id']

        return jsonify({
            'success': True, 
            'token': str(uuid.uuid4().hex),
            'user': user_res
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/check-duplicate', methods=['GET'])
def check_duplicate():
    phone = request.args.get('phone')
    name = request.args.get('name', '')
    email = request.args.get('email', '')
    service = request.args.get('service')
    
    conn = get_db_connection()
    try:
        if service:
            res = conn.execute('''
                SELECT COUNT(*) FROM users u
                JOIN workers w ON u.id = w.user_id
                WHERE (u.phone = ? OR LOWER(u.name) = LOWER(?)) AND w.service = ?
            ''', (phone, name, service)).fetchone()
            return jsonify({'exists': res[0] > 0})
            
        res = conn.execute('''
            SELECT COUNT(*) FROM users 
            WHERE phone = ? OR LOWER(name) = LOWER(?) OR (email != '' AND LOWER(email) = LOWER(?))
        ''', (phone, name, email)).fetchone()
        
        return jsonify({'exists': res[0] > 0})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/api/workers/register', methods=['POST'])
def register_worker():
    data = request.json
    user_data = data.get('user')
    worker_data = data.get('worker')
    
    conn = get_db_connection()
    try:
        # 1. User setup
        user = conn.execute('SELECT id FROM users WHERE phone = ?', (user_data.get('phone'),)).fetchone()
        if user:
            user_id = user['id']
        else:
            user_id = 'user_' + str(uuid.uuid4().hex)
            conn.execute('''
                INSERT INTO users (id, name, email, phone, password, role)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, user_data.get('name'), user_data.get('email'), user_data.get('phone'), user_data.get('password'), 'worker'))
            
        # 2. Worker setup
        worker_id = 'worker_' + str(uuid.uuid4().hex)
        conn.execute('''
            INSERT INTO workers (id, user_id, service, cost, lat, lng, bio, gender, experience, slots)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (worker_id, user_id, worker_data.get('service'), worker_data.get('cost'), 
              worker_data.get('latitude'), worker_data.get('longitude'), worker_data.get('bio'), 
              worker_data.get('gender'), worker_data.get('experience', 0), json.dumps(worker_data.get('slots', {}))))
              
        conn.commit()
        token = str(uuid.uuid4().hex)
        return jsonify({'success': True, 'token': token, 'user': {'id': user_id, 'name': user_data.get('name'), 'role': 'worker', 'workerId': worker_id}})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/workers', methods=['GET'])
def get_workers():
    service = request.args.get('service')
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    
    conn = get_db_connection()
    try:
        query = '''
            SELECT w.*, u.name, u.phone, u.email 
            FROM workers w
            JOIN users u ON w.user_id = u.id
            WHERE w.verified = 1
        '''
        params = []
        if service and service != 'all':
            query += ''' AND (
                LOWER(w.service) = LOWER(?) 
                OR LOWER(w.service) LIKE LOWER(?)
                OR LOWER(REPLACE(w.service, '_', ' ')) LIKE LOWER(?)
            )'''
            params.append(service)
            params.append('%_' + service)
            params.append('%' + service + '%')
            
        workers = conn.execute(query, params).fetchall()
        
        result = []
        for w in workers:
            dist = haversine(lat, lng, w['lat'], w['lng']) if lat and lng else 0
            result.append({
                'id': w['id'],
                '_id': w['id'],
                'userId': w['user_id'],
                'service': w['service'],
                'cost': w['cost'],
                'lat': w['lat'],
                'lng': w['lng'],
                'bio': w['bio'],
                'verified': bool(w['verified']),
                'gender': w['gender'],
                'experience': w['experience'],
                'rating': w['rating'],
                'totalReviews': w['total_reviews'],
                'name': w['name'],
                'phone': w['phone'],
                'distance': round(dist, 1),
                'slots': json.loads(w['slots'] or '{}')
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/workers/<worker_id>', methods=['GET'])
def get_worker(worker_id):
    conn = get_db_connection()
    try:
        worker = conn.execute('''
            SELECT w.*, u.name, u.phone, u.email 
            FROM workers w
            JOIN users u ON w.user_id = u.id
            WHERE w.id = ?
        ''', (worker_id,)).fetchone()
        
        if not worker:
            return jsonify({'error': 'Worker not found'}), 404
            
        stats = conn.execute('''
            SELECT COUNT(*) as bookings, SUM(price) as earnings
            FROM bookings
            WHERE worker_id = ? AND status = 'completed'
        ''', (worker_id,)).fetchone()
            
        return jsonify({
            'id': worker['id'],
            '_id': worker['id'],
            'userId': worker['user_id'],
            'service': worker['service'],
            'cost': worker['cost'],
            'lat': worker['lat'],
            'lng': worker['lng'],
            'bio': worker['bio'],
            'verified': bool(worker['verified']),
            'gender': worker['gender'],
            'experience': worker['experience'],
            'rating': worker['rating'],
            'totalReviews': worker['total_reviews'],
            'name': worker['name'],
            'phone': worker['phone'],
            'earnings': stats['earnings'] or 0,
            'totalBookings': stats['bookings'] or 0,
            'available': True,
            'slots': json.loads(worker['slots'] or '{}')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/workers/<worker_id>/availability', methods=['PATCH'])
def toggle_availability(worker_id):
    # Quick fix for availability toggle
    return jsonify({'success': True, 'available': True})

@app.route('/api/bookings', methods=['POST'])
def create_booking():
    data = request.json
    booking_id = 'book_' + str(uuid.uuid4().hex)
    location = data.get('location', {})
    
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO bookings (id, user_id, worker_id, service_key, slot, price, address, lat, lng, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (booking_id, data.get('userId'), data.get('workerId'), data.get('service'), data.get('slot'), 
              data.get('price'), data.get('address'), location.get('lat', 0), location.get('lng', 0), data.get('notes')))
              
        conn.commit()
        return jsonify({'success': True, 'bookingId': booking_id})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/bookings/user', methods=['GET'])
def get_user_bookings():
    user_id = request.args.get('userId')
    conn = get_db_connection()
    try:
        bookings = conn.execute('''
            SELECT b.*, u.name as worker_name
            FROM bookings b
            JOIN workers w ON b.worker_id = w.id
            JOIN users u ON w.user_id = u.id
            WHERE b.user_id = ?
            ORDER BY b.created_at DESC
        ''', (user_id,)).fetchall()
        
        res = []
        for b in bookings:
            res.append({
                '_id': b['id'],
                'workerName': b['worker_name'],
                'service': b['service_key'],
                'slot': b['slot'],
                'price': b['price'],
                'status': b['status'],
                'createdAt': b['created_at']
            })
        return jsonify(res)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/bookings/worker/<worker_id>', methods=['GET'])
def get_worker_bookings(worker_id):
    conn = get_db_connection()
    try:
        bookings = conn.execute('''
            SELECT b.*, u.name as user_name
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            WHERE b.worker_id = ?
            ORDER BY b.created_at DESC
        ''', (worker_id,)).fetchall()
        
        res = []
        for b in bookings:
            res.append({
                '_id': b['id'],
                'userName': b['user_name'],
                'service': b['service_key'],
                'slot': b['slot'],
                'price': b['price'],
                'status': b['status'],
                'createdAt': b['created_at']
            })
        return jsonify(res)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/bookings/<booking_id>/status', methods=['PATCH'])
def update_booking_status(booking_id):
    data = request.json
    conn = get_db_connection()
    try:
        conn.execute('UPDATE bookings SET status = ? WHERE id = ?', (data.get('status'), booking_id))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    conn = get_db_connection()
    try:
        users = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        workers = conn.execute('SELECT COUNT(*) FROM workers').fetchone()[0]
        bookings = conn.execute('SELECT COUNT(*) FROM bookings').fetchone()[0]
        earnings = conn.execute("SELECT SUM(price) FROM bookings WHERE status = 'completed'").fetchone()[0] or 0
        
        return jsonify({
            'totalUsers': users,
            'totalWorkers': workers,
            'totalBookings': bookings,
            'totalEarnings': earnings,
            'pendingVerifications': 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/admin/bookings', methods=['GET'])
def get_all_bookings():
    conn = get_db_connection()
    try:
        bookings = conn.execute('''
            SELECT b.*, u.name as user_name
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            ORDER BY b.created_at DESC
        ''').fetchall()
        res = []
        for b in bookings:
            res.append({
                '_id': b['id'],
                'userId': b['user_id'],
                'workerId': b['worker_id'],
                'serviceKey': b['service_key'],
                'slot': b['slot'],
                'price': b['price'],
                'status': b['status'],
                'userName': b['user_name'],
                'createdAt': b['created_at']
            })
        return jsonify(res)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/admin/users', methods=['GET'])
def get_all_users():
    conn = get_db_connection()
    try:
        users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
        res = []
        for u in users:
            res.append({
                '_id': u['id'],
                'name': u['name'],
                'email': u['email'],
                'phone': u['phone'],
                'role': u['role'],
                'createdAt': u['created_at']
            })
        return jsonify(res)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/admin/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = get_db_connection()
    try:
        # Cascade delete workers and bookings associated with user
        conn.execute('DELETE FROM bookings WHERE user_id = ?', (user_id,))
        workers = conn.execute('SELECT id FROM workers WHERE user_id = ?', (user_id,)).fetchall()
        for w in workers:
            conn.execute('DELETE FROM bookings WHERE worker_id = ?', (w['id'],))
        conn.execute('DELETE FROM workers WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/admin/workers/<worker_id>', methods=['DELETE'])
def delete_worker(worker_id):
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM bookings WHERE worker_id = ?', (worker_id,))
        conn.execute('DELETE FROM workers WHERE id = ?', (worker_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()



if __name__ == '__main__':
    print("Starting Flask server with SQLite DB...")
    port = int(os.environ.get('PORT', 80))
    app.run(host='0.0.0.0', port=port, debug=False)

