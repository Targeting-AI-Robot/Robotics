from gps import *
import time
import socket
import sys
import math
import IMU
import os

########## socket ##########
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)



########## GPS values parsing ##########
gpsd = gps(mode=WATCH_ENABLE|WATCH_NEWSTYLE) 

sock.bind(('', 8082))

SEND_IP = '192.168.2.216'
SEND_PORT = 8082

def TPVParser():
    report = gpsd.next() #
    msg = ''
    if report['class'] == 'TPV':
        msg += str(getattr(report, 'time', 'nan')) + ','
        msg += str(getattr(report, 'lat', 'nan')) + ','
        msg += str(getattr(report, 'lon', 'nan')) + ','
        msg += str(getattr(report, 'alt', 'nan')) + ','
        msg += str(getattr(report, 'climb', 'nan')) + ','
        msg += str(getattr(report, 'speed', 'nan')) + ','
        msg += str(getattr(report, 'track', 'nan')) + ','
        msg += str(getattr(report, 'device', 'nan')) + ','
        msg += str(getattr(report, 'mode', 'nan')) + ','
        msg += str(getattr(report, 'epx', 'nan')) + ','
        msg += str(getattr(report, 'epy', 'nan')) + ','
        msg += str(getattr(report, 'epc', 'nan')) + ','
        msg += str(getattr(report, 'ept', 'nan')) + ','
        msg += str(getattr(report, 'epv', 'nan')) + ','
        msg += str(getattr(report, 'eps', 'nan')) + ','
        msg += str(getattr(report, 'class', 'nan')) + ','
        msg += str(getattr(report, 'tag', 'nan'))
    return msg



########## heading value ##########

RAD_TO_DEG = 57.29578
M_PI = 3.14159265358979323846
MAG_LPF_FACTOR = 0.4    # Low pass filter constant magnetometer
ACC_LPF_FACTOR = 0.4    # Low pass filter constant for accelerometer
ACC_MEDIANTABLESIZE = 9     # Median filter table size for accelerometer. Higher = smoother but a longer delay
MAG_MEDIANTABLESIZE = 9     # Median filter table size for magnetometer. Higher = smoother but a longer delay


# Calibrating the compass isnt mandatory, however a calibrated 
# compass will result in a more accurate heading value.

magXmin =  -468
magYmin =  -439
magZmin =  -1534
magXmax =  1751
magYmax =  1817
magZmax =  979

oldXMagRawValue = 0
oldYMagRawValue = 0
oldZMagRawValue = 0
oldXAccRawValue = 0
oldYAccRawValue = 0
oldZAccRawValue = 0

#Setup the tables for the mdeian filter. Fill them all with '1' so we dont get devide by zero error 
acc_medianTable1X = [1] * ACC_MEDIANTABLESIZE
acc_medianTable1Y = [1] * ACC_MEDIANTABLESIZE
acc_medianTable1Z = [1] * ACC_MEDIANTABLESIZE
acc_medianTable2X = [1] * ACC_MEDIANTABLESIZE
acc_medianTable2Y = [1] * ACC_MEDIANTABLESIZE
acc_medianTable2Z = [1] * ACC_MEDIANTABLESIZE
mag_medianTable1X = [1] * MAG_MEDIANTABLESIZE
mag_medianTable1Y = [1] * MAG_MEDIANTABLESIZE
mag_medianTable1Z = [1] * MAG_MEDIANTABLESIZE
mag_medianTable2X = [1] * MAG_MEDIANTABLESIZE
mag_medianTable2Y = [1] * MAG_MEDIANTABLESIZE
mag_medianTable2Z = [1] * MAG_MEDIANTABLESIZE

IMU.detectIMU()     #Detect if BerryIMUv1 or BerryIMUv2 is connected.
IMU.initIMU()       #Initialise the accelerometer, gyroscope and compass

