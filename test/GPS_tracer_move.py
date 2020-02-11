from __future__ import division
import sys
import socket
import argparse
import Queue
import time
from AriaPy import *
from utils import get_gps, calc_gps, gps2pose, gps2dd
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
arg_dict = manager.dict({'stop_flag': False})

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
            if not op_first:
                print("Robot stop for other process...")
                for _ in range(13):
                    robot.unlock()
                    ArUtil.sleep(1000)
                    robot.lock()
            op_first = False
            print("Robot ready to move")
            while lat1 is None:	 
                lat1, lon1, base_heading = get_gps()
         
            print("########## GPS point of robot",lat1, lon1, base_heading)
            
            # sleep while there is no gps to go or robot is moving
            print("is GPS list empty?", len(GPS_list) == 0)

            while not GPS_list:
                robot.unlock()
                ArUtil.sleep(500)
                robot.lock()
            
            print("GPS point received")
            lat2, lon2 = GPS_list.pop(0)
            print("calc to dd")
            # TODO robot_state             	 
            dist, theta = gps2dd(lat1, lon1, lat2, lon2, base_heading)
            print(dist, theta)
            print("Running now...")
    
            # Setting goal of robot
            #gotoPoseAction.setGoal(pose)
            robot.setHeading(robot.getTh() - theta)
            robot.unlock()
            ArUtil_sleep(5000)
            robot.lock()
            robot.move(dist)
            ArUtil_sleep(5000)
            robot.unlock()
            ArUtil_sleep(500)
            robot.lock()

            while robot.getVel() != 0:
                robot.unlock()
                ArUtil_sleep(500)
                robot.lock()
                # Move until stop.
                print("Current robot pose  -> X :",robot.getX(),"Y :",robot.getY())
                if arg_dict['stop_flag']:
                    print("############# stop ##########")
                    del GPS_list[:]
                    robot.setVel(0)
                    arg_dict['stop_flag'] = False
                    robot.unlock()
                    break
                
            print("Current robot pose  -> X :",robot.getX(),"Y :",robot.getY())
            robot.unlock()
            ArUtil.sleep(500)
            print("End one loop")

    except:
        Aria.exit(0)

    Aria.exit(0)
