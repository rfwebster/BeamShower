# -*- coding: utf-8 -*-
"""
Created on 2021-11-13

@author: rfwebster
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QTimer
from PyQt5.QtTest import QTest
from ui.beamshower import Ui_MainWindow

import math

_status = 0  # online
try:
    from PyJEM import detector, TEM3
    TEM3.connect()
except(ImportError):
    from PyJEM.offline import detector, TEM3
    _status = 1  # offline

lens = TEM3.Lens3()
deflector = TEM3.Def3()
eos = TEM3.EOS3()
det = TEM3.Detector3()
apt = TEM3.Apt3()


class Window(QMainWindow, Ui_MainWindow):
    TIME_LIMIT = 15*60*1000

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.startButton.clicked.connect(self.go)

        self.cl1 = 1000
        self.cl2 = 1000
        self.cl3 = 1000
        self.bk_cl1 = 0
        self.bk_cl2 = 0
        self.bk_cl3 = 0

        try:
            self.probe_size = eos.GetSpotSize()
        except Exception as e:
            print('Error getting spot size:', e)

        # determine inserted detectors:
        self.inserted_detectors = []
        for d in detector.get_attached_detector():
            if det.GetPosition(d) == 1:
                self.inserted_detectors.append(d)
        print("Inserted Detectors: {}".format(self.inserted_detectors))

        self.time = self.TIME_LIMIT
        self.time_count = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.countdown)

    def countdown(self):
        """
        counts down from the self.time and updates the progress bar
        when finihed resets the TEM condtions
        :return:
        """
        self.time_count += 1000
        value = int(self.time_count/self.time * 100)

        time_remaining = int(self.time-self.time_count)
        mins = math.floor((time_remaining / 1000) / 60)
        secs = int((time_remaining / 1000) % 60)
        if value < 100:
            self.progressBar.setValue(value)
            self.progressBar.setFormat("Time Remaining: {:2} : {:2}".format(mins, secs))
        else:
            self.progressBar.setValue(100)
            self.timer.stop()
            # reset TEM
            self.reset()
            self.statusBar.showMessage("Start Beam Shower")
            self.progressBar.setFormat("")
            self.startButton.setEnabled(True)

    def go(self):
        """
        Runs the program
            - Saves the current conditions
            - Blanks the beam
            - Sets the probe size to 5/4
            - Sets the CL lens values for beam shower
            - Removes detectors
            - Blanks beam under the sample (using deflectors)
            - Unblanks B
        run
        :return:
        """
        self.startButton.setDisabled(True)
        self.save_cl_values()
        self.blank_beam(True)
        self.statusBar().showMessage("Blanking Beam")
        QTimer.singleShot(2000, lambda: None)
        self.get_conditions()
        self.statusBar().showMessage("Setting Lenses")
        QTimer.singleShot(2000, lambda: None)
        eos.SelectSpotSize(4)  # set spot size 4
        self.set_cl_values()
        self.statusBar().showMessage("Removing Detectors")
        self.remove_detectors()
        QTimer.singleShot(2000, lambda: None)
        self.statusBar().showMessage("Inserting OL and SA Apertures")
        self.insert_aperture(2, 4)
        self.insert_aperture(4, 4)
        QTimer.singleShot(2000, lambda: None)
        self.statusBar().showMessage("Remove CL Aperture")
        self.remove_aperture(1, 0)
        QTimer.singleShot(2000, lambda: None)
        self.statusBar().showMessage("Lowering Screen")
        det.SetScreen(0)
        QTimer.singleShot(2000, lambda: None)
        self.blank_beam(False)
        self.startButton.setText("Running Beam Shower")

        print(self.time)
        # wait for the time and do the progress bar and label
        self.timer.start(1000)

    def get_conditions(self):
        """
        Gets conditions from the UI
        TODO: make relative change
        :return:
        """
        self.time = int(self.time_spinBox.text())*60*1000
        self.cl1 = int(self.CL1_spinBox.text(), 16)
        print(self.cl1)
        self.cl2 = int(self.CL2_spinBox.text(), 16)
        self.cl3 = int(self.CL3_spinBox.text(), 16)

        return

    def save_cl_values(self):
        """
        Saves the orignal CL values to a file as a backup
        :return:
        """
        self.bk_cl1 = lens.GetCL1()
        self.bk_cl2 = lens.GetCL2()
        self.bk_cl3 = lens.GetCL3()
        txt = "cl1:{}\n" \
              "cl2:{}\n" \
              "cl3:{}".format(self.bk_cl1, self.bk_cl2, self.bk_cl3)
        print(txt)
        with open("cl-values.txt", "w") as f:
            f.write(txt)

    def blank_beam(self, blank):
        """
        Blanks Beam if input is True
        :param blank:
        :return:
        """
        if blank is True:
            # blank beam
            deflector.SetBeamBlank(1)
        else:
            # un-blank beam
            deflector.SetBeamBlank(0)

    def set_cl_values(self):
        """
        Sets the condensor lens values to those used for the beam shower
        TODO - work for more than one spot size
        TODO: make relative change - need to find out what the relative values are
        :return:
        """
        lens.SetFLCAbs(0, self.cl1)
        lens.SetFLCAbs(1, self.cl2)
        lens.SetFLCAbs(2, self.cl3)

    def insert_aperture(self,k,s):
        apt.SelectKind(k)
        apt.SetSize(s)

    def remove_aperture(self,k,s):
        apt.SelectKind(k)
        apt.SetSize(s)

    def remove_detectors(self):
        """
        Removes all detectors
        :return:
        """
        for d in self.inserted_detectors:
            det.SetPosition(d, 1)
        det.SetScreen(0)

    def insert_detectors(self):
        """
        Inserts all detectors
        :return:
        """
        for d in self.inserted_detectors:
            det.SetPosition(d, 1)
        det.SetScreen(2)

    def reset(self):
        """
        Resets all deflectors, apertutres and detectors to orignal values
        :return:
        """
        self.blank_beam(True)
        self.statusBar().showMessage("Resetting Lenses")
        lens.SetFLCSwAllLens(0)
        eos.SelectSpotSize(self.probe_size)
        QTimer.singleShot(2000, lambda: None)
        self.statusBar().setText("")
        self.statusBar().showMessage("Inserting Detectors")
        self.insert_detectors()
        QTimer.singleShot(2000, lambda: None)

        self.statusBar().showMessage("Removing SA and OL Apertures")
        self.remove_aperture(2, 0)
        self.remove_aperture(4, 0)
        QTimer.singleShot(2000, lambda: None)
        self.blank_beam(False)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    win = Window()
    win.show()
    sys.exit(app.exec())