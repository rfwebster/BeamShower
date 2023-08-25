import threading
import logging
import sys
import tkinter as tk
from tkinter import ttk
import tkinter.font as font
import math
from threading import  Thread, Event, Timer
_status = 0  # online
try:
    from PyJEM import detector, TEM3
    TEM3.connect()
except ImportError:
    from PyJEM.offline import detector, TEM3
    _status = 1  # offline

lens = TEM3.Lens3()
deflector = TEM3.Def3()
eos = TEM3.EOS3()
det = TEM3.Detector3()
apt = TEM3.Apt3()


'''
A class representing a GUI window for controlling an electron beam shower application.

The Window class provides a graphical user interface for setting up the conditions for a beam shower and starting the beam shower process. It includes various UI elements such as labels, spinboxes, buttons, a progress bar, and a status bar.

Main functionalities of the Window class include:
- Setting up the UI with labels, spinboxes, buttons, and a progress bar
- Getting user input for time and CL values
- Saving the current CL values
- Blanking the beam
- Setting the lenses with the user input CL values
- Removing detectors and inserting apertures
- Starting the beam shower and updating the progress bar
- Stopping the beam shower
- Resetting the lenses, removing apertures, and inserting detectors

'''
class Window(tk.Tk):
    TIME_LIMIT = 15 * 60 * 1000
    TIME_INCREMENT = 100

    def __init__(self):
        super().__init__()
        self.title('Beam Shower')
        self.geometry('300x380')
        self.setup_ui()

        self.bk_cl1 = 0
        self.bk_cl2 = 0
        self.bk_cl3 = 0

        try:
            self.probe_size = eos.GetSpotSize()
        except Exception as e:
            logging.error('Error getting spot size', exc_info=True)

        # determine inserted detectors:
        self.detectors = []
        for det in detector.get_attached_detector():
            self.detectors.append(det)
        logging.info('Inserted Detectors: %s', self.detectors)

        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # Set the callback for window close event





    def setup_ui(self):
        normal_fonts = font.Font(family='Helvetica', size=12)
        bold_fonts = font.Font(family='Helvetica', size=12, weight='bold')

        PAD_X = 10
        PAD_Y = 8

        TIME_MIN = 0
        TIME_MAX = 90
        TIME_INCREMENT = 1
        CL_MIN = 0
        CL_MAX = 65535
        CL_INCREMENT = 16

        TIME_DEFAULT = 10
        CL1_DEFAULT = 0
        CL2_DEFAULT = 65535
        CL3_DEFAULT = 16



        self.time_var = tk.IntVar(value=TIME_DEFAULT)
        self.CL1_var = tk.IntVar(value=CL1_DEFAULT)
        self.CL2_var = tk.IntVar(value=CL2_DEFAULT)
        self.CL3_var = tk.IntVar(value=CL3_DEFAULT)

        self.centralwidget = ttk.Frame(self)
        self.centralwidget.pack(fill=tk.BOTH, expand=False)

        self.label_set = ttk.Label(self.centralwidget, text='Set Conditions:', font=bold_fonts)
        self.label_set.pack(pady=PAD_Y)

        self.form_frame = ttk.Frame(self.centralwidget)
        self.form_frame.pack(padx=10, pady=5)

        self.time_label = ttk.Label(self.form_frame, text='Time (min)')
        self.time_label.grid(row=0, column=0, padx=PAD_X, pady=PAD_Y)

        self.time_spinbox = ttk.Spinbox(self.form_frame, textvariable=self.time_var,
                                        from_=TIME_MIN, to=TIME_MAX, increment=TIME_INCREMENT,
                                        font=normal_fonts, justify=tk.CENTER, width=10)
        self.time_spinbox.grid(row=0, column=1, padx=PAD_X, pady=PAD_Y)

        self.CL1_label = ttk.Label(self.form_frame, text='CL1')
        self.CL1_label.grid(row=1, column=0, padx=PAD_X, pady=PAD_Y)

        self.CL1_spinbox = ttk.Spinbox(self.form_frame, textvariable=self.CL1_var,
                                        from_=CL_MIN, to=CL_MAX, increment=CL_INCREMENT,
                                        font=normal_fonts, justify=tk.CENTER, width=10)
        self.CL1_spinbox.grid(row=1, column=1, padx=PAD_X, pady=PAD_Y)

        self.CL2_label = ttk.Label(self.form_frame, text='CL2')
        self.CL2_label.grid(row=2, column=0, padx=PAD_X, pady=PAD_Y)

        self.CL2_spinbox = ttk.Spinbox(self.form_frame, textvariable=self.CL2_var,
                                        from_=CL_MIN, to=CL_MAX, increment=CL_INCREMENT,
                                        font=normal_fonts, justify=tk.CENTER, width=10)
        self.CL2_spinbox.grid(row=2, column=1, padx=PAD_X, pady=PAD_Y)

        self.CL3_label = ttk.Label(self.form_frame, text='CL3')
        self.CL3_label.grid(row=3, column=0, padx=PAD_X, pady=PAD_Y)

        self.CL3_spinbox = ttk.Spinbox(self.form_frame, textvariable=self.CL3_var,
                                        from_=CL_MIN, to=CL_MAX, increment=CL_INCREMENT,
                                        font=normal_fonts, justify=tk.CENTER, width=10)
        self.CL3_spinbox.grid(row=3, column=1, padx=PAD_X, pady=PAD_Y)

        self.start_button = ttk.Button(self.centralwidget, text='Start Beam Shower', command=self.start_beam_shower,
                                        width=20)
        self.start_button.pack(pady=PAD_Y)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.centralwidget, orient='horizontal', length=200, mode='determinate',
                                            variable=self.progress_var)
        self.progress_bar.pack(pady=PAD_Y)

        self.status_bar = ttk.Label(self, text='', anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    def on_closing(self):
        self.stop_beam_shower()  # Stop the beam shower if running
        self.destroy()  # Close the window

    def start_beam_shower(self):
        self.save_cl_values()
        self.blank_beam(True)
        self.status_bar_message('Blanking Beam')
        self.after(2000, lambda: None)
        self.get_conditions()
        self.status_bar_message('Setting Lenses')
        self.after(2000, lambda: None)
        eos.SelectSpotSize(4)
        self.set_cl_values()
        self.status_bar_message('Removing Detectors')
        self.remove_detectors()
        self.after(2000, lambda: None)
        self.status_bar_message('Inserting OL and SA Apertures')
        self.insert_aperture(2, 4)
        self.insert_aperture(4, 4)
        self.after(2000, lambda: None)
        self.status_bar_message('Remove CL Aperture')
        self.remove_aperture(1, 0)
        self.after(2000, lambda: None)
        self.status_bar_message('Lowering Screen')
        det.SetScreen(0)
        self.after(2000, lambda: None)
        self.blank_beam(False)
        self.status_bar_message('Running Beam Shower')
        self.start_button.config(state=tk.NORMAL)
        self.start_button.config(text="Stop Beam Shower")
        self.start_button.config(command=self.stop_beam_shower)
        
        # Start the beam shower in a new thread using threading.Timer
        self.beam_shower_thread = Timer(0, self.run_beam_shower)
        self.beam_shower_thread.start()

    def run_beam_shower(self):
        try:         
            # Update progress bar while the beam shower is running
            total_steps = int(self.time / self.TIME_INCREMENT)
            for step in range(total_steps):
                if hasattr(self, 'beam_shower_thread') and not self.beam_shower_thread.is_alive():
                    self.beam_shower_thread.cancel()  # Stop the beam shower thread
                    break  # Stop the loop if the beam_shower_thread has been stopped
                progress_percentage = (step / total_steps) * 100
                self.progress_var.set(progress_percentage)
                self.update_idletasks()
                threading.Event().wait(timeout=self.TIME_INCREMENT / 1000)  # Sleep for the desired interval
        finally:
            self.progress_var.set(100)  # Ensure progress bar is set to 100% even if beam shower was stopped abruptly

        # Beam shower is complete or stopped, reset UI and thread
        self.reset()

    def stop_beam_shower(self):
        if hasattr(self, 'beam_shower_thread') and self.beam_shower_thread.is_alive():
            self.beam_shower_thread.cancel()  # Stop the beam shower thread
            self.reset()


    def get_conditions(self):
        self.time = int(self.time_spinbox.get(), 10) * 60 * 1000
        self.cl1 = int(self.CL1_spinbox.get(), 16)
        logging.info(self.cl1)
        self.cl2 = int(self.CL2_spinbox.get(), 16)
        self.cl3 = int(self.CL3_spinbox.get(), 16)

        return

    def save_cl_values(self):
        self.bk_cl1 = lens.GetCL1()
        self.bk_cl2 = lens.GetCL2()
        self.bk_cl3 = lens.GetCL3()
        txt = f'cl1:{self.bk_cl1}\n' \
              f'cl2:{self.bk_cl2}\n' \
              f'cl3:{self.bk_cl3}'
        logging.info(txt)
        with open('cl-values.txt', 'w') as f:
            f.write(txt)

    def blank_beam(self, blank):
        if blank is True:
            deflector.SetBeamBlank(1)
        else:
            deflector.SetBeamBlank(0)

    def set_cl_values(self):
        lens.SetFLCAbs(0, self.cl1)
        lens.SetFLCAbs(1, self.cl2)
        lens.SetFLCAbs(2, self.cl3)

    def insert_aperture(self, k, s):
        apt.SelectKind(k)
        apt.SetSize(s)

    def remove_aperture(self, k, s):
        apt.SelectKind(k)
        apt.SetSize(s)

    def remove_detectors(self):
        for d in range(len(self.detectors)):
            det.SetPosition(d, 1)
        det.SetScreen(0)

    def insert_detectors(self):
        for d in range(len(self.detectors)):
            det.SetPosition(d, 1)
        det.SetScreen(2)

    def reset(self):
        self.blank_beam(True)
        self.status_bar_message('Resetting Lenses')
        lens.SetFLCSwAllLens(0)
        eos.SelectSpotSize(self.probe_size)
        self.after(2000, lambda: None)
        self.status_bar_message('')
        self.status_bar_message('Inserting Detectors')
        self.insert_detectors()
        self.after(2000, lambda: None)

        self.status_bar_message('Removing SA and OL Apertures')
        self.remove_aperture(2, 0)
        self.remove_aperture(4, 0)
        self.after(2000, lambda: None)
        self.blank_beam(False)

        self.start_button.config(text="Start Beam Shower")
        self.start_button.config(command=self.start_beam_shower)
        self.status_bar_message('Beam Shower Finished!')

    def status_bar_message(self, message):
        self.status_bar.config(text=message)

    def __del__(self):
        self.stop_beam_shower()

if __name__ == '__main__':
    app = Window()
    app.mainloop()
