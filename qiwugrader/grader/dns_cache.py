# encoding=utf-8
# ---------------------------------------
#   version：0.2
#   create：2016-04-26
#   update: 2018-06-05
#   author：九茶<bone_ace@163.com> & Feliciano.Long
# ---------------------------------------

import socket
# from gevent import socket

_dnscache = {}


def _set_dns_cache():
    """ DNS缓存 """

    def _getaddrinfo(*args, **kwargs):
        if args in _dnscache:
            # print str(args) + " in cache"
            return _dnscache[args]
        else:
            # print str(args) + " not in cache"
            _dnscache[args] = socket._getaddrinfo(*args, **kwargs)
            return _dnscache[args]

    if not hasattr(socket, '_getaddrinfo'):
        socket._getaddrinfo = socket.getaddrinfo
        socket.getaddrinfo = _getaddrinfo
