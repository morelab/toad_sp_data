import asyncio

from gmqtt import Client as MQTTClient
from gmqtt.mqtt.constants import MQTTv311
from time import time
from typing import List

from toad_sp_data import logger, loop, protocol, smartplug


class Gatherer(MQTTClient):
    """A Gatherer requests power measurements from SmartPlugs, maps the
    measurement to the corresponding SmartPlug ID and send them to the MQTT
    broker."""

    def __init__(
        self, client_id="Gatherer", *args, smartplug_ids={},
    ):  # pragma: no cover
        """
        Constructor for Gatherer.

        :param client_id: ID to give to the MQTT client
        :param args: args to pass to the MQTT client constructor
        :param smartplug_ids: dictionary with SP MACs as keys and IDs as values
        """
        super().__init__(client_id, *args)
        self.sp_ids = smartplug_ids

    async def connect(
        self, host, port=1883, ssl=False, keepalive=60, version=MQTTv311, raise_exc=True
    ):
        await super().connect(host, port, ssl, keepalive, version, raise_exc)

    def on_connect(self, *args):  # pragma: no cover
        logger.log_info_verbose("Connected to MQTT broker")

    def on_disconnect(self, *args):  # pragma: no cover
        logger.log_info_verbose("Disconnected from MQTT broker")

    def on_subscribe(self, *args):  # pragma: no cover
        logger.log_info_verbose("Subscribed to topic")

    async def get_power_senml(self, ip: str) -> dict:
        """
        Request power measurement from a smartplug and return a senml with the
        ID of the device that replied.

        :param ip: IP to send request to
        :return: response formatted as senml with corresponding ID
        """
        ok, power = await smartplug.get_power(ip=ip)
        if not ok:
            logger.log_error_verbose(f"Failed to get power from '{ip}'")
            return {}
        info = smartplug.extract_info(power)
        return self.info_to_senml(info)

    def pub_to_mqtt(self, senml) -> None:
        """
        Publish a power measurement from a smartplug formatted as senml to the
        MQTT broker at topic {protocol.MQTT_PUB_TOPIC}

        :param senml: senml measurement to post
        :return: None
        """
        # TODO: check if dumping and encoding senml is necessary
        self.publish(protocol.MQTT_PUB_TOPIC, senml)

    async def run_once(self, ip: str) -> None:
        """
        1. Request measurement from IP
        2. Send measurement to MQTT broker
        3. Sleep {RETRY_TIME} seconds

        :param ip: IP address to send requests to
        :return: None, the loop will never exit by itself
        """
        ok, power = await smartplug.get_power(ip=ip)
        if not ok:
            # await asyncio.sleep(RETRY_TIME)
            return
        info = smartplug.extract_info(power)
        senml = self.info_to_senml(info)
        self.pub_to_mqtt(senml)
        # asyncio.sleep(RETRY_TIME)

    async def run(self, ips: List[str]):
        """
        Run a Loop for each ip a SmartPlug might be listening at.

        :param ips: List of potential SmartPlug IP addresses.
        :return: this function runs forever
        """
        loops = []
        for ip in ips:
            # create loop for possible smartplug at ip=ip
            loops.append(loop.Loop(async_func=self.run_once, arguments=(ip,)))
        for sp_loop in loops:
            sp_loop.start()
        asyncio.get_event_loop().run_forever()

    def info_to_senml(self, info: dict) -> dict:
        """
        Convert a dict returned by extract_info() to senml.

        :param info: Return value of extract_info
        :return: Info in SenML format
        """
        for expected_key in ("power", "relay_state", "mac"):
            if expected_key not in info.keys():
                # TODO: handle invalid input
                return {}
        base_name = self.sp_ids.get(info["mac"])
        if base_name is None:
            return {}
        return {
            "e": [{"v": float(info.get("power")), "t": time()}],
            "bn": base_name,
            "bu": "W",
        }
