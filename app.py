from flask import Flask, render_template, jsonify, request
import mysql.connector
from datetime import datetime, timedelta
import random

app = Flask(__name__)

# ── Configuración de la base de datos ──────────────────────────
DB_CONFIG = {
    "host":     "localhost",       # ← endpoint RDS en AWS
    "user":     "root",            # ← tu usuario MySQL
    "password": "tu_password",     # ← tu contraseña
    "database": "iotdb"
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

# ── Script SQL (ejecutar una sola vez en MySQL) ────────────────
# CREATE TABLE almacenes (
#   id        INT PRIMARY KEY,
#   nombre    VARCHAR(50),
#   ubicacion VARCHAR(100)
# );
# INSERT INTO almacenes VALUES (1, 'Almacén Principal', 'Planta baja');
#
# CREATE TABLE sensores (
#   id          INT AUTO_INCREMENT PRIMARY KEY,
#   almacen_id  INT,
#   timestamp   DATETIME,
#   temperatura FLOAT,
#   humedad     FLOAT,
#   FOREIGN KEY (almacen_id) REFERENCES almacenes(id)
# );

# ── Datos simulados (cuando no hay BD lista) ───────────────────
def datos_simulados():
    ahora = datetime.now()
    registros = []
    for i in range(20):
        ts = ahora - timedelta(minutes=i * 3)
        registros.append({
            "almacen_nombre": "Almacén Principal",
            "ubicacion":      "Planta baja",
            "timestamp":      ts.strftime("%Y-%m-%d %H:%M:%S"),
            "temperatura":    round(12 + random.uniform(-1.5, 1.5), 1),
            "humedad":        round(85 + random.uniform(-5, 5), 1),
        })
    return registros

def resumen_simulado():
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {
        "nombre":    "Almacén Principal",
        "ubicacion": "Planta baja",
        "ultimo": {
            "temperatura": round(12 + random.uniform(-1.5, 1.5), 1),
            "humedad":     round(85 + random.uniform(-5, 5), 1),
            "timestamp":   ahora,
        },
        "avg_temp": 12.1,
        "avg_hum":  84.8,
    }

# ── Rutas ──────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/datos", methods=["POST"])
def recibir_datos():
    """Recibe datos del ESP32 y los guarda en MySQL."""
    try:
        data       = request.json
        temp       = data["temperatura"]
        hum        = data["humedad"]
        almacen_id = data.get("almacen_id", 1)
        ts         = datetime.now()

        db  = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO sensores (almacen_id, timestamp, temperatura, humedad) VALUES (%s, %s, %s, %s)",
            (almacen_id, ts, temp, hum)
        )
        db.commit()
        db.close()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 500


@app.route("/api/datos")
def api_datos():
    """Últimos 40 registros con JOIN a almacenes."""
    try:
        db  = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute("""
            SELECT
                s.id,
                a.nombre    AS almacen_nombre,
                a.ubicacion,
                s.timestamp,
                s.temperatura,
                s.humedad
            FROM sensores s
            JOIN almacenes a ON s.almacen_id = a.id
            WHERE a.id = 1
            ORDER BY s.timestamp DESC
            LIMIT 40
        """)
        rows = cur.fetchall()
        for r in rows:
            if hasattr(r["timestamp"], "strftime"):
                r["timestamp"] = r["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        db.close()
        return jsonify(rows)
    except Exception:
        return jsonify(datos_simulados())


@app.route("/api/resumen")
def api_resumen():
    """Último valor y promedio de 1h del almacén."""
    try:
        db  = get_db()
        cur = db.cursor(dictionary=True)

        cur.execute("SELECT id, nombre, ubicacion FROM almacenes WHERE id = 1")
        alm = cur.fetchone()

        cur.execute("""
            SELECT temperatura, humedad, timestamp
            FROM sensores
            WHERE almacen_id = 1
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        ultimo = cur.fetchone()

        cur.execute("""
            SELECT AVG(temperatura) AS avg_temp, AVG(humedad) AS avg_hum
            FROM sensores
            WHERE almacen_id = 1
            AND timestamp >= NOW() - INTERVAL 1 HOUR
        """)
        promedios = cur.fetchone()

        if ultimo and hasattr(ultimo["timestamp"], "strftime"):
            ultimo["timestamp"] = ultimo["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

        db.close()
        return jsonify({
            "nombre":    alm["nombre"],
            "ubicacion": alm["ubicacion"],
            "ultimo":    ultimo,
            "avg_temp":  round(promedios["avg_temp"] or 0, 1),
            "avg_hum":   round(promedios["avg_hum"]  or 0, 1),
        })
    except Exception:
        return jsonify(resumen_simulado())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)