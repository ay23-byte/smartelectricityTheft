# # =============================
# # SMART ELECTRICITY THEFT SYSTEM (FINAL + TWILIO)
# # =============================

# import numpy as np
# import sqlite3
# from sklearn.ensemble import IsolationForest
# from flask import Flask, render_template_string, request, redirect, session, jsonify
# from twilio.rest import Client   # ✅ TWILIO

# # ---------------- DATABASE ----------------
# conn = sqlite3.connect('theft.db', check_same_thread=False)
# c = conn.cursor()

# c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)''')
# c.execute('''CREATE TABLE IF NOT EXISTS thefts (
#     voltage REAL,
#     current REAL,
#     power REAL,
#     lat REAL,
#     lon REAL
# )''')

# c.execute("INSERT OR IGNORE INTO users VALUES ('admin','admin123')")
# conn.commit()

# # ---------------- TWILIO CONFIG ----------------
# TWILIO_SID = "AC5f108cdadf17b4a6548540fe7553e7d4"
# TWILIO_AUTH = "f72240ac7c5aa3b2d397d66103ea75ca"
# TWILIO_FROM = "+1 838 332 3441"
# TWILIO_TO = "+919838502403"

# client = Client(TWILIO_SID, TWILIO_AUTH)

# # ---------------- MODEL ----------------
# model = IsolationForest(contamination=0.1)
# model.fit(np.random.rand(200,3))

# # ---------------- DATA ----------------
# def generate_data():
#     v = np.random.normal(220, 5)
#     i = np.random.normal(5, 1)

#     if np.random.rand() > 0.85:
#         i *= 3

#     return v, i, v*i

# def generate_location():
#     return np.random.uniform(28.5,28.9), np.random.uniform(77.0,77.5)

# # ---------------- APP ----------------
# app = Flask(__name__)
# app.secret_key = 'secret'

# # ---------------- LOGIN ----------------
# @app.route('/', methods=['GET','POST'])
# def login():
#     if request.method == 'POST':
#         u = request.form['username']
#         p = request.form['password']

#         c.execute('SELECT * FROM users WHERE username=? AND password=?',(u,p))
#         if c.fetchone():
#             session['user']=u
#             return redirect('/dashboard')

#     return '''
#     <body style="background:#020617;color:white;text-align:center;font-family:sans-serif">
#     <h1>⚡ Smart Grid Login</h1>
#     <form method="POST">
#     <input name="username" placeholder="Username"><br><br>
#     <input name="password" type="password" placeholder="Password"><br><br>
#     <button style="padding:10px 20px">Login</button>
#     </form>
#     </body>
#     '''

# # ---------------- LAYOUT ----------------
# def layout(content):
#     return f"""
#     <html>
#     <head>
#     <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
#     <style>
#     body {{
#         margin:0;
#         font-family:sans-serif;
#         background:#020617;
#         color:white;
#     }}
#     .sidebar {{
#         width:220px;
#         height:100vh;
#         position:fixed;
#         background:#0f172a;
#         padding:20px;
#     }}
#     .sidebar a {{
#         display:block;
#         padding:12px;
#         margin:10px 0;
#         background:#1e293b;
#         color:white;
#         text-decoration:none;
#         border-radius:8px;
#         text-align:center;
#     }}
#     .main {{
#         margin-left:240px;
#         padding:20px;
#     }}
#     .card {{
#         padding:20px;
#         background:rgba(255,255,255,0.05);
#         border-radius:15px;
#         margin-bottom:20px;
#     }}
#     </style>
#     </head>

#     <body>

#     <div class="sidebar">
#     <h2>⚡ Smart Grid</h2>
#     <a href="/dashboard">Dashboard</a>
#     <a href="/map">Map</a>
#     </div>

#     <div class="main">
#     {content}
#     </div>

#     </body>
#     </html>
#     """

# # ---------------- LIVE API (WITH SMS ALERT) ----------------
# @app.route('/api/live')
# def live():
#     data=[]

#     for _ in range(10):
#         v,i,p = generate_data()
#         pred = model.predict([[v,i,p]])
#         status = 'YES' if pred[0]==-1 else 'NO'

#         lat, lon = generate_location()

#         if status=='YES':
#             # SAVE DATA
#             c.execute('INSERT INTO thefts VALUES (?,?,?,?,?)',(v,i,p,lat,lon))
#             conn.commit()

