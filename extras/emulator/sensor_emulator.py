import asyncio
import json
import random
from gmqtt import Client as MQTTClient

import logging
import os
logging.basicConfig(level=logging.INFO)

broker = os.environ.get("BROKER")


class Handler:
    def __init__(self):
        self.connected = False

    def on_connect(self, client, flags, rc, properties):
        print("Connected")
        self.connected = True

    def on_disconnect(self, client, packet, exc=None):
        print("Disconnected")
        self.connected = False


async def main(BROKER, TOPIC):

    handler = Handler()
    client = MQTTClient("sensor-emulator")
    client.on_connect = handler.on_connect
    client.on_disconnect = handler.on_disconnect

    await client.connect(BROKER)

    try:
        while True:
            if handler.connected:
                temperature = round(random.uniform(20.0, 40.0), 1)  # Simulando uma temperatura entre 20 e 40°C
                luminosity = round(random.uniform(0.0, 100.0), 1)
                axis_x = random.uniform(0.0, 1)
                axis_y = random.uniform(0.0, 1)
                axis_z = random.uniform(0.0, 1)
                payload = json.dumps({"Temperatura":temperature,"Umidade":45,"Luminosidade":luminosity,"Eixo_X":axis_x,"Eixo_Y":axis_y,"Eixo_Z":axis_z})
                client.publish(TOPIC, payload)
                print(f"Publicado: {payload} no tópico {TOPIC}")

            await asyncio.sleep(2)

    except asyncio.CancelledError:
        print("Encerrando a publicação de dados...")
        await client.disconnect()


if __name__ == "__main__":

    topic = "emulator/sensor"

    try:
        asyncio.run(main(broker, topic))
    except KeyboardInterrupt:
        print("Interrompido pelo usuário.")
