import socket
import struct


class test_send:

    def __init__(self):
        #ADC.setup()
        # setup i2c to motorshield
        # Potentiometer pin:
        self.POT_PIN = "AIN2"
        self.POT_LEFT = 0.771
        self.POT_RIGHT = 0.346
        self.POT_MIDDLE = (self.POT_LEFT + self.POT_RIGHT) / 2
        self.POT_TOL = 0.01
        # autopilot
        self.auto = True
        # list of GPS coords to travel to
        self.destinations = []
        self.receivedDrive = None
        self.robot_ip = "192.168.0.60"
        self.receive_port = 8840
        self.send_port = 8000
        self.base_station_ip = None
        self.driveFormat = "<??hh"
        self.gpsFormat = "<?hhhhhh"
        self.rtbFormat = "<fffffhhhhhh"
        self.sock = socket.socket(socket.AF_INET,  # Internet
                                socket.SOCK_DGRAM)  # UDP
        self.sock.bind((self.robot_ip, self.receive_port))
        self.sock2 = socket.socket(socket.AF_INET,  # Internet
                                socket.SOCK_DGRAM)
        self.sock2.bind((self.robot_ip, self.send_port))
        self.sock.setblocking(False)
        self.sock2.setblocking(False)
        self.bound = False

    def receiveData(self):
        try:
            data, addr = self.sock.recvfrom(1024)  # buffer size is 1024 bytes
            self.base_station_ip = addr
            self.bound = True
            unpacked = struct.unpack(self.driveFormat, data)
            if unpacked[0]:
                self.receivedDrive = unpacked[1:]
            else:
                unpacked = struct.unpack(self.gpsFormat, data)
                self.destinations.append(unpacked[1:])
            print unpacked
        except:
            pass

    # sends data in message back to the base station
    def sendData(self):
        if self.bound:
            MESSAGE = struct.pack(self.rtbFormat, 10, 9, 1, 2, 3, 4, 1.0, 2.0, 3.0, 4.0, 5.0)
            print MESSAGE
            print self.base_station_ip
            print self.send_port
            self.sock2.sendto(MESSAGE, (self.base_station_ip[0], self.send_port))
        pass
        # TODO: do this
        # read data from sensors or read class variables
def main():
    robot = test_send()
    try:
        while True:
            robot.receiveData()
            robot.sendData()
    except KeyboardInterrupt:
        print "exiting"

main()
