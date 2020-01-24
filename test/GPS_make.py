import socket
import sys
import time
import os
    
def receive():
    receive = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    #print("create socket")
    receive.bind(('',8081))
    while(True):
        file_len = len(os.walk('/home/ai/Desktop/data').next()[2])# fix path
        directory = []
        if(file_len>100):# remove oldest data file
            files_path = '/home/ai/Desktop/data/'#fix path
            directory = os.listdir(files_path)
            directory.sort()
            #print(directory[0])
            os.remove('data/'+directory[0])
        data, addr = receive.recvfrom(65535)
        data = data.decode('UTF-8')
        value = data.split(',')
        if value[1] =='nan':# if gps data is none, not make file
            print('this is nan')
            continue
        f = open('data/'+time.strftime('%H%M%S')+'.csv','w')
        #f.write('Time,lon,lat,alt,climb,speed,track,device,mode,epx,epy,epc,ept,epv,eps,class,tag\n')
        f.write(data+'\n')
        #print(data)
        f.close()

if __name__=='__main__':
    receive()
