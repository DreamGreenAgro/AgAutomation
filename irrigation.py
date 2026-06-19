import sqlite3
import os
from flask import Flask, jsonify, request, redirect, render_template_string

app = Flask(__name__)
DB_NAME = "market.db"
# deploy checkpoint
# --- EMBEDDED FRONTEND UI BLUEPRINTS ---
DRIVER_FORM_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Transporter Onboarding</title>
    <style>
        :root { --primary: #1565c0; --bg: #e3f2fd; }
        body { font-family: system-ui, sans-serif; background-color: var(--bg); margin: 0; padding: 15px; color: #333; }
        .form-container { max-width: 500px; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin: 0 auto; }
        h2 { color: var(--primary); margin-top: 0; font-size: 1.4rem; border-bottom: 2px solid var(--bg); padding-bottom: 10px; }
        label { display: block; margin-bottom: 5px; font-weight: 600; font-size: 0.9rem; }
        input { width: 100%; padding: 12px; margin-bottom: 15px; border: 2px solid #ccc; border-radius: 8px; box-sizing: border-box; font-size: 1rem; background-color: #fafafa; }
        button { width: 100%; background-color: var(--primary); color: white; border: none; padding: 14px; font-size: 1.1rem; font-weight: bold; border-radius: 8px; cursor: pointer; margin-top: 10px; }
    </style>
</head>
<body>
<div class="form-container">
    <h2>🚛 Transporter Onboarding</h2>
    <form action="/submit_driver" method="POST">
        <label for="full_name">Driver / Company Name</label>
        <input type="text" id="full_name" name="full_name" placeholder="e.g., Tinashe Logistics" required>
        <label for="phone_number">WhatsApp / Phone Number</label>
        <input type="text" id="phone_number" name="phone_number" placeholder="e.g., +263773333333" required>
        <label for="vehicle_reg">Vehicle Registration Number</label>
        <input type="text" id="vehicle_reg" name="vehicle_reg" placeholder="e.g., ABW-9999" required>
        <label for="license_num">Driver's License Number</label>
        <input type="text" id="license_num" name="license_num" placeholder="e.g., DL-9938210" required>
        <label for="truck_capacity">Truck Maximum Capacity (Tonnes)</label>
        <input type="number" id="truck_capacity" name="truck_capacity" placeholder="e.g., 7.5" step="any" required>
        <button type="submit">Register & Verify Vehicle ✅</button>
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
    <title>Easy Farm Market Upload</title>
    <style>
        :root { --primary: #2e7d32; --bg: #f1f8e9; }
        body { font-family: system-ui, sans-serif; background-color: var(--bg); margin: 0; padding: 15px; color: #333; }
        .form-container { max-width: 500px; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin: 0 auto; }
        h2 { color: var(--primary); margin-top: 0; font-size: 1.4rem; border-bottom: 2px solid var(--bg); padding-bottom: 10px; }
        .section-title { font-size: 0.95rem; font-weight: bold; color: #555; margin: 20px 0 10px 0; text-transform: uppercase; }
        label { display: block; margin-bottom: 5px; font-weight: 600; font-size: 0.9rem; }
        input, select, textarea { width: 100%; padding: 12px; margin-bottom: 15px; border: 2px solid #ccc; border-radius: 8px; box-sizing: border-box; font-size: 1rem; background-color: #fafafa; }
        .row { display: flex; gap: 10px; }
        .row .col { flex: 1; }
        button { width: 100%; background-color: var(--primary); color: white; border: none; padding: 14px; font-size: 1.1rem; font-weight: bold; border-radius: 8px; cursor: pointer; margin-top: 10px; }
    </style>
</head>
<body>
<div class="form-container">
    <h2>🧑‍🌾 List Your Harvest</h2>
    <form action="/submit_farmer" method="POST">
        <div class="section-title">1. About Your Farm</div>
        <label for="farm_name">Farm or Enterprise Name</label>
        <input type="text" id="farm_name" name="farm_name" placeholder="e.g., DGAgroo Farm" required>
        <label for="location_city">Nearest Market Hub/City</label>
        <select id="location_city" name="location_city" required>
            <option value="Chegutu">Chegutu</option>
            <option value="Harare">Harare</option>
            <option value="Chinhoyi">Chinhoyi</option>
        </select>
        <label for="directions_intel">Simple Driving Directions</label>
        <textarea id="directions_intel" name="directions_intel" placeholder="e.g., Turn right at the Chicken Slice..."></textarea>
        <div class="section-title">2. Crop Details & Sales Strategy</div>
        <label for="crop_type">What Crop are you selling?</label>
        <select id="crop_type" name="crop_type" required>
            <option value="Onions">Onions</option>
            <option value="Groundnuts">Groundnuts</option>
            <option value="Potatoes">Potatoes</option>
        </select>
        <div class="row">
            <div class="col" style="flex: 1.5;">
                <label for="expected_yield">How much do you have?</label>
                <input type="number" id="expected_yield" name="expected_yield" placeholder="e.g. 150" required step="any">
            </div>
            <div class="col" style="flex: 1;">
                <label for="yield_unit">Unit Measure</label>
                <select id="yield_unit" name="yield_unit" required>
                    <option value="Square Meters">Sq Meters</option>
                    <option value="Bags">Bags</option>
                    <option value="Crates">Crates</option>
                </select>
            </div>
        </div>
        <label for="sale_condition">How do you want to hand it over?</label>
        <select id="sale_condition" name="sale_condition" required>
            <option value="Buy directly from the field (Buyer harvests/pulls)">Buyer must harvest directly from my field</option>
            <option value="Pre-packed at farm gate (Ready for pickup)">Pre-packed at farm gate</option>
        </select>
        <div class="row">
            <div class="col">
                <label for="expected_date">Ready Date</label>
                <input type="date" id="expected_date" name="expected_date" required>
            </div>
            <div class="col">
                <label for="growth_stage">Current Stage</label>
                <select id="growth_stage" name="growth_stage" required>
                    <option value="Near Maturity">Near Maturity</option>
                    <option value="Harvested & Stored">Harvested & Stored</option>
                </select>
            </div>
        </div>
        <button type="submit">Broadcast to Buyers 🚀</button>
    </form>
</div>
</body>
</html>
"""

BUYER_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Buyer Market Hub</title>
    <style>
        :root { --primary: #2e7d32; --accent: #1565c0; --bg: #f5f5f5; }
        body { font-family: system-ui, sans-serif; background-color: var(--bg); margin: 0; padding: 20px; color: #333; }
        .header { max-width: 800px; margin: 0 auto 20px auto; display: flex; justify-content: space-between; align-items: center; }
        h1 { color: #1b5e20; margin: 0; font-size: 1.6rem; }
        .nav-links a { text-decoration: none; font-weight: bold; margin-left: 15px; color: var(--accent); }
        .market-grid { max-width: 800px; margin: 0 auto; display: grid; grid-template-columns: 1fr; gap: 15px; }
        .listing-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border-left: 5px solid var(--primary); }
        .listing-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }
        .crop-title { font-size: 1.3rem; font-weight: bold; margin: 0; color: #111; }
        .volume-badge { background: #e8f5e9; color: #2e7d32; padding: 4px 10px; border-radius: 20px; font-weight: bold; font-size: 0.9rem; }
        .info-row { margin: 6px 0; font-size: 0.95rem; }
        .info-label { font-weight: 600; color: #666; }
        .logistics-box { background: #f9f9f9; padding: 12px; border-radius: 8px; margin-top: 15px; border: 1px solid #e0e0e0; }
        .logistics-title { font-weight: bold; font-size: 0.85rem; text-transform: uppercase; color: #555; margin-bottom: 5px; }
        .action-btn { display: inline-block; background: var(--primary); color: white; padding: 10px 16px; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; text-decoration: none; margin-top: 10px; font-size: 0.9rem; }
        .action-btn:hover { opacity: 0.9; }
    </style>
</head>
<body>
<div class="header">
    <h1>🛒 Live Produce Marketplace</h1>
    <div class="nav-links">
        <a href="/register">+ Sell Crop</a>
        <a href="/register_driver">+ Onboard Truck</a>
    </div>
</div>

<div class="market-grid">
    {% if not listings %}
        <div style="text-align:center; padding:40px; background:white; border-radius:12px;">No live crop listings available right now.</div>
    {% endif %}
    {% for item in listings %}
    <div class="listing-card">
        <div class="listing-header">
            <h3 class="crop-title">📦 {{ item.crop_futures_intel.commodity }}</h3>
            <span class="volume-badge">{{ item.crop_futures_intel.available_volume }}</span>
        </div>
        
        <div class="info-row"><span class="info-label">📍 Farm:</span> {{ item.seller_info.farm_name }} ({{ item.seller_info.origin_location }})</div>
        <div class="info-row"><span class="info-label">📝 Handover Strategy:</span> {{ item.crop_futures_intel.farmer_sale_terms }}</div>
        <div class="info-row"><span class="info-label">📅 Ready Date:</span> {{ item.crop_futures_intel.projected_harvest_release_date }} | <span class="info-label">🌱 Growth:</span> {{ item.crop_futures_intel.current_biological_stage }}</div>
        <div class="info-row" style="margin-top:10px;"><span class="info-label">🗺️ Navigation Notes:</span> <small style="color:#555;">{{ item.seller_info.navigation_notes }}</small></div>

        <div class="logistics-box">
            <div class="logistics-title">Logistics & Freight Status</div>
            {% if item.active_logistics_bids.assigned_carrier_name == "Open for Bids" %}
                <span style="color:#e65100; font-weight:bold;">⏳ No carrier attached yet (Open for bids)</span>
            {% else %}
                <div>🚛 <strong>Carrier:</strong> {{ item.active_logistics_bids.assigned_carrier_name }} ({{ item.active_logistics_bids.verified_vehicle_registration }})</div>
                <div>💰 <strong>Freight Quote:</strong> {{ item.active_logistics_bids.freight_cost_quote }} | 📦 <strong>Limit:</strong> {{ item.active_logistics_bids.hauling_capacity_limit }}</div>
            {% endif %}
        </div>
        
        <button class="action-btn" onclick="alert('Order request initialized for {{ item.crop_futures_intel.commodity }}!')">Secure This Harvest 💳</button>
    </div>
    {% endfor %}
</div>
</body>
</html>
"""

def init_commercial_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        phone_number TEXT NOT NULL UNIQUE,
        role TEXT CHECK(role IN ('farmer', 'buyer', 'driver')) NOT NULL
    )""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS farmers (
        farmer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        farm_name TEXT NOT NULL,
        location_city TEXT NOT NULL,
        map_pin TEXT NOT NULL,
        directions_intel TEXT,
        FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
    )""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expected_harvests (
        harvest_id INTEGER PRIMARY KEY AUTOINCREMENT,
        farmer_id INTEGER,
        crop_type TEXT NOT NULL,
        yield_quantity REAL NOT NULL,
        yield_unit TEXT NOT NULL, 
        sale_condition TEXT NOT NULL,
        expected_harvest_date TEXT NOT NULL,
        growth_stage TEXT NOT NULL,
        FOREIGN KEY(farmer_id) REFERENCES farmers(farmer_id) ON DELETE CASCADE
    )""")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS drivers (
        driver_profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE,
        vehicle_reg_number TEXT NOT NULL UNIQUE,
        drivers_license_number TEXT NOT NULL UNIQUE,
        truck_capacity_tonnes REAL NOT NULL,
        verification_status TEXT DEFAULT 'pending_review' CHECK(verification_status IN ('pending_review', 'verified', 'suspended')),
        FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
    )""")
    
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO users (full_name, phone_number, role) VALUES ('Chipo Transporter', '+263771111111', 'driver')")
        cursor.execute("INSERT INTO drivers (user_id, vehicle_reg_number, drivers_license_number, truck_capacity_tonnes, verification_status) VALUES (1, 'AGE-4921-ZW', 'DL-9938210-B', 7.5, 'verified')")
        
        cursor.execute("INSERT INTO users (full_name, phone_number, role) VALUES ('Denis Farmer', '+263772222222', 'farmer')")
        cursor.execute("INSERT INTO farmers (user_id, farm_name, location_city, map_pin, directions_intel) VALUES (2, 'DGAgroo', 'Chegutu', 'No Pin', 'At chicken slice turn right')")
        cursor.execute("""
            INSERT INTO expected_harvests (farmer_id, crop_type, yield_quantity, yield_unit, sale_condition, expected_harvest_date, growth_stage) 
            VALUES (1, 'Onions', 150, 'Square Meters', 'Buy directly from the field (Buyer harvests/pulls)', '2026-06-17', 'Near Maturity')
        """)
    
    conn.commit()
    conn.close()

if not os.path.exists(DB_NAME):
    init_commercial_db()
else:
    init_commercial_db()

# --- INTERACTIVE VISUAL ENDPOINTS ---
@app.route('/register', methods=['GET'])
def serve_farmer_form():
    return render_template_string(FARMER_FORM_HTML)

@app.route('/register_driver', methods=['GET'])
def serve_driver_form():
    return render_template_string(DRIVER_FORM_HTML)

# --- PROCESS SUBMISSIONS ---
@app.route('/submit_farmer', methods=['POST'])
def handle_submission():
    farm_name = request.form.get('farm_name')
    location_city = request.form.get('location_city')
    directions_intel = request.form.get('directions_intel')
    crop_type = request.form.get('crop_type')
    yield_qty = request.form.get('expected_yield', type=float)
    yield_unit = request.form.get('yield_unit')
    sale_condition = request.form.get('sale_condition')
    expected_date = request.form.get('expected_date')
    growth_stage = request.form.get('growth_stage')

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO farmers (user_id, farm_name, location_city, map_pin, directions_intel) VALUES (2, ?, ?, 'No Pin', ?)", (farm_name, location_city, directions_intel))
    assigned_farmer_id = cursor.lastrowid 
    cursor.execute("INSERT INTO expected_harvests (farmer_id, crop_type, yield_quantity, yield_unit, sale_condition, expected_harvest_date, growth_stage) VALUES (?, ?, ?, ?, ?, ?, ?)", (assigned_farmer_id, crop_type, yield_qty, yield_unit, sale_condition, expected_date, growth_stage))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/submit_driver', methods=['POST'])
def handle_driver_submission():
    full_name = request.form.get('full_name')
    phone_number = request.form.get('phone_number')
    vehicle_reg = request.form.get('vehicle_reg')
    license_num = request.form.get('license_num')
    truck_capacity = request.form.get('truck_capacity', type=float)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (full_name, phone_number, role) VALUES (?, ?, 'driver')", (full_name, phone_number))
        new_user_id = cursor.lastrowid
        cursor.execute("INSERT INTO drivers (user_id, vehicle_reg_number, drivers_license_number, truck_capacity_tonnes, verification_status) VALUES (?, ?, ?, ?, 'verified')", (new_user_id, vehicle_reg, license_num, truck_capacity))
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.rollback()
        return f'<div style="font-family:sans-serif;padding:30px;text-align:center;"><h3 style="color:red;">Submission Conflict</h3><p>{str(e)}</p><a href="/register_driver">Go Back</a></div>'
    finally:
        conn.close()
    return redirect('/dashboard')

# --- VISUAL BUYER MARKET DASHBOARD ---
@app.route('/dashboard', methods=['GET'])
def visual_dashboard():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.farm_name, f.location_city, f.directions_intel,
               h.crop_type, h.yield_quantity, h.yield_unit, h.sale_condition, h.expected_harvest_date, h.growth_stage
        FROM farmers f
        JOIN expected_harvests h ON f.farmer_id = h.farmer_id
    """)
    db_rows = cursor.fetchall()
    conn.close()
    
    market_listings = []
    for row in db_rows:
        market_listings.append({
            "seller_info": {"farm_name": row["farm_name"], "origin_location": row["location_city"], "navigation_notes": row["directions_intel"]},
            "crop_futures_intel": {"commodity": row["crop_type"], "available_volume": f"{row['yield_quantity']} {row['yield_unit']}", "farmer_sale_terms": row["sale_condition"], "projected_harvest_release_date": row["expected_harvest_date"], "current_biological_stage": row["growth_stage"]},
            "active_logistics_bids": {"assigned_carrier_name": "Open for Bids"}
        })
    return render_template_string(BUYER_DASHBOARD_HTML, listings=market_listings)

# --- RETUNING ORIGINAL ENDPOINT FOR MAXIMUM NESTED DATA VISUALS ---
@app.route('/explore_market', methods=['GET'])
def explore_market():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT f.farm_name, f.location_city, f.directions_intel,
               h.harvest_id, h.crop_type, h.yield_quantity, h.yield_unit, h.sale_condition, h.expected_harvest_date, h.growth_stage
        FROM farmers f
        JOIN expected_harvests h ON f.farmer_id = h.farmer_id
    """)
    db_rows = cursor.fetchall()
    conn.close()
    
    market_listings = []
    for row in db_rows:
        market_listings.append({
            "harvest_id": row["harvest_id"],
            "seller_info": {
                "farm_name": row["farm_name"],
                "origin_location": row["location_city"],
                "navigation_notes": row["directions_intel"]
            },
            "crop_futures_intel": {
                "commodity": row["crop_type"],
                "available_volume": f"{row['yield_quantity']} {row['yield_unit']}",
                "farmer_sale_terms": row["sale_condition"],
                "projected_harvest_release_date": row["expected_harvest_date"],
                "current_biological_stage": row["growth_stage"]
            },
            "active_logistics_bids": {
                "assigned_carrier_name": "Open for Bids",
                "freight_cost_quote": "N/A"
            }
        })
    return jsonify({"active_commercial_market_ledger": market_listings})

if __name__ == '__main__':
    print("\n🚀 Engine Running. Open /dashboard to view the buyer hub...")
    app.run(debug=False, port=5000)