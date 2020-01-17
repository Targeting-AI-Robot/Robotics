from __future__ import division
from AriaPy import *
import sys
from time import sleep
from utils import get_gps, calc_gps

##############
# initalize  #
##############

class PyTime(ArTime):
    def __init__(self):
        super(PyTime, self).__init__()

class PyPose(ArPose):
    def __init__(self):
        super(PyPose, self).__init__()

print "STEP 1" 
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

print "STEP 2"
sonar = ArSonarDevice()
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

def printRobotPos():
    print(robot.getPose())

robot.addSensorInterpTask(printRobotPos)

print "STEP 3"
limiter = ArActionLimiterForwards("speed limiter near", 300, 600, 250)
limiterFar = ArActionLimiterForwards("speed limiter far", 300, 1100, 400)
tableLimiter = ArActionLimiterTableSensor()

print "STEP 4"
robot.addAction(tableLimiter, 100)
robot.addAction(limiter, 95)
robot.addAction(limiterFar, 90)

print "STEP 5"
gotoPoseAction = ArActionGotoStraight("gotostraight")
robot.addAction(gotoPoseAction, 50)

stop = ArActionStop("stop")
robot.addAction(stop, 40)

print "STEP 6"
robot.enableMotors()
robot.comInt(ArCommands.SOUNDTOG, 0)
duration = 30000

print "STEP 7"
goalNum = 0
start = PyTime()
start.setToNow()


##############
# globar var #
##############

GPS_list = [(500,0),(1000,0),(0,500)]
# TODO robot_state  

################
# init for GPS #
################

sx = None
sy = None

##############
#    main    #
##############

# num of adjustment
goal_num = 2
first = True
print "STEP 8"
try: 
    while Aria.getRunning():
        print("start loop")
        robot.lock()
        # sleep while there is no gps to go or robot is moving
        while not first and not gotoPoseAction.haveAchievedGoal():
            print("achieved",gotoPoseAction.haveAchievedGoal())
            print("pose",robot.getX(),robot.getY())
            ArUtil.sleep(100)

        while not GPS_list:
            ArUtil.sleep(100)
    
        first = False
        sx, sy, cur_theta = get_gps()
        ex, ey = GPS_list.pop(0)
        print(type(ex),ex)
        print(type(ey),ey)

        #dist, dtheta = calc_gps(sx, sy, ex, ey)
        
        #robot.setPose(0,0,0)
        pose = PyPose()
        print("running now...")
    
        pose.setPose(ex, ey)
        #sleep(10000)
        count = 0
        while True:
            count += 1
            
            gotoPoseAction.setGoal(pose)
            print("sleep")
            robot.unlock()
            while not gotoPoseAction.haveAchievedGoal():
                ArUtil.sleep(100)
                print(robot.getX(), robot.getY(), gotoPoseAction.haveAchievedGoal())
            robot.lock()
            if count == goal_num:
                break
            
        robot.unlock()
        ArUtil.sleep(500)
        print("end one loop")

except:
    Aria.exit(0)


Aria.exit(0)
