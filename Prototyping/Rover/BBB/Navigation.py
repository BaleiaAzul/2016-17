import math
import Utils
import mag as MAG
import gps as GPS
import Adafruit_BBIO.ADC as ADC

class Navigation:
    """ Navigation code """
    def __init__(self, pot_left, pot_middle, pot_right, pot_tol, pot_pin):
        # autopilot
        self.auto = True
        # list of GPS coords to travel to
        self.destinations = []
        self.mag = MAG.Magnetometer()
        self.gps = GPS.GPS()
        self.POT_PIN = pot_pin
        self.POT_LEFT = pot_left
        self.POT_RIGHT = pot_right
        self.POT_MIDDLE = pot_middle
        self.POT_TOL = pot_tol


    # returns a float of how far from straight the potentiomer is. > 0 for Right, < 0 for left
    # returns -1 if error
    def readPot(self):
        result = self.POT_MIDDLE - ADC.read(self.POT_PIN)
        if result > self.POT_MIDDLE - self.POT_RIGHT or result < self.POT_MIDDLE - self.POT_LEFT:
            print result
            return -1
        return result

    # returns heading of front body or -1 if error
    def getMag(self):
        rawMag = self.mag.read()
        print "back: " + str(rawMag)
        pot = self.readPot()
        angle = Utils.translateValue(pot, self.POT_LEFT - self.POT_MIDDLE, self.POT_RIGHT - self.POT_MIDDLE, -40, 40)
        print "front: " + str((rawMag + angle) % 360)
        return (rawMag + angle) % 360

    # returns gps data
    # TODO: get GPS to work
    def getGPS(self):
        return self.gps.read()

    # calculates the desired heading
    # returns a value between 0 and 360 inclusive
    # TODO: calculate direction between current GPS location and destination
    # note that destinations is an array of arrays; destination GPS location
    #  is at [0] which contains [lat, long]
    def calculateDesiredHeading(self):
        currLocation = self.gps.getCoords()
        currLat = currLocation[0]
        currLong = currLocation[1]
        x_distance = self.destinations[0][0] - currLat;
        y_distance = self.destinations[0][1] - currLong;
        theta = math.atan2(x_distance, y_distance)
        return Utils.translateValue(self, theta, -1 * math.pi, math.pi, 0, 360)

    # calculates desired new GPS coordinate based on distance
    # from current GPS location and current heading in degrees
    def calculateDesiredNewCoordinate(self, currHeading, distance):
        theta = Utils.translateValue(self, currHeading, 0, 360, -1 * math.pi, math.pi)
        x = distance * math.cos(theta)
        y = distance * math.sin(theta)
        coords = {x, y}
        return coords

    # returns a turn value from -100 to 100 based on the difference between the current heading and the desired heading
    def calculateDesiredTurn(self, curHeading):
        desiredHeading = self.calculateDesiredHeading()
        difHeading = abs(curHeading - desiredHeading)
        if ((curHeading > desiredHeading and difHeading > 180) or
            (curHeading < desiredHeading and difHeading < 180)):
            #turn right
            return Utils.translateValue(difHeading % 180, 0, 180, 0, 10)
        else:
            #turn left
            return -1 * Utils.translateValue(difHeading % 180, 0, 180, 0, 10)

    # returns True for autopilot False for manual control
    def getAuto(self):
        return self.auto

    # sets the Autopilot
    def setAuto(self, autoVal):
        self.auto = autoVal

    def get_pot_left(self):
        return self.POT_LEFT

    def get_pot_right(self):
        return self.POT_RIGHT

    def get_pot_middle(self):
        return self.POT_MIDDLE

    # appends a destination to the list of destinations
    def append_destiniation(self, dest):
        self.destinations.append(dest)
