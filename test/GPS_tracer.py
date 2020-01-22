import sys
import socket
import argparse
import Queue
import time
from __future__ import division
from AriaPy import *
from time import sleep
from utils import get_gps, calc_gps, gps2pose, get_gps
from threading import Thread

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
GPS_list = Queue.Queue() # commander GPS list

# TODO : Make this var to parameter
goal_num = 2             # modification count
gps_mode = False         # choose GPS point or 'mm' coordinates

#####################
# Start Main Thread #
#####################

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--ip',type=str,default='10.0.0.216')
    parser.add_argument('-p','--port',type=int,default=9000)
    FLAGS,_ = parser.parse_known_args()

    ###########################
    # Aria library initialize #
    ###########################

    Aria.init()

    # receiving GPS point from commander
    class ReceiveGPSThread(Thread):

        def __init__(self, GPS_list):
            Thread.__init__(self)
            self.GPS_list = GPS_list

        def run(self):
            recv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            recv_socket.bind((FLAGS.ip,FLAGS.port))
            recv_socket.listen(5)
            client_socket,_ = recv_socket.accept()

            while True:
                data = client_socket.recv(1024)
                ex, ey = data.decode().split()
                print("########## Packet received ##########")
                print("LAT :", ex, "LON :", ey)
                GPS_list.put((float(ex),float(ey)))

    ####################
    # Start GPS Thread #
    ####################

    receiveThread = ReceiveGPSThread(GPS_list)
    receiveThread.start()

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
    robot.addSensorInterpTask(printRobotPos)
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
    
    try: 
        while Aria.getRunning():
            print("Start robot moving loop")
            robot.lock()

            # sleep while there is no gps to go or robot is moving
            print("robot has achieved")
            print("GPS empty?",GPS_list.empty())

            while GPS_list.empty():
                robot.unlock()
                ArUtil.sleep(500)
                # print(GPS_list.empty())
                robot.lock()
            
            print("GPS list is not empty")
            first = False
            lat2, lon2 = GPS_list.get()
            GPS_list.task_done()
            
            if (lat2, lon2) == (-1,-1):
                print("exit")
                break

            # TODO robot_state 
            if gps_mode:	 
                #lat1, lon1, base_heading = get_gps()	
                lat1, lon1, base_heading = 0,0,0	
                ex, ey = gps2pose(lat1, lon1, lat2, lon2, base_heading)	
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
