import socket
from socket_connection import SocketConnection


class SimpleMessageHandler:
    def handle_message(self, message):
        print(message)


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('', 38240))
sc = SocketConnection(s, SimpleMessageHandler())

while True:
    message = input()
    sc.write(message)
