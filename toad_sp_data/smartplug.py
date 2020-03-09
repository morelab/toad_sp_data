"""Encryption, decryption and consumption-getting functions for TPLink HS110
SmartPlugs based on the research made by softScheck in
https://www.softscheck.com/en/reverse-engineering-tp-link-hs110/"""

import asyncio
import json
from struct import pack
from typing import Any, Tuple

from toad_sp_data import logger


class DecryptionException(Exception):
    """
    Decryption errors have to be handled and depend not on the decryptors
    actions but on the message being decrypted.

    Encryption errors depend on the payload and will never happen if the
    payload is correct, making an exception for encryption unnecessary.
    """

    pass


def encrypt(payload: bytes) -> bytes:
    """
    Encrypt payload to be sent to a SP.

    :param payload: raw payload
    :return: encrypted payload
    """
    key = 171
    result = pack(">I", len(payload))
    for i in payload:
        key = x = key ^ i
        result += bytes([x])
    return result


def decrypt(response: bytes) -> bytes:
    """
    Decrypt a response from a SP.

    :param response: raw encrypted response from the SP
    :return: decrypted response from the SP
    """
    if response is None or len(response) < 4:
        raise DecryptionException("Invalid or null response")
    # strip unused bytes
    if response[:4] == b"\x00\x00\x00?":
        response = response[4:]
    # decrypt message
    try:
        key = 171
        result = b""
        for i in response:
            x = key ^ i
            key = i
            result += bytes([x])
    except json.JSONDecodeError:
        raise DecryptionException("Could not decode JSON from decrypted response")
    return result


async def send_command(cmd: dict, ip: str, port: int = 9999) -> Tuple[bool, Any]:
    """
    Send a command to a SmartPlug.

    :param cmd: dict containing command to send
    :param ip: IP address of target SP
    :param port: port of target SP
    :return: (True/False if command was successful, decrypted response)
    """
    logger.log_info_verbose(
        "[SP]\tSend command to SP: addr({}:{}) msg({})".format(ip, port, cmd)
    )
    try:
        reader, writer = await asyncio.open_connection(ip, port)
        writer.write(encrypt(json.dumps(cmd).encode("utf-8")))
        writer.write_eof()
        await writer.drain()
        data = await reader.read()
        writer.close()
        await writer.wait_closed()
        if len(data) == 0:
            return False, {}
        decrypted = decrypt(data[4:])
        return True, json.loads(decrypted)
    except Exception as err:
        logger.log_error_verbose(f"[SP]\tError: '{str(err)}'")
        return False, err


async def get_consumption(ip: str, port: int = 9999) -> Tuple[bool, Any]:
    """
    Get current consumption from a SmartPlug.

    :param ip: P address of target SP
    :param port: port of target SP
    :return: (True/False if command was successful, decrypted response)
    """
    cmd: dict = {"emeter": {"get_realtime": {}}, "system": {"get_sysinfo": {}}}
    return await send_command(cmd, ip, port)


def _extract_info(response: dict) -> dict:
    """
    Internal function. Extract power, state and MAC address from SP response.

    :param response: decrypted response from SmartPlug
    :return: dict with keys "power", "relay_state" and "mac"
    """
    power_key = (
        "power" if "power" in response["emeter"]["get_realtime"].keys() else "power_mw"
    )
    power = response["emeter"]["get_realtime"][power_key]
    if power_key == "power_mw":
        power = power / 1000.0
    info = {
        "power": power,  # in W
        "relay_state": response["system"]["get_sysinfo"]["relay_state"],
        "mac": response["system"]["get_sysinfo"]["mac"],
    }
    logger.log_info_verbose(f"[SP]\tExtract info from response: {info}")
    return info
