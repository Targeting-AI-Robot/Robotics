from __future__ import division
from AriaPy import *
import sys

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
first = True
goalNum = 0
start = PyTime()
start.setToNow()

print "STEP 8"
while Aria.getRunning():
    robot.lock()
    pose = PyPose()
    print("goal",gotoPoseAction.haveAchievedGoal())
    if first or gotoPoseAction.haveAchievedGoal():
        first = False
        goalNum += 1
	print("running now...")

        if goalNum > 4:
            goalNum = 1
            break
        if goalNum == 1:
            pose.setPose(0, 0, 0)
            gotoPoseAction.setGoal(pose)
	    print "POSE......(0, 0, 0)"
            #gotoPoseAction.setGoal(pose.setPose(0, 0, 0))
        elif goalNum == 2:
            pose.setPose(1000, 0, 0)
            gotoPoseAction.setGoal(pose)
	    print "POSE......(2500, 0, 0)"
            #gotoPoseAction.setGoal(pose.setPose(2500, 0, 0))
        elif goalNum == 3:
            pose.setPose(1000, 1000, 0)
            gotoPoseAction.setGoal(pose)
            print "POSE......(2500, 2500, 0)"
            #gotoPoseAction.setGoal(pose.setPose(2500, 2500, 0))
        elif goalNum == 4:
            pose.setPose(1000, 1000, 0)
            gotoPoseAction.setGoal(pose)
	    print "POSE......(0, 2500, 0)"
            #gotoPoseAction.setGoal(pose.setPose(2500, 2500, 0))

    robot.unlock()
    ArUtil.sleep(500)


    if start.mSecSince() >= duration:
        gotoPoseAction.cancelGoal()
        robot.unlock()
        ArUtil.sleep(3000)
        break

Aria.exit(0)
