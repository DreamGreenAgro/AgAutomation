import sqlite3
import os
from flask import Flask, jsonify, request, redirect, render_template_string

app = Flask(__name__)
DB_NAME = "market.db"

# ==========================================
# 1. UPDATED ROLE SELECTION GATEWAY (THREE ROLES)
# ==========================================
@app.route('/')
def home():
    CHOICE_PAGE_HTML = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to Dream Green Agro</title>
        <style>
            :root { --primary: #1565c0; --bg: #e3f2fd; --accent: #2e7d32; --buyer-color: #e65100; }
            body { font-family: system-ui, sans-serif; background-color: var(--bg); margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 100vh; box-sizing: border-box; }
            .gateway-container { max-width: 900px; width: 100%; background: white; padding: 40px; border-radius: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center; }
            h1 { color: #333; margin-bottom: 10px; font-size: 2rem; }
            p { color: #666; margin-bottom: 30px; font-size: 1.05rem; }
            .options-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }
            @media (max-width: 768px) { .options-grid { grid-template-columns: 1fr; } }
            .option-card { border: 2px solid #e0e0e0; border-radius: 12px; padding: 25px; cursor: pointer; text-decoration: none; color: inherit; transition: all 0.2s ease; display: flex; flex-direction: column; align-items: center; }
            .option-card.farmer:hover { border-color: var(--accent); transform: translateY(-2px); box-shadow: 0 4px 10px rgba(46,125,50,0.1); }
            .option-card.driver:hover { border-color: var(--primary); transform: translateY(-2px); box-shadow: 0 4px 10px rgba(21,101,192,0.1); }
            .option-card.buyer:hover { border-color: var(--buyer-color); transform: translateY(-2px); box-shadow: 0 4px 10px rgba(230,81,0,0.1); }
            .icon { font-size: 2.8rem; margin-bottom: 15px; }
            .option-title { font-weight: 600; font-size: 1.25rem; color: #333; margin-bottom: 8px; }
            .option-desc { font-size: 0.88rem; color: #777; line-height: 1.4; }
        </style>
    </head>
    <body>
        <div class="gateway-container">
            <h1>Welcome to Dream Green Agro</h1>
            <p>Please select how you would like to continue:</p>
            <div class="options-grid">
                <a href="/register" class="option-card farmer">
                    <div class="icon">🧑‍🌾</div>
                    <div class="option-title">Farmer / Seller</div>
                    <div class="option-desc">List any harvest variety, manage produce quantities, and market directly to buyers.</div>
                </a>
                <a href="/register_driver" class="option-card driver">
                    <div class="icon">🚛</div>
                    <div class="option-title">Driver</div>
                    <div class="option-desc">Onboard your commercial vehicle and handle logistics distributions.</div>
                </a>
                <a href="/register_buyer" class="option-card buyer">
                    <div class="icon">🛒</div>
                    <div class="option-title">Buyer / Off-taker</div>
                    <div class="option-desc">Sourcing bulk commodities, viewing active harvests, and placing direct orders.</div>
                </a>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(CHOICE_PAGE_HTML)

# ==========================================
# 2. EMBEDDED FRONTEND UI BLUEPRINTS
# ==========================================
FARMER_FORM_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>List Your Harvest</title>
    <style>
        :root { --primary: #2e7d32; --bg: #e8f5e9; }
        body { font-family: system-ui, sans-serif; background-color: var(--bg); margin: 0; padding: 15px; color: #333; }
        .form-container { max-width: 500px; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin: auto; }
        h2 { color: var(--primary); margin-top: 0; border-bottom: 2px solid var(--bg); padding-bottom: 8px; }
        label { display: block; margin-bottom: 5px; font-weight: 600; font-size: 0.9rem; }
        input, select, textarea { width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-size: 0.95rem; }
        .unit-group { display: flex; gap: 10px; margin-bottom: 15px; }
        .unit-group input { margin-bottom: 0; flex: 2; }
        .unit-group select { margin-bottom: 0; flex: 1; }
        button { width: 100%; background: var(--primary); color: white; border: none; padding: 12px; border-radius: 6px; font-size: 1rem; font-weight: bold; cursor: pointer; }
        button:hover { background: #1b5e20; }
        .back-btn { display: inline-block; margin-bottom: 15px; color: var(--primary); text-decoration: none; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="form-container">
        <a href="/" class="back-btn">← Back to Selection</a>
        <h2>🧑‍🌾 Market Your Harvest</h2>
        <form action="/api/list_harvest" method="POST">
            <label>Farm / Seller Name</label>
            <input type="text" name="farm_name" placeholder="e.g., Green Valley Estates" required>
            
            <label>Nearest Market Hub / City</label>
            <input type="text" name="hub" placeholder="e.g., Chegutu" required>
            
            <label>Crop / Produce Type (Open Market Input)</label>
            <input type="text" name="crop" placeholder="e.g., Butternut, Tomatoes, White Maize, Honey" required>
            
            <label>Quantity Available & Metric Unit</label>
            <div class="unit-group">
                <input type="number" step="any" name="quantity" placeholder="e.g., 500" required>
                <select name="unit">
                    <option value="KG">KG</option>
                    <option value="Tons">Tons</option>
                    <option value="Bags (50kg)">Bags (50kg)</option>
                    <option value="Crates">Crates</option>
                    <option value="Litres">Litres</option>
                    <option value="Boxes">Boxes</option>
                </select>
            </div>
            
            <label>Additional Details (Optional)</label>
            <textarea name="details" rows="2" placeholder="e.g., Grade A premium quality, washed, ready for dispatch..."></textarea>
            
            <button type="submit">Submit to Global Market</button>
        </form>
    </div>
</body>
</html>
"""

BUYER_FORM_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Buyer Procurement Portal</title>
    <style>
        :root { --primary: #e65100; --bg: #fff3e0; }
        body { font-family: system-ui, sans-serif; background-color: var(--bg); margin: 0; padding: 15px; color: #333; }
        .form-container { max-width: 500px; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin: auto; }
        h2 { color: var(--primary); margin-top: 0; border-bottom: 2px solid var(--bg); padding-bottom: 8px; }
        label { display: block; margin-bottom: 5px; font-weight: 600; font-size: 0.9rem; }
        input, select, textarea { width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-size: 0.95rem; }
        button { width: 100%; background: var(--primary); color: white; border: none; padding: 12px; border-radius: 6px; font-size: 1rem; font-weight: bold; cursor: pointer; }
        button:hover { background: #bf360c; }
        .back-btn { display: inline-block; margin-bottom: 15px; color: var(--primary); text-decoration: none; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="form-container">
        <a href="/" class="back-btn">← Back to Selection</a>
        <h2>🛒 Buyer Registration</h2>
        <form action="/api/register_buyer" method="POST">
            <label>Buyer / Company Name</label>
            <input type="text" name="buyer_name" placeholder="e.g., Fresh Choice Markets" required>
            
            <label>Contact Phone Number</label>
            <input type="tel" name="phone" placeholder="e.g., +263..." required>
            
            <label>Target Sourcing Hub / City</label>
            <input type="text" name="target_hub" placeholder="e.g., Chegutu" required>
            
            <label>Commodity / Crop looking to Buy</label>
            <input type="text" name="crop_needed" placeholder="e.g., Onions, Maize, Potatoes" required>
            
            <button type="submit">Register Sourcing Requirements</button>
        </form>
    </div>
</body>
</html>
"""

DRIVER_FORM_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Transporter Onboarding</title>
    <style>
        :root { --primary: #1565c0; --bg: #e3f2fd; }
        body { font-family: system-ui, sans-serif; background-color: var(--bg); margin: 0; padding: 15px; color: #333; }
        .form-container { max-width: 500px; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin: auto; }
        h2 { color: var(--primary); margin-top: 0; border-bottom: 2px solid var(--bg); padding-bottom: 8px; }
        label { display: block; margin-bottom: 5px; font-weight: 600; font-size: 0.9rem; }
        input, select, textarea { width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; font-size: 0.95rem; }
        button { width: 100%; background: var(--primary); color: white; border: none; padding: 12px; border-radius: 6px; font-size: 1rem; font-weight: bold; cursor: pointer; }
        button:hover { background: #0d47a1; }
        .back-btn { display: inline-block; margin-bottom: 15px; color: var(--primary); text-decoration: none; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="form-container">
        <a href="/" class="back-btn">← Back to Selection</a>
        <h2>🚛 Transporter Onboarding</h2>
        <form action="/api/register_driver" method="POST">
            <label>Driver Full Name</label>
            <input type="text" name="driver_name" placeholder="e.g., John Doe" required>
            
            <label>Phone Number</label>
            <input type="tel" name="phone" placeholder="e.g., +263..." required>
            
            <label>Vehicle Type</label>
            <select name="vehicle_type">
                <option value="1-3 Ton Truck">1-3 Ton Truck</option>
                <option value="5-7 Ton Truck">5-7 Ton Truck</option>
                <option value="10+ Ton Rigid">10+ Ton Rigid</option>
                <option value="Motorcycle/Utility">Motorcycle/Utility</option>
            </select>
            
            <label>Base Operation City/Hub</label>
            <input type="text" name="base_hub" placeholder="e.g., Harare / Chegutu" required>
            
            <button type="submit">Complete Transporter Registration</button>
        </form>
    </div>
</body>
</html>
"""

# ==========================================
# 3. ROUTE CONTROLLERS
# ==========================================
@app.route('/register')
def serve_farmer_form():
    return render_template_string(FARMER_FORM_HTML)

@app.route('/register_driver')
def serve_driver_form():
    return render_template_string(DRIVER_FORM_HTML)

@app.route('/register_buyer')
def serve_buyer_form():
    return render_template_string(BUYER_FORM_HTML)

# ==========================================
# 4. DATABASE API ENDPOINTS
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
        
        # Format quantity with unit combined or store separately
        quantity_str = f"{quantity} {unit}"
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS harvest (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_name TEXT, hub TEXT, crop TEXT, quantity TEXT, details TEXT
            )
        ''')
        cursor.execute('INSERT INTO harvest (farm_name, hub, crop, quantity, details) VALUES (?, ?, ?, ?, ?)',
                       (farm_name, hub, crop, quantity_str, details))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Harvest successfully listed on the open market!"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/register_driver', methods=['POST'])
def api_register_driver():
    try:
        driver_name = request.form.get('driver_name')
        phone = request.form.get('phone')
        vehicle_type = request.form.get('vehicle_type')
        base_hub = request.form.get('base_hub')
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drivers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                driver_name TEXT, phone TEXT, vehicle_type TEXT, base_hub TEXT
            )
        ''')
        cursor.execute('INSERT INTO drivers (driver_name, phone, vehicle_type, base_hub) VALUES (?, ?, ?, ?)',
                       (driver_name, phone, vehicle_type, base_hub))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Transporter registered successfully!"}), 201
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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS buyers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                buyer_name TEXT, phone TEXT, target_hub TEXT, crop_needed TEXT
            )
        ''')
        cursor.execute('INSERT INTO buyers (buyer_name, phone, target_hub, crop_needed) VALUES (?, ?, ?, ?)',
                       (buyer_name, phone, target_hub, crop_needed))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Buyer registration saved successfully!"}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)