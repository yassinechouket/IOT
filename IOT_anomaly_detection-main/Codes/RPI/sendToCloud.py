import random
import json
from paho.mqtt import client as mqtt_client
from bleak import BleakClient
import asyncio

broker = 'broker.emqx.io'
port = 1883
topic = "IOT/Data"
password_encryption = 'IA1.1'


def KSA(key):
    key_length = len(key)
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % key_length]) % 256
        S[i], S[j] = S[j], S[i]
    return S


def PRGA(S):
    i = 0
    j = 0
    while True:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        S[i], S[j] = S[j], S[i]
        K = S[(S[i] + S[j]) % 256]
        yield K


def RC4(key, plaintext):
    S = KSA(key)
    keystream = PRGA(S)
    cipher = []
    for byte in plaintext:
        cipher_byte = byte ^ next(keystream)
        cipher.append(cipher_byte)
    return bytes(cipher)


class MyDelegate:
    def __init__(self):
        self.client = None  # Initialize client here

    async def handleNotification(self, characteristic, data):
        # Handle the notification (now with 3 arguments)
        data_string = data.decode("utf-8")
        if data_string[6] == "n":
            print("Not a number")
        else:
            print(float(data_string[6:-2]))
            self.publish_mqtt(data_string[6:-2])

    def publish_mqtt(self, data):
        global client
        msg = json.dumps({"temp": float(data)})
        print(msg)
        encrypted_data = RC4(password_encryption.encode(), msg.encode())
        pub_msg = json.dumps({"data": list(encrypted_data)})

        result = client.publish(topic, pub_msg, qos=0, retain=False)
        status = result.rc
        if status == 0:
            print(f"Send `{pub_msg}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print(f"Failed to connect, return code {rc}")

    client = mqtt_client.Client(client_id=f'publish-{random.randint(0, 1000)}', protocol=mqtt_client.MQTTv311)


    client.on_connect = on_connect
    client.connect(broker, port, keepalive=3)
    return client


client = connect_mqtt()
client.loop_start()


async def run():
    device_address = "08:B6:1F:B9:67:CA"  # Update with your device address
    delegate = MyDelegate()

    async with BleakClient(device_address) as client:
        # Subscribe to notifications from the characteristic (UUID to match the device)
        await client.start_notify("6E400003-B5A3-F393-E0A9-E50E24DCCA9E", delegate.handleNotification)

        while True:
            await asyncio.sleep(1)  # Keep the loop running


asyncio.run(run())
