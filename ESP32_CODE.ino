#include "credentials.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>

#define DHTPIN  // Ajustar según corresponda
#define DHTTYPE DHT22    

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(115200);
  dht.begin();

  // Conexión WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Conectando al WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi conectado");
  Serial.print("IP local: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  float temp = dht.readTemperature();
  float hum  = dht.readHumidity();

  // Verificar lectura del sensor
  if (isnan(temp) || isnan(hum)) {
    Serial.println("Error leyendo sensor, reintentando...");
    delay(5000);
    return;
  }

  Serial.printf("Temp: %.1f C  Hum: %.1f%%\n", temp, hum);

  // Enviar datos si hay WiFi
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(SERVER_URL);
    http.addHeader("Content-Type", "application/json");

    String payload = "{\"temperatura\":" + String(temp, 1)
                   + ",\"humedad\":"     + String(hum, 1) + "}";

    int httpCode = http.POST(payload);

    if (httpCode > 0) {
      Serial.println("HTTP " + String(httpCode) + ": " + http.getString());
    } else {
      Serial.println("Error: " + http.errorToString(httpCode));
    }
    http.end();
  } else {
    Serial.println("WiFi desconectado, reintentando...");
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  }

  delay(10000); // Envía cada 10 segundos
}
