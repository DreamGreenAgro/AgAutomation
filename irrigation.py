import sqlite3
import os
from flask import Flask, jsonify, request, redirect, render_template_string, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='static')
DB_NAME = "market.db"

# Configure file uploads
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Global CSS styles
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
        background-size: cover; background-position: center; background-attachment: fixed;
        margin: 0; padding: 15px; display: flex; justify-content: center; align-items: center; min-height: 100vh; box-sizing: border-box; 
    }
    .gateway-container, .form-container { 
        max-width: 550px; width: 100%; background: rgba(255, 255, 255, 0.94); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
        padding: 35px 25px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.25); box-sizing: border-box;
    }
    .brand-header { text-align: center; margin-bottom: 25px; }
    .brand-logo-container {
        width: 110px; height: 110px; background-color: #0b0c10; border-radius: 20px;
        display: inline-flex; align-items: center; justify-content: center;
        margin-bottom: 12px; box-shadow: 0 5px 15px rgba(0,0,0,0.2); border: 2px solid #2e7d32; overflow: hidden; padding: 5px;
    }
    .brand-logo-container img { width: 100%; height: 100%; object-fit: contain; }
    .brand-title { font-size: 1.8rem; font-weight: 800; color: var(--text); margin: 0; letter-spacing: -0.5px; }
    .brand-subtitle { font-size: 0.95rem; color: #546e7a; margin: 5px 0 0 0; }
    h2 { font-size: 1.4rem; font-weight: 700; margin-top: 0; margin-bottom: 20px; text-align: center; }
    label { display: block; margin-bottom: 6px; font-weight: 600; font-size: 0.88rem; color: #37474f; text-align: left; }
    input, select, textarea { width: 100%; padding: 12px; margin-bottom: 18px; border: 1px solid #cfd8dc; border-radius: 8px; box-sizing: border-box; font-size: 1rem; background: #fafafa; transition: all 0.2s ease; }
    input[type="file"] { padding: 8px; background: #fff; cursor: pointer; }
    button { width: 100%; border: none; padding: 14px; border-radius: 8px; font-size: 1.05rem; font-weight: bold; color: white; cursor: pointer; transition: all 0.2s ease; box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
    button:hover { transform: translateY(-1px); box-shadow: 0 6px 15px rgba(0,0,0,0.2); }
    .back-btn { display: inline-flex; align-items: center; margin-bottom: 20px; color: #546e7a; text-decoration: none; font-size: 0.9rem; font-weight: 600; }
</style>
"""

@app.route('/')
def home():
    CHOICE_PAGE_HTML = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to Dream Green Agro</title>
        {COMMON_STYLE}
    </head>
    <body>
        <div class="gateway-container">
            <div class="brand-header">
                <div class="brand-logo-container"><img src="/static/logo.webp" alt="Logo"></div>
                <h1 class="brand-title">Dream Green Agro</h1>
                <p class="brand-subtitle">Connecting ecosystem logistics & agricultural markets</p>
            </div>
            <div style="display: flex; flex-direction: column; gap: 15px; margin-top: 10px;">
                <a href="/register" style="text-decoration: none; color: inherit; display: flex; padding: 18px; border: 1px solid #e0e0e0; border-radius: 12px; background: #fff;">
                    <div style="font-size: 2.2rem; margin-right: 18px;">🧑‍🌾</div>
                    <div><div style="font-weight:700;">Farmer / Seller</div><div style="font-size:0.85rem; color:#7f8c8d;">Market your harvest varieties with multi-photo catalogs.</div></div>
                </a>
                <a href="/register_driver" style="text-decoration: none; color: inherit; display: flex; padding: 18px; border: 1px solid #e0e0e0; border-radius: 12px; background: #fff;">
                    <div style="font-size: 2.2rem; margin-right: 18px;">🚛</div>
                    <div><div style="font-weight:700;">Driver / Transporter</div><div style="font-size:0.85rem; color:#7f8c8d;">Onboard transport assets with vehicle verification photos.</div></div>
                </a>
                <a href="/register_buyer" style="text-decoration: none; color: inherit; display: flex; padding: 18px; border: 1px solid #e0e0e0; border-radius: 12px; background: #fff;">
                    <div style="font-size: 2.2rem; margin-right: 18px;">🛒</div>
                    <div><div style="font-weight:700;">Buyer / Off-taker</div><div style="font-size:0.85rem; color:#7f8c8d;">Source broad crop distributions and place direct orders.</div></div>
                </a>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(CHOICE_PAGE_HTML)

# Note the 'multiple' attribute inside the input tag below
FARMER_FORM_HTML = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>List Your Harvest</title>
    {COMMON_STYLE}
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
            <input type="text" name="crop" placeholder="e.g., Butternut, Tomatoes" required>
            
            <label>Quantity & Metric Unit</label>
            <input type="text" name="quantity" placeholder="e.g., 500 KG" required>
            
            <label>Upload Produce Photos (You can select multiple)</label>
            <input type="file" name="produce_photos" accept="image/*" multiple required>
            
            <label>Batch Details (Optional)</label>
            <textarea name="details" rows="2" placeholder="e.g., Grade A quality..."></textarea>
            
            <button type="submit" style="background: var(--primary);">Publish Produce Listing</button>
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
    <title>Transporter Onboarding</title>
    {COMMON_STYLE}
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
            <input type="text" name="vehicle_type" placeholder="e.g., 5-7 Ton Truck" required>
            
            <label>Primary Freight Base City</label>
            <input type="text" name="base_hub" placeholder="e.g., Chegutu" required>
            
            <label>Upload Vehicle Photos (You can select multiple)</label>
            <input type="file" name="vehicle_photos" accept="image/*" multiple required>
            
            <button type="submit" style="background: var(--driver-color);">Register Fleet Asset</button>
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
    <title>Procurement Portal</title>
    {COMMON_STYLE}
</head>
<body>
    <div class="form-container">
        <a href="/" class="back-btn">← Back to Selection</a>
        <h2 style="color: var(--buyer-color);">🛒 Enterprise Buyer Registration</h2>
        <form action="/api/register_buyer" method="POST">
            <label>Buyer Account Name</label>
            <input type="text" name="buyer_name" required>
            <label>Phone Number</label>
            <input type="tel" name="phone" required>
            <label>Delivery Destination</label>
            <input type="text" name="target_hub" required>
            <label>Target Commodities Seeking</label>
            <input type="text" name="crop_needed" required>
            <button type="submit" style="background: var(--buyer-color);">Submit Sourcing Target</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/register')
def serve_farmer_form(): return render_template_string(FARMER_FORM_HTML)

@app.route('/register_driver')
def serve_driver_form(): return render_template_string(DRIVER_FORM_HTML)

@app.route('/register_buyer')
def serve_buyer_form(): return render_template_string(BUYER_FORM_HTML)

@app.route('/api/list_harvest', methods=['POST'])
def api_list_harvest():
    try:
        farm_name = request.form.get('farm_name')
        hub = request.form.get('hub')
        crop = request.form.get('crop')
        quantity = request.form.get('quantity')
        details = request.form.get('details', '')
        
        saved_paths = []
        files = request.files.getlist('produce_photos') # Grab list of multiple photos
        for idx, file in enumerate(files):
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"harvest_{farm_name.replace(' ', '_')}_{idx}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                saved_paths.append(f"/uploads/{unique_filename}")
                
        photo_paths_str = ",".join(saved_paths)
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS harvest (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_name TEXT, hub TEXT, crop TEXT, quantity TEXT, details TEXT, photo_path TEXT
            )
        ''')
        try: cursor.execute('ALTER TABLE harvest ADD COLUMN photo_path TEXT')
        except sqlite3.OperationalError: pass
            
        cursor.execute('INSERT INTO harvest (farm_name, hub, crop, quantity, details, photo_path) VALUES (?, ?, ?, ?, ?, ?)',
                       (farm_name, hub, crop, quantity, details, photo_paths_str))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": f"Successfully listed harvest with {len(saved_paths)} images!"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/register_driver', methods=['POST'])
def api_register_driver():
    try:
        driver_name = request.form.get('driver_name')
        phone = request.form.get('phone')
        vehicle_type = request.form.get('vehicle_type')
        base_hub = request.form.get('base_hub')
        
        saved_paths = []
        files = request.files.getlist('vehicle_photos')
        for idx, file in enumerate(files):
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"driver_{driver_name.replace(' ', '_')}_{idx}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                saved_paths.append(f"/uploads/{unique_filename}")
                
        photo_paths_str = ",".join(saved_paths)
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drivers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_name TEXT, phone TEXT, vehicle_type TEXT, base_hub TEXT, photo_path TEXT
            )
        ''')
        try: cursor.execute('ALTER TABLE drivers ADD COLUMN photo_path TEXT')
        except sqlite3.OperationalError: pass
            
        cursor.execute('INSERT INTO drivers (driver_name, phone, vehicle_type, base_hub, photo_path) VALUES (?, ?, ?, ?, ?)',
                       (driver_name, phone, vehicle_type, base_hub, photo_paths_str))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": f"Driver profile loaded with {len(saved_paths)} truck files!"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/register_buyer', methods=['POST'])
def api_register_buyer():
    try:
        buyer_name = request.form.get('buyer_name')
        phone = request.form.get('phone')
        target_hub = request.form.get('target_hub')
        crop_needed = request.form.get('crop_needed')
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO buyers (buyer_name, phone, target_hub, crop_needed) VALUES (?, ?, ?, ?)', (buyer_name, phone, target_hub, crop_needed))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Buyer added!"}), 201
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)