#             # 🔥 SEND SMS ALERT
#             try:
#                 client.messages.create(
#                     body=f"⚠️ Electricity Theft Detected!\nPower: {round(p,2)}W\nLocation: {round(lat,3)}, {round(lon,3)}",
#                     from_=TWILIO_FROM,
#                     to=TWILIO_TO
#                 )
#             except Exception as e:
#                 print("SMS Error:", e)

#         data.append({
#             "v":round(v,2),
#             "i":round(i,2),
#             "p":round(p,2),
#             "status":status
#         })

#     return jsonify(data)

# # ---------------- DASHBOARD ----------------
# @app.route('/dashboard')
# def dashboard():
#     content = """
#     <h1>⚡ Live Dashboard</h1>

#     <div class="card">
#     <canvas id="chart"></canvas>
#     </div>

#     <table border=1 width="100%" id="table">
#     <tr><th>V</th><th>I</th><th>P</th><th>Status</th></tr>
#     </table>

#     <script>
#     const ctx = document.getElementById('chart').getContext('2d');
#     const chart = new Chart(ctx, {
#         type: 'line',
#         data: {
#             labels: [],
#             datasets: [{
#                 label: 'Power',
#                 data: [],
#                 borderWidth: 2
#             }]
#         }
#     });

#     function updateData() {
#         fetch('/api/live')
#         .then(res=>res.json())
#         .then(data=>{
#             let table = document.getElementById("table");

#             data.forEach(d=>{
#                 let row = table.insertRow(-1);
#                 row.innerHTML = `<td>${d.v}</td><td>${d.i}</td><td>${d.p}</td>
#                 <td style="color:${d.status=='YES'?'red':'lime'}">${d.status}</td>`;

#                 chart.data.labels.push('');
#                 chart.data.datasets[0].data.push(d.p);

#                 if(chart.data.labels.length > 20){
#                     chart.data.labels.shift();
#                     chart.data.datasets[0].data.shift();
#                 }

#                 chart.update();

#                 if(d.status == 'YES'){
#                     console.log("Theft detected!");
#                 }
#             });
#         });
#     }

#     setInterval(updateData, 3000);
#     </script>
#     """

#     return layout(content)

# # ---------------- MAP ----------------
# @app.route('/map')
# def map_view():
#     content = """
#     <h1>📍 Theft Map</h1>
#     <div id="map" style="height:500px;"></div>

#     <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
#     <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
#     <script src="https://unpkg.com/leaflet.heat/dist/leaflet-heat.js"></script>

#     <script>
#     var map = L.map('map').setView([28.6,77.2],11);

#     L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

#     fetch('/api/thefts')
#     .then(res=>res.json())
#     .then(data=>{
#         let pts=[];
#         data.forEach(p=>{
#             let latlng=[p.lat,p.lon];
#             L.marker(latlng).addTo(map);
#             pts.push(latlng);
#         });
#         L.heatLayer(pts,{radius:25}).addTo(map);
#     });
#     </script>
#     """

#     return layout(content)

# # ---------------- THEFT API ----------------
# @app.route('/api/thefts')
# def thefts():
#     c.execute("SELECT lat, lon FROM thefts")
#     return jsonify([{"lat":r[0],"lon":r[1]} for r in c.fetchall()])

# # ---------------- RUN ----------------
# if __name__ == '__main__':
#     app.run(debug=True)

# =============================
# SMART ELECTRICITY THEFT SYSTEM (ULTIMATE)
# =============================

# =============================
# SMART ELECTRICITY THEFT SYSTEM (FINAL BOSS)
# =============================

# =============================
# FINAL BOSS: SMART GRID AI SYSTEM
# =============================



# import numpy as np
# import sqlite3
# import time
# from sklearn.ensemble import IsolationForest
# from flask import Flask, request, redirect, session, jsonify

# # ---------------- DATABASE ----------------
# conn = sqlite3.connect('theft.db', check_same_thread=False)
# c = conn.cursor()

# c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)')
# c.execute('''CREATE TABLE IF NOT EXISTS thefts (
#     voltage REAL,
#     current REAL,
#     power REAL,
#     lat REAL,
#     lon REAL
# )''')

# c.execute("INSERT OR IGNORE INTO users VALUES ('admin','admin123')")
# conn.commit()

