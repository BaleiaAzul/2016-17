#!/usr/bin/env python
import Adafruit_BBIO.UART as uart
import serial
from time import sleep
from math import *
from sabertooth import *
import argparse
from timedeltatype import *

uart.setup("UART1")
uart.setup("UART2")
ser1 = serial.Serial(port="/dev/ttyO1", baudrate=9600)
ser2 = serial.Serial(port="/dev/ttyO2", baudrate=38400)
ser1.close()
ser2.close()
ser1.open()
ser2.open()

motors = {}
motors["mot1"] = Sabertooth(ser2, 128, 0)
motors["mot4"] = Sabertooth(ser2, 128, 4)
motors["wrist_angle"] = Sabertooth(ser2, 129, 0)
motors["base_rot"] = Sabertooth(ser2, 129, 4)
motors["test"] = Sabertooth(ser1, 128, 0)
motors["test_1"] = Sabertooth(ser1, 128, 4)

def float_range(min, max):
    def float_test(x):
        x = float(x)
        if x < min or x > max:
            raise argparse.ArgumentTypeError("%r not in range [%.1f, %.1f]"%(x,min,max))
        return x
    return float_test


parser = argparse.ArgumentParser(description='Arm control script')
parser.add_argument('joint', choices=motors.keys(), help='The joint to control.')
parser.add_argument('strength', type=float_range(-1,1), help='Strength as a value between -1 and 1. -1 is reverse')
parser.add_argument('duration', type=TimeDeltaType(), help='Amonut of time to run the motor for')
args = parser.parse_args()

print "Running %s at %.3f for %.3fs"%(args.joint, args.strength, args.duration.total_seconds())
motors[args.joint].write(args.strength)
