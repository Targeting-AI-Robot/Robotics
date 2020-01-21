from __future__ import division
from AriaPy import *
import sys
import socket
import argparse
from utils import get_gps, calc_gps, gps2pose, get_gps
from threading import Thread
import Queue


##############
# initalize  #
##############

class PyTime(ArTime):
    def __init__(self):
        super(PyTime, self).__init__()

class PyPose(ArPose):
    def __init__(self):
        super(PyPose, self).__init__()

####################
# global variables #
####################

robot = None
FLAGS = None
GPS_list = Queue.Queue()

# TODO robot_state  

################
# init for GPS #
################

# Are you using these, Mr.Lee?
# sx = None
# sy = None

####################
# define functions #
####################

def printRobotPos():
    print(robot.getPose())

def recv_gps():
    recv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    recv_socket.bind((FLAGS.ip,FLAGS.port))
    recv_socket.listen(5)
    client_socket,_ = recv_socket.accept()

    while True:
        data = client_socket.recv(1024)
        ex, ey = data.decode().split()
        print("##################recv packet :",(float(ex),float(ey)))
        GPS_list.put((float(ex),float(ey)))

########
# Main #
########

if __name__ == '__main__':
    ####################
    # Start GPS Thread #
    ####################

    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--ip',type=str,default='10.0.0.216')
    parser.add_argument('-p','--port',type=int,default=9000)
    FLAGS,_ = parser.parse_known_args()

    receiving_gps = Thread(target=recv_gps)
    receiving_gps.start()

    ##################
    # Robot Movement #
    ##################

    Aria.init()
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
    duration = 30000

    start = PyTime()
    start.setToNow()

    # num of adjustment
    goal_num = 2
    gps_mode = False
    first = True
    print "STEP 8"
    try: 
        while Aria.getRunning():
            print("start loop")
            robot.lock()
            # sleep while there is no gps to go or robot is moving
            print("robot has achieved")
            print("GPS empty?",GPS_list.empty())

            while GPS_list.empty():
                pass
                ArUtil.sleep(100)

            print("GPS list is not empty")
            first = False
            lat2, lon2 = GPS_list.pop(0)
            print(type(ex),ex)
            print(type(ey),ey)

            #dist, dtheta = calc_gps(sx, sy, ex, ey)
            
            #robot.setPose(0,0,0)
            pose = PyPose()
            print("running now...")
            if gps_mode:
                lat1, lon1, base_heading = get_gps()
                ex, ey = gps2pose(lat1, lon1, lat2, lon2, base_heading)
            else:
                ex, ey = lat2, lon2
                pose.setPose(ex, ey)

            print("running now")
            count = 0
            
            first = True
            robot.unlock()

            while True:
                robot.lock()
                print("if boolean:",first, gotoPoseAction.haveAchievedGoal())
                if first or gotoPoseAction.haveAchievedGoal():
                    if count == goal_num:
                        break

                    first = False
                    print("run count", count)
                    count += 1
            
                    print("achieved:",gotoPoseAction.haveAchievedGoal())
                    print("pose",robot.getX(),robot.getY())
                    print("set goal of robot",pose.getX(), pose.getY())
                    gotoPoseAction.setGoal(pose)
                    
                print("unlock robot")
                robot.unlock()
                ArUtil.sleep(500)

            robot.unlock()
            ArUtil.sleep(100)
            print("end one loop")

    except:
        Aria.exit(0)

    receiving_gps.join()
    GPS_list.join()

    Aria.exit(0)