# # ---------------- ML MODEL ----------------
# model = IsolationForest(contamination=0.1)
# model.fit(np.random.rand(200,3))

# # ---------------- TWILIO ----------------
# TWILIO_SID = "AC5f108cdadf17b4a6548540fe7553e7d4"
# TWILIO_AUTH = "f72240ac7c5aa3b2d397d66103ea75ca"
# TWILIO_FROM = "+1 838 332 3441"
# TWILIO_TO = "+919838502403"

# try:
#     from twilio.rest import Client
#     client = Client(TWILIO_SID, TWILIO_AUTH)
# except:
#     client = None

# last_alert_time = 0

# # ---------------- DATA ----------------
# def generate_data():
#     v = np.random.normal(220, 5)
#     i = np.random.normal(5, 1)
#     if np.random.rand() > 0.85:
#         i *= 3
#     return v, i, v*i

# def generate_location():
#     return np.random.uniform(28.5, 28.9), np.random.uniform(77.0, 77.5)

# # ---------------- APP ----------------
# app = Flask(__name__)
# app.secret_key = 'secret'

# # ---------------- LOGIN ----------------
# @app.route('/', methods=['GET','POST'])
# def login():
#     if request.method == 'POST':
#         u = request.form['username']
#         p = request.form['password']
#         c.execute('SELECT * FROM users WHERE username=? AND password=?',(u,p))
#         if c.fetchone():
#             session['user']=u
#             return redirect('/dashboard')

#     return '''
#     <body style="background:#020617;color:white;text-align:center;font-family:sans-serif">
#     <h1>⚡ Smart Grid AI</h1>
#     <form method='POST'>
#     <input name='username' placeholder='Username'><br><br>
#     <input name='password' type='password' placeholder='Password'><br><br>
#     <button>Login</button>
#     </form>
#     </body>
#     '''

# # ---------------- API ----------------
# @app.route('/api/live')
# def api_live():
#     global last_alert_time

#     data = []
#     for _ in range(20):
#         v,i,p = generate_data()
#         pred = model.predict([[v,i,p]])
#         status = 'YES' if pred[0]==-1 else 'NO'

#         lat, lon = generate_location()

#         if status=='YES':
#             c.execute('INSERT INTO thefts VALUES (?,?,?,?,?)',(v,i,p,lat,lon))
#             conn.commit()

#             if client and time.time() - last_alert_time > 30:
#                 last_alert_time = time.time()
#                 try:
#                     client.messages.create(
#                         body=f"⚠ Theft! Power:{round(p,2)}W @ {lat},{lon}",
#                         from_=TWILIO_FROM,
#                         to=TWILIO_TO
#                     )
#                 except:
#                     pass

#         data.append({
#             "voltage": round(v,2),
#             "current": round(i,2),
#             "power": round(p,2),
#             "status": status,
#             "lat": lat,
#             "lon": lon
#         })

#     return jsonify(data)

# # ---------------- DASHBOARD ----------------
# @app.route('/dashboard')
# def dashboard():
#     if 'user' not in session:
#         return redirect('/')

#     return '''
#     <html>
#     <body style="background:#020617;color:white;text-align:center;font-family:sans-serif">

#     <h1>⚡ Smart Grid Control Center</h1>

#     <a href="/map" style="color:cyan">📍 Map</a> |
#     <a href="/earth" style="color:orange">🌍 Earth 3D</a>

#     <table border=1 style="margin:auto;background:white;color:black">
#     <tr><th>Voltage</th><th>Current</th><th>Power</th><th>Status</th></tr>
#     <tbody id="data"></tbody>
#     </table>

#     <script>
#     function load(){
#         fetch('/api/live')
#         .then(res=>res.json())
#         .then(data=>{
#             let rows="";
#             data.forEach(d=>{
#                 rows+=`<tr>
#                 <td>${d.voltage}</td>
#                 <td>${d.current}</td>
#                 <td>${d.power}</td>
#                 <td style="color:${d.status==='YES'?'red':'green'}">${d.status}</td>
#                 </tr>`;
#             });
#             document.getElementById("data").innerHTML=rows;
#         });
#     }
#     setInterval(load,2000);
#     load();
#     </script>

#     </body>
#     </html>
#     '''

