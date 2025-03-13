import asyncio
import logging
from asyncua import Client
from gmqtt import Client as MQTTClient
import os

_logger = logging.getLogger(__name__)

# Configurações MQTT
MQTT_BROKER = os.getenv("MQTT_BROKER", "131.255.82.115")
MQTT_PORT = os.getenv("MQTT_PORT", "1883")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "esp32/17/monitor/cmd")
CLIENT_ID = os.getenv("CLIENT_ID", "opcua_mqtt_bridge")

# Cliente MQTT
mqtt_client = MQTTClient(CLIENT_ID)

async def find_value_node(server, path):
    try:
        root_node = server.get_root_node()
        objects_node = await root_node.get_child(["0:Objects"])
        current_node = objects_node

        for level in path:
            children = await current_node.get_children()
            next_node = None

            for child in children:
                display_name = await child.read_display_name()
                if display_name == level:
                    next_node = child
                if level in display_name.Text:
                    next_node = child
                    break

            if next_node is None:
                _logger.error(f"Nó com o nome contendo '{level}' não encontrado.")
                return None
            current_node = next_node

        return current_node

    except Exception as e:
        _logger.error(f"Erro ao buscar o nó com o caminho {path}: {e}")
        return None

async def connect_mqtt():
    """ Conecta ao broker MQTT """
    await mqtt_client.connect(MQTT_BROKER, MQTT_PORT)

class SubHandler:
    """
    Subscription Handler. To receive events from server for a subscription
    data_change and event methods are called directly from receiving thread.
    Do not do expensive, slow or network operation there. Create another
    thread if you need to do such a thing
    """

    def datachange_notification(self, node, val, data):
        message = "ON" if val == "ON" else "OFF"
        print(f"Valor do OPC UA mudou para {val}, enviando '{message}' via MQTT...")
        mqtt_client.publish(MQTT_TOPIC, message, qos=1)

    def event_notification(self, event):
        print("New event", event)

async def main():

    url = "opc.tcp://FA3ST:8081/"

    await connect_mqtt()

    while True:

        async with Client(url=url) as client:

            node_path = ["AASEnvironment", "Submodel:Control", "LedControl", "Value"]
            node = await find_value_node(client, node_path)
            handler = SubHandler()
            sub = await client.create_subscription(100, handler)
            handle = await sub.subscribe_data_change(node)

            print(f"Subscribed to node: {node}, handle: {handle}")

            while True:
                await asyncio.sleep(5)
                await client.check_connection()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
