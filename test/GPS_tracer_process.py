from __future__ import division
import sys
import socket
import argparse
import Queue
import time
import numpy as np
from AriaPy import *
from utils import get_gps, calc_gps, gps2pose
from multiprocessing import Process, Manager
#from threading import Thread

#############################
# C++ class to Python class #
#############################

class PyTime(ArTime):
    def __init__(self):
        super(PyTime, self).__init__()

class PyPose(ArPose):
    def __init__(self):
        super(PyPose, self).__init__()

####################
# global variables #
####################

robot = None             # P3-AT Robot
FLAGS = None             # server ip address and connection port
#GPS_list = Queue.Queue() # commander GPS list
manager = Manager()
GPS_list = manager.list()
arg_dict = manager.dict({'stop_flag': False, 'img_flag': True})

# TODO : Make this var to parameter
goal_num = 2             # modification count
gps_mode = True         # choose GPS point or 'mm' coordinates
#gps_mode = False         # choose GPS point or 'mm' coordinates

def recv_gps():
    recv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    recv_socket.bind((FLAGS.ip,FLAGS.port))
    recv_socket.listen(5)
    client_socket,_ = recv_socket.accept()

    while True:
        data = client_socket.recv(1024)
        decoded = data.decode().split()
        if len(decoded) < 2 or len(decoded) > 3:
            continue
                
        ex, ey = decoded
        decoded_data = (float(ex),float(ey))
                
        if decoded_data == (-1.0,-1.0):
            print("########## recv stop packet ##########")
            arg_dict['stop_flag'] = True
            continue
                    
        print("########## Packet received ##########")
        print("LAT :", ex, "LON :", ey)
        #GPS_list.put((float(ex),float(ey)))
        GPS_list.append((float(ex),float(ey)))
        print("size of GPS_list", len(GPS_list))

def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf
        
def recv_img():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('192.168.2.170', 8282)) # Address must be changed later
    num = 0

    while True:
        # send request by flag
        if(arg_dict['img_flag']):
            sock.send('req'.encode())
            length = recvall(sock, 16)
            stringData = recvall(sock, int(length))
            data = np.fromstring(stringData, dtype='uint8')
            
            decimg1 = cv2.imdecode(data,1)
            
            length = recvall(sock, 16)
            stringData = recvall(sock, int(length))
            data = np.fromstring(stringData, dtype='uint8')
            
            decimg2 = cv2.imdecode(data,1)
            
            cv2.imwrite('test/image/image_' + num + '_L.png', decimg1)
            cv2.imwrite('test/image/image_' + num + '_R.png', decimg2)
            num = (num + 1) % 8
            
            

def turn_and_take(robot):
    # rotate 45
    robot.setHeading(robot.getTh() + 45)
    robot.unlock()
    ArUtil.sleep(3000)
    robot.lock()

    # send command to take picture
    # make function in utils.py and use it
    
    
def detect():
    # take one picture using segmentation and depth to return gps
    # make function in utils.py and use it
    return enermy_gps()

