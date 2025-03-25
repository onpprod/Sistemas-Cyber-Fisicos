import asyncio
import os
import logging
from .base_code import AssetConnection
from asyncua import Client as Opcua
from gmqtt import Client as MqttClient

MQTT_BROKER = os.getenv("MQTT_BROKER", "131.255.82.115")
MQTT_PORT = os.getenv("MQTT_PORT", "1883")
CLIENT_ID = os.getenv("CLIENT_ID", "esp32_17")

async def main():

    url = "opc.tcp://FA3ST:8081/"

    MQTT_BROKER = os.getenv("MQTT_BROKER", "131.255.82.115")
    MQTT_PORT = os.getenv("MQTT_PORT", "1883")
    CLIENT_ID = os.getenv("CLIENT_ID", "esp32/17")
    MQTT_TOPIC_COMMAND = os.getenv("MQTT_TOPIC_COMMAND", "command")

    # Cliente MQTT
    mqtt = MqttClient(CLIENT_ID)
    await mqtt.connect(MQTT_BROKER, MQTT_PORT)

    while True:

        async with Opcua(url=url) as opcua_client:

            led_control_path = ["AASEnvironment", "Submodel:Control", "LedControl", "Value"]
            led_control_topic = "esp32/N/monitor/cmd"

            led_control_payload_1 = "ON"
            led_control_payload_1_validate = "ON"
            led_control_connection_1 = AssetConnection(
                mqtt,
                led_control_topic,
                led_control_payload_1,
                opcua_client,
                led_control_path,
                led_control_payload_1_validate
                )

            led_control_payload_2 = "OFF"
            led_control_payload_2_validate = "OFF"
            led_control_connection_2 = AssetConnection(
                mqtt,
                led_control_topic,
                led_control_payload_2,
                opcua_client,
                led_control_path,
                led_control_payload_2_validate
            )

            await led_control_connection_1.start()
            await led_control_connection_2.start()

            while True:
                await asyncio.sleep(5)
                await opcua_client.check_connection()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("asyncua").setLevel(logging.WARNING)

    asyncio.run(main())