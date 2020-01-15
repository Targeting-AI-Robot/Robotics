from AriaPy import *
import sys

class PyTime(ArTime):
    def __init__(self):
        super(ArTime, self).__init__()

class PyPose(ArPose):
    def __init__(self):
        super(ArPose, self).__init__()

Aria_init()
parser = ArArgumentParser(sys.argv)
parser.loadDefaultArguments()
robot = ArRobot()
conn = ArRobotConnector(parser, robot)

robot.runAsync(true)

limiter = ArActionLimiterForwards("speed limiter near", 300, 600, 250)
limiterFar = ArActionLimiterForwards("speed limiter far", 300, 1100, 400)
tableLimiter = ArActionLimiterTableSensor()

robot.addAction(tableLimiter, 100)
robot.addAction(limiter, 95)
robot.addAction(limiterFar, 90)

gotoPose = ArActionGotoStraight("gotostraight")
robot.addAction(gotoPose, 50)

stop = ArActionStop("stop")
robot.addAction(stop, 40)

robot.enableMotors()
robot.comInt(ArCommands_SOUNDTOG, 0);

duration = 30000

first = True
goalNum = 0
start = PyTime()
start.setToNow()

while Aria.getRunning():
    robot.lock()
    if first or gotoPoseAction.haveAchievedGoal():
        first = False
        goalNum += 1

        if goalNum > 4:
            goalNum = 1
        if goalNum == 1:
            gotoPoseAction.setGoal(ArPose(2500, 0))
        elif goalNum == 2:
            gotoPoseAction.setGoal(ArPose(2500, 2500))
        elif goalNum == 3:
            gotoPoseAction.setGoal(ArPose(0, 2500))
        elif goalNum == 4:
            gotoPoseAction.setGoal(ArPose(0, 0))

    if start.mSecSince() >= duration:
        gotoPoseAction.cancelGoal();
        robot.unlock();
        ArUtil.sleep(3000);
        break

    robot.unlock();
    ArUtil.sleep(100);

Aria.exit(0);
