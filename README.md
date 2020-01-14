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

## useful link
AriaCoda  
https://github.com/reedhedges/AriaCoda

How to use C++ class in python ( SWIG C++/Python: inheritance proxy objects )  
https://stackoverflow.com/questions/25962662/swig-c-python-inheritance-proxy-objects
