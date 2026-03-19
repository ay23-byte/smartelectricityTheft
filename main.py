

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