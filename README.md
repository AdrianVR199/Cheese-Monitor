# Caso de estudio - monitor de maduración de quesos

**Estudiantes:**
- Miguel Angel Franco Restrepo (22506163)
- Saulo Quiñones Góngora (22506635)
- Adrian Felipe Vargas Rojas (22505561)

**Curso:** Inteligencia Artificial aplicada a Internet de las Cosas

**Institución:** Universidad Autónoma de Occidente

**Periodo:** 2026-1S

---

## 1. Resumen del proyecto

Este proyecto consiste en el despliegue de un sistema de monitoreo de temperatura y humedad para cámaras de maduración de quesos, utilizando un ESP32 con sensor DHT22 como dispositivo IoT.

La solución fue implementada en dos modalidades complementarias:

- **Implementación local** — usando máquinas virtuales con LXD, HAProxy y Keepalived para alta disponibilidad con failover automático.
- **Implementación en AWS** — usando EC2 y RDS con separación de subredes pública y privada.

En ambos casos la aplicación web Flask recibe los datos del ESP32, los almacena en una base de datos MySQL y los presenta en un dashboard web con opción de exportación a CSV.

---

## 2. Objetivo de la práctica

- Configurar un objeto inteligente (ESP32 + DHT22) para que transmita datos a un servidor.
- Implementar un servidor web que reciba, procese y almacene los datos del sensor.
- Aplicar buenas prácticas de infraestructura: separación de capas, alta disponibilidad, seguridad en red y gestión de credenciales.

---


## 3. Caso de uso

El sistema simula el monitoreo ambiental de una cámara de maduración de quesos, donde el control de temperatura y humedad es crítico para garantizar la calidad del producto. El sensor DHT22 mide las condiciones del ambiente cada 10 segundos y transmite los datos al servidor, que los almacena y los presenta en un dashboard en tiempo real.

---

## 4. Descripción de la aplicación

La aplicación desarrollada en Flask:

- Recibe datos de temperatura y humedad del ESP32 mediante HTTP POST en formato JSON.
- Almacena los registros en una base de datos MySQL (tabla `sensores`) con referencia al almacén correspondiente (tabla `almacenes`).
- Presenta un dashboard web con la última lectura, promedios de la última hora e historial de los últimos 40 registros.
- Permite exportar todos los registros como archivo CSV descargable desde el navegador.
- Incluye datos simulados como fallback en caso de que la base de datos no esté disponible.

### Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Dashboard web |
| POST | `/datos` | Recibe datos del ESP32 |
| GET | `/api/datos` | Últimos 40 registros en JSON |
| GET | `/api/resumen` | Última lectura y promedio de 1h |
| GET | `/api/exportar-csv` | Descarga CSV con todos los registros |

---

## 5. Implementación local (VMs + LXD + HAProxy)

Se diseñó e implementó una arquitectura de alta disponibilidad en un entorno local virtualizado, utilizando VirtualBox con Vagrant para la gestión de cuatro máquinas virtuales. La solución garantiza disponibilidad continua del servicio mediante balanceo de carga y failover automático.

### Arquitectura local

```
Cliente
   |
   | → IP Virtual (Keepalived/VRRP)
   |
   ├── LB1 (HAProxy master)  ─┐
   └── LB2 (HAProxy backup)  ─┤
                               |
               ┌───────────────┴───────────────┐
               ↓                               ↓
        VM A (LXD)                      VM B (LXD)
        ├── web-server (Flask)          └── web-server (Flask)
        └── bd-container (MySQL)            (conecta a bd-container en VM A)
```

### Componentes

| Componente | Detalle |
|---|---|
| LB1 | HAProxy master + Keepalived (VRRP) |
| LB2 | HAProxy backup + Keepalived (failover automático) |
| IP Virtual | Dirección IP compartida entre LB1 y LB2 |
| VM-A | LXD con contenedor `web-server` (Flask) y `bd-container` (MySQL) |
| VM-B | LXD con contenedor `web-server` (Flask) conectado a BD en VM A |

