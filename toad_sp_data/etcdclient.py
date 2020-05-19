"""Helper submodule for operations on ETCD."""
from typing import Dict

import etcd  # import python-ectd module


def get_smartplug_ids(host: str, port: int, key: str) -> Dict[str, str]:
    """
    Retrieve smartplug mac addresses and identifiers from ETCD.

    :param host: ETCD host
    :param port: ETCD port
    :param key: parent key of all childs with SP MACs as keys and IDs as values
    :return: dict with MAC addresses as keys and IDs as values
    """
    client = etcd.Client(host=host, port=port)
    ids = {}
    parent: etcd.EtcdResult = ...
    try:
        parent = client.read(key)
    except etcd.EtcdKeyNotFound:
        return {}
    for child in parent.children:
        k = child.key.split("/")[-1]
        ids[k] = child.value
    return ids


def get_cached_ips(host: str, port: int, key: str) -> Dict[str, str]:
    """
    Retrieved previously known IP addresses of smartplugs.

    :param host: ETCD host
    :param port: ETCD port
    :param key: parent key of all the cached ID->IP association
    :return: dict with smartplug IDs as keys and IPs as values
    """
    client = etcd.Client(host=host, port=port)
    ips = {}
    parent: etcd.EtcdResult = ...
    try:
        parent = client.read(key)
    except etcd.EtcdKeyNotFound:
        return {}
    for child in parent.children:
        k = child.key.split("/")[-1]
        ips[k] = child.value
    return ips


def put_cached_ip(host: str, port: int, key: str, sp_id: str, sp_ip: str) -> None:
    """
    Write an ID->IP association to ETCD.

    :param host: ETCD host
    :param port: ETCD port
    :param key: Key of cached addresses
    :param sp_id: ID of the smartplug
    :param sp_ip: IP of the smartplug
    :return: None
    """
    client = etcd.Client(host=host, port=port)
    client.write(f"{key}/{sp_id}", sp_ip)
