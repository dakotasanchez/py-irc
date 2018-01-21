#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket

class SocketLib(object):

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(60)
        self.host = 'localhost'
        self.port = 10000

    def connect(self):
        self.sock.connect((self.host, self.port))

    def disconnect(self):
        self.sock.shutdown(socket.SHUT_RDWR)

    def send(self, data):
        try:
            if type(data) is str:
                data = data.encode()
            self.sock.send(bytes(data))
        except:
            print('Error sending')

    def receive(self, length):
        return self.sock.recv(length)