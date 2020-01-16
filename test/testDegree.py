from math import sin, acos, cos, pi, atan2

def calc_gps(lat1, lon1, lat2, lon2):  
    dx = lat2-lat1
    dy = lon2-lon1

    rad = atan2(dx, dy)
    degree = (rad*180)/pi

    return degree

print(calc_gps(3,0,0,3))