# # ---------------- MAP ----------------
# @app.route('/map')
# def map_view():
#     return '''
#     <html>
#     <head>
#     <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
#     <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
#     <style>
#     html,body,#map{height:100%;margin:0;}
#     </style>
#     </head>
#     <body>
#     <div id="map"></div>

#     <script>
#     var map = L.map('map').setView([28.6,77.2],11);

#     L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

#     let markers=[];

#     function load(){
#         markers.forEach(m=>map.removeLayer(m));
#         markers=[];

#         fetch('/api/live')
#         .then(r=>r.json())
#         .then(data=>{
#             data.forEach(d=>{
#                 if(d.status==="YES"){
#                     let m=L.marker([d.lat,d.lon]).addTo(map)
#                     .bindPopup("⚠ Theft");
#                     markers.push(m);
#                 }
#             });
#         });
#     }

#     setInterval(load,3000);
#     load();
#     </script>
#     </body>
#     </html>
#     '''

# # ---------------- EARTH ----------------
# @app.route('/earth')
# def earth():
#     return '''
#     <html>
#     <head>

#     <script src="https://cesium.com/downloads/cesiumjs/releases/1.111/Build/Cesium/Cesium.js"></script>
#     <link href="https://cesium.com/downloads/cesiumjs/releases/1.111/Build/Cesium/Widgets/widgets.css" rel="stylesheet">

#     <style>
#     html,body,#c{width:100%;height:100%;margin:0;}
#     </style>

#     </head>

#     <body>

#     <div id="c"></div>

#     <script>
#     Cesium.Ion.defaultAccessToken="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJhYmQ4MzE0Mi0yZjViLTRhZDgtYmJlNS00Y2IzZmY3Mzc4M2YiLCJpZCI6NDA1NTUxLCJpYXQiOjE3NzM4Mjg0OTh9.J7z-oQ0aO7ttHSRWpNEIsbHG7COIuh5Zt9-DuR3wncI";

#     const viewer=new Cesium.Viewer('c',{
#         animation:false,
#         timeline:false
#     });

#     viewer.camera.setView({
#         destination: Cesium.Cartesian3.fromDegrees(77.2,28.6,1500000)
#     });

#     let entities=[];

#     function load(){
#         fetch('/api/live')
#         .then(r=>r.json())
#         .then(data=>{

#             entities.forEach(e=>viewer.entities.remove(e));
#             entities=[];

#             data.forEach(d=>{
#                 if(d.status==="YES"){
#                     let e=viewer.entities.add({
#                         position: Cesium.Cartesian3.fromDegrees(d.lon,d.lat),
#                         point:{pixelSize:12,color:Cesium.Color.RED},
#                         label:{text:"⚠ Theft",pixelOffset:new Cesium.Cartesian2(0,-20)}
#                     });
#                     entities.push(e);
#                 }
#             });

#         });
#     }

#     setInterval(load,3000);
#     load();
#     </script>

#     </body>
#     </html>
#     '''

# # ---------------- RUN ----------------
# if __name__ == "__main__":
#     app.run(debug=True)

# import numpy as np
# import sqlite3
# import time
# import requests
# from sklearn.ensemble import IsolationForest
# from flask import Flask, request, redirect, session, jsonify

# # ---------------- DATABASE ----------------
# conn = sqlite3.connect('theft.db', check_same_thread=False)
# c = conn.cursor()

# c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)')
# c.execute('''CREATE TABLE IF NOT EXISTS thefts (
#     voltage REAL,
#     current REAL,
#     power REAL,
#     lat REAL,
#     lon REAL
# )''')

# c.execute("INSERT OR IGNORE INTO users VALUES ('admin','admin123')")
# conn.commit()

# # ---------------- ML MODEL ----------------
# model = IsolationForest(contamination=0.1)
# model.fit(np.random.rand(200,3))

# # ---------------- GLOBAL LOCATION ----------------
# current_lat = 28.6
# current_lon = 77.2

# # ---------------- TWILIO ----------------
# TWILIO_SID = "AC5f108cdadf17b4a6548540fe7553e7d4"
# TWILIO_AUTH = "f72240ac7c5aa3b2d397d66103ea75ca"
# TWILIO_FROM = "+1 838 332 3441"
# TWILIO_TO = "+919838502403"


# try:
#     from twilio.rest import Client
#     client = Client(TWILIO_SID, TWILIO_AUTH)
# except:
#     client = None

# last_alert_time = 0