def headingDirection():
    global oldXMagRawValue
    global oldYMagRawValue
    global oldZMagRawValue
    global oldXAccRawValue
    global oldYAccRawValue
    global oldZAccRawValue
    #Read the accelerometer,gyroscope and magnetometer values
    ACCx = IMU.readACCx()
    ACCy = IMU.readACCy()
    ACCz = IMU.readACCz()
    MAGx = IMU.readMAGx()
    MAGy = IMU.readMAGy()
    MAGz = IMU.readMAGz()


    #Apply compass calibration    
    MAGx -= (magXmin + magXmax) /2
    MAGy -= (magYmin + magYmax) /2
    MAGz -= (magZmin + magZmax) /2

    #### Apply low pass filter ####
    MAGx =  MAGx  * MAG_LPF_FACTOR + oldXMagRawValue*(1 - MAG_LPF_FACTOR);
    MAGy =  MAGy  * MAG_LPF_FACTOR + oldYMagRawValue*(1 - MAG_LPF_FACTOR);
    MAGz =  MAGz  * MAG_LPF_FACTOR + oldZMagRawValue*(1 - MAG_LPF_FACTOR);
    ACCx =  ACCx  * ACC_LPF_FACTOR + oldXAccRawValue*(1 - ACC_LPF_FACTOR);
    ACCy =  ACCy  * ACC_LPF_FACTOR + oldYAccRawValue*(1 - ACC_LPF_FACTOR);
    ACCz =  ACCz  * ACC_LPF_FACTOR + oldZAccRawValue*(1 - ACC_LPF_FACTOR);

    oldXMagRawValue = MAGx
    oldYMagRawValue = MAGy
    oldZMagRawValue = MAGz
    oldXAccRawValue = ACCx
    oldYAccRawValue = ACCy
    oldZAccRawValue = ACCz

    #### Median filter for accelerometer ####
    # cycle the table
    for x in range (ACC_MEDIANTABLESIZE-1,0,-1 ):
        acc_medianTable1X[x] = acc_medianTable1X[x-1]
        acc_medianTable1Y[x] = acc_medianTable1Y[x-1]
        acc_medianTable1Z[x] = acc_medianTable1Z[x-1]

    # Insert the lates values
    acc_medianTable1X[0] = ACCx
    acc_medianTable1Y[0] = ACCy
    acc_medianTable1Z[0] = ACCz    

    # Copy the tables
    acc_medianTable2X = acc_medianTable1X[:]
    acc_medianTable2Y = acc_medianTable1Y[:]
    acc_medianTable2Z = acc_medianTable1Z[:]

    # Sort table 2
    acc_medianTable2X.sort()
    acc_medianTable2Y.sort()
    acc_medianTable2Z.sort()

    # The middle value is the value we are interested in
    ACCx = acc_medianTable2X[ACC_MEDIANTABLESIZE/2];
    ACCy = acc_medianTable2Y[ACC_MEDIANTABLESIZE/2];
    ACCz = acc_medianTable2Z[ACC_MEDIANTABLESIZE/2];



    ######################################### 
    #### Median filter for magnetometer ####
    #########################################
    # cycle the table
    for x in range (MAG_MEDIANTABLESIZE-1,0,-1 ):
        mag_medianTable1X[x] = mag_medianTable1X[x-1]
        mag_medianTable1Y[x] = mag_medianTable1Y[x-1]
        mag_medianTable1Z[x] = mag_medianTable1Z[x-1]

    # Insert the latest values    
    mag_medianTable1X[0] = MAGx
    mag_medianTable1Y[0] = MAGy
    mag_medianTable1Z[0] = MAGz    

    # Copy the tables
    mag_medianTable2X = mag_medianTable1X[:]
    mag_medianTable2Y = mag_medianTable1Y[:]
    mag_medianTable2Z = mag_medianTable1Z[:]

    # Sort table 2
    mag_medianTable2X.sort()
    mag_medianTable2Y.sort()
    mag_medianTable2Z.sort()

    # The middle value is the value we are interested in
    MAGx = mag_medianTable2X[MAG_MEDIANTABLESIZE/2];
    MAGy = mag_medianTable2Y[MAG_MEDIANTABLESIZE/2];
    MAGz = mag_medianTable2Z[MAG_MEDIANTABLESIZE/2];

    #Convert Accelerometer values to degrees

    AccXangle =  (math.atan2(ACCy,ACCz)*RAD_TO_DEG)
    AccYangle =  (math.atan2(ACCz,ACCx)+M_PI)*RAD_TO_DEG

    #Change the rotation value of the accelerometer to -/+ 180 and
    #move the Y axis '0' point to up.  This makes it easier to read.
    if AccYangle > 90:
        AccYangle -= 270.0
    else:
        AccYangle += 90.0

    ### Tilt compensated heading ###
    #Normalize accelerometer raw values.
    accXnorm = ACCx/math.sqrt(ACCx * ACCx + ACCy * ACCy + ACCz * ACCz)
    accYnorm = ACCy/math.sqrt(ACCx * ACCx + ACCy * ACCy + ACCz * ACCz)

    #Calculate pitch and roll

    pitch = math.asin(accXnorm)
    roll = -math.asin(accYnorm/math.cos(pitch))


    #Calculate the new tilt compensated values
    magXcomp = MAGx*math.cos(pitch)+MAGz*math.sin(pitch)

    #The compass and accelerometer are orientated differently on the LSM9DS0 and LSM9DS1 and the Z axis on the compass
    #is also reversed. This needs to be taken into consideration when performing the calculations
    if(IMU.LSM9DS0):
        magYcomp = MAGx*math.sin(roll)*math.sin(pitch)+MAGy*math.cos(roll)-MAGz*math.sin(roll)*math.cos(pitch)   #LSM9DS0
    else:
        magYcomp = MAGx*math.sin(roll)*math.sin(pitch)+MAGy*math.cos(roll)+MAGz*math.sin(roll)*math.cos(pitch)   #LSM9DS1


    #Calculate tilt compensated heading
    tiltCompensatedHeading = 180 * math.atan2(magYcomp,magXcomp)/M_PI

    if tiltCompensatedHeading < 0:
                tiltCompensatedHeading += 360

    ### END ###
    return tiltCompensatedHeading




########## main ##########
try:
    while True:
        msg = TPVParser()
        if not msg == '':
            msg += ',' + str(round(headingDirection(),3))
            print(msg)
            sock.sendto(msg.encode(), (SEND_IP, SEND_PORT))
        time.sleep(0.01)
except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
    print("Done.\nExiting.")
