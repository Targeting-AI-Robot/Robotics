import socket

SERVER_IP = '10.0.0.216'
SERVER_PORT = 9000

def run():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((SERVER_IP, SERVER_PORT))
    while True:
        line = raw_input("?input :")
        s.send(line.encode())

if __name__ == '__main__':
    run()
