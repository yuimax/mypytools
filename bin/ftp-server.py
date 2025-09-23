# pip install pyftpdlib

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

authorizer = DummyAuthorizer()
authorizer.add_user('guest', 'guest', 'C:/usr/pub', perm='elradfmwT')

handler = FTPHandler
handler.authorizer = authorizer

server = FTPServer(('0.0.0.0', 2121), handler)
server.serve_forever()
