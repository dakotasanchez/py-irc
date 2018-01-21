#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import (QDesktopWidget, QApplication, QWidget, QPushButton, QTextEdit, QLabel, QLineEdit,
                             QGridLayout)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QColor
from client import SocketLib

class Window(QWidget):

    def __init__(self):
        super().__init__()
        self.connection = SocketLib()
        self.init_ui()
        self.joined_rooms = []
        self.current_room = None
        self.keywords = ['list', 'create', 'join', 'leave']

    def init_thread(self):

        self.receive_thread = ReceiveThread(self.connection)
        self.receive_thread.append_signal.connect(self.received)
        self.receive_thread.start()

    def init_ui(self):
        self.resize(800,500)
        self.center()
        self.setWindowTitle('IRC Client')

        # Create Widgets
        self.connect_btn = QPushButton('Connect', self)
        self.connect_btn.clicked.connect(self.connect)
        self.send_btn = QPushButton('Send', self)
        self.send_btn.clicked.connect(self.send)


        self.receive_area = QTextEdit()
        self.receive_area.setEnabled(False)
        self.send_area = QLineEdit()

        # Create layout
        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(self.connect_btn, 1, 0)
        grid.addWidget(self.receive_area, 2, 0, 5, 5)
        grid.addWidget(self.send_area, 7, 0, 1, 4)
        grid.addWidget(self.send_btn, 7, 4)

        self.setLayout(grid)
        self.show()

    def keyPressEvent(self, e):
        if e == Qt.Key_Enter:
            self.send()

    def center(self):
        g = self.frameGeometry()
        c = QDesktopWidget().availableGeometry().center()
        g.moveCenter(c)
        self.move(g.topLeft())

    def connect(self):
        self.connection.connect()
        self.connect_btn.setEnabled(False)
        self.init_thread()

    def send(self):
        send = self.send_area.text()
        self.send_area.clear()
        self.send_area.setFocus()
        if len(send) == 0:
            return
        send_split = send.split()

        # See if we're just switching rooms
        if send_split[0].lower() == 'switch' and len(send_split) > 1:
            if send_split[1] in self.joined_rooms:
                self.current_room = send_split[1]
                self.receive_area.append('You have switched into ' + self.current_room)
            return

        # If we're not sending a command, prepend current room
        if send_split[0].lower() not in self.keywords:
            if self.current_room is not None:
                self.connection.send(self.current_room + ' ' + send)
            else:
                self.receive_area.append('You are not in a room currently')
        else:
            self.connection.send(send)

    def received(self, data):
        if data is None:
            self.receive_area.append('Connection has been closed')
            return

        data_split = data.split('|')
        command = data_split[0]

        append = ''
        # list members in room
        if command == 'fff0':
            append += 'Members in ' + data_split[1] + ': ' + data_split[2]
        # room doesn't exist, no member list
        elif command == 'fff1':
            append += 'Cannot list, ' + data_split[1] + ' does not exist.'
        # room list
        elif command == 'fff2':
            append += 'Rooms: ' + data_split[1]
        # created room
        elif command == 'fff3':
            append += 'Created ' + data_split[1] + '. You are now in ' + data_split[1] + '.'
            self.joined_rooms.append(data_split[1])
            self.current_room = data_split[1]
        # joined room
        elif command == 'fff4':
            append += 'Joined ' + data_split[1] + '.'
            self.joined_rooms.append(data_split[1])
            self.current_room = data_split[1]
        # left room
        elif command == 'fff5':
            append += 'Left ' + data_split[1] + '.'
            self.joined_rooms.remove(data_split[1])
            if data_split[1] == self.current_room:
                if len(self.joined_rooms) > 0:
                    self.current_room = self.joined_rooms[0]
                    append += '\nYou are now in ' + self.current_room + '.'
                else:
                    self.current_room = None
                    append += '\nYou are now in no rooms.'

        # normal chat message
        elif command == 'fff6':
            append += data_split[1]
        # error in last command
        elif command == 'ffff':
            append = 'Server: Error in last command.'

        self.receive_area.setTextColor(QColor('red'))
        self.receive_area.append(append)
        self.receive_area.setTextColor(QColor('black'))

    def shutdown(self):
        self.connection.disconnect()


class ReceiveThread(QThread):

    append_signal = pyqtSignal(object)

    def __init__(self, connection):
        QThread.__init__(self)
        self.connection = connection

    def run(self):
        while True:
            try:
                data = self.connection.receive(1024)
                if len(bytes(data)) == 0:
                    break
                data = data.decode()
                self.append_signal.emit(data)
            except Exception as e:
                print(e)
                break
        self.append_signal.emit(None)


if __name__ == '__main__':

    app = QApplication(sys.argv)
    w = Window()
    ret = app.exec_()
    w.shutdown()
    sys.exit(ret)
