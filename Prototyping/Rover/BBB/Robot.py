import Adafruit_BBIO.ADC as ADC
import Adafruit_PCA9685
import PID
import math
import threading
import MiniMotor
import BigMotor
import Robot_comms
import Navigation
import Utils
import sys


class Robot(object):
    """
    Class for controlling the whole robot.

    Attributes:
        pot_pid (PID.PID): PID controller for the potentiometer.
        nav (Navigation.Navigation): Object for managing navigation.
        motors (list of Motor.Motor): The list (of length 4, 0-based) of motors.
        r_comms (Robot_comms.Robot_comms): Object for managing communicationg
            with the base station.
        automode (int): Code for what mode the rover is in in regards to
            autonomous driving.

    ROBOT motor configuration:

    Front
    +---+
    3   4
     \ /
      0
     / \
    1   2
    +---+
    Back
    """

    def __init__(self, is_using_big_motor):
        """
        Args:
            is_using_big_motor (bool): True if using BigMotor for controller motors.
        """
        ADC.setup()

        self.pot_pid = PID.PID(-0.1, 0, 0)

        self.nav = Navigation.Navigation(0.55000, (0.55000 + 0.11111) / 2, 0.11111, 0.01, "AIN2")
        # setup motors
        # motor: throttle, F, B
        # 1: 8,  9,  10
        # 2: 13, 12, 11
        # 3: 2,  4,  3
        # 4: 7,  6,  5

        if not is_using_big_motor:
            # setup i2c to motorshield
            pwm = Adafruit_PCA9685.PCA9685(address=0x60, busnum=1)
            pwm.set_pwm_freq(60)
            self.motors = [

                None,  # motor IDs are 1-based, so placeholder for index 0
                MiniMotor.MiniMotor(1, 8, 9, 10, pwm),
                MiniMotor.MiniMotor(2, 13, 12, 11, pwm),
                MiniMotor.MiniMotor(3, 2, 4, 3, pwm),
                MiniMotor.MiniMotor(4, 7, 6, 5, pwm),
            ]
        elif is_using_big_motor:
            self.motors = [
                BigMotor.BigMotor(1, "P8_13"),
                BigMotor.BigMotor(2, "P9_28"),
                BigMotor.BigMotor(3, "P9_14"),
                BigMotor.BigMotor(4, "P9_22")
                ]
        self.r_comms = Robot_comms.Robot_comms("192.168.0.50", 8840, 8841, "<?hh", "<?ff", "<ffffffff")
        self.automode = 0

    def driveMotor(self, motor_id, motor_val):
        """
        Drive one motor.

        Args:
            motor_id (int): The 1-based ID of the motor to drive
            motor_val (int): How much power to drive the motor. Use negative
                numbers to drive in reverse.
        """
        if motor_id < 1 or motor_id > 4:
            print "bad motor num: " + motor_id
            return
        self.motors[motor_id - 1].set_motor(motor_val)

    def stopMotor(self, motor_id):
        """
        Stop one motor.

        Args:
            motor_id (int): The 1-based ID of the motor to stop
        """
        if motor_id < 1 or motor_id > 4:
            print "bad motor num: " + motor_id
            return
        self.motors[motor_id].set_motor_exactly(0)

    def getDriveParms(self):
        """
        Gets the driving parameters of the rover.

        Returns:
            tuple of (int, int): The drive parameters in the format (throttle, turn).
                For the turn value, 100 is full right, -100 is full left, and 0
                is straight.
        """
        if self.r_comms.receivedDrive is None:
            return 0, 0
        auto = self.r_comms.receivedDrive[0]
        if auto:
            if self.automode == 0:  # Auto drive normally
                if self.nav.isObstacle():  # if obstacle in front then switch mode
                    self.automode = 1
                else:
                    return 20, self.nav.calculateDesiredTurn(self.nav.getMag(), self.nav.calculateDesiredHeading())
            if self.automode == 1:  # Turn rover head to left to prepare to scan
                if self.nav.readPot() < self.nav.get_pot_left():
                    leftheading = (self.nav.getMag() - 40) % 360
                    if leftheading < 0:
                        leftheading = 360 - leftheading
                    return 0, self.nav.calculateDesiredTurn(self.nav.getMag(), leftheading)
                else:
                    self.automode = 2
            if self.automode == 2:  # Scan in front of rover at an arch from left to right recording values
                if self.nav.readPot() > self.nav.get_pot_right():
                    self.nav.appendScannedHeadings()
                    rightheading = (self.nav.getMag() + 40) % 360
                    return 0, self.nav.calculateDesiredTurn(self.nav.getMag(), rightheading)
                else:
                    self.nav.addDestination()  # Get a new heading and add a temp value to coordinate list
                    self.automode = 0  # start driving in auto normally
        else:
            return self.r_comms.receivedDrive[1], self.r_comms.receivedDrive[2]

    # returns automatic drive parms from gps, mag, sonar and destination
    # TODO: figure out a way to change throttle while on autopilot?
    def getAutoDriveParms(self):
        # print self.getGPS()
        return 10, self.nav.calculateDesiredTurn(self.nav.getMag(), self.nav.calculateDesiredHeading())

    # returns a tuple of (motor1, motor2, motor3, motor4) from the driveParms modified by the pot reading
    def convertParmsToMotorVals(self, driveParms):
        potReading = self.nav.readPot()
        if potReading != -1:
            # Potentiometer is good. Run PID.
            self.setPIDTarget(self.pot_pid, int(driveParms[1]), -100, 100)
            scaledPotReading = Utils.translateValue(potReading, self.nav.get_pot_left() - self.nav.get_pot_middle(), \
                                                    self.nav.get_pot_right() - self.nav.get_pot_middle(), 100, -100)
            self.pot_pid.run(scaledPotReading)
            finalTurn = self.pot_pid.getOutput()
            print str(driveParms)
            result = (self.scale_motor_val(driveParms[0] + finalTurn),
                      self.scale_motor_val(driveParms[0] - finalTurn),
                      self.scale_motor_val(driveParms[0] - finalTurn),
                      self.scale_motor_val(driveParms[0] + finalTurn))
            return result
        else:
            print "Pot Error"
            # Potentiometer error
            # reset PID:
            self.pot_pid.setTarget(0)
            print str(driveParms)
            result = (self.scale_motor_val(driveParms[0] + driveParms[1]),
                      self.scale_motor_val(driveParms[0] - driveParms[1]),
                      self.scale_motor_val(driveParms[0] - driveParms[1]),
                      self.scale_motor_val(driveParms[0] + driveParms[1]))
            print str(result)
            return result

    @staticmethod
    def setPIDTarget(pid, inputVal, minVal, maxVal):
        if inputVal < minVal or inputVal > maxVal:
            pid.setTarget(0)
        elif pid.getTarget() != inputVal:
            pid.setTarget(inputVal)

    # a monotonically increasing function with output of -256 < x < 256
    # scales the motor value for driving the motors so that it never has a value outside of the safe range
    @staticmethod
    def scale_motor_val(val):
        return math.atan(val / 40) * (255 * 2 / math.pi)

    def get_robot_comms(self):
        return self.r_comms

    def get_nav(self):
        return self.nav