### Infraestructura
La arquitectura se compone de cuatro máquinas virtuales con los siguientes roles:

- **2 Load Balancers (haServer1 y haServer2)**: Configurados con HAProxy y Keepalived mediante el protocolo VRRP, que gestiona una IP virtual flotante (192.168.1.100). En caso de fallo del balanceador primario, el secundario toma automáticamente la IP virtual, garantizando continuidad del servicio sin intervención manual.
- **2 Servidores de aplicación (VM-A y VM-B)**: Cada uno contiene un contenedor LXD con la aplicación web desarrollada en Flask y servida con Gunicorn. Únicamente server1 aloja un contenedor adicional con la base de datos MySQL.

### Aplicación web
La aplicación permite la visualización en tiempo real de datos de temperatura y humedad provenientes de un sensor DHT22 conectado a una ESP32, en el contexto de monitoreo de una cámara de maduración de quesos. Incluye:

- Visualización de valores actuales y promedios por hora
- Gráficas históricas de temperatura y humedad
- Exportación de datos en formato CSV
- Identificador de servidor para verificar el balanceo de carga

### Base de datos
Se utilizó MySQL desplegado en un contenedor LXD en server1. Se configuró el parámetro bind-address = 0.0.0.0 para permitir conexiones externas, y se definieron proxy devices en LXD para redirigir el tráfico de los puertos 80 (aplicación web) y 3306 (MySQL) hacia los contenedores correspondientes.

### Integración con ESP32
El dispositivo ESP32 con sensor DHT22 envía datos de temperatura y humedad cada 10 segundos mediante HTTP POST a la IP virtual del balanceador, dentro de la misma red local. Los datos son almacenados en MySQL y visualizados en tiempo real en el dashboard.

---

## 6. Implementación en AWS (EC2 + RDS)

La solución fue desplegada en AWS siguiendo un modelo de separación de capas: el servidor web en una subred pública accesible desde internet y la base de datos en una subred privada sin acceso externo.

### 6.1 Arquitectura AWS

```
ESP32 (DHT22)
     |
     | WiFi → HTTP POST (JSON)
     ↓
Internet Gateway (iot_gateway)
     |
     ↓
VPC vpc_IoT (192.168.0.0/16)
     |
     ├── Subred pública IoT_server (192.168.1.0/24)
     │        EC2 Ubuntu t2.micro
     │        IP elástica: 32.196.10.168
     │        Flask en puerto 5000
     │        Gestionado por systemd
     │              |
     │              | Puerto 3306 (solo desde sg-servidor-iot)
     │              ↓
     └── Subred privada IoT_db (192.168.2.0/24)
              RDS MySQL db.t3.micro
              Sin IP pública
              Solo accesible desde la EC2
```

### 5.1 Infraestructura AWS

| Componente | Detalle |
|---|---|
| VPC | `vpc_IoT` — CIDR `192.168.0.0/16` |
| Subred pública | `IoT_server` — `192.168.1.0/24` — AZ `us-east-1a` |
| Subred privada | `IoT_db` — `192.168.2.0/24` — AZ `us-east-1a` |
| Internet Gateway | `iot_gateway` — adjunto a `vpc_IoT` |
| Tabla de rutas | `0.0.0.0/0 → iot_gateway` asociada solo a `IoT_server` |
| EC2 | Ubuntu Server 22.04 LTS — `t2.micro` |
| IP elástica | `32.196.10.168` — fija, no cambia entre sesiones |
| RDS | MySQL 8.4 — `db.t3.micro` — 20 GiB gp2 |
| Subnet group RDS | `subnet-group-iot` — subredes `IoT_db` y `subnet-extra` |

### 6.2 Configuración de Security Groups

Se implementó un modelo de mínimo privilegio:

#### sg-servidor-iot (EC2)