#####################
# Start Main Thread #
#####################

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--ip',type=str,default='0.0.0.0')
    parser.add_argument('-p','--port',type=int,default=9000)
    FLAGS,_ = parser.parse_known_args()

    ###########################
    # Aria library initialize #
    ###########################

    Aria.init()

    ####################
    # Start GPS Thread #
    ####################

    recv_gps_proc = Process(target=recv_gps)
    recv_gps_proc.start()
    
    #############################
    # Start img receiver Thread #
    #############################
    
    recv_img_proc = Process(target=recv_img)
    recv_img_proc.start()

    ##################
    # Robot settings #
    ##################
    
    parser = ArArgumentParser(sys.argv)
    parser.loadDefaultArguments()
    robot = ArRobot()
    conn = ArRobotConnector(parser, robot)
    laserCon = ArLaserConnector(parser, robot, conn)

    if not conn.connectRobot(robot):
        print 'Error connecting to robot'
        Aria.logOptions()
        print 'Could not connect to robot, exiting.'
        Aria.exit(1)

    sonar = ArSonarDevice()
    # robot.addSensorInterpTask(printRobotPos)
    robot.addRangeDevice(sonar)
    robot.runAsync(True)

    if not Aria_parseArgs():
        Aria.logOptions()
        Aria.exit(2)
  

    print 'Connecting to laser and waiting 1 sec...'
    laser = None
    if(laserCon.connectLasers()):
        print 'Connected to lasers as configured in parameters'
        laser = robot.findLaser(1)
    else:
        print 'Warning: unable to connect to lasers. Continuing anyway!'

    limiter = ArActionLimiterForwards("speed limiter near", 300, 600, 250)
    limiterFar = ArActionLimiterForwards("speed limiter far", 300, 1100, 400)
    tableLimiter = ArActionLimiterTableSensor()

    robot.addAction(tableLimiter, 100)
    robot.addAction(limiter, 95)
    robot.addAction(limiterFar, 90)

    gotoPoseAction = ArActionGotoStraight("gotostraight")
    robot.addAction(gotoPoseAction, 50)

    stop = ArActionStop("stop")
    robot.addAction(stop, 40)

    robot.enableMotors()
    robot.comInt(ArCommands.SOUNDTOG, 0)

    start = PyTime()
    start.setToNow()

    ##################
    # Robot Movement #
    ##################
    op_first = True
    try: 
        while Aria.getRunning():
            print("Start robot moving loop")
            robot.lock()
            lat1, lon1, base_heading = None, None, None
            diff = None

            #############
            #  detect   #
            #############
            if not op_first and gps_mode:
                print("Robot stop for other process...")

                for _ in range(8):
                    turn_and_take(robot)
                detect()
                
                for _ in range(13):
                    robot.unlock()
                    ArUtil.sleep(1000)
                    robot.lock()
            op_first = False
            print("Robot ready to move")
            while gps_mode and lat1 is None:     
                lat1, lon1, base_heading = get_gps()
                diff = base_heading + robot.getTh()
            if gps_mode:
                print("########## GPS point of robot",lat1, lon1, base_heading)
            else:
                print("########## pose of robot",robot.getX(), robot.getY())
            
            # sleep while there is no gps to go or robot is moving
            print("is GPS list empty?", len(GPS_list) == 0)

            while not GPS_list:
                robot.unlock()
                ArUtil.sleep(500)
                robot.lock()
            
            print("GPS list is not empty")
            first = False
            lat2, lon2 = GPS_list.pop(0)

            # TODO robot_state 
            if gps_mode:     
                #lat1, lon1, base_heading = get_gps()
                #print("##########",lat1, lon1, base_heading)
                #lat1, lon1, base_heading = 0,0,0    
                ex, ey = gps2pose(lat1, lon1, lat2, lon2, diff)
                print("diff", diff)    
                ex += robot.getX()
                ey += robot.getY()
            else:    
                ex, ey = lat2, lon2    
                
            #dist, dtheta = calc_gps(sx, sy, ex, ey)
            print("Calculated pose     -> X :", ex, "Y :", ey)
            pose = PyPose()
            pose.setPose(ex, ey)

            print("Running now...")
            count = 0
            
            first = True
            robot.unlock()

            while True:
                robot.lock()
                print("first and achieved?", first, gotoPoseAction.haveAchievedGoal())
                #print("stop_flag", arg_dict['stop_flag'])
                if arg_dict['stop_flag']:
                    print("############# stop ##########")
                    del GPS_list[:]
                    gotoPoseAction.cancelGoal()
                    arg_dict['stop_flag'] = False
                    break
                if first or gotoPoseAction.haveAchievedGoal():
                    # Move first time and correct until the set number is reached.
                    if count == goal_num:
                        break

                    first = False
                    print("run count", count)
                    count += 1
            
                    print("Achieved:",gotoPoseAction.haveAchievedGoal())
                    print("Current robot pose  -> X :",robot.getX(),"Y :",robot.getY())
                    print("Set next robot goal -> X :",pose.getX(),"Y :", pose.getY())
                    
                    # Setting goal of robot
                    gotoPoseAction.setGoal(pose)
                    
                print("Current robot pose  -> X :",robot.getX(),"Y :",robot.getY())
                robot.unlock()
                ArUtil.sleep(500)
                

            robot.unlock()
            ArUtil.sleep(500)
            print("End one loop")

    except:
        Aria.exit(0)

    Aria.exit(0)
