import sqlite3
import os
from datetime import timedelta
from flask import Flask, jsonify, request, redirect, render_template, render_template_string, send_from_directory, session, abort
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
# Fail fast if SECRET_KEY is not provided — prevents forging sessions in production
_secret_key = os.environ.get('SECRET_KEY')
if not _secret_key:
    raise RuntimeError("SECRET_KEY environment variable is required. Set it before starting the application.")
app = Flask(__name__, static_folder='static')
app.secret_key = _secret_key
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
DB_NAME = "market.db"

# Global CSS Framework
COMMON_STYLE = """
<style>
    :root {
        --primary: #2e7d32;
        --primary-dark: #1b5e20;
        --driver-color: #1565c0;
        --buyer-color: #e65100;
        --text: #2c3e50;
    }

    body {
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
        background: linear-gradient(rgba(0, 0, 0, 0.45), rgba(0, 0, 0, 0.45)),
                    url('https://images.unsplash.com/photo-1500937386664-56d1dfef3854?q=80&w=1000&auto=format&fit=crop');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        margin: 0;
        padding: 15px;
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        box-sizing: border-box;
    }

    .gateway-container, .form-container, .dashboard-container {
        max-width: 600px;
        width: 100%;
        background: rgba(255, 255, 255, 0.94);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        padding: 35px 25px;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.25);
        box-sizing: border-box;
    }

    .dashboard-container { max-width: 1000px; }

    .brand-header { text-align: center; margin-bottom: 25px; }
    .brand-logo-container {
        width: 110px; height: 110px; background-color: #0b0c10; border-radius: 20px;
        display: inline-flex; align-items: center; justify-content: center;
        margin-bottom: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        border: 2px solid #2e7d32; overflow: hidden; padding: 5px;
    }
    .brand-logo-container img { width: 100%; height: 100%; object-fit: contain; }
    .brand-title { font-size: 1.8rem; font-weight: 800; color: var(--text); margin: 0; letter-spacing: -0.5px; }
    .brand-subtitle { font-size: 0.95rem; color: #546e7a; margin: 5px 0 0 0; }

    h2 { font-size: 1.4rem; font-weight: 700; margin-top: 0; margin-bottom: 20px; text-align: center; }
    label { display: block; margin-bottom: 6px; font-weight: 600; font-size: 0.88rem; color: #37474f; text-align: left; }

    input, select, textarea {
        width: 100%; padding: 12px; margin-bottom: 18px;
        border: 1px solid #cfd8dc; border-radius: 8px;
        box-sizing: border-box; font-size: 1rem;
        background: #fafafa; transition: all 0.2s ease;
    }
    input[type="file"] { padding: 8px; background: #fff; cursor: pointer; }
    input:focus, select:focus, textarea:focus {
        border-color: var(--primary); outline: none; background: white; box-shadow: 0 0 0 3px rgba(46,125,50,0.15);
    }

    button {
        width: 100%; border: none; padding: 14px;
        border-radius: 8px; font-size: 1.05rem; font-weight: bold;
        color: white; cursor: pointer; transition: all 0.2s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    button:hover { transform: translateY(-1px); box-shadow: 0 6px 15px rgba(0,0,0,0.2); }

    .back-btn { display: inline-flex; align-items: center; margin-bottom: 20px; color: #546e7a; text-decoration: none; font-size: 0.9rem; font-weight: 600; }
    .back-btn:hover { color: #263238; }

    /* Dashboard Grid Rules */
    .market-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 20px; margin-top: 15px; }
    .market-card { background: white; border-radius: 12px; border: 1px solid #e0e0e0; overflow: hidden; display: flex; flex-direction: column; }
    .card-img { width: 100%; height: 170px; object-fit: cover; background: #eaeaea; }
    .card-body { padding: 15px; flex: 1; display: flex; flex-direction: column; }
    .card-title { font-weight: 700; font-size: 1.1rem; margin: 0 0 5px 0; color: var(--text); }
    .card-meta { font-size: 0.85rem; color: #7f8c8d; margin-bottom: 8px; }
    .badge { display: inline-block; padding: 4px 8px; font-size: 0.75rem; font-weight: 700; border-radius: 4px; color: white; width: max-content; margin-bottom: 10px; }
</style>
"""