| Tipo | Puerto | Origen | Propósito |
|---|---|---|---|
| SSH | 22 | IP del administrador | Acceso administrativo |
| TCP personalizado | 5000 | 0.0.0.0/0 | Recepción de datos del ESP32 y acceso al dashboard |

#### sg-base-datos (RDS)

| Tipo | Puerto | Origen | Propósito |
|---|---|---|---|
| MySQL/Aurora | 3306 | sg-servidor-iot | Solo el servidor puede conectarse a la BD |

Este diseño garantiza que la base de datos nunca sea accesible desde internet, solo desde la instancia EC2. Como nota adicional, Flask usa el puerto 5000 por defecto, si bien los puertos estándar web son el 80 y el 443, usarlos directamente con Flask requiere configuración adicional que va más allá del alcance de esta práctica. Para un despliegue en producción se añadiría una capa intermedia que gestione el tráfico en el puerto 80, pero para esta implementación académica el puerto 5000 es suficiente y funcional.

### 6.3 Flujo de tráfico

1. El ESP32 envía un HTTP POST cada 10 segundos a `http://32.196.10.168:5000/datos`.
2. El Internet Gateway recibe el tráfico y lo enruta hacia la EC2 en la subred pública.
3. Flask procesa el JSON y lo escribe en la tabla `sensores` de MySQL.
4. La EC2 se comunica con RDS a través de la red privada de la VPC (puerto 3306).
5. El usuario accede al dashboard desde el navegador en `http://32.196.10.168:5000`.

---

## 7. Hardware y firmware

### Componentes

| Componente | Detalle |
|---|---|
| Microcontrolador | ESP32 |
| Sensor | DHT22 (temperatura y humedad) |
| Conexión | WiFi 2.4 GHz |
| Pin de datos | GPIO 15 |

### Estructura del firmware

```
ESP32_CODE/
├── ESP32_CODE.ino    ← Sketch principal
└── credentials.h    ← Credenciales WiFi y URL del servidor
```

### credentials.h

Las credenciales se separan del código principal por seguridad:

```cpp
#ifndef CREDENTIALS_H
#define CREDENTIALS_H

#define WIFI_SSID     "RED_WIFI"
#define WIFI_PASSWORD "PASSWORD_WIFI"
#define SERVER_URL    "http://URL:5000/datos"

#endif
```

### Formato del JSON enviado por el ESP32

```json
{
  "almacen_id": 1,
  "temperatura": 12.5,
  "humedad": 84.3
}
```

---

## 8. Estructura del proyecto

```
Cheese-Monitor/
├── app.py               ← Aplicación principal Flask
└── templates/
    └── dashboard.html   ← Dashboard web
```

---

## 9. Despliegue en AWS

### 9.1 Requisitos previos

- Instancia EC2 corriendo con Ubuntu 22.04 LTS
- RDS MySQL disponible en subred privada
- Security Groups configurados como se describe en la sección 5.2

### 9.2 Configuración del entorno en la EC2

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv mysql-client -y
python3 -m venv ~/servidor-iot/venv
source ~/servidor-iot/venv/bin/activate
pip install flask mysql-connector-python
```

### 9.3 Clonar el repositorio

```bash
cd ~
git clone https://github.com/tu-usuario/Cheese-Monitor.git
cd Cheese-Monitor
```

### 9.4 Gestión de credenciales

Las credenciales **nunca** deben estar en el código. Se gestionan mediante un archivo de variables de entorno:

```bash
nano ~/.env-iot
```

Contenido (sin comillas ni `export`):
```
DB_HOST=db-instance-iot.cv664u28me10.us-east-1.rds.amazonaws.com
DB_USER=admin
DB_PASS=tu_password
DB_NAME=iot_db
```

El `app.py` las lee así:
```python
import os

