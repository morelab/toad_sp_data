import asyncio
from time import time
from typing import List

from gmqtt import Client as MQTTClient
from gmqtt.mqtt.constants import MQTTv311

from toad_sp_data import config, etcdclient, logger, loop, protocol, smartplug


class Gatherer(MQTTClient):
    """A Gatherer requests power measurements from SmartPlugs, maps the
    measurement to the corresponding SmartPlug ID and send them to the MQTT
    broker."""

    def __init__(
            self,
            event_loop: asyncio.AbstractEventLoop,
            client_id="Gatherer",
            *args,
            smartplug_ids={},
    ):  # pragma: no cover
        """
        Constructor for Gatherer.

        :param client_id: ID to give to the MQTT client
        :param args: args to pass to the MQTT client constructor
        :param smartplug_ids: dictionary with SP MACs as keys and IDs as values
        """
        super().__init__(client_id, *args)
        self.event_loop = event_loop
        self.sp_ids = smartplug_ids
        try:
            self.cached_ips = etcdclient.get_cached_ips(
                config.ETCD_HOST, config.ETCD_PORT, config.ETCD_CACHE_KEY
            )
        except Exception as err:
            logger.log_error(err.__str__())
            self.cached_ips = {}

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

    async def get_power_senml(self, ip: str) -> List:
        """
        Request power measurement from a smartplug and return a senml with the
        ID of the device that replied.

        :param ip: IP to send request to
        :return: response formatted as senml with corresponding ID
        """
        ok, power = await smartplug.get_power(ip=ip)
        if not ok:
            logger.log_error_verbose(f"Failed to get power from '{ip}'")
            return []
        info = smartplug.extract_info(power)
        return self.info_to_senml(info)

    def pub_to_mqtt(self, senml) -> None:
        """
        Publish a power measurement from a smartplug formatted as senml to the
        MQTT broker at topic {protocol.MQTT_PUB_TOPIC}

        :param senml: senml measurement to post
        :return: None
        """
        logger.log_info_verbose(f"[SP]\tPublish to MQTT: {senml}")
        for db in config.MQTT_DATA_BASES:
            topic = f"{protocol.MQTT_PUB_TOPIC}/{db}"
            logger.log_info_verbose(f"[SP]\tTopic: {topic}")
            self.publish(topic, senml)

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
            logger.log_info(f"[SP]\tFailed to get power from {ip}")
            cached = False
            for _, cip in self.cached_ips.items():
                if ip == cip:
                    cached = True
                    break
            if cached:
                await asyncio.sleep(config.SLEEP_TIME_SHORT)
            else:
                # Give less priority to unregistered IPs
                await asyncio.sleep(config.SLEEP_TIME_LONG)
            return
        info = smartplug.extract_info(power)
        # logger.log_info(f"[SP]\tObtained {info} from {ip}")
        senml = self.info_to_senml(info)
        self.pub_to_mqtt(wrap_senml(senml))
        # Update local and remote (ETCD) IP cache
        sp_id = self.sp_ids.get(info["mac"])
        self.cached_ips[sp_id] = ip
        try:
            logger.log_info(f"[SP]\tCaching IP {ip} for SP {sp_id}")
            etcdclient.put_cached_ip(
                config.ETCD_HOST, config.ETCD_PORT, config.ETCD_CACHE_KEY, sp_id, ip
            )
        except Exception as err:
            logger.log_error(err.__str__())
        await asyncio.sleep(config.SLEEP_TIME_SHORT)

    def start(self, ips: List[str]):
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
            sp_loop.start(self.event_loop)

    def info_to_senml(self, info: dict) -> List[dict]:
        """
        Convert a dict returned by extract_info() to senml.

        :param info: Return value of extract_info
        :return: Info in SenML format
        """
        for expected_key in ("power", "relay_state", "mac"):
            if expected_key not in info.keys():
                logger.log_error("[SP]\tMissing field in info dictionary")
                return [{}]
        mac = info["mac"]
        base_name = self.sp_ids.get(mac)
        if base_name is None:
            logger.log_error(f"[SP]\tNo ID found for SmartPlug with MAC '{mac}'.")
            return [{}]
        return [
            {
                "bn": f"{base_name}/{protocol.MEASUREMENT}",
                "bu": "W",
                "t": time(),
                "v": float(info.get("power")),
            },
            {
                "bn": f"{base_name}/{protocol.STATUS}",
                "bu": "S",
                "t": time(),
                "v": info.get("relay_state")
            }
        ]


def wrap_senml(senml):
    """
    Wrap the senml in the format used by IoToad compontents.

    :param senml: senml to wrap
    :return: wrapped senml
    """
    return {protocol.PAYLOAD_DATA_FIELD: senml}


def create_gatherer(event_loop: asyncio.AbstractEventLoop) -> Gatherer:
    # Load smartplug IDs
    ids = etcdclient.get_smartplug_ids(
        config.ETCD_HOST, config.ETCD_PORT, config.ETCD_ID_KEY
    )
    logger.log_info(f"IDs: [{ids}]")

    # Create gatherer
    return Gatherer(event_loop=event_loop, smartplug_ids=ids)
