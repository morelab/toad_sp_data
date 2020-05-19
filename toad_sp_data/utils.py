import socket
import struct
from typing import List


def ip_range(start: str, end: str) -> List[str]:
    """
    From https://stackoverflow.com/a/17641585/7557549.

    :param start: lowest IP address
    :param end: highest IP address
    :return: start, all addresses in between, end
    """
    start_n = struct.unpack(">I", socket.inet_aton(start))[0]
    end_n = struct.unpack(">I", socket.inet_aton(end))[0]
    return [socket.inet_ntoa(struct.pack(">I", i)) for i in range(start_n, end_n)]
