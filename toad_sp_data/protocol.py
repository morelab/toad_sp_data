# MQTT topics
_MQTT_CATEGORY = "data"
_MQTT_FROM = "sp_data"
# The MQTT_PUB_TOPIC will be later appended the database, e.g. "influx_data"
MQTT_PUB_TOPIC = f"{_MQTT_CATEGORY}/{_MQTT_FROM}"

MEASUREMENT = "power"
PAYLOAD_DATA_FIELD = "data"
