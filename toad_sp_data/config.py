from os import path
import configparser

_config = configparser.ConfigParser()
_config_path = path.join(
    *path.split(path.dirname(path.abspath(__file__)))[:-1], "config", "config.ini"
)
_config.read(_config_path)

_etcd_config = _config["ETCD"]
_gatherer_config = _config["GATHERER"]
_logger_config = _config["LOGGER"]
_mqtt_config = _config["MQTT"]
_workspace_config = _config["WORKSPACE"]

# Configuration variables
# ETCD
ETCD_HOST = _etcd_config.get("host")
ETCD_PORT = int(_etcd_config.get("port"))
ETCD_ID_KEY = _etcd_config.get("id_key")
ETCD_CACHE_KEY = _etcd_config.get("cache_key")
# Gatherer
SLEEP_TIME_SHORT = float(_gatherer_config.get("sleep_time_short"))
SLEEP_TIME_LONG = float(_gatherer_config.get("sleep_time_long"))

# Logger
LOGGER_VERBOSE = _logger_config.getboolean("verbose")
# MQTT
MQTT_BROKER_HOST = _mqtt_config.get("broker_host")
MQTT_BROKER_PORT = int(_mqtt_config.get("broker_port"))
MQTT_RESPONSE_TIMEOUT = int(_mqtt_config.get("response_timeout"))
MQTT_DATA_BASES = _mqtt_config.get("data_bases").split(",")

# WORKSPACE
WS_IP_RANGE_START = _workspace_config.get("ip_range_start")
WS_IP_RANGE_END = _workspace_config.get("ip_range_end")