DB_CONFIG = {
    "host":     os.environ.get("DB_HOST"),
    "user":     os.environ.get("DB_USER"),
    "password": os.environ.get("DB_PASS"),
    "database": os.environ.get("DB_NAME")
}
```

### 9.5 Crear la base de datos y tablas en RDS

Desde la EC2:
```bash
mysql -h db-instance-iot.cv664u28me10.us-east-1.rds.amazonaws.com -u admin -p
```

```sql
CREATE DATABASE iot_db;
USE iot_db;

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

### 9.6 Configuración del servicio systemd

Para que el servidor arranque automáticamente con la EC2 sin intervención manual:

```bash
sudo nano /etc/systemd/system/iot-server.service
```

```ini
[Unit]
Description=Servidor IoT Flask
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/Cheese-Monitor
EnvironmentFile=/home/ubuntu/.env-iot
ExecStart=/home/ubuntu/servidor-iot/venv/bin/python app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable iot-server
sudo systemctl start iot-server
```

Verificar estado:
```bash
sudo systemctl status iot-server
```

---

## 10. Configuración local (opcional)

Para correr la aplicación localmente sin AWS:

```bash
pip install flask mysql-connector-python
```

Configura el `DB_CONFIG` en `app.py` con datos locales:
```python
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "tu_password",
    "database": "iot_db"
}
```

En `credentials.h` del ESP32 cambia la URL a la IP local de tu PC:
```cpp
#define SERVER_URL "http://192.168.X.X:5000/datos"
```

> El ESP32 y el PC deben estar en la misma red WiFi.
---

## 11. Comandos útiles

```bash
# Ver estado del servidor
sudo systemctl status iot-server

# Reiniciar el servidor
sudo systemctl restart iot-server

# Ver logs en tiempo real
sudo journalctl -u iot-server -f

# Conectarse a la base de datos desde la EC2
mysql -h db-instance-iot.cv664u28me10.us-east-1.rds.amazonaws.com -u admin -p

# Ver últimas lecturas
# USE iot_db;
# SELECT * FROM sensores ORDER BY id DESC LIMIT 10;
```

---

## 12. Pruebas y validación

### 12.1 Verificar conexión entre la ESP32 y el servidor:
El monitor Serial del ESP32 debe mostrar:
```
WiFi conectado
IP local: 192.x.x.x
Temp: 12.5 C  Hum: 84.3%
HTTP 200: {"status": "ok"}
```

### 12.2 Verificar datos en la base de datos
```sql
USE iot_db;
SELECT * FROM sensores ORDER BY id DESC LIMIT 10;
```

### 12.3 Verificar dashboard
Acceder desde el navegador a `http://32.196.10.168:5000` y confirmar que las lecturas se actualizan.

### 12.4 Verificar exportación CSV
Hacer clic en el botón de exportación del dashboard y confirmar que el archivo descargado contiene los registros correctos.

### 12.5 Verificar aislamiento de la BD
Intentar conectarse a RDS directamente desde un PC externo debe fallar, confirmando que la base de datos está correctamente aislada en la subred privada.

---

## 13. Resultados obtenidos

- Despliegue exitoso del servidor Flask en EC2 con IP elástica fija
- Base de datos MySQL en subred privada sin acceso público
- ESP32 transmitiendo datos cada 10 segundos de forma estable
- Dashboard web accesible públicamente con actualización en tiempo real
- Exportación de datos a CSV funcional
- Servidor configurado con systemd para auto-arranque

---

## 14. Lecciones aprendidas

- El subnet group de RDS requiere mínimo 2 zonas de disponibilidad aunque solo se use una.
- Las variables de entorno en systemd requieren un formato diferente al de `.bashrc` (sin `export`).
- Las IPs públicas de EC2 en AWS Academy cambian entre sesiones; una IP elástica resuelve este problema.
- El Security Group de la base de datos debe referenciar el SG del servidor, no una IP, para mayor robustez.

---

## 15. Uso académico

Este proyecto fue desarrollado con fines educativos en el contexto de prácticas de Inteligencia Artificial aplicada a Internet de las Cosas.
