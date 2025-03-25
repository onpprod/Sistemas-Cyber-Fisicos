import asyncio
import os
import logging
from .base_code import RobotConnection
from asyncua import Client as Opcua
from gmqtt import Client as MqttClient

async def main():

    url = "opc.tcp://FA3ST:8081/"
    MQTT_BROKER = os.getenv("MQTT_BROKER", "131.255.82.115")
    MQTT_PORT = os.getenv("MQTT_PORT", "1883")
    CLIENT_ID = os.getenv("CLIENT_ID", "esp32/17")
    MQTT_TOPIC_COMMAND = os.getenv("MQTT_TOPIC_COMMAND", "command")

    # Cliente MQTT
    mqtt = MqttClient(CLIENT_ID)
    await mqtt.connect(MQTT_BROKER, MQTT_PORT)


    # Modifique os caminhos sem alterar as chaves do dicionário ({"chave": [valor]})
    paths = {
        "operational_state": ["AASEnvironment", "Submodel:PickAndPlace", "Control", "Value"],

        "x_pick_position": ["AASEnvironment", "Submodel:PickAndPlace", "Pick", "X", "Value"],
        "y_pick_position": ["AASEnvironment", "Submodel:PickAndPlace", "Pick", "Y", "Value"],
        "z_pick_position": ["AASEnvironment", "Submodel:PickAndPlace", "Pick", "Z", "Value"],

        "x_place_position": ["AASEnvironment", "Submodel:PickAndPlace", "Place", "X", "Value"],
        "y_place_position": ["AASEnvironment", "Submodel:PickAndPlace", "Place", "Y", "Value"],
        "z_place_position": ["AASEnvironment", "Submodel:PickAndPlace", "Place", "Z", "Value"]
    }

    while True:

        async with Opcua(url=url) as opcua_client:
            robot = RobotConnection(paths, opcua_client, mqtt, MQTT_TOPIC_COMMAND)

            await robot.start()

            while True:
                await asyncio.sleep(5)
                await opcua_client.check_connection()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("asyncua").setLevel(logging.WARNING)

    asyncio.run(main())
