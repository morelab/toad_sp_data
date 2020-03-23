"""Helper submodule for operations on ETCD."""
import etcd  # import python-ectd module


def get_smartplug_ids(host, port, key):
    """
    Retrieve smartplug mac addresses and identifiers from ETCD.

    :param host: ETCD host
    :param port: ETCD port
    :param key: parent key of all childs with SP MACs as keys and IDs as values
    :return: dict with MAC addresses as keys and IDs as values
    """
    client = etcd.Client(host=host, port=port)
    ids = {}
    parent = {}
    try:
        parent = client.read(key)
    except etcd.EtcdKeyNotFound:
        return {}
    for child in parent.children:
        k = child.key.split("/")[-1]
        ids[k] = child.value
    return ids
