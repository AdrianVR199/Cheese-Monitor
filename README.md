# 🧀 Monitor de Maduración de Quesos — Guía de configuración

---

## 📁 Estructura del proyecto

```
ChesseMonitor/
├── app.py
└── templates/
    └── dashboard.html
```

---

## 🖥️ OPCIÓN A — Correrlo en local (tu PC)

### 1. Instala dependencias
```bash
py -m pip install flask mysql-connector-python
```

### 2. Abre `app.py` y cambia estas líneas con tus datos de MySQL local:
```python
DB_CONFIG = {
    "host":     "localhost",    # ← déjalo así
    "user":     "root",         # ← tu usuario de MySQL
    "password": "tu_password",  # ← tu contraseña de MySQL
    "database": "iotdb"         # ← déjalo así
}
```

### 3. Crea la base de datos en MySQL
Abre MySQL Workbench o tu cliente favorito y ejecuta:
```sql
CREATE DATABASE iotdb;
USE iotdb;

CREATE TABLE almacenes (
  id        INT PRIMARY KEY,
  nombre    VARCHAR(50),
  ubicacion VARCHAR(100)
);
INSERT INTO almacenes VALUES (1, 'Almacén Principal', 'Planta baja');

CREATE TABLE sensores (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  almacen_id  INT,
  timestamp   DATETIME,
  temperatura FLOAT,
  humedad     FLOAT,
  FOREIGN KEY (almacen_id) REFERENCES almacenes(id)
);
```

### 4. Corre la app
```bash
py app.py
```

### 5. Abre el dashboard en tu navegador
```
http://localhost:5000
```

### 6. Configura el ESP32
En el código del ESP32 cambia la URL del servidor a la IP de tu PC:
```cpp
const char* serverUrl = "http://192.168.X.X:5000/datos";
// reemplaza 192.168.X.X con la IP local de tu PC
// para verla corre en PowerShell: ipconfig
```
> ⚠️ El ESP32 y tu PC deben estar conectados a la **misma red WiFi**.

---

## ☁️ OPCIÓN B — Correrlo en AWS (EC2 Ubuntu)

### 1. Conéctate al servidor por SSH
```bash
ssh -i tu-key.pem ubuntu@<IP_PUBLICA_EC2>
```

### 2. Instala dependencias en el servidor
```bash
sudo apt update && sudo apt install python3-pip -y
pip install flask mysql-connector-python
```

### 3. Sube los archivos del proyecto al servidor
Desde tu PC (en otra terminal):
```bash
scp -i tu-key.pem -r ./ChesseMonitor ubuntu@<IP_PUBLICA_EC2>:/home/ubuntu/
```

### 4. Abre `app.py` y cambia estas líneas con los datos de tu RDS:
```python
DB_CONFIG = {
    "host":     "tu-endpoint.rds.amazonaws.com",  # ← endpoint de RDS (lo encuentras en la consola AWS → RDS)
    "user":     "admin",                           # ← usuario que pusiste al crear RDS
    "password": "tu_password",                     # ← contraseña que pusiste al crear RDS
    "database": "iotdb"                            # ← déjalo así
}
```

### 5. Crea la base de datos en RDS
Conéctate a MySQL desde el servidor EC2:
```bash
mysql -h <endpoint-rds> -u admin -p
```
Luego ejecuta:
```sql
CREATE DATABASE iotdb;
USE iotdb;

CREATE TABLE almacenes (
  id        INT PRIMARY KEY,
  nombre    VARCHAR(50),
  ubicacion VARCHAR(100)
);
INSERT INTO almacenes VALUES (1, 'Almacén Principal', 'Planta baja');

CREATE TABLE sensores (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  almacen_id  INT,
  timestamp   DATETIME,
  temperatura FLOAT,
  humedad     FLOAT,
  FOREIGN KEY (almacen_id) REFERENCES almacenes(id)
);
```

### 6. Corre la app en el servidor
```bash
cd /home/ubuntu/ChesseMonitor
py app.py
# Si py no funciona usa:
python3 app.py
```

Para que no se detenga al cerrar la terminal:
```bash
nohup python3 app.py &
```

### 7. Abre el dashboard en tu navegador
```
http://<IP_PUBLICA_EC2>:5000
```

### 8. Configura el ESP32
En el código del ESP32 cambia la URL del servidor a la IP pública de EC2:
```cpp
const char* serverUrl = "http://<IP_PUBLICA_EC2>:5000/datos";
```
> ⚠️ Asegúrate de que el **Security Group de EC2** tenga abierto el puerto **5000** en Inbound Rules.

---

## 📡 Formato del dato que envía el ESP32

El ESP32 hace un POST con este JSON:
```json
{
  "almacen_id": 1,
  "temperatura": 12.5,
  "humedad": 84.3
}
```

---

## ✅ Resumen rápido de qué cambiar

| | Local | AWS |
|---|---|---|
| `host` en DB_CONFIG | `localhost` | endpoint de RDS |
| `user` en DB_CONFIG | tu usuario MySQL local | `admin` |
| URL en el ESP32 | IP local de tu PC | IP pública de EC2 |
| Puerto a abrir | ninguno extra | puerto 5000 en Security Group |
