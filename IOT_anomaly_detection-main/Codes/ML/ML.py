import numpy as np
import time
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from influxdb import InfluxDBClient
import json
from paho.mqtt import client as mqtt_client

# ---- MQTT Settings ----
mqtt_broker = 'localhost'  # si ce script tourne sur ta machine hôte
mqtt_port = 1883
mqtt_topic = "IOT/Anomalies"
mqtt_client_id = f'anomaly-detector'
mqtt_user = ''
mqtt_pass = ''

# ---- InfluxDB Settings ----
# IMPORTANT: si le script tourne **sur ta machine hôte**, utilise 'localhost'
# Si le script tourne DANS un conteneur Docker dans le même réseau, utilise 'influxdb'
influx_client = InfluxDBClient(
    host='localhost',      # ⬅️ 'localhost' si le script est lancé depuis l'extérieur du conteneur
    port=8086,
    username='admin',
    password='admin123',
    database='ble_data'
)

# ---- MQTT Connection ----
def connect_mqtt():
    client = mqtt_client.Client(mqtt_client_id)
    if mqtt_user:
        client.username_pw_set(mqtt_user, mqtt_pass)

    def on_connect(client, userdata, flags, rc):
        print("✅ MQTT connecté" if rc == 0 else f"❌ Connexion échouée : {rc}")
    client.on_connect = on_connect
    client.connect(mqtt_broker, mqtt_port)
    return client

mqtt = connect_mqtt()
mqtt.loop_start()

# ---- Read from InfluxDB ----
def read_temperature_data():
    query = 'SELECT "value" FROM "temperature" ORDER BY time DESC LIMIT 200'
    result = influx_client.query(query)
    points = list(result.get_points())
    values = [p["value"] for p in points if "value" in p]
    return np.array(values)

# ---- Anomaly Detection ----
def perform_anomaly_detection(data):
    data = data.reshape(-1, 1)
    model = IsolationForest(contamination=0.05)
    model.fit(data)
    labels = model.predict(data)
    anomalies = data[labels == -1]
    anomaly_indices = np.where(labels == -1)[0]

    # Plot
    plt.clf()
    plt.scatter(range(len(data)), data, c='blue', label='Normal')
    plt.scatter(anomaly_indices, anomalies, c='red', label='Anomalie')
    plt.xlabel("Index")
    plt.ylabel("Température")
    plt.title("Détection d'anomalies (Isolation Forest)")
    plt.legend()
    plt.pause(0.01)

    # MQTT : publication des anomalies
    for idx in anomaly_indices:
        msg = json.dumps({
            "type": "anomaly",
            "value": float(data[idx]),
            "index": int(idx)
        })
        mqtt.publish(mqtt_topic, msg)

# ---- Main loop ----
plt.ion()
fig = plt.figure(figsize=(10, 6))

while True:
    try:
        data = read_temperature_data()
        if len(data) > 10:
            perform_anomaly_detection(data)
        else:
            print("⏳ Pas assez de données pour analyse.")
        time.sleep(10)
    except Exception as e:
        print(f"⚠️ Erreur : {e}")
        time.sleep(10)
