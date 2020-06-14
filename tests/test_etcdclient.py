import etcd
import pytest
import uuid

from tests import ETCD_HOST, ETCD_PORT, ETCD_ID_KEY, ETCD_CACHE_KEY
from toad_sp_data import etcdclient


class TmpClient(etcd.Client):
    expected = {
        "CA:FE:CA:FE:CA:FE": "sp_w.r0.c0",
        "FE:CA:FE:CA:FE:CA": "sp_w.r1.c1",
    }

    def __init__(self, host, port, key):
        super().__init__(host, port)
        self.key = key


class TmpCacheClient(etcd.Client):
    expected = {
        "sp_w.r0.c0": "0.0.0.0",
        "sp_w.r1.c1": "0.0.0.1",
    }

    def __init__(self, host, port, key):
        super().__init__(host, port)
        self.key = key


@pytest.fixture
def tmp_client():
    key = f"{ETCD_ID_KEY}/{uuid.uuid4()}"
    client = TmpClient(ETCD_HOST, ETCD_PORT, key)
    for k, v in client.expected.items():
        client.write(f"{key}/{k}", v)
    yield client
    for k, v in client.expected.items():
        client.delete(f"{key}/{k}")


@pytest.fixture
def tmp_cache_client():
    key = f"{ETCD_CACHE_KEY}/{uuid.uuid4()}"
    client = TmpCacheClient(ETCD_HOST, ETCD_PORT, key)
    for k, v in client.expected.items():
        client.write(f"{key}/{k}", v)
    yield client
    for k, v in client.expected.items():
        client.delete(f"{key}/{k}")


def test_get_smartplug_ids(tmp_client):
    ids = etcdclient.get_smartplug_ids(ETCD_HOST, ETCD_PORT, tmp_client.key)
    assert len(ids) == len(tmp_client.expected)
    for k, v in ids.items():
        assert k in tmp_client.expected and ids.get(k) == tmp_client.expected.get(k)


def test_get_smartplug_ips(tmp_cache_client):
    ips = etcdclient.get_cached_ips(ETCD_HOST, ETCD_PORT, tmp_cache_client.key)
    assert len(ips) == len(tmp_cache_client.expected)
    for k, v in ips.items():
        assert k in tmp_cache_client.expected and ips.get(
            k
        ) == tmp_cache_client.expected.get(k)
