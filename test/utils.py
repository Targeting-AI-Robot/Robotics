# -*- coding: cp949 -*-
from math import sin, acos, cos, pi, atan2, sqrt
from threading import Thread
import socket
import os
import csv

GPS_list = []
FLAGS = None

def recv_GPS(ip, port):
    recv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    recv_socket.bind((ip,port))
    recv_socket.listen(5)
    client_socket,_ = recv_socket.accept()

    while True:
        data = client_socket.recv(65535)

def get_gps():
    path = "/home/lee/gps/data/" # fix path
    file_list = os.listdir(path) # get file list
    if(len(file_list)<13): # lack of gps data
        return None,None # return None
    file_list.sort()# find oldest file
    lon = 0
    lat = 0
    for name in file_list[4:]: # get lon,lat value each file and sum
        f = open("data/" +name, 'r')
        lines = csv.reader(f)
        for line in lines:
            lon += float(line[1])
            lat += float(line[2])
        f.close()
    lon = lon / len(file_list[4:])
    lat = lat / len(file_list[4:])
    return lon, lat #get avg gps data

# http://egloos.zum.com/metashower/v/313035
# https://lovestudycom.tistory.com/entry/%EC%9C%84%EB%8F%84-%EA%B2%BD%EB%8F%84-%EA%B3%84%EC%82%B0%EB%B2%95
def calc_gps(lat1, lon1, lat2, lon2):  
    lat1 = deg2rad(lat1)
    lon1 = deg2rad(lon1)
    lat2 = deg2rad(lat2)
    lon2 = deg2rad(lon2)

    # meter
    dist = sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(lon1 - lon2)
    dist = acos(dist)
    dist = rad2deg(dist)
    dist = dist * 60 * 1.1515
    dist = dist * 1.609344 
    dist = dist * 1000.0

    # 0 ~ 360 degree
    dLon = lon2 - lon1
    y = sin(dLon) * cos(lat2)
    x = cos(lat1)*sin(lat2) - sin(lat1)*cos(lat2)*cos(dLon)
    brng = (rad2deg(atan2(y, x)) + 360) % 360 

    return dist, brng

def deg2rad(deg):
    return deg * pi / 180  

  
def rad2deg(rad):
    return rad * 180 / pi

def main():
    t = Thread(target=recv_GPS, args=(FLAGS.ip, FLAGS.port))
    t.daemon = True
    t.start()

    t.join()

if __name__ == '__main__':
    print(calc_gps(52.2296756,21.0122287,52.406374,16.9251681))
    print(calc_gps(-41.32, 174.81, 40.96, -5.50))
    print(get_bearing1(-41.32, 174.81, 40.96, -5.50))
    print(get_bearing2(-41.32, 174.81, 40.96, -5.50))
    print(get_bearing3(-41.32, 174.81, 40.96, -5.50))
    print(get_bearing4(-41.32, 174.81, 40.96, -5.50))

