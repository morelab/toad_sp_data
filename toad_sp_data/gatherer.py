import asyncio

from gmqtt import Client as MQTTClient
from time import time

from toad_sp_data import config, logger, loop, protocol, smartplug


class Gatherer(MQTTClient):
    def __init__(self, *args, conf=config.mqtt_config):  # pragma: no cover
        # TODO: connect to MQTT broker
        super().__init__(*args)
        self.config = conf

    def on_connect(self, *args):  # pragma: no cover
        logger.log_info_verbose("Connected to MQTT broker")

    def on_disconnect(self, *args):  # pragma: no cover
        logger.log_info_verbose("Disconnected from MQTT broker")

    def on_subscribe(self, *args):  # pragma: no cover
        logger.log_info_verbose("Subscribed to topic")

    @staticmethod
    async def get_power_senml(ip: str) -> dict:
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
        return info_to_senml(info)

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
        senml = info_to_senml(info)
        self.pub_to_mqtt(senml)
        # asyncio.sleep(RETRY_TIME)

    async def run(self):
        # TODO assign IPs
        ips = ["127.0.0.1"]
        loops = []
        for ip in ips:
            # create loop for possible smartplug at ip=ip
            loops.append(loop.Loop(async_func=self.run_once, arguments=(ip,)))
        for sp_loop in loops:
            sp_loop.start()
        asyncio.get_event_loop().run_forever()


def info_to_senml(info: dict) -> dict:
    """
    Convert a dict returned by extract_info() to senml.

    :param info: Return value of extract_info
    :return: Info in SenML format
    """
    for expected_key in ("power", "relay_state", "mac"):
        if expected_key not in info.keys():
            # TODO: handle invalid input
            return {}
    base_name = "_"  # TODO
    return {
        "e": [{"v": float(info.get("power")), "t": time()}],
        "bn": base_name,
        "bu": "W",
    }