# # ---------------- DATA ----------------
# def generate_data():
#     v = np.random.normal(220, 5)
#     i = np.random.normal(5, 1)
#     if np.random.rand() > 0.85:
#         i *= 3
#     return v, i, v*i

# def generate_location():
#     return current_lat, current_lon

# # ---------------- APP ----------------
# app = Flask(__name__)
# app.secret_key = 'secret'

# # ---------------- LOGIN ----------------
# @app.route('/', methods=['GET','POST'])
# def login():
#     if request.method == 'POST':
#         u = request.form['username']
#         p = request.form['password']
#         c.execute('SELECT * FROM users WHERE username=? AND password=?',(u,p))
#         if c.fetchone():
#             session['user']=u
#             return redirect('/dashboard')

#     return '''
#     <body style="background:#020617;color:white;text-align:center;font-family:sans-serif">
#     <h1>⚡ Smart Grid AI</h1>
#     <form method='POST'>
#     <input name='username'><br><br>
#     <input name='password' type='password'><br><br>
#     <button>Login</button>
#     </form>
#     </body>
#     '''

# # ---------------- CITY SEARCH ----------------
# @app.route('/set_city', methods=['POST'])
# def set_city():
#     global current_lat, current_lon

#     city = request.form['city']
#     url = f"https://nominatim.openstreetmap.org/search?format=json&q={city}"

#     res = requests.get(url, headers={"User-Agent":"Mozilla/5.0"}).json()

#     if len(res) > 0:
#         current_lat = float(res[0]['lat'])
#         current_lon = float(res[0]['lon'])
#         return "✅ Location Updated"
#     else:
#         return "❌ City not found"

# # ---------------- API ----------------
# @app.route('/api/live')
# def api_live():
#     global last_alert_time

#     data = []
#     for _ in range(20):
#         v,i,p = generate_data()
#         pred = model.predict([[v,i,p]])
#         status = 'YES' if pred[0]==-1 else 'NO'

#         lat, lon = generate_location()

#         if status=='YES':
#             c.execute('INSERT INTO thefts VALUES (?,?,?,?,?)',(v,i,p,lat,lon))
#             conn.commit()

#             if client and time.time() - last_alert_time > 30:
#                 last_alert_time = time.time()
#                 try:
#                     client.messages.create(
#                         body=f"⚠ Theft! Power:{round(p,2)}W @ {lat},{lon}",
#                         from_=TWILIO_FROM,
#                         to=TWILIO_TO
#                     )
#                 except:
#                     pass

#         data.append({
#             "voltage": round(v,2),
#             "current": round(i,2),
#             "power": round(p,2),
#             "status": status,
#             "lat": lat,
#             "lon": lon
#         })

#     return jsonify(data)

# # ---------------- DASHBOARD ----------------
# @app.route('/dashboard')
# def dashboard():
#     if 'user' not in session:
#         return redirect('/')

#     return '''
#     <html>
#     <body style="background:#020617;color:white;text-align:center;font-family:sans-serif">

#     <h1>⚡ Smart Grid Control Center</h1>

#     <h2>🌍 Search City</h2>
#     <input id="city" placeholder="Enter city (Mumbai, Delhi...)">
#     <button onclick="setCity()">Search</button>

#     <br><br>

#     <a href="/map" style="color:cyan">📍 Map</a> |
#     <a href="/earth" style="color:orange">🌍 Earth 3D</a>

#     <table border=1 style="margin:auto;background:white;color:black">
#     <tr><th>Voltage</th><th>Current</th><th>Power</th><th>Status</th></tr>
#     <tbody id="data"></tbody>
#     </table>

#     <script>
#     function setCity(){
#         let city = document.getElementById("city").value;

#         fetch('/set_city',{
#             method:'POST',
#             headers:{'Content-Type':'application/x-www-form-urlencoded'},
#             body:`city=${city}`
#         })
#         .then(res=>res.text())
#         .then(msg=>alert(msg));
#     }

#     function load(){
#         fetch('/api/live')
#         .then(res=>res.json())
#         .then(data=>{
#             let rows="";
#             data.forEach(d=>{
#                 rows+=`<tr>
#                 <td>${d.voltage}</td>
#                 <td>${d.current}</td>
#                 <td>${d.power}</td>
#                 <td style="color:${d.status==='YES'?'red':'green'}">${d.status}</td>
#                 </tr>`;
#             });
#             document.getElementById("data").innerHTML=rows;
#         });
#     }

