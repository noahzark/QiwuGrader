import sys
import os
from grader.compatible import assemble_server_class

# only serve the logs directory
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.chdir(log_dir)

if sys.argv[1:]:
    port = int(sys.argv[1])
else:
    port = 8000
server_address = ('0.0.0.0', port)

HandlerClass, ServerClass = assemble_server_class()

httpd = ServerClass(server_address, HandlerClass)

sa = httpd.socket.getsockname()
print("Serving HTTP on", sa[0], "port", sa[1], "...")
httpd.serve_forever()
