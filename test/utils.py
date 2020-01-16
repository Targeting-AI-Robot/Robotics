# -*- coding: cp949 -*-
from math import sin, acos, cos, pi

def get_gps():
    x = 0
    y = 0
    # gps 계산해서 리턴
    return x, y

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
    print(dist)
    print(cos(lat1))
    print((cos(lat1)*sin(dist)))    
    # radian
    theta = acos((sin(lat2)-sin(lat1)*cos(dist))/(cos(lat1)*sin(dist)))*(180/pi)
  
    return dist, theta  
  
def deg2rad(deg):
    return deg * pi / 180  

  
def rad2deg(rad):
    return rad * 180 / pi

if __name__ == '__main__':
    print(calDistance(10,0,0,0))
    print(calDistance(0,1,0,0))
    