#     setInterval(load,2000);
#     load();
#     </script>

#     </body>
#     </html>
#     '''

# # ---------------- MAP (FINAL UPGRADED) ----------------
# @app.route('/map')
# def map_view():
#     return f'''
#     <html>
#     <head>

#     <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
#     <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
#     <script src="https://unpkg.com/leaflet.heat/dist/leaflet-heat.js"></script>

#     <style>
#     html,body,#map{{height:100%;margin:0;}}

#     .pulse {{
#         width: 12px;
#         height: 12px;
#         background: red;
#         border-radius: 50%;
#         position: relative;
#     }}
#     .pulse::after {{
#         content:'';
#         width:30px;
#         height:30px;
#         border:2px solid red;
#         border-radius:50%;
#         position:absolute;
#         top:-9px;
#         left:-9px;
#         animation:pulse 1.5s infinite;
#     }}
#     @keyframes pulse {{
#         0%{{transform:scale(0.5);opacity:1;}}
#         100%{{transform:scale(2);opacity:0;}}
#     }}
#     </style>

#     </head>

#     <body>

#     <div id="map"></div>

#     <script>

#     var map = L.map('map').setView([{current_lat},{current_lon}],11);

#     L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);

#     let markers=[];
#     let heat;

#     function load(){{

#         markers.forEach(m=>map.removeLayer(m));
#         markers=[];

#         if(heat) map.removeLayer(heat);

#         fetch('/api/live')
#         .then(r=>r.json())
#         .then(data=>{{

#             let heatPoints=[];

#             data.forEach(d=>{{
#                 if(d.status==="YES"){{

#                     let icon=L.divIcon({{
#                         html:'<div class="pulse"></div>',
#                         iconSize:[20,20]
#                     }});

#                     let m=L.marker([d.lat,d.lon],{{icon:icon}})
#                     .addTo(map)
#                     .bindPopup("⚠ Theft");

#                     markers.push(m);
#                     heatPoints.push([d.lat,d.lon,1]);
#                 }}
#             }});

#             heat=L.heatLayer(heatPoints,{{radius:25,blur:15}}).addTo(map);

#         }});
#     }}

#     setInterval(load,3000);
#     load();

#     </script>
#     </body>
#     </html>
#     '''

# # ---------------- EARTH ----------------
# @app.route('/earth')
# def earth():
#     return f'''
#     <html>
#     <head>

#     <script src="https://cesium.com/downloads/cesiumjs/releases/1.111/Build/Cesium/Cesium.js"></script>
#     <link href="https://cesium.com/downloads/cesiumjs/releases/1.111/Build/Cesium/Widgets/widgets.css" rel="stylesheet">

#     <style>
#     html, body, #c {{
#         width: 100%;
#         height: 100%;
#         margin: 0;
#         overflow: hidden;
#     }}
#     </style>

#     </head>

#     <body>

#     <div id="c"></div>

#     <script>

#     try {{

#         // ✅ STEP 1: TOKEN
#         Cesium.Ion.defaultAccessToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI5ZTI4MGQwYS1hYzBlLTRjNDgtYTUzMi01NzUwNjkyMDVhYzQiLCJpZCI6NDA1NTUxLCJpYXQiOjE3NzM5MDY2ODB9.HzmrtJi7ayGSPxJ7Npsi0waFpcs7d7b-vNMdItD7b28";

#         // ✅ STEP 2: SIMPLE VIEWER (NO TERRAIN = NO ERROR)
#         const viewer = new Cesium.Viewer('c', {{
#             animation: false,
#             timeline: false,
#             baseLayerPicker: true
#         }});

#         // ✅ STEP 3: CAMERA FIX
#         viewer.camera.setView({{
#             destination: Cesium.Cartesian3.fromDegrees({current_lon},{current_lat},2000000)
#         }});

#         let entities = [];

#         function load(){{
#             fetch('/api/live')
#             .then(r=>r.json())
#             .then(data=>{{

#                 entities.forEach(e=>viewer.entities.remove(e));
#                 entities=[];

