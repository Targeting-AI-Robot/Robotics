from math import sin, acos, cos, pi, atan2, sqrt
from threading import Thread
import socket, csv, os
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

def enermy_gps():
    # pixel width, maximum value for hw is 105.022455
    # maximum value = 256 * tan(pi/180*13.9) / tan(pi/180*31.1)
    min_distance = 100
    
    #image path from raspberry pi
    files_path = './images/left/'

    #TODO : select only left picture
    file_list = os.listdir(files_path)
    #print(file_list)
    #input("wait")
    file_list = [files_path+filename for filename in file_list]
    from predict import predict_segment
    images = predict_segment(file_list)

    #suppose that this picture is left
    remove_leftside(images, min_distance)
    people_count = np.sum(np.sum(images / 255, axis = -1), axis=-1)
    selected = np.argmax(people_count, axis=-1)
    print("people_image",people_count)
    #####################
    #Delete after test!##
    selected = 0       ##
    #####################
    print("selected",selected)
    x_diff = calc_x_diff(selected, file_list, images[selected])
    print(x_diff)
    return None

def calc_x_diff(selected, file_list, mask):
    # segmentated image is left image
    left_image_name = "./images/left/capture_512_{}_L.png".format(selected)
    right_image_name = "./images/right/capture_512_{}_R.png".format(selected)
    
    left_image = np.array(Image.open(left_image_name))
    right_image = np.array(Image.open(right_image_name))
    #plt.imshow(mask)
    #plt.show()
    template, lx, ly = make_template(mask, left_image)
    print("normxcorr2 template shape",template.shape)
    print("normxcorr2 right_image shape",right_image.shape)
    
    out = normxcorr2(template, rgb2gray(right_image), mode="full")
    show3D(out)
    rx, ry = argmax2D(out)
    return abs(rx - lx)

def make_template(segmented, left_image):
    
    i,j = np.where(segmented == 255)
    lx1 = np.min(i)
    lx2 = np.max(i)
    ly1 = np.min(j)
    ly2 = np.max(j)
    print(segmented.shape)
    print(left_image.shape)
    
    
    mask = (segmented[lx1:lx2,ly1:ly2] 
            * rgb2gray(left_image)[lx1:lx2,ly1:ly2])
    plt.figure("segmented")
    #plt.imshow(segmented[lx1:lx2,ly1:ly2] )
    plt.imshow(segmented)
    plt.figure("left_image")
    #plt.imshow(rgb2gray(left_image)[lx1:lx2,ly1:ly2])
    plt.imshow(rgb2gray(left_image))
    plt.figure("mask")
    plt.imshow(mask)
    
    plt.show()
    mask /= 255
    print("lx, ly", lx2, ly2)
    
    return mask, lx2, ly2

def remove_leftside(images, min_distance):
    images[:,:,:min_distance] = 0

def rgb2gray(color_image):
    gray_image = (0.2125*color_image[:,:,0] + 0.7154*color_image[:,:,1]
                + 0.0721*color_image[:,:,2])
    return gray_image

def argmax2D(image):
    h, w = image.shape
    max_index = np.argmax(image) 
    return max_index//w, max_index%w

def show3D(out):
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    fig = plt.figure()
    x = np.zeros(out.shape)
    y = np.zeros(out.shape)
    
    ax = fig.add_subplot(111, projection='3d')
    for i in range(len(x)):
        for j in range(len(x[i])):
            x[i,j] = i
            y[i,j] = j
    from matplotlib import cm
    ax.plot_surface(x,y,out, cmap=cm.coolwarm)
    #fig.colorbar(ax, shrink=0.5, aspect=5)
    plt.show()



# https://github.com/Sabrewarrior/normxcorr2-python
def normxcorr2(template, image, mode="full"):
    import numpy as np
    from scipy.signal import fftconvolve
   
    # If this happens, it is probably a mistake
    if np.ndim(template) > np.ndim(image) or \
            len([i for i in range(np.ndim(template)) if template.shape[i] > image.shape[i]]) > 0:
        print("normxcorr2: TEMPLATE larger than IMG. Arguments may be swapped.")
    print(template.shape)
    template = template - np.mean(template)
    image = image - np.mean(image)

    a1 = np.ones(template.shape)
    # Faster to flip up down and left right then use fftconvolve instead of scipy's correlate
    ar = np.flipud(np.fliplr(template))
    out = fftconvolve(image, ar.conj(), mode=mode)
    
    image = fftconvolve(np.square(image), a1, mode=mode) - \
            np.square(fftconvolve(image, a1, mode=mode)) / (np.prod(template.shape))

    # Remove small machine precision errors after subtraction
    image[np.where(image < 0)] = 0

    template = np.sum(np.square(template))
    out = out / np.sqrt(image * template)

    # Remove any divisions by 0 or very close to 0
    out[np.where(np.logical_not(np.isfinite(out)))] = 0
    
    print("argmax2D(out)",argmax2D(out))

    return out

def recv_GPS(ip, port):
    recv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    recv_socket.bind((ip,port))
    recv_socket.listen(5)
    client_socket,_ = recv_socket.accept()

    while True:
        data = client_socket.recv(65535)

def get_gps():
    file_num = 5
    path = "./data/" # fix path
    file_list = os.listdir(path) # get file list
    if(len(file_list)<file_num): # lack of gps data
        return None,None,None # return None
    file_list.sort()# find oldest file
    lon = 0
    lat = 0
    hd = 0
    for name in file_list[-file_num:]: # get lon,lat value each file and sum
        f = open("data/" +name, 'r')
        lines = csv.reader(f)
        for line in lines:
            lon += float(line[1])
            lat += float(line[2])
            hd = float(line[-1])
        f.close()
    lon = lon / len(file_list[-file_num:])
    lat = lat / len(file_list[-file_num:])
    return lon, lat, hd #get avg gps data

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
    
#mili meter and degree
def gps2dd(lat1, lon1, lat2, lon2, base_heading):
    dist, heading = calc_gps(lat1, lon1, lat2, lon2)
    theta = heading - base_heading
    print("calc done")
    return dist*1000, theta    

def gps2pose(lat1, lon1, lat2, lon2, diff):
    dist, heading = calc_gps(lat1, lon1, lat2, lon2)
    print("dist",dist)
    print("heading",heading)

    theta = heading - diff

    print("theta",theta)

    theta = deg2rad(theta)
    # meter to millimeter
    pose = (1000*dist*cos(theta), -1000*dist*sin(theta))
    return pose


if __name__ == '__main__':
    enermy_gps()
