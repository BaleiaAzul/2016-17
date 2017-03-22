"""
Reads a Digital IO on the Beaglebone Black
to determine the on/off characteristic of a
limit switch.

Written by Jaden Bottemiller in January 2017
EE Team of Husky Robotics
Questions/Comments? Email: jadenjb@uw.edu
(Untested as of 2/6/2017)

"""
import Adafruit_BBIO.GPIO as GPIO  # Ignore compiler errors
from Sensor import Sensor
from Util import Util


class Limit(Sensor):

    # Sets pin of limit switch
    def __init__(self, pin):
        self._pin = str(pin)
        GPIO.setup(self._pin, GPIO.IN)

    # Returns on/off (boolean) characteristic of the pin
    # at any given time
    def getValue(self):
        return GPIO.input(self._pin)

    # Returns data for packet
    def getDataForPacket(self):
        return Util.inttobin(int(self.getValue()), 1)
