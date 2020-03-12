from os import path
import configparser

config = configparser.ConfigParser()
config_path = path.join(
    *path.split(path.dirname(path.abspath(__file__)))[:-1], "config", "config.ini"
)
config.read(config_path)
mqtt_config = dict(config["MQTT"])
