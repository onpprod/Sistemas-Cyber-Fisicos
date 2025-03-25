import json
import logging
import asyncio
import os
from gmqtt import Client as MqttClient
from asyncua import Node

_logger = logging.getLogger(__name__)

# Configurações MQTT


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

class BaseHandler:
    def __init__(self, payload, validator, mqtt_client, mqtt_topic):
        self.payload = payload
        self.validator = validator
        self.mqtt_client = mqtt_client
        self.mqtt_topic = mqtt_topic

    def datachange_notification(self, node, val, data):
        if isinstance(val, str) and isinstance(self.validator, str):
            if val.upper() == self.validator.upper():
                self.mqtt_client.publish(self.mqtt_topic, self.payload, qos=0)
                _logger.info(f"MQTT PUB: {self.payload}")
        elif val == self.validator:
            self.mqtt_client.publish(self.mqtt_topic, self.payload, qos=0)
            _logger.info(f"MQTT PUB: {self.payload}")

class AssetConnection:
    """
    Uma classe usada para criar conexões entre AAS e Asset

    """

    _node = None
    _handler = None
    _handle = None
    _subscription = None

    def __init__(self, mqtt_client: MqttClient, mqtt_topic:str, mqtt_payload:str, opcua_client, opcua_node, opcua_expected_value):
        self.mqtt_client = mqtt_client
        self.mqtt_topic = mqtt_topic
        self.mqtt_payload = mqtt_payload
        self.opcua_client = opcua_client
        self.opcua_node = opcua_node
        self.opcua_expected_value = opcua_expected_value

    async def start(self):
        self._node = await find_value_node(self.opcua_client, self.opcua_node)
        self._handler = BaseHandler(self.mqtt_payload, self.opcua_expected_value, self.mqtt_client, self.mqtt_topic)
        self._subscription = await self.opcua_client.create_subscription(500, self._handler)
        self._handle = await self._subscription.subscribe_data_change(self._node)
        _logger.info(f"Subscribed to node: {self._node}, handle: {self._handle}")

class RobotHandler:
    def __init__(self, mqtt_client, mqtt_topic):
        self.mqtt_client = mqtt_client
        self.mqtt_topic = mqtt_topic

        self.xin: Node | None = None
        self.yin: Node | None = None
        self.zin: Node | None = None
        self.xout: Node | None = None
        self.yout: Node | None = None
        self.zout: Node | None = None

    async def datachange_notification(self, node, val, data):
        _logger.info("Python: New data change event %s %s", node, val)

        if not (isinstance(val, str) and val.lower() in {"calibrate", "start", "idle", "move", "home"}):
            _logger.info("[pick_and_place] data_change: Unknown value passed to node: %s", val)
            return

        message: dict = {}

        if val.lower() == "start":
            try:
                x_pick_value, y_pick_value, z_pick_value, = await asyncio.gather(
                    self.xin.read_value(),
                    self.yin.read_value(),
                    self.zin.read_value(),
                )

                x_place_value, y_place_value, z_place_value = await asyncio.gather(
                    self.xout.read_value(),
                    self.yout.read_value(),
                    self.zout.read_value()
                )

                message = {
                    "data": {
                        "cmd": "start",
                        "in_coord": {
                            "x": str(x_pick_value),
                            "y": str(y_pick_value),
                            "z": str(z_pick_value),
                        },
                        "out_coord": {
                            "x": str(x_place_value),
                            "y": str(y_place_value),
                            "z": str(z_place_value),
                        }
                    }
                }

            except Exception as e:
                _logger.error(f"Erro ao obter os valores do OPC UA: {e}")
                return

        elif val.lower() == "calibrate":
            message = {
                "data": {
                    "cmd": "calibrate"
                }
            }

        elif val.lower() == "move":
            x_pick_value, y_pick_value, z_pick_value, = await asyncio.gather(
                self.xin.read_value(),
                self.yin.read_value(),
                self.zin.read_value(),
            )

            message = {
                "data": {
                    "cmd": "move",
                    "in_coord": {
                        "x": str(x_pick_value),
                        "y": str(y_pick_value),
                        "z": str(z_pick_value),
                    },

                }
            }

        elif val.lower() == "home":
            message = {
                "data": {
                    "cmd": "home"
                }
            }

        try:
            if not message:
                return

            payload = json.dumps(message)
            self.mqtt_client.publish(self.mqtt_topic, payload)


        except Exception as e:
            _logger.error(f"Erro ao enviar mensagem em tópico: {e}")

class RobotConnection:
    def __init__(self, paths: dict, opcua_client, mqtt_client: MqttClient, mqtt_topic:str):
        self.paths = paths
        self.opcua_client = opcua_client
        self.mqtt_client = mqtt_client
        self.mqtt_topic = mqtt_topic
        self.subscription_handler = RobotHandler(self.mqtt_client, self.mqtt_topic)
        self.subscription_handler_interface = None

    async def start(self):
        self.subscription_handler.xin = await find_value_node(self.opcua_client, self.paths["x_pick_position"])
        self.subscription_handler.yin = await find_value_node(self.opcua_client, self.paths["y_pick_position"])
        self.subscription_handler.zin = await find_value_node(self.opcua_client, self.paths["z_pick_position"])

        self.subscription_handler.xout = await find_value_node(self.opcua_client, self.paths["x_place_position"])
        self.subscription_handler.yout = await find_value_node(self.opcua_client, self.paths["y_place_position"])
        self.subscription_handler.zout = await find_value_node(self.opcua_client, self.paths["z_place_position"])

        await asyncio.sleep(10)
        await self.subscribe_to_data_change(self.paths["operational_state"])

    async def subscribe_to_data_change(self, path):
        node = await find_value_node(self.opcua_client, path)
        subscription = await self.opcua_client.create_subscription(500, self.subscription_handler)
        handle = await subscription.subscribe_data_change(node)

        self.subscription_handler_interface = subscription

        print(f"Subscribed to node: {node}, handle: {handle}")

        while True:
            await asyncio.sleep(1)