class DriveParams:
    """
    Object to hold drive parameters, so that only one thread can access it
    at a time.

    Attributes:
        throttle, turn (float): The current drive parameters
        is_stopped (bool): Whether the robot should be stopped.
        lock (threading.Lock): The lock that protects the data.
    """
    def __init__(self):
        self.throttle = 0.0
        self.turn = 0.0
        self.is_stopped = False
        self.lock = threading.Lock()

    def set(self, throttle, turn):
        """
        Args:
            throttle, turn (float)
        """
        with self.lock:
            self.throttle = float(throttle)
            self.turn = float(turn)

    def stop(self):
        """
        Use this method when you want to stop the robot.
        """
        with self.lock:
            self.is_stopped = True

    def get(self):
        """
        Returns:
            either tuple of (float, float) or None: The throttle and turn, or
                None if the robot should be stopped.
        """
        with self.lock:
            if self.is_stopped:
                temp = None
            else:
                temp = self.throttle, self.turn
        return temp


class DriveThread(threading.Thread):
    """
    Thread that continuously reads the throttle and turn from a DriveParams
    object and makes the robot move accordingly.

    Attributes:
        robot (Robot): Object for controlling the robot.
        drive_params (DriveParams): Read the throttle and turn from this object.
    """
    def __init__(self, drive_params, is_using_big_motor):
        super(DriveThread, self).__init__()
        self.robot = Robot(is_using_big_motor)
        self.drive_params = drive_params

    def run(self):
        """
        Overrides a method in threading.Thread. Do not call this method
        directly; use start() instead.
        """
        while True:
            drive_params = self.drive_params.get()
            if drive_params is None:
                break
            motor_params = self.robot.convertParmsToMotorVals(drive_params)
            for i in range(1, 5):
                self.robot.driveMotor(i, motor_params[i - 1])
        for i in range(1, 5):
            self.robot.stopMotor(i)


def main():
    choice = raw_input('Control robot with keyboard? (y/n) ')
    if choice[0] == 'y':
        drive_params = DriveParams()
        drive_thread = DriveThread(drive_params, sys.argv[1])
        drive_thread.start()
        print 'Enter throttle followed by turn, separated by spaces.'
        print 'For turn, 100 is full right, -100 is full left.'
        try:
            while True:
                in_str = raw_input('input: ')
                in_list = in_str.split()
                throttle = float(in_list[0])
                turn = float(in_list[1])
                drive_params.set(throttle, turn)
        except KeyboardInterrupt:
            drive_params.stop()
            drive_thread.join()
    else:
        robot = Robot(sys.argv[1])
        try:
            while True:
                robot.get_robot_comms().receiveData(robot.get_nav())
                robot.get_robot_comms().sendData(robot.get_nav())
                driveParms = robot.getDriveParms()
                MotorParms = robot.convertParmsToMotorVals(driveParms)
                for i in range(1, 5):
                    robot.driveMotor(i, MotorParms[i - 1])

        except KeyboardInterrupt:
            for i in range(1, 5):
                try:
                    robot.stopMotor(i)
                except:
                    print("motor: " + str(i) + " disconnected")
            robot.r_comms.closeConn()
            print "exiting"

if __name__ == "__main__":
    main()
