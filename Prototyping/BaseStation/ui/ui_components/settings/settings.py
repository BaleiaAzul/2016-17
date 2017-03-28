from PyQt4 import QtCore
from ..map import Generator
import math

"""
Operate the settings page in the main ui
Reads from .settings on startup and writes over .settings on shutdown
"""


class Settings:
    def __init__(self, ui):
        self.main = ui

        self.cam_list = []

        self.main.generate.clicked.connect(self.generate_new_map)

        # Connect map generation updates
        self.main.tile_size.valueChanged.connect(self.update_ui)
        self.main.tile_15.textEdited.connect(self.update_ui)
        self.main.tile_16.textEdited.connect(self.update_ui)
        self.main.tile_17.textEdited.connect(self.update_ui)
        self.main.tile_18.textEdited.connect(self.update_ui)
        self.main.tile_19.textEdited.connect(self.update_ui)
        self.main.api_select.currentIndexChanged.connect(self.update_ui)

        self.setup()

    def update_ui(self):
        if self.main.api_select.currentText().compare("Bing") == 0:
            self.main.tile_size.setMaximum(1500)
        else:
            self.main.tile_size.setMaximum(640)
        self.main.tile_size_label.setText(str(self.main.tile_size.value()) + " px")
        zoom15 = 4.7773
        zoom16 = 2.3887
        zoom17 = 1.1943
        zoom18 = 0.5972
        zoom19 = 0.2968

        distance15 = "{0:.2f}".format((int(self.main.tile_size.value()) * math.sqrt(int(self.main.tile_15.text())) * zoom15) / 1000)
        distance16 = "{0:.2f}".format((int(self.main.tile_size.value()) * math.sqrt(int(self.main.tile_16.text()) * zoom16)) / 1000)
        distance17 = "{0:.2f}".format((int(self.main.tile_size.value()) * math.sqrt(int(self.main.tile_17.text()) * zoom17)) / 1000)
        distance18 = "{0:.2f}".format((int(self.main.tile_size.value()) * math.sqrt(int(self.main.tile_18.text()) * zoom18)) / 1000)
        distance19 = "{0:.2f}".format((int(self.main.tile_size.value()) * math.sqrt(int(self.main.tile_19.text()) * zoom19)) / 1000)

        self.main.tile_15_label.setText(str(distance15) + " km")
        self.main.tile_16_label.setText(str(distance16) + " km")
        self.main.tile_17_label.setText(str(distance17) + " km")
        self.main.tile_18_label.setText(str(distance18) + " km")
        self.main.tile_19_label.setText(str(distance19) + " km")

    def generate_new_map(self):
        name = self.main.map_name.text()
        lat = self.main.lat.text()
        lng = self.main.lng.text()
        tile_size = self.main.tile_size.value()
        api = self.main.api_select.itemText(self.main.api_select.currentIndex())
        zoom15 = self.main.tile_15.text()
        zoom16 = self.main.tile_16.text()
        zoom17 = self.main.tile_17.text()
        zoom18 = self.main.tile_18.text()
        zoom19 = self.main.tile_19.text()


        # Generate a new map
        arr = [zoom15, zoom16, zoom17, zoom18, zoom19]
        g = Generator.Generator(tile_size, api, arr)
        result = g.generate_maps(name, lat, lng)
        # result = self.comm.generate_new_map(name, lat, lng, tile_size, api, zoom15, zoom16, zoom17, zoom18, zoom19)

        # If we generated successfully (user data is validated)
        if result:
            self.main.map_name.setText("")
            self.main.lat.setText("")
            self.main.lng.setText("")

    # Utility function to get the default map name
    def get_map_name(self):
        return self.main.map_val.text()

    # Get the urls that each feed is set to on startup
    def get_camera_urls(self):
        temp = []

        temp.append(self.cam_list[self.main.cam1.currentIndex()])
        temp.append(self.cam_list[self.main.cam2.currentIndex()])
        temp.append(self.cam_list[self.main.cam3.currentIndex()])

        return temp

    # Saves the current state of the settings page except for generation of new map form
    def save(self):
        # Write over the settings file
        f = open(".settings", "w")
        # Write the map name we will open on startup (not validated)
        f.write("default_map=" + str(self.main.map_val.text()) + "\n")

        output = "cams="
        for i in range(0, len(self.cam_list)):
            if i == len(self.cam_list) - 1:
                output += self.main.cam1.itemText(i) + "," + self.cam_list[i] + "\n"
            else:
                output += self.main.cam1.itemText(i) + "," + self.cam_list[i] + ","

        f.write(output)

        # Write the currently selected camera for each feed
        f.write("default_cam_1=" + str(self.main.cam1.currentIndex()) + "\n")
        f.write("default_cam_2=" + str(self.main.cam2.currentIndex()) + "\n")
        f.write("default_cam_3=" + str(self.main.cam3.currentIndex()) + "\n")

        f.close()

    def setup(self):
        # Read settings from the settings file
        f = open(".settings", "r")

        # Read in map value
        self.main.map_val.setText(f.next().strip('\n').split("=")[1])

        # Read in the list of cameras and their friendly names
        camStr = f.next().strip('\n').split("=", 1)[1]
        # Cam list alternates friendly name, file location, name...
        camList = camStr.split(",")

        list = QtCore.QStringList()

        for i in range(0, len(camList)):
            if i % 2 == 0:
                # Add the names of the cameras
                list.append(camList[i])
            else:
                # Add the URLS to the list
                self.cam_list.append(camList[i])

        # Add the options to the selection boxes
        self.main.cam1.addItems(list)
        self.main.cam2.addItems(list)
        self.main.cam3.addItems(list)

        # Read in default indices of the select boxes
        self.main.cam1.setCurrentIndex(int(f.next().strip('\n').split("=")[1]))
        self.main.cam2.setCurrentIndex(int(f.next().strip('\n').split("=")[1]))
        self.main.cam3.setCurrentIndex(int(f.next().strip('\n').split("=")[1]))

        f.close()