# Configure secure file uploads
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ==========================================
# IDEMPOTENT SCHEMA MIGRATION
# ==========================================
def init_db_fresh():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Create tables only if they do not exist — preserves all existing data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS harvest (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farm_name TEXT,
            hub TEXT,
            crop TEXT,
            quantity TEXT,
            details TEXT,
            photo_path TEXT,
            user_id INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_name TEXT,
            phone TEXT,
            vehicle_type TEXT,
            base_hub TEXT,
            photo_path TEXT,
            user_id INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS buyers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_name TEXT,
            phone TEXT,
            target_hub TEXT,
            crop_needed TEXT,
            user_id INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Ensure buyer records can be associated with authenticated users if schema was created earlier
def ensure_buyer_user_link():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(buyers)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'user_id' not in columns:
        cursor.execute('ALTER TABLE buyers ADD COLUMN user_id INTEGER')
        conn.commit()
    conn.close()

# Run the idempotent migration on application startup
init_db_fresh()
ensure_buyer_user_link()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    user = cursor.execute('SELECT id, username, role FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if not user:
        session.pop('user_id', None)
        return None
    return user

def get_buyer_profile(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    profile = cursor.execute('SELECT * FROM buyers WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    return profile

def find_matches_for_buyer(buyer_profile):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    crop_needed = (buyer_profile['crop_needed'] or '').strip().lower()
    target_hub = (buyer_profile['target_hub'] or '').strip().lower()

    harvest_matches = []
    if crop_needed:
        keywords = [keyword.strip() for keyword in crop_needed.split(',') if keyword.strip()]
        where_clauses = ' OR '.join(['lower(crop) LIKE ?' for _ in keywords])
        params = [f"%{keyword}%" for keyword in keywords]
        harvest_matches = cursor.execute(f'SELECT * FROM harvest WHERE {where_clauses}', params).fetchall()

    driver_matches = []
    if target_hub:
        driver_matches = cursor.execute('SELECT * FROM drivers WHERE lower(base_hub) LIKE ?', (f"%{target_hub}%",)).fetchall()
    conn.close()
    return {'harvest': harvest_matches, 'drivers': driver_matches}

LOGIN_HTML = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Dream Green Agro</title>
    {COMMON_STYLE}
    <style>
        button {{ background: var(--primary); }}
        button:hover {{ background: var(--primary-dark); }}
        .helper-links {{ display: flex; justify-content: space-between; gap: 10px; margin-top: 15px; }}
    </style>
</head>
<body>
    <div class="form-container">
        <h2 style="color: var(--primary);">🔐 Sign In</h2>
        <form action="/login" method="POST">
            <label>Username</label>
            <input type="text" name="username" placeholder="Username" required>
            <label>Password</label>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        <div class="helper-links">
            <a href="/signup">Create an account</a>
            <a href="/">Back to portal</a>
        </div>
    </div>
</body>
</html>
"""

SIGNUP_HTML = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sign Up - Dream Green Agro</title>
    {COMMON_STYLE}
    <style>
        button {{ background: var(--primary); }}
        button:hover {{ background: var(--primary-dark); }}
        .helper-links {{ display: flex; justify-content: space-between; gap: 10px; margin-top: 15px; }}
    </style>
</head>
<body>
    <div class="form-container">
        <h2 style="color: var(--primary);">📝 Register Account</h2>
        <form action="/signup" method="POST">
            <label>Username</label>
            <input type="text" name="username" placeholder="Choose a username" required>
            <label>Password</label>
            <input type="password" name="password" placeholder="Choose a password" required>
            <label>Role</label>
            <select name="role">
                <option value="user">User</option>
                <option value="farmer">Farmer</option>
                <option value="driver">Driver</option>
                <option value="buyer">Buyer</option>
            </select>
            <button type="submit">Create Account</button>
        </form>
        <div class="helper-links">
            <a href="/login">Have an account? Login</a>
            <a href="/">Back to portal</a>
        </div>
    </div>
</body>
</html>
"""

# Serve uploaded files publicly
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/')
def home():
    current_user = get_current_user()
    if current_user:
        if current_user['role'].lower() == 'buyer':
            user_section = f"""
                <p style=\"font-size:1rem;color:#37474f;margin-bottom:18px;\">Welcome back, <strong>{current_user['username']}</strong>! Review your science-backed sourcing match recommendations.</p>
                <a href=\"/matches\" class=\"option-card buyer\">🎯 View Recommended Matches</a>
                <a href=\"/register_buyer\" class=\"option-card buyer\">🛒 Update Sourcing Preferences</a>
                <a href=\"/dashboard\" class=\"option-card buyer\">📊 View Dashboard</a>
                <a href=\"/logout\" class=\"option-card buyer\" style=\"border-color:#e65100;\">🔓 Logout</a>
            """
        else:
            user_section = f"""
                <p style=\"font-size:1rem;color:#37474f;margin-bottom:18px;\">Welcome back, <strong>{current_user['username']}</strong>! Choose a marketplace action or visit the dashboard.</p>
                <a href=\"/dashboard\" class=\"option-card buyer\">📊 View Dashboard</a>
                <a href=\"/register\" class=\"option-card farmer\">🧑‍🌾 List Harvest</a>
                <a href=\"/register_driver\" class=\"option-card driver\">🚛 Register Driver</a>
                <a href=\"/logout\" class=\"option-card buyer\" style=\"border-color:#e65100;\">🔓 Logout</a>
            """
    else:
        user_section = f"""
            <p style=\"font-size:1rem;color:#37474f;margin-bottom:18px;\">Please log in or create an account to manage your listings safely.</p>
            <a href=\"/login\" class=\"option-card farmer\">🔐 Login</a>
            <a href=\"/signup\" class=\"option-card driver\">📝 Register</a>
        """

    HOME_PAGE_HTML = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to Dream Green Agro</title>
        {COMMON_STYLE}
        <style>
            .options-grid {{ display: flex; flex-direction: column; gap: 15px; width: 100%; margin-top: 10px; }}
            .option-card {{
                border: 1px solid #e0e0e0; border-radius: 12px; padding: 18px;
                cursor: pointer; text-decoration: none; color: inherit; transition: all 0.2s ease;
                display: flex; align-items: center; background: #fff; text-align: left;
            }}
            .option-card:hover {{ transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.08); }}
            .option-card.farmer:hover {{ border-color: var(--primary); }}
            .option-card.driver:hover {{ border-color: var(--driver-color); }}
            .option-card.buyer:hover {{ border-color: var(--buyer-color); }}
            .icon {{ font-size: 2.2rem; margin-right: 18px; min-width: 45px; text-align: center; }}
            .option-details {{ flex: 1; }}
            .option-title {{ font-weight: 700; font-size: 1.15rem; color: #2c3e50; margin-bottom: 3px; }}
            .option-desc {{ font-size: 0.85rem; color: #7f8c8d; line-height: 1.3; }}
            .plain-link {{ display: block; margin-top: 18px; color: var(--primary); font-weight: bold; text-decoration: none; text-align:center; }}
        </style>
    </head>
    <body>
        <div class="gateway-container">
            <div class="brand-header">
                <div class="brand-logo-container">
                    <img src="/static/logo.webp" alt="Dream Green Agro Logo" onerror="this.style.display='none';">
                </div>
                <h1 class="brand-title">Dream Green Agro</h1>
                <p class="brand-subtitle">Connecting ecosystem logistics & agricultural markets</p>
            </div>
            <div class="options-grid">
                {user_section}
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(HOME_PAGE_HTML)

FARMER_FORM_HTML = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>List Your Harvest - Dream Green Agro</title>
    {COMMON_STYLE}
    <style>
        .unit-group {{ display: flex; gap: 10px; margin-bottom: 0; }}
        .unit-group input {{ flex: 2; }}
        .unit-group select {{ flex: 1; }}
        button {{ background: var(--primary); }}
        button:hover {{ background: var(--primary-dark); }}
    </style>
</head>
<body>
    <div class="form-container">
        <a href="/" class="back-btn">← Back to Selection</a>
        <h2 style="color: var(--primary);">🧑‍🌾 Open Market Harvest Listing</h2>
        <form action="/api/list_harvest" method="POST" enctype="multipart/form-data">
            <label>Farm / Seller Identity</label>
            <input type="text" name="farm_name" placeholder="e.g., Green Valley Estates" required>

            <label>Nearest Local Delivery Hub / City</label>
            <input type="text" name="hub" placeholder="e.g., Chegutu" required>

            <label>Crop / Produce Type</label>
            <input type="text" name="crop" placeholder="e.g., Butternut, Tomatoes, White Maize" required>

            <div style="display: flex; gap: 10px;">
                <div style="flex: 2;"><label>Quantity</label></div>
                <div style="flex: 1;"><label>Metric Unit</label></div>
            </div>
            <div class="unit-group">
                <input type="number" step="any" name="quantity" placeholder="500" required>
                <select name="unit">
                    <option value="KG">KG</option>
                    <option value="Tons">Tons</option>
                    <option value="Bags (50kg)">Bags (50kg)</option>
                    <option value="Crates">Crates</option>
                    <option value="Litres">Litres</option>
                </select>
            </div>

            <label>Upload Produce Photo</label>
            <input type="file" name="produce_photo" accept="image/*" required>

            <label>Batch Details or Quality Grade (Optional)</label>
            <textarea name="details" rows="2" placeholder="e.g., Grade A premium quality, washed..."></textarea>

            <button type="submit">Publish Produce Listing</button>
        </form>
    </div>
</body>
</html>
"""

DRIVER_FORM_HTML = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Transporter Onboarding - Dream Green Agro</title>
    {COMMON_STYLE}
    <style>
        button {{ background: var(--driver-color); }}
        button:hover {{ background: #0d47a1; }}
        input:focus, select:focus {{ border-color: var(--driver-color); box-shadow: 0 0 0 3px rgba(21,101,192,0.15); }}
    </style>
</head>
<body>
    <div class="form-container">
        <a href="/" class="back-btn">← Back to Selection</a>
        <h2 style="color: var(--driver-color);">🚛 Logistics Onboarding</h2>
        <form action="/api/register_driver" method="POST" enctype="multipart/form-data">
            <label>Driver / Enterprise Full Name</label>
            <input type="text" name="driver_name" placeholder="e.g., John Doe" required>

            <label>Active Contact Number</label>
            <input type="tel" name="phone" placeholder="e.g., +263..." required>

            <label>Available Haulage Vehicle Type</label>
            <select name="vehicle_type">
                <option value="1-3 Ton Truck">1-3 Ton Truck</option>
                <option value="5-7 Ton Truck">5-7 Ton Truck</option>
                <option value="10+ Ton Rigid">10+ Ton Rigid</option>
                <option value="Motorcycle/Utility">Motorcycle/Utility</option>
            </select>

            <label>Primary Freight Base City</label>
            <input type="text" name="base_hub" placeholder="e.g., Harare / Chegutu" required>

            <label>Upload Vehicle Photo</label>
            <input type="file" name="vehicle_photo" accept="image/*" required>

            <button type="submit">Register Fleet Asset</button>
        </form>
    </div>
</body>
</html>
"""

BUYER_FORM_HTML = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Procurement Portal - Dream Green Agro</title>
    {COMMON_STYLE}
    <style>
        button {{ background: var(--buyer-color); }}
        button:hover {{ background: #bf360c; }}
        input:focus, select:focus {{ border-color: var(--buyer-color); box-shadow: 0 0 0 3px rgba(230,81,0,0.15); }}
    </style>
</head>
<body>
    <div class="form-container">
        <a href="/" class="back-btn">← Back to Selection</a>
        <h2 style="color: var(--buyer-color);">🛒 Enterprise Buyer Registration</h2>
        <form action="/api/register_buyer" method="POST">
            <label>Buyer / Procurement Account Name</label>
            <input type="text" name="buyer_name" placeholder="e.g., Fresh Choice Markets" required>

            <label>Procurement Team Phone Number</label>
            <input type="tel" name="phone" placeholder="e.g., +263..." required>

            <label>Intended Sourcing Delivery Destination</label>
            <input type="text" name="target_hub" placeholder="e.g., Chegutu Hub" required>

            <label>Target Commodities Seeking</label>
            <input type="text" name="crop_needed" placeholder="e.g., Onions, Honey, Potatoes" required>

            <button type="submit">Submit Sourcing Target</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/dashboard')
def dashboard():
    current_user = get_current_user()
    logged_in = current_user is not None
    username = current_user['username'] if logged_in else 'Guest'
    role = (current_user['role'] or 'user').lower() if logged_in else 'guest'

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    harvests = cursor.execute("SELECT * FROM harvest").fetchall()
    drivers = cursor.execute("SELECT * FROM drivers").fetchall()

    fetch_all_harvest_cards = ''
    if harvests:
        for row in harvests:
            fetch_all_harvest_cards += f'''
                <div class="market-card">
                    <img class="card-img" src="{row['photo_path'] if row['photo_path'] else '/static/logo.webp'}" alt="Produce" onerror="this.src='/static/logo.webp';">
                    <div class="card-body">
                        <span class="badge" style="background: var(--primary);">{row['crop']}</span>
                        <div class="card-title">{row['farm_name']} — {row['hub']}</div>
                        <div class="card-meta">📦 {row['quantity']}</div>
                        <p style="font-size: 0.85rem; color: #555; margin: 0;">{row['details']}</p>
                    </div>
                </div>
            '''
    else:
        fetch_all_harvest_cards = '<p style="color:#37474f;">No harvest listings are available yet.</p>'

    fetch_all_driver_cards = ''
    if drivers:
        for row in drivers:
            fetch_all_driver_cards += f'''
                <div class="market-card">
                    <img class="card-img" src="{row['photo_path'] if row['photo_path'] else '/static/logo.webp'}" alt="Vehicle" onerror="this.src='/static/logo.webp';">
                    <div class="card-body">
                        <span class="badge" style="background: var(--driver-color);">{row['vehicle_type']}</span>
                        <div class="card-title">{row['driver_name']}</div>
                        <div class="card-meta">📞 Contact: {row['phone']}</div>
                        <div class="card-meta" style="margin: 0; font-weight: 600;">📍 Operational Hub: {row['base_hub']}</div>
                    </div>
                </div>
            '''
    else:
        fetch_all_driver_cards = '<p style="color:#37474f;">No transport providers are registered yet.</p>'

    role_section = ''
    header_actions = ''
    if logged_in:
        header_actions = f'<a href="/logout" style="background:#e65100;">Logout</a><div style="margin-top: 15px;"><a href="/feedback" style="color: #2e7d32; text-decoration: none; font-weight: bold; display: inline-block; padding: 10px 15px; background: rgba(46, 125, 50, 0.1); border-radius: 4px;">💬 Share System Feedback</a></div>'
        if role == 'farmer':
            farmer_harvests = cursor.execute('SELECT * FROM harvest WHERE user_id = ?', (current_user['id'],)).fetchall()
            harvest_cards = ''
            if farmer_harvests:
                for row in farmer_harvests:
                    harvest_cards += f'''
                        <div class="market-card">
                            <img class="card-img" src="{row['photo_path'] if row['photo_path'] else '/static/logo.webp'}" alt="Produce" onerror="this.src='/static/logo.webp';">
                            <div class="card-body">
                                <span class="badge" style="background: var(--primary);">{row['crop']}</span>
                                <div class="card-title">{row['farm_name']} — {row['hub']}</div>
                                <div class="card-meta">📦 {row['quantity']}</div>
                                <p style="font-size: 0.85rem; color: #555; margin: 0;">{row['details']}</p>
                                <a href="/api/delete/harvest/{row['id']}" class="back-btn" style="display:inline-block;margin-top:14px;background:#d32f2f;color:#fff;">🗑️ Delete Listing</a>
                            </div>
                        </div>
                    '''
            if not harvest_cards:
                harvest_cards = '<p style="color:#37474f;">You have no crop listings yet.</p>'
            role_section = f'''
                <h3>🧑‍🌾 Your Harvest Listings</h3>
                <div class="market-grid">{harvest_cards}</div>
                <h3>📤 List a New Harvest</h3>
                <div class="form-container" style="background:#fff; padding:20px; box-shadow:none; border:none;">
                    <form action="/api/list_harvest" method="POST" enctype="multipart/form-data">
                        <label>Farm / Seller Identity</label>
                        <input type="text" name="farm_name" placeholder="e.g., Green Valley Estates" required>
                        <label>Nearest Local Delivery Hub / City</label>
                        <input type="text" name="hub" placeholder="e.g., Chegutu" required>
                        <label>Crop / Produce Type</label>
                        <input type="text" name="crop" placeholder="e.g., Butternut, Tomatoes, White Maize" required>
                        <div style="display:flex; gap:10px;"><div style="flex:2;"><label>Quantity</label></div><div style="flex:1;"><label>Metric Unit</label></div></div>
                        <div style="display:flex; gap:10px;"><input type="number" step="any" name="quantity" placeholder="500" required><select name="unit"><option value="KG">KG</option><option value="Tons">Tons</option><option value="Bags (50kg)">Bags (50kg)</option><option value="Crates">Crates</option><option value="Litres">Litres</option></select></div>
                        <label>Upload Produce Photo</label>
                        <input type="file" name="produce_photo" accept="image/*" required>
                        <label>Batch Details or Quality Grade (Optional)</label>
                        <textarea name="details" rows="2" placeholder="e.g., Grade A premium quality, washed..."></textarea>
                        <button type="submit" style="background: var(--primary);">Publish Produce Listing</button>
                    </form>
                </div>
            '''
        elif role == 'buyer':
            header_actions = f'<a href="/matches" class="helper-link" style="background: var(--primary);">View Matches</a><a href="/logout" style="background:#e65100;">Logout</a><div style="margin-top: 15px;"><a href="/feedback" style="color: #2e7d32; text-decoration: none; font-weight: bold; display: inline-block; padding: 10px 15px; background: rgba(46, 125, 50, 0.1); border-radius: 4px;">💬 Share System Feedback</a></div>'
            buyer_profile = cursor.execute('SELECT * FROM buyers WHERE user_id = ?', (current_user['id'],)).fetchone()
            buyer_name = buyer_profile['buyer_name'] if buyer_profile else ''
            phone = buyer_profile['phone'] if buyer_profile else ''
            target_hub = buyer_profile['target_hub'] if buyer_profile else ''
            crop_needed = buyer_profile['crop_needed'] if buyer_profile else ''
            profile_message = 'Update your sourcing requirements below.' if buyer_profile else 'Tell us what crops and hubs you are looking for.'
            role_section = f'''
                <h3>🛒 Buyer Sourcing Profile</h3>
                <div class="summary-box" style="margin-bottom:24px;">
                    <p style="margin:0;"><strong>{profile_message}</strong></p>
                    <p style="margin:8px 0 0 0;">Current buyer account: <strong>{buyer_name or username}</strong></p>
                </div>
                <div class="form-container" style="background:#fff; padding:20px; box-shadow:none; border:none;">
                    <form action="/api/register_buyer" method="POST">
                        <label>Buyer / Procurement Account Name</label>
                        <input type="text" name="buyer_name" value="{buyer_name}" placeholder="e.g., Fresh Choice Markets" required>
                        <label>Procurement Team Phone Number</label>
                        <input type="tel" name="phone" value="{phone}" placeholder="e.g., +263..." required>
                        <label>Intended Sourcing Delivery Destination</label>
                        <input type="text" name="target_hub" value="{target_hub}" placeholder="e.g., Chegutu Hub" required>
                        <label>Target Commodities Seeking</label>
                        <input type="text" name="crop_needed" value="{crop_needed}" placeholder="e.g., Onions, Honey, Potatoes" required>
                        <button type="submit" style="background: var(--buyer-color);">Save Sourcing Preferences</button>
                    </form>
                </div>
            '''
        elif role == 'driver':
            header_actions = f'<a href="/logout" style="background:#e65100;">Logout</a><div style="margin-top: 15px;"><a href="/feedback" style="color: #2e7d32; text-decoration: none; font-weight: bold; display: inline-block; padding: 10px 15px; background: rgba(46, 125, 50, 0.1); border-radius: 4px;">💬 Share System Feedback</a></div>'
            driver_profile = cursor.execute('SELECT * FROM drivers WHERE user_id = ?', (current_user['id'],)).fetchone()
            if driver_profile:
                role_section = f'''
                    <h3>🚛 Your Logistics Hub</h3>
                    <div class="market-card" style="padding:18px; border:none; box-shadow:0 10px 20px rgba(0,0,0,0.05);">
                        <div class="card-body">
                            <div class="card-title">{driver_profile['driver_name']}</div>
                            <div class="card-meta">📍 Base hub: {driver_profile['base_hub']}</div>
                            <div class="card-meta">🚚 Vehicle: {driver_profile['vehicle_type']}</div>
                            <div class="card-meta">📞 Contact: {driver_profile['phone']}</div>
                        </div>
                    </div>
                    <h3>📡 Logistics Network</h3>
                    <p style="color:#37474f;">Your hub has been matched to available harvest listings and transport requests in the same region.</p>
                '''
            else:
                role_section = f'''
                    <h3>🚛 Logistics Hub Setup</h3>
                    <p style="color:#37474f;">You have not yet registered a driver profile. Please register to manage your hub and vehicle details.</p>
                    <a href="/register_driver" class="helper-link" style="background: var(--driver-color);">Register Driver Profile</a>
                '''
        else:
            header_actions = f'<a href="/logout" style="background:#e65100;">Logout</a><div style="margin-top: 15px;"><a href="/feedback" style="color: #2e7d32; text-decoration: none; font-weight: bold; display: inline-block; padding: 10px 15px; background: rgba(46, 125, 50, 0.1); border-radius: 4px;">💬 Share System Feedback</a></div>'
            role_section = f'''
                <h3>👤 General Dashboard</h3>
                <p style="color:#37474f;">Welcome to your account dashboard. Use the actions above to interact with the marketplace.</p>
            '''
    else:
        header_actions = '<a href="/login" class="helper-link" style="background: var(--primary);">Login</a><a href="/signup" class="helper-link" style="background: var(--buyer-color);">Sign Up</a>'
        role_section = f'''
            <div class="summary-box" style="margin-bottom:24px;">
                <h3>👋 Welcome Guest</h3>
                <p style="margin: 8px 0 0 0; color:#37474f;">You may browse all active listings here. Log in or create an account to sell, buy or register transport.</p>
                <div style="margin-top: 14px; display:flex; gap:12px; flex-wrap:wrap;">
                    <a href="/login" class="helper-link" style="background: var(--primary);">Login</a>
                    <a href="/signup" class="helper-link" style="background: var(--buyer-color);">Sign Up</a>
                </div>
            </div>
        '''

    conn.close()

    DASHBOARD_HTML = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Marketplace Feed - Dream Green Agro</title>
        {COMMON_STYLE}
        <style>
            body {{ display: block; padding: 40px 15px; }}
            .dashboard-container {{ max-width: 1100px; margin: auto; }}
            h3 {{ color: var(--text); border-bottom: 2px solid #cfd8dc; padding-bottom: 8px; margin-top: 30px; }}
            .header-actions {{ display:flex; gap:14px; flex-wrap:wrap; margin-top:12px; }}
            .header-actions a {{ text-decoration:none; color:#fff; padding:10px 16px; border-radius:10px; font-weight:700; }}
            .summary-box {{ background: #f4f8fb; border: 1px solid #cfd8dc; border-radius: 16px; padding: 18px; margin-bottom: 24px; }}
            .helper-link {{ display: inline-block; padding: 10px 16px; border-radius: 10px; color: #fff; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="dashboard-container">
            <a href="/" class="back-btn">← Back to Portal Selection</a>
            <div class="brand-header" style="text-align: left; display: flex; align-items: center; gap: 20px;">
                <div class="brand-logo-container" style="width: 70px; height: 70px; margin-bottom: 0;">
                    <img src="/static/logo.webp" alt="Logo" onerror="this.style.display='none';">
                </div>
                <div>
                    <h1 class="brand-title" style="font-size: 1.6rem;">Dream Green Agro</h1>
                    <p class="brand-subtitle">{ 'Welcome back, ' + username.title() if logged_in else 'Public Market Feed' }</p>
                    <div class="header-actions">
                        {header_actions}
                    </div>
                </div>
            </div>
            {role_section}
            <h3>🧑‍🌾 Active Crop Harvest Offers</h3>
            <div class="market-grid">{fetch_all_harvest_cards}</div>
            <h3>🚛 Logistical Transit Fleets</h3>
            <div class="market-grid">{fetch_all_driver_cards}</div>
        </div>
    </body>
    </html>
    """
    return render_template_string(DASHBOARD_HTML, logged_in=logged_in)

# Auth routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        user = cursor.execute('SELECT id, username, password FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session.permanent = True
            return redirect('/dashboard')
        return render_template_string(LOGIN_HTML.replace('🔐 Sign In', '🔐 Sign In - Invalid credentials'))
    current_user = get_current_user()
    if current_user:
        return redirect('/dashboard')
    return render_template_string(LOGIN_HTML)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, generate_password_hash(password), role))
            conn.commit()
            user_id = cursor.lastrowid
            session['user_id'] = user_id
            session.permanent = True
            return redirect('/dashboard')
        except sqlite3.IntegrityError:
            return render_template_string(SIGNUP_HTML.replace('📝 Register Account', '📝 Register Account - Username taken'))
        finally:
            conn.close()
    current_user = get_current_user()
    if current_user:
        return redirect('/dashboard')
    return render_template_string(SIGNUP_HTML)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Form routes
@app.route('/register')
def serve_farmer_form(): return render_template_string(FARMER_FORM_HTML)
@app.route('/register_driver')
def serve_driver_form(): return render_template_string(DRIVER_FORM_HTML)
@app.route('/register_buyer')
def serve_buyer_form():
    current_user = get_current_user()
    if not current_user:
        return redirect('/login')
    if current_user['role'].lower() != 'buyer':
        return redirect('/dashboard')
    buyer_profile = get_buyer_profile(current_user['id'])
    if buyer_profile:
        return redirect('/matches')
    return render_template_string(BUYER_FORM_HTML)

@app.route('/api/matches')
def api_matches():
    current_user = get_current_user()
    if not current_user:
        return jsonify({'status': 'error', 'message': 'Login required'}), 403
    if current_user['role'].lower() != 'buyer':
        return jsonify({'status': 'error', 'message': 'Access restricted to buyer accounts'}), 403
    buyer_profile = get_buyer_profile(current_user['id'])
    if not buyer_profile:
        return jsonify({'status': 'error', 'message': 'Buyer profile not found. Please register your sourcing preferences.'}), 404

    matches = find_matches_for_buyer(buyer_profile)
    return jsonify({
        'status': 'success',
        'buyer': {
            'buyer_name': buyer_profile['buyer_name'],
            'target_hub': buyer_profile['target_hub'],
            'crop_needed': buyer_profile['crop_needed']
        },
        'harvest_matches': [dict(row) for row in matches['harvest']],
        'driver_matches': [dict(row) for row in matches['drivers']]
    })

@app.route('/matches')
def show_matches():
    current_user = get_current_user()
    if not current_user:
        return redirect('/login')
    if current_user['role'].lower() != 'buyer':
        return redirect('/dashboard')

    buyer_profile = get_buyer_profile(current_user['id'])
    if not buyer_profile:
        return redirect('/register_buyer')

    matches = find_matches_for_buyer(buyer_profile)
    harvest_cards = ''
    if matches['harvest']:
        for row in matches['harvest']:
            harvest_cards += f'''
                <div class="market-card">
                    <img class="card-img" src="{row['photo_path'] if row['photo_path'] else '/static/logo.webp'}" alt="Produce" onerror="this.src='/static/logo.webp';">
                    <div class="card-body">
                        <span class="badge" style="background: var(--primary);">{row['crop']}</span>
                        <div class="card-title">{row['farm_name']} — {row['hub']}</div>
                        <div class="card-meta">📦 {row['quantity']}</div>
                        <p style="font-size: 0.85rem; color: #555; margin: 0;">{row['details']}</p>
                    </div>
                </div>
            '''
    else:
        harvest_cards = '<p style="color:#37474f;">No harvest listings currently match your sourcing targets.</p>'

    driver_cards = ''
    if matches['drivers']:
        for row in matches['drivers']:
            driver_cards += f'''
                <div class="market-card">
                    <img class="card-img" src="{row['photo_path'] if row['photo_path'] else '/static/logo.webp'}" alt="Driver" onerror="this.src='/static/logo.webp';">
                    <div class="card-body">
                        <span class="badge" style="background: var(--driver-color);">{row['vehicle_type']}</span>
                        <div class="card-title">{row['driver_name']}</div>
                        <div class="card-meta">📍 {row['base_hub']}</div>
                        <div class="card-meta">📞 {row['phone']}</div>
                    </div>
                </div>
            '''
    else:
        driver_cards = '<p style="color:#37474f;">No transport providers currently list the hub you are sourcing to.</p>'

    MATCHES_HTML = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Recommended Matches - Dream Green Agro</title>
        {COMMON_STYLE}
        <style>
            body {{ display: block; padding: 40px 15px; }}
            .dashboard-container {{ max-width: 1100px; margin: auto; }}
            .summary-box {{ background: #f4f8fb; border: 1px solid #cfd8dc; border-radius: 16px; padding: 18px; margin-bottom: 24px; }}
            .summary-box strong {{ color: var(--text); }}
            .section-title {{ display: flex; justify-content: space-between; align-items: center; gap: 15px; flex-wrap: wrap; }}
            .section-title h3 {{ margin: 0; }}
            .helper-link {{ display: inline-block; background: var(--primary); color: #fff; padding: 10px 16px; border-radius: 10px; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="dashboard-container">
            <a href="/" class="back-btn">← Back to Portal Selection</a>
            <div class="brand-header" style="text-align: left; display: flex; align-items: center; gap: 20px;">
                <div class="brand-logo-container" style="width: 70px; height: 70px; margin-bottom: 0;">
                    <img src="/static/logo.webp" alt="Logo" onerror="this.style.display='none';">
                </div>
                <div>
                    <h1 class="brand-title" style="font-size: 1.6rem;">Recommendation Dashboard</h1>
                    <p class="brand-subtitle">Personalized matches for {buyer_profile['buyer_name']} at {buyer_profile['target_hub']}</p>
                </div>
            </div>
            <div class="summary-box">
                <p><strong>Target hub:</strong> {buyer_profile['target_hub']}</p>
                <p><strong>Crop need:</strong> {buyer_profile['crop_needed']}</p>
                <p style="margin:0;">We apply case-insensitive keyword matching so listings like "Tomatoes" and "tomatoes" are treated as the same commodity.</p>
            </div>
            <div class="section-title">
                <h3>🎯 Harvest Listings Matching Your Crop Needs</h3>
                <a class="helper-link" href="/api/matches">Download JSON</a>
            </div>
            <div class="market-grid">
                {harvest_cards}
            </div>
            <div class="section-title" style="margin-top: 32px;">
                <h3>🚛 Drivers Serving Your Target Hub</h3>
                <a class="helper-link" href="/dashboard">View Full Marketplace</a>
            </div>
            <div class="market-grid">
                {driver_cards}
            </div>
        </div>
    </body>
    </html>
    '''
    return render_template_string(MATCHES_HTML)

# ==========================================
# API ENDPOINTS
# ==========================================

@app.route('/api/list_harvest', methods=['POST'])
def api_list_harvest():
    try:
        farm_name = request.form.get('farm_name')
        hub = request.form.get('hub')
        crop = request.form.get('crop')
        quantity = request.form.get('quantity')
        unit = request.form.get('unit')
        details = request.form.get('details', '')
        quantity_str = f"{quantity} {unit}"

        photo_path = ""
        if 'produce_photo' in request.files:
            file = request.files['produce_photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"harvest_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                photo_path = f"/uploads/{unique_filename}"

        current_user = get_current_user()
        if not current_user:
            return redirect('/login')
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO harvest (farm_name, hub, crop, quantity, details, photo_path, user_id) VALUES (?, ?, ?, ?, ?, ?, ?)', (farm_name, hub, crop, quantity_str, details, photo_path, current_user['id']))
        conn.commit()
        conn.close()
        return redirect('/dashboard')
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/register_driver', methods=['POST'])
def api_register_driver():
    try:
        driver_name = request.form.get('driver_name')
        phone = request.form.get('phone')
        vehicle_type = request.form.get('vehicle_type')
        base_hub = request.form.get('base_hub')

        photo_path = ""
        if 'vehicle_photo' in request.files:
            file = request.files['vehicle_photo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"driver_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                photo_path = f"/uploads/{unique_filename}"

        current_user = get_current_user()
        if not current_user:
            return redirect('/login')
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO drivers (driver_name, phone, vehicle_type, base_hub, photo_path, user_id) VALUES (?, ?, ?, ?, ?, ?)', (driver_name, phone, vehicle_type, base_hub, photo_path, current_user['id']))
        conn.commit()
        conn.close()
        return redirect('/dashboard')
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/delete/harvest/<int:item_id>')
def api_delete_harvest(item_id):
    current_user = get_current_user()
    if not current_user:
        return redirect('/login')
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    item = cursor.execute('SELECT user_id FROM harvest WHERE id = ?', (item_id,)).fetchone()
    if item and item['user_id'] == current_user['id']:
        cursor.execute('DELETE FROM harvest WHERE id = ?', (item_id,))
        conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/api/delete/drivers/<int:item_id>')
def api_delete_driver(item_id):
    current_user = get_current_user()
    if not current_user:
        return redirect('/login')
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    item = cursor.execute('SELECT user_id FROM drivers WHERE id = ?', (item_id,)).fetchone()
    if item and item['user_id'] == current_user['id']:
        cursor.execute('DELETE FROM drivers WHERE id = ?', (item_id,))
        conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/api/register_buyer', methods=['POST'])
def api_register_buyer():
    try:
        current_user = get_current_user()
        if not current_user:
            return redirect('/login')
        if current_user['role'].lower() != 'buyer':
            return redirect('/dashboard')

        buyer_name = request.form.get('buyer_name')
        phone = request.form.get('phone')
        target_hub = request.form.get('target_hub')
        crop_needed = request.form.get('crop_needed')
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        existing = cursor.execute('SELECT id FROM buyers WHERE user_id = ?', (current_user['id'],)).fetchone()
        if existing:
            cursor.execute('UPDATE buyers SET buyer_name = ?, phone = ?, target_hub = ?, crop_needed = ? WHERE user_id = ?', (buyer_name, phone, target_hub, crop_needed, current_user['id']))
        else:
            cursor.execute('INSERT INTO buyers (buyer_name, phone, target_hub, crop_needed, user_id) VALUES (?, ?, ?, ?, ?)', (buyer_name, phone, target_hub, crop_needed, current_user['id']))
        conn.commit()
        conn.close()
        return redirect('/matches')
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/feedback')
def feedback_page():
    if 'user_id' not in session:
        return redirect('/login')
    return render_template('feedback.html', active_page='feedback')


@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    if 'user_id' not in session:
        return jsonify({"status": "error", "message": "Login required"}), 401
    feedback_text = request.form.get('feedback_text')
    if not feedback_text:
        return redirect('/feedback?status=empty')
    conn = sqlite3.connect('market.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute("INSERT INTO feedback (user_id, role, message) VALUES (?, ?, ?)",
                   (session['user_id'], session.get('role', 'unknown'), feedback_text))
    conn.commit()
    conn.close()
    return redirect('/feedback?status=success')


@app.route('/dream-admin-feedback')
def view_feedback():
    if 'user_id' not in session:
        return redirect('/login')
    conn = sqlite3.connect('market.db')
    cursor = conn.cursor()
    cursor.execute("SELECT role, timestamp, message, user_id FROM feedback ORDER BY timestamp DESC")
    all_feedback = cursor.fetchall()
    conn.close()
    
    html_template = """
    <!DOCTYPE html>
    <html><head><title>Admin Panel</title><style>body{background:#121815;color:#fff;padding:20px;font-family:sans-serif;}.card{background:rgba(255,255,255,0.05);padding:15px;margin-bottom:10px;border-left:4px solid #2e7d32;}.card p{margin:8px 0 0 0;color:#ccc;}</style></head>
    <body><h2>Incoming Feedback</h2>
    {% for item in feedback_list %}<div class="card"><strong>Role:</strong> {{item[0]}} | <strong>User ID:</strong> {{item[3]}}<p>"{{item[2]}}"</p></div>{% endfor %}
    </body></html>
    """
    from flask import render_template_string
    return render_template_string(html_template, feedback_list=all_feedback)
    app.run(host='0.0.0.0', port=10000)