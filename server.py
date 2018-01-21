#!/usr/bin/python3
# -*- coding: utf-8 -*-

import socket
import threading

class Server(object):

    def __init__(self):
        self.client_count = 0
        self.threads = []
        self.rooms = {}
        self.host = ''
        self.port = 10000
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))

    def start(self):
        self.sock.listen(10)

        while True:
            client_sock, addr = self.sock.accept()
            client_sock.settimeout(600)
            thread = ClientSession(self.client_count, client_sock, self)
            self.threads.append(thread)
            self.client_count += 1
            thread.start()

    def signal_receive(self, data, id):
        data = data.decode('utf-8')
        id = str(id)
        if data == 'EXIT':
            for r in self.rooms.keys():
                if id in self.rooms[r]:
                    self.rooms[r].remove(id)
            return

        data = data.split()
        message = ' '

        source = [t for t in self.threads if str(t.id) == id][0]
        if source is None:
            print('Error finding source')
            return

        if data[0].lower() == 'list':
            if len(data) > 1:
                if data[1] in self.rooms.keys():
                    for m in self.rooms[data[1]]:
                        message += str(m)
                        message += ' '
                    source.send('fff0|' + data[1] + '|' + message)
                else:
                    source.send('fff1|' + data[1])
                return

            for k in self.rooms.keys():
                message += k
                message += ' '
            source.send('fff2|' + message)
            return

        elif data[0].lower() == 'create':
            if len(data) > 1:
                self.rooms[data[1]] = [id,]
                source.send('fff3|' + data[1])
            else:
                source.send('ffff')
            return

        elif data[0].lower() == 'join':
            if len(data) > 1 and data[1] in self.rooms.keys():
                self.rooms[data[1]].append(id)
                source.send('fff4|' + data[1])
            else:
                source.send('ffff')
            return

        elif data[0].lower() == 'leave':
            if len(data) > 1 and data[1] in self.rooms.keys():
                self.rooms[data[1]].remove(id)
                source.send('fff5|' + data[1])
            else:
                source.send('ffff')
            return

        elif data[0] in self.rooms.keys():
            for t in self.threads:
                if str(t.id) in self.rooms[data[0]]:
                    temp = data[1:]
                    temp = ' '.join(temp)
                    t.send('fff6|' + str(id) + ': ' + temp)


class ClientSession(threading.Thread):

    def __init__(self, id, client_sock, parent):
        super(ClientSession, self).__init__()
        self.id = id
        self.client_sock = client_sock
        self.parent = parent

    def run(self):
        print('Starting session for ' + str(self.id))

        while True:
            try:
                data = self.client_sock.recv(1024)
                if len(bytes(data)) == 0:
                    break
                self.parent.signal_receive(data, self.id)
            except Exception as e:
                print(e)
                break

        self.parent.signal_receive('EXIT'.encode(), self.id)
        print('Exiting session for ' + str(self.id))
        self.client_sock.shutdown(socket.SHUT_RDWR)


    def send(self, data):
        if type(data) is str:
            data = data.encode()
        self.client_sock.send(bytes(data))


if __name__ == '__main__':

    s = Server()
    s.start()