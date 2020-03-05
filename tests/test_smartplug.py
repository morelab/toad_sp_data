from pytest import fail
from json import loads, JSONDecodeError

from toad_sp_data import smartplug


# test payload both with and without encryption
_decrypted = '{"emeter": {"get_realtime": {}}, "system": {"get_sysinfo": {}}}'.encode(
    "utf-8"
)
_encrypted = (
    b"\x00\x00\x00?\xd0\xf2\x97\xfa\x9f\xeb\x8e\xfc\xde\xe4\xc4\xbf\x9d\xfa"
    b"\x9f\xeb\xb4\xc6\xa3\xc2\xae\xda\xb3\xde\xbb\x99\xa3\x83\xf8\x85\xf8"
    b"\xd4\xf4\xd6\xa5\xdc\xaf\xdb\xbe\xd3\xf1\xcb\xeb\x90\xb2\xd5\xb0\xc4"
    b"\x9b\xe8\x91\xe2\x8b\xe5\x83\xec\xce\xf4\xd4\xaf\xd2\xaf\xd2"
)


def test_encrypt():
    encrypted = smartplug.encrypt(_decrypted)
    assert encrypted == _encrypted
    # encrypt a null message
    try:
        smartplug.encrypt(None)
        fail("Expected TypeError")
    except TypeError:
        pass


def test_decrypt():
    expected = loads(_decrypted.decode("utf-8"))
    decrypted = smartplug.decrypt(_encrypted)
    assert loads(decrypted.decode("utf-8")) == expected
    decrypted = smartplug.decrypt(_encrypted[4:])
    assert loads(decrypted.decode("utf-8")) == expected
    # decrypt a null message
    try:
        smartplug.decrypt(None)
        fail("Expected TypeError")
    except TypeError:
        pass
    # decrypt an empty
    try:
        invalid = smartplug.decrypt(b"")
        loads(invalid)
        fail("Expected JSONDecodeError")
    except JSONDecodeError:
        pass
    # decrypt an invalid message
    try:
        invalid = smartplug.decrypt(_encrypted[1:])
        loads(invalid)
        fail("Expected JSONDecodeError")
    except JSONDecodeError:
        pass
