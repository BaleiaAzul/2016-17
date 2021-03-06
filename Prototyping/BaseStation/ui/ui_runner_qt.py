from PyQt4 import QtGui, uic
import sys
from ui_components.map import Map
from ui_components.ip_scanner import IPCheckerLayout
from ui_components.camera_streaming import UI
from ui_components.emergency_stop import stop
from ui_components.settings import settings
from ui_components import Command, comms_update
from ui_components.arm_viz import arm_widget
from ui_components.sensors import SensorChecker
from ui_components.list_widget import list_widget
from ui_components.auto_indicator import auto


def quitting():
    # Close all open sockets
    sock.shutdown()
    # Shutdown the networking thread
    iplist.worker_thread.quit()
    # Save the changes to the settings by the user
    setting_widget.save()


# Specifying the new PyQt4 applicataion and main window
app = QtGui.QApplication(sys.argv)

# Call this function when we are about to quit
app.aboutToQuit.connect(quitting)
win = QtGui.QMainWindow()

# Load the UI into the main window
main = uic.loadUi("ui.ui", win)

win.resize(1200, 675)

'''Create all the custom widgets for the UI'''
sensors = SensorChecker.SensorData()
sock = comms_update.CommsUpdate()
setting_widget = settings.Settings(main)
stop_widget = stop.Stop()

vlc_widget = UI.Player(setting_widget.get_camera_urls(), 300, 200)
iplist = IPCheckerLayout.IPList({"192.168.0.22": "Camera One", "192.168.0.42": "Camera Two"}, 500)
arm = arm_widget.arm_widget()
list_wid = list_widget.ListWidget()
map = Map.Map(setting_widget.get_map_name())
command_line = Command.command(map, sock, list_wid)
auto_lab = auto.Auto()

'''Add all the custom widgets to the UI containers'''
# Create the emergency stop button
main.stop_container.addWidget(stop_widget)
# Shows the video streams in their own windows of size 300x200 px
main.camera_container.addWidget(vlc_widget)
# Updates IP state every 50 milliseconds. Maps the name to the status.
main.sensor_container.addWidget(iplist)
# Add the arm visualization
main.joystick_container.addWidget(arm)
# Add the sensor reading widget
main.reading_container.addWidget(sensors)
# Add the map to the ui
main.map_container.addWidget(map)
# Add the command line to the ui
main.map_container.addWidget(command_line)
# Add the marker list view to the ui
main.list_container.addWidget(list_wid)
# Add the label that indicates autonomous mode to the ui
main.list_container.addWidget(auto_lab)

'''Connect all events for each of the components to talk to one another'''
command_line.signalStatus.connect(sock.send_auto_mode)
list_wid.signalStatus.connect(command_line.update)
sock.signalStatus.connect(sensors.update_ui)
sock.signalUpdate.connect(map.update_rover_pos)
command_line.autoTrigger.connect(auto_lab.toggle_ui)
map.signal.connect(list_wid.add_to_ui)
stop_widget.stopEvent.connect(sock.stopping)
list_wid.callToDelete.connect(map.remove_marker)
list_wid.highlightMarker.connect(map.highlight_marker)


# Show window and execute the app
win.show()

sys.exit(app.exec_())
