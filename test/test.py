from AriaPy import *
import sys

class PyTime(ArTime):
    def __init__(self):
        super(PyTime, self).__init__()

class PyPose(ArPose):
    def __init__(self):
        super(PyPose, self).__init__()

Aria_init()
parser = ArArgumentParser(sys.argv)
parser.loadDefaultArguments()
robot = ArRobot()
conn = ArRobotConnector(parser, robot)

robot.runAsync(True)

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

first = True
goalNum = 0
start = PyTime()
start.setToNow()

while Aria.getRunning():
    robot.lock()
    pose = PyPose()
    if first or gotoPoseAction.haveAchievedGoal():
        first = False
        goalNum += 1
	print("running now...")
        if goalNum > 4:
            goalNum = 1
        if goalNum == 1:
            pose.setPose(0, 0, 0)
            gotoPoseAction.setGoal(pose)
            #gotoPoseAction.setGoal(pose.setPose(0, 0, 0))
        elif goalNum == 2:
            pose.setPose(2500, 0, 0)
            gotoPoseAction.setGoal(pose.setPose(2500, 0, 0))
            #gotoPoseAction.setGoal(pose.setPose(2500, 0, 0))
        elif goalNum == 3:
            pose.setPose(2500, 2500, 0)
            gotoPoseAction.setGoal(pose)
            #gotoPoseAction.setGoal(pose.setPose(2500, 2500, 0))
        elif goalNum == 4:
            pose.setPose(2500, 2500, 0)
            gotoPoseAction.setGoal(pose)
            #gotoPoseAction.setGoal(pose.setPose(2500, 2500, 0))

    robot.unlock()
    ArUtil.sleep(100)


    if start.mSecSince() >= duration:
        gotoPoseAction.cancelGoal()
        robot.unlock()
        ArUtil.sleep(3000)
        break

Aria.exit(0)
