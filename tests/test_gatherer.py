import asyncio

import pytest
import uuid
from time import time

from gmqtt import Client as MQTTClient
from gmqtt.mqtt.constants import MQTTv311
from tests import MQTT_BROKER_HOST, MQTT_BROKER_PORT
from toad_sp_data import gatherer  # , protocol

_sample_senml = {
    "e": [{"v": 42.0, "t": time()}],
    "bn": "w.r0.c0",
    "bu": "W",
}


class TestListener(MQTTClient):
    """Test class that subscribes to an MQTT channel and compares the payloaad
    against the expected payload."""

    def __init__(self, client_id, topic, expected):
        super().__init__(client_id)
        self.expected = expected
        self.topic = topic
        self.on_message = self.on_message_compare

    async def connect_to_broker(self):
        await super().connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, version=MQTTv311)
        self.subscribe(self.topic, qos=0)

    def on_message_compare(self, client, topic, payload, qos, properties):
        # assert payload == self.expected
        assert False  # FIXME: why is this never run?

    async def stop(self):
        await self.disconnect()


@pytest.mark.asyncio
async def test_pub_to_mqtt():
    topic = f"test/{uuid.uuid4()}"
    listener = TestListener("", topic=topic, expected=_sample_senml)
    await listener.connect_to_broker()
    client = gatherer.Gatherer(event_loop=asyncio.get_event_loop())
    await client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT)
    client.publish(topic, _sample_senml, qos=1)
    await client.disconnect()
    await listener.stop()