#                 data.forEach(d=>{{
#                     if(d.status==="YES"){{
#                         let e = viewer.entities.add({{
#                             position: Cesium.Cartesian3.fromDegrees(d.lon,d.lat),
#                             point: {{
#                                 pixelSize: 15,
#                                 color: Cesium.Color.RED
#                             }},
#                             label: {{
#                                 text: "⚠ Theft",
#                                 pixelOffset: new Cesium.Cartesian2(0,-20)
#                             }}
#                         }});
#                         entities.push(e);
#                     }}
#                 }});

#             }});
#         }}

#         setInterval(load,3000);
#         load();

#     }} catch(e) {{
#         document.body.innerHTML = "<h1 style='color:red'>ERROR: " + e + "</h1>";
#         console.error(e);
#     }}

#     </script>

#     </body>
#     </html>
#     '''
# # ---------------- RUN ----------------
# if __name__ == "__main__":
#     app.run(debug=True)

import numpy as np
import sqlite3
import time
import requests
import os
from sklearn.ensemble import IsolationForest
from flask import Flask, request, redirect, session, jsonify


## accessing the stuff

import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Access them using os
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH")
TWILIO_FROM = os.getenv("TWILIO_FROM")
TWILIO_TO = os.getenv("TWILIO_TO")



# ---------------- DATABASE ----------------
conn = sqlite3.connect('theft.db', check_same_thread=False)
c = conn.cursor()

c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT, password TEXT)')
c.execute('''CREATE TABLE IF NOT EXISTS thefts (
    voltage REAL,
    current REAL,
    power REAL,
    lat REAL,
    lon REAL,
    city TEXT
)''')

c.execute("INSERT OR IGNORE INTO users VALUES ('admin','admin123')")
conn.commit()

# ---------------- ML MODEL ----------------
model = IsolationForest(contamination=0.1)
model.fit(np.random.rand(200,3))

# ---------------- MULTI CITY ----------------
tracked_cities = [
    {"name": "Delhi", "lat": 28.6, "lon": 77.2},
    {"name": "Mumbai", "lat": 19.07, "lon": 72.87},
    {"name": "Bangalore", "lat": 12.97, "lon": 77.59},
    {"name": "Kolkata", "lat": 22.57, "lon": 88.36},
    {"name": "Chennai", "lat": 13.08, "lon": 80.27}
]

# ---------------- TWILIO ----------------
TWILIO_SID = "AC5f108cdadf17b4a6548540fe7553e7d4"
TWILIO_AUTH = "f72240ac7c5aa3b2d397d66103ea75ca"
TWILIO_FROM = "+1 838 332 3441"
TWILIO_TO = "+919838502403"


try:
    from twilio.rest import Client
    client = Client(TWILIO_SID, TWILIO_AUTH)
except:
    client = None

last_alert_time = 0

# ---------------- DATA ----------------
def generate_data():
    v = np.random.normal(220, 5)
    i = np.random.normal(5, 1)
    if np.random.rand() > 0.85:
        i *= 3
    return v, i, v*i

def generate_location():
    city = np.random.choice(tracked_cities)
    return city["lat"], city["lon"], city["name"]

# ---------------- APP ----------------
app = Flask(__name__)
app.secret_key = 'secret'

# ---------------- LOGIN ----------------
@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']
        c.execute('SELECT * FROM users WHERE username=? AND password=?',(u,p))
        if c.fetchone():
            session['user']=u
            return redirect('/dashboard')

    return '''
    <body style="background:#000;color:#00ffff;text-align:center;font-family:Orbitron">
    <h1>🚀 SMART GRID AI</h1>
    <form method='POST'>
    <input name='username'><br><br>
    <input name='password' type='password'><br><br>
    <button>Login</button>
    </form>
    </body>
    '''

# ---------------- API ----------------
@app.route('/api/live')
def api_live():
    global last_alert_time

    data = []
    for _ in range(20):
        v,i,p = generate_data()
        pred = model.predict([[v,i,p]])
        status = 'YES' if pred[0]==-1 else 'NO'

        lat, lon, city = generate_location()

        if status=='YES':
            c.execute('INSERT INTO thefts VALUES (?,?,?,?,?,?)',(v,i,p,lat,lon,city))
            conn.commit()

            if client and time.time() - last_alert_time > 30:
                last_alert_time = time.time()
                try:
                    client.messages.create(
                        body=f"⚠ Theft in {city}\nPower:{round(p,2)}W",
                        from_=TWILIO_FROM,
                        to=TWILIO_TO
                    )
                except:
                    pass

        data.append({
            "voltage": round(v,2),
            "current": round(i,2),
            "power": round(p,2),
            "status": status,
            "lat": lat,
            "lon": lon,
            "city": city
        })

    return jsonify(data)

# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')

    return '''
    <html>
    <head>
    <style>
    body {
        background: radial-gradient(circle, #020617, #000);
        color: cyan;
        font-family: Orbitron;
        text-align:center;
    }
    table {
        margin:auto;
        box-shadow:0 0 20px cyan;
    }
    td,th {
        padding:10px;
        border:1px solid cyan;
    }
    </style>
    </head>

    <body>

    <h1>🛰 NASA CONTROL PANEL</h1>

    <a href="/map">📍 Map</a> |
    <a href="/earth">🌍 3D Earth</a>

    <table>
    <tr><th>City</th><th>Voltage</th><th>Current</th><th>Power</th><th>Status</th></tr>
    <tbody id="data"></tbody>
    </table>

    <script>
    function load(){
        fetch('/api/live')
        .then(r=>r.json())
        .then(data=>{
            let rows="";
            data.forEach(d=>{
                rows+=`<tr>
                <td>${d.city}</td>
                <td>${d.voltage}</td>
                <td>${d.current}</td>
                <td>${d.power}</td>
                <td style="color:${d.status==='YES'?'red':'lime'}">${d.status}</td>
                </tr>`;
            });
            document.getElementById("data").innerHTML=rows;
        });
    }
    setInterval(load,2000);
    load();
    </script>

    </body>
    </html>
    '''

# ---------------- MAP ----------------
@app.route('/map')
def map_view():
    return '''
    <html>
    <head>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.heat/dist/leaflet-heat.js"></script>
    <style>html,body,#map{height:100%;margin:0;}</style>
    </head>

    <body>
    <div id="map"></div>

    <script>
    var map = L.map('map').setView([22.5,78.9],5);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

    let markers=[];
    let heat;

    function load(){
        markers.forEach(m=>map.removeLayer(m));
        markers=[];

        if(heat) map.removeLayer(heat);

        fetch('/api/live')
        .then(r=>r.json())
        .then(data=>{

            let heatPoints=[];

            data.forEach(d=>{
                if(d.status==="YES"){
                    let m=L.marker([d.lat,d.lon]).addTo(map)
                    .bindPopup("⚠ Theft in "+d.city);
                    markers.push(m);
                    heatPoints.push([d.lat,d.lon,1]);
                }
            });

            heat=L.heatLayer(heatPoints).addTo(map);
        });
    }

    setInterval(load,3000);
    load();
    </script>

    </body>
    </html>
    '''

# ---------------- EARTH 3D ----------------
@app.route('/earth')
def earth():
    return '''
    <html>
    <head>
    <script src="https://cesium.com/downloads/cesiumjs/releases/1.111/Build/Cesium/Cesium.js"></script>
    <link href="https://cesium.com/downloads/cesiumjs/releases/1.111/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
    <style>html,body,#c{width:100%;height:100%;margin:0;}</style>
    </head>

    <body>
    <div id="c"></div>

    <script>
    Cesium.Ion.defaultAccessToken="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI5ZTI4MGQwYS1hYzBlLTRjNDgtYTUzMi01NzUwNjkyMDVhYzQiLCJpZCI6NDA1NTUxLCJpYXQiOjE3NzM5MDY2ODB9.HzmrtJi7ayGSPxJ7Npsi0waFpcs7d7b-vNMdItD7b28";

    const viewer=new Cesium.Viewer('c',{animation:false,timeline:false});

    viewer.camera.setView({
        destination: Cesium.Cartesian3.fromDegrees(78,22,3000000)
    });

    let entities=[];

    function load(){
        fetch('/api/live')
        .then(r=>r.json())
        .then(data=>{

            entities.forEach(e=>viewer.entities.remove(e));
            entities=[];

            data.forEach(d=>{
                if(d.status==="YES"){
                    let e=viewer.entities.add({
                        position: Cesium.Cartesian3.fromDegrees(d.lon,d.lat),
                        point:{pixelSize:12,color:Cesium.Color.RED},
                        label:{text:d.city}
                    });
                    entities.push(e);
                }
            });

        });
    }

    setInterval(load,3000);
    load();
    </script>

    </body>
    </html>
    '''

# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)