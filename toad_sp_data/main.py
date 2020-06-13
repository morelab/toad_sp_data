#!/usr/bin/env python3

import asyncio

from toad_sp_data import config, gatherer, logger, utils

if __name__ == "__main__":

    # Load range of IPs to query
    ips = utils.ip_range(config.WS_IP_RANGE_START, config.WS_IP_RANGE_END)
    logger.log_info(f"IPs: {', '.join(ips)}")

    loop = asyncio.get_event_loop()

    g = gatherer.create_gatherer(loop)

    # Connect to MQTT broker
    asyncio.get_event_loop().run_until_complete(
        g.connect(host=config.MQTT_BROKER_HOST, port=config.MQTT_BROKER_PORT)
    )

    # Start Query Loops
    g.start(ips)
    asyncio.get_event_loop().run_forever()
