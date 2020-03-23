import etcd
import pytest
import uuid

from tests import ETCD_HOST, ETCD_PORT, ETCD_KEY
from toad_sp_data import etcdclient


class TmpClient(etcd.Client):
    expected = {
        "CA:FE:CA:FE:CA:FE": "w.r0.c0",
        "FE:CA:FE:CA:FE:CA": "w.r1.c1",
    }

    def __init__(self, host, port, key):
        super().__init__(host, port)
        self.key = key


@pytest.fixture
def tmp_client():
    key = f"{ETCD_KEY}/{uuid.uuid4()}"
    client = TmpClient(ETCD_HOST, ETCD_PORT, key)
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
