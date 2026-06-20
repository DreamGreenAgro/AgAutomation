import sqlite3
import os
from flask import Flask, jsonify, request, redirect, render_template_string

app = Flask(__name__, static_folder='static')
DB_NAME = "market.db"

# Global CSS and Header Template to keep branding identical across all pages
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
    
    .gateway-container, .form-container { 
        max-width: 550px; 
        width: 100%; 
        background: rgba(255, 255, 255, 0.94); 
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        padding: 35px 25px; 
        border-radius: 20px; 
        box-shadow: 0 10px 30px rgba(0,0,0,0.25); 
        box-sizing: border-box;
    }
    
    /* Branding Header Area configured for your custom logo */
    .brand-header {
        text-align: center;
        margin-bottom: 25px;
    }
    .brand-logo-container {
        width: 110px;
        height: 110px;
        background-color: #0b0c10;
        border-radius: 20px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 12px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        border: 2px solid #2e7d32;
        overflow: hidden;
        padding: 5px;
    }
    .brand-logo-container img {
        width: 100%;
        height: 100%;
        object-fit: contain;
    }
    .brand-title {
        font-size: 1.8rem;
        font-weight: 800;
        color: var(--text);
        margin: 0;
        letter-spacing: -0.5px;
    }
    .brand-subtitle {
        font-size: 0.95rem;
        color: #546e7a;
        margin: 5px 0 0 0;
    }

    h2 { font-size: 1.4rem; font-weight: 700; margin-top: 0; margin-bottom: 20px; text-align: center; }
    label { display: block; margin-bottom: 6px; font-weight: 600; font-size: 0.88rem; color: #37474f; text-align: left; }
    input, select, textarea { 
        width: 100%; padding: 12px; margin-bottom: 18px; 
        border: 1px solid #cfd8dc; border-radius: 8px; 
        box-sizing: border-box; font-size: 1rem; 
        background: #fafafa; transition: all 0.2s ease;
    }
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
    
    .back-btn { 
        display: inline-flex; align-items: center; margin-bottom: 20px; 
        color: #546e7a; text-decoration: none; font-size: 0.9rem; font-weight: 600;
    }
    .back-btn:hover { color: #263238; }
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
        </style>
    </head>
    <body>
        <div class="gateway-container">
            <div class="brand-header">
                <div class="brand-logo-container">
                    <img src="/static/logo.webp" alt="Dream Green Agro Logo">
                </div>
                <h1 class="brand-title">Dream Green Agro</h1>
                <p class="brand-subtitle">Connecting ecosystem logistics & agricultural markets</p>
            </div>
            <div class="options-grid">
                <a href="/register" class="option-card farmer">
                    <div class="icon">🧑‍🌾</div>
                    <div class="option-details">
                        <div class="option-title">Farmer / Seller</div>
                        <div class="option-desc">Market your dynamic harvest varieties to bulk buyers.</div>
                    </div>
                </a>
                <a href="/register_driver" class="option-card driver">
                    <div class="icon">🚛</div>
                    <div class="option-details">
                        <div class="option-title">Driver / Transporter</div>
                        <div class="option-desc">Onboard commercial transport assets for regional fulfillment.</div>
                    </div>
                </a>
                <a href="/register_buyer" class="option-card buyer">
                    <div class="icon">🛒</div>
                    <div class="option-details">
                        <div class="option-title">Buyer / Off-taker</div>
                        <div class="option-desc">Source broad crop distributions and place direct orders.</div>
                    </div>
                </a>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(CHOICE_PAGE_HTML)

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
        <form action="/api/list_harvest" method="POST">
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
        <form action="/api/register_driver" method="POST">
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

@app.route('/register')
def serve_farmer_form():
    return render_template_string(FARMER_FORM_HTML)

@app.route('/register_driver')
def serve_driver_form():
    return render_template_string(DRIVER_FORM_HTML)

@app.route('/register_buyer')
def serve_buyer_form():
    return render_template_string(BUYER_FORM_HTML)

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