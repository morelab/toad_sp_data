from json import dumps, loads, JSONDecodeError

import pytest

from tests import mocks
from toad_sp_data import smartplug

# test payload both with and without encryption
_command = {"emeter": {"get_realtime": {}}, "system": {"get_sysinfo": {}}}
_decrypted = dumps(_command).encode("utf-8")
_encrypted = (
    b"\x00\x00\x00?\xd0\xf2\x97\xfa\x9f\xeb\x8e\xfc\xde\xe4\xc4\xbf\x9d\xfa"
    b"\x9f\xeb\xb4\xc6\xa3\xc2\xae\xda\xb3\xde\xbb\x99\xa3\x83\xf8\x85\xf8"
    b"\xd4\xf4\xd6\xa5\xdc\xaf\xdb\xbe\xd3\xf1\xcb\xeb\x90\xb2\xd5\xb0\xc4"
    b"\x9b\xe8\x91\xe2\x8b\xe5\x83\xec\xce\xf4\xd4\xaf\xd2\xaf\xd2"
)


@pytest.fixture
async def smartplug_mock(unused_tcp_port, event_loop) -> mocks.SmartPlugMock:
    sp_mock = mocks.SmartPlugMock("127.0.0.1", unused_tcp_port, event_loop)
    await sp_mock.start()
    yield sp_mock
    await sp_mock.stop()


def test_encrypt():
    encrypted = smartplug.encrypt(_decrypted)
    assert encrypted == _encrypted
    # encrypt a null message
    try:
        smartplug.encrypt(None)
        pytest.fail("Expected TypeError")
    except TypeError:
        pass


def test_decrypt():
    expected = loads(_decrypted.decode("utf-8"))
    decrypted = smartplug.decrypt(_encrypted)
    assert loads(decrypted.decode("utf-8")) == expected
    decrypted = smartplug.decrypt(_encrypted)
    assert loads(decrypted.decode("utf-8")) == expected
    # decrypt a null message
    try:
        smartplug.decrypt(None)
        pytest.fail("Expected exception caused by null payload")
    except smartplug.DecryptionException:
        pass
    # decrypt an empty
    try:
        smartplug.decrypt(b"")
        pytest.fail("Expected exception caused by empty payload")
    except smartplug.DecryptionException:
        pass
    # decrypt an invalid message
    try:
        invalid_payload = smartplug.decrypt(_encrypted[1:])
        loads(invalid_payload)
        pytest.fail("Expected exception caused by invalid payload")
    except JSONDecodeError:
        pass


def test_decrypt_command():
    cmd = smartplug.decrypt_command(_encrypted)
    assert cmd == _command
    try:
        smartplug.decrypt_command(b"")
        pytest.fail("Decrypting empty command should raise DecryptionException")
    except smartplug.DecryptionException:
        pass
    try:
        smartplug.decrypt_command(b"\xca\xfe\xca\xfe")
        pytest.fail("Decrypting improperly formatted command should raise Exception")
    except smartplug.DecryptionException:
        pass


def test_encrypt_command():
    encrypted = smartplug.encrypt_command(_command)
    # dumping the json may alter the byte order
    assert smartplug.decrypt_command(encrypted) == _command
    try:
        smartplug.encrypt_command(None)
    except TypeError:
        pytest.fail("JSON dump should have initialized an empty dictionary")


@pytest.mark.asyncio
async def test_send_command(smartplug_mock):
    ok, response = await smartplug.send_command(
        smartplug_mock.ok_command, smartplug_mock.addr, smartplug_mock.port
    )
    assert ok and type(response) is dict and response == mocks.SmartPlugMock.ok_response
    ok, response = await smartplug.send_command(
        {"_": "_"}, smartplug_mock.addr, smartplug_mock.port
    )
    assert not ok and type(response) is dict and response == {}


@pytest.mark.asyncio
async def test_get_consumption(smartplug_mock):
    ok, response = await smartplug.get_consumption(
        smartplug_mock.addr, smartplug_mock.port
    )
    assert ok and type(response) is dict and response == mocks.SmartPlugMock.ok_response
    ok, _ = await smartplug.get_consumption("0.0.0.0", 0)
    assert not ok


@pytest.mark.asyncio
async def test_extract_info(smartplug_mock):
    expected = {"mac": "CA:FE:CA:FE:CA:FE", "power": 42, "relay_state": 1}
    info = smartplug.extract_info(smartplug_mock.ok_response)
    assert info == expected
    # test old version of smartplugs
    response = dict(smartplug_mock.ok_response)
    response["emeter"]["get_realtime"]["power_mw"] = (
        response["emeter"]["get_realtime"].pop("power") * 1000.0
    )
    expected["power"] = float(expected["power"])
    assert info == expected
