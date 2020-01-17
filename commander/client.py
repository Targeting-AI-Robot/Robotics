import socket
import re

SERVER_IP = '10.0.0.216'
SERVER_PORT = 9000

expression = re.compile('-?[0-9]+.[0-9]+ -?[0-9]+.[0-9]+')

def run():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((SERVER_IP, SERVER_PORT))
    while True:
        line = raw_input()
        match = re.match(expression, line)
        if match == None:
            print('doens\'t match!')
        else:
            s.send(line.encode())

if __name__ == '__main__':
    run()
