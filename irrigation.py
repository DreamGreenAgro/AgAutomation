import sqlite3
import os
from flask import Flask, jsonify, request, redirect, render_template_string

app = Flask(__name__)
DB_NAME = "market.db"

# ==========================================
# 1. NEW ROLE SELECTION GATEWAY (HOME ROUTE)
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
            :root { --primary: #1565c0; --bg: #e3f2fd; --accent: #2e7d32; }
            body { font-family: system-ui, sans-serif; background-color: var(--bg); margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 100vh; box-sizing: border-box; }
            .gateway-container { max-width: 600px; width: 100%; background: white; padding: 30px; border-radius: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center; }
            h1 { color: #333; margin-bottom: 10px; font-size: 1.8rem; }
            p { color: #666; margin-bottom: 30px; font-size: 1rem; }
            .options-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            @media (max-width: 480px) { .options-grid { grid-template-columns: 1fr; } }
            .option-card { border: 2px solid #e0e0e0; border-radius: 12px; padding: 25px; cursor: pointer; text-decoration: none; color: inherit; transition: all 0.2s ease; display: flex; flex-direction: column; align-items: center; }
            .option-card:hover { border-color: var(--primary); transform: translateY(-2px); box-shadow: 0 4px 10px rgba(21,101,192,0.1); }
            .icon { font-size: 2.5rem; margin-bottom: 15px; }
            .option-title { font-weight: 600; font-size: 1.2rem; color: #333; margin-bottom: 8px; }
            .option-desc { font-size: 0.85rem; color: #777; line-height: 1.4; }
        </style>
    </head>
    <body>
        <div class="gateway-container">
            <h1>Welcome to Dream Green Agro</h1>
            <p>Please select how you would like to continue:</p>
            <div class="options-grid">
                <a href="/register" class="option-card">
                    <div class="icon">🧑‍🌾</div>
                    <div class="option-title">Farmer</div>
                    <div class="option-desc">List your harvest, manage produce, and connect with market hubs.</div>
                </a>
                <a href="/register_driver" class="option-card">
                    <div class="icon">🚛</div>
                    <div class="option-title">Driver</div>
                    <div class="option-desc">Onboard your commercial vehicle and handle logistics distributions.</div>
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
        button { width: 100%; background: var(--primary); color: white; border: none; padding: 12px; border-radius: 6px; font-size: 1rem; font-weight: bold; cursor: pointer; }
        button:hover { background: #1b5e20; }
        .back-btn { display: inline-block; margin-bottom: 15px; color: var(--primary); text-decoration: none; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="form-container">
        <a href="/" class="back-btn">← Back to Selection</a>
        <h2>🧑‍🌾 List Your Harvest</h2>
        <form action="/api/list_harvest" method="POST">
            <label>Farm or Enterprise Name</label>
            <input type="text" name="farm_name" placeholder="e.g., DGAgroo Farm" required>
            
            <label>Nearest Market Hub/City</label>
            <input type="text" name="hub" placeholder="e.g., Chegutu" required>
            
            <label>Crop for Sale</label>
            <input type="text" name="crop" placeholder="e.g., Onions / Maize" required>
            
            <label>Quantity Available</label>
            <input type="number" name="quantity" placeholder="e.g., 150" required>
            
            <button type="submit">Submit Harvest Listing</button>
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
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS harvest (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_name TEXT, hub TEXT, crop TEXT, quantity REAL
            )
        ''')
        cursor.execute('INSERT INTO harvest (farm_name, hub, crop, quantity) VALUES (?, ?, ?, ?)',
                       (farm_name, hub, crop, quantity))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Harvest successfully listed!"}), 201
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)