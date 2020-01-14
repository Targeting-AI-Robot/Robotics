## This robotics project for P3AT

### command for run
Run roscore.
```
roscore
```
Open another termial and run python program.
```
python2 simple.py -robotPort /dev/ttyUSB0
```
or
```
python simple.py -robotPort /dev/ttyUSB0
```

If there is permission error in ttyUSB0 port, run this code.
```
sudo chmod a+rw /dev/ttyUSB0
```

## dependencies for this project

geopy - PyPI

Webpage : https://pypi.org/project/geopy/
```
pip install geopy
```

## useful link
AriaCoda
https://github.com/reedhedges/AriaCoda
