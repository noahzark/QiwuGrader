import sys
import os

_is_python_2 = True
if sys.version_info >= (3, 0):
    _is_python_2 = False

file_encoding = None
if not _is_python_2:
    file_encoding = 'utf-8'


def encode_str(str_obj):
    if _is_python_2:
        return str_obj
    else:
        return str_obj.encode('utf-8')


def to_str(str_obj):
    if _is_python_2:
        return str_obj
    else:
        if isinstance(str_obj, str):
            return str_obj
        return str(str_obj, encoding='utf-8')


def write_utf_bom():
    open_mode = _is_python_2 and 'w' or 'wb'
    path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), 'logs')
    with open(os.path.join(path,'QiwuTest.csv'), open_mode) as f:
        import codecs
        f.write(codecs.BOM_UTF8)


def open_config_file(file_name):
    if _is_python_2:
        return open(file_name, 'r')
    return open(file_name, 'r', encoding=file_encoding)


def assemble_server_class():
    if _is_python_2:
        import BaseHTTPServer
        from SimpleHTTPServer import SimpleHTTPRequestHandler

        handler_class = SimpleHTTPRequestHandler
        server_class = BaseHTTPServer.HTTPServer
    else:
        import http
        import socketserver

        handler_class = http.server.SimpleHTTPRequestHandler
        server_class = socketserver.TCPServer
    return handler_class, server_class
