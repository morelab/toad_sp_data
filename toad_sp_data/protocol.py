# MQTT topics
_MQTT_CATEGORY = "data"
_MQTT_TO = "influx_data"
_MQTT_FROM = "sp_data"
MQTT_PUB_TOPIC = f"{_MQTT_CATEGORY}/{_MQTT_TO}/{_MQTT_FROM}"

MEASUREMENT = "power"
PAYLOAD_DATA_FIELD = "data"
