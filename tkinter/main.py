
import tkinter as tk
from tkinter import ttk
import tkinter.font as font
import time

#######################################################################
pause_apt = 1.8 # time to wait (in s) after inserting/removing apertures
pause_det = 1.8 # time to wait (in s) after inserting/removing detectors
CL1_val = 20000 # CL1 value to set
CL2_val = 20000 # CL2 value to set
CL3_val = 20000 # CL3 value to set
#######################################################################

_status = 0  # online
try:
    from PyJEM import detector, TEM3
    TEM3.connect()
except ImportError:
    from PyJEM.offline import detector, TEM3
    _status = 1  # offline

lens = TEM3.Lens3()
defl = TEM3.Def3()
eos = TEM3.EOS3()
det = TEM3.Detector3()
apt = TEM3.Apt3()

# get the attached detectors
global detectors
detectors = []
for d in detector.get_attached_detector():
    detectors.append(d)
print(f'Detectors Configuration: {detectors}')


def blank_beam(blank):
    """
    Blanks beam using  the in-built beam blanker.
    """
    if blank is True:
        defl.SetBeamBlank(1)
        print("beam blanked")

    else:
        defl.SetBeamBlank(0)
        print("beam unblanked")

def IL_blank(blank):
    """
    Blanks beam below the specimen using the IL deflector 2.
    """
    if blank is True:
        defl.SetFLA2(65535,65535)
        #defll.SetIS2(65535,65535) # other option to test on F200
        print("IL blanked")

    else:
        defl.SetNtrl(17) # for FLA2 (which I assume is IL deflector 2)
        print("IL unblanked")

def lower_screen():
    det.SetScreen(0)
    time.sleep(2)

def insert_aperture(k, s):
    """
    Inserts an aperture of kind k and size s.
    """
    print("inserting aperture {} with size {}".format(k, s))
    try:
        apt.SelectKind(k)
        apt.SetSize(s)
        time.sleep(pause_apt)
    except Exception as e:
        print("Error: {}\n".format(e))
    else: return

    try:
        print("Trying extended apertures")
        apt.SelectExpKind(k)
        apt.SetExpSize(s)
        time.sleep(pause_apt)
    except Exception as e:
        print("Error: {}".format(e))
    else: return

def remove_aperture(k, s):
    """
    Removes an aperture of kind k and size s.
    """
    print("removing aperture {} with size {}".format(k, s))

    try:
        apt.SelectKind(k)
        apt.SetSize(0)
        time.sleep(pause_apt)
    except Exception as e:
        print("Error: {}\n".format(e))
    else: return

    try:
        print("Trying extended apertures")
        apt.SelectExpKind(k)
        apt.SetExpSize(0)
        time.sleep(pause_apt)
    except Exception as e:
        print("Error: {}".format(e))
    else: return


def insert_detectors():
    """
    Inserts all detectors.
    """
    global detectors
    for d in detectors:
        det.SetPosition(d, 1)
        print("inserting detector {}".format(d))
        time.sleep(pause_det)

    det.SetScreen(1)

def remove_detectors():
    """
    Removes all detectors.
    """
    global detectors
    for d in detectors:
        det.SetPosition(d, 0)
        print("removing detector {}".format(d))
        time.sleep(pause_det) # 

    det.SetScreen(0)




class BeamShowerApp(tk.Tk):
    """
    A class giving a GUI window for controlling an electron beam shower application.
    """
    time_increment = 1/60

    def __init__(self):
        """
        Initializes the Window class and sets up the UI.
        """
        super().__init__()
        self.title('Beam Shower')
        #self.geometry('300x380')
        self.setup_ui()
        self.configure(bg="black")

        self.save_TEM_conditions()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # Set the callback for window close event


    def setup_ui(self) -> None:
        normal_fonts = font.Font(family='Helvetica', size=12)
        bold_fonts = font.Font(family='Helvetica', size=12, weight='bold')

        style = ttk.Style()
        # Set the background color to black and text color to light green
        style.configure('TLabel', background='black', foreground='light green')

        padx = 10
        pady = 8

        time_min = 1
        time_max = 90
        time_step = 1
        time_default = 10
        self.stop_beam_shower_flag = False
        self.num_start_button_clicks = 0

        self.time_var = tk.IntVar(value=time_default)

        self.centralwidget = ttk.Frame(self,style='TLabel')
        self.centralwidget.pack(fill=tk.BOTH, expand=False)

        self.label_set = ttk.Label(self.centralwidget, text='Set Conditions:', font=bold_fonts, 
                                   style='TLabel')
        self.label_set.pack(pady=pady)

        self.form_frame = ttk.Frame(self.centralwidget,style='TLabel')
        self.form_frame.pack(padx=padx, pady=pady)

        self.time_label = ttk.Label(self.form_frame, text='Time (min)',
                                    style='TLabel')
        self.time_label.grid(row=0, column=0, padx=padx, pady=pady)

        self.time_spinbox = ttk.Spinbox(self.form_frame, textvariable=self.time_var,
                                        from_=time_min, to=time_max, increment=time_step,
                                        font=normal_fonts, justify=tk.CENTER, width=10)
        self.time_spinbox.grid(row=0, column=1, padx=padx, pady=pady)

        self.start_button = ttk.Button(self.centralwidget, text='Start Beam Shower', command=self.start_beam_shower,
                                        width=20)
        self.start_button.pack(pady=pady)

        self.progress_var = tk.DoubleVar()
        
        self.progress_bar = ttk.Progressbar(self.centralwidget, orient='horizontal', length=200, mode='determinate',
                                            variable=self.progress_var)
        self.progress_bar.pack(pady=pady)

        self.status_bar = ttk.Label(self, text='', anchor=tk.W,
                                    style='TLabel')
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def on_closing(self) -> None:
        self.stop_beam_shower()  # Stop the beam shower if running
        self.reset_conditions()  # Reset the conditions
        self.destroy()  # Close the window

    def start_beam_shower(self) -> None:
        """
        Starts the beam shower and updates the progress bar and status bar accordingly.

        If in STEM mode, the function sets the time attribute and starts the beam shower. It then runs a time loop to update
        the progress bar and status bar, and waits for the time increment. If an error occurs, it updates the status bar with
        the error message. If not in STEM mode, it updates the status bar with an error message.

        Args:
            None

        Returns:
            None
        """
        # Check if in STEM mode

        if self.get_mode() == 1:
            self.stop_beam_shower_flag = False
            self.start_button.config(text="Stop Beam Shower")
            self.start_button.config(command=self.stop_beam_shower)
            try:
                # Set the time attribute
                self.time = self.time_var.get()

                self.set_conditions()

                print(
                    f'Starting Beam Shower for {self.time} minutes.'
                )

                # run the time loop
                self.total_steps = int(self.time / self.time_increment)
                self.step = 0
                self.update_beam_shower()

            except Exception as e:
                # Update the status bar with the error message
                self.status_bar_message(f'Error: {str(e)}')

        else:
            # Update the status bar with an error message
            self.status_bar_message("Error: Not in STEM mode")
         
            

    def update_beam_shower(self) -> None:
        """
        Updates the progress bar and status bar for the beam shower.

        If the beam shower is still running, it updates the progress bar and status bar with the remaining time and waits
        for the time increment. If the beam shower is finished, it updates the progress bar and status bar accordingly.

        Args:
            None

        Returns:
            None
        """
        # Calculate the remaining time
        remaining_time = (self.total_steps - self.step) * self.time_increment * 60
        minutes = int(remaining_time // 60)
        seconds = int(remaining_time % 60)

        # Update the status bar with the remaining time
        self.status_bar_message(f'Remaining time: {minutes:02d}:{seconds:02d}')

        # Update the progress bar
        progress_percentage = (self.step / self.total_steps) * 100
        self.progress_var.set(progress_percentage)
        # self.update_idletasks()

        # Check if the beam shower is stopped
        if self.stop_beam_shower_flag:
            # Check if the stop button has been clicked
            self.status_bar_message('Stopping Beam Shower')
            # self.update_idletasks()
            self.reset_conditions()
            self.status_bar_message('Beam Shower Stopped')
            return

        elif self.step >= self.total_steps:
            # Update the status bar
            self.progress_var.set(100)
            # self.update_idletasks()
            self.reset_conditions()

        else:
            # Wait for the time increment
            self.step += 1
            self.after(int(self.time_increment * 60 * 1000), self.update_beam_shower)


    def stop_beam_shower(self) -> None:
        """
        Stops the Beam Shower and resets the status bar message.
        """
        self.stop_beam_shower_flag = True
        print(self.stop_beam_shower_flag)
        
    def get_mode(self) -> int:
        #check the TEM is in STEM mode
        return 1
    
    def save_TEM_conditions(self)-> None:
        self.probesize = eos.GetSpotSize()
        self.CL1 = lens.GetCL1()
        self.CL2 = lens.GetCL2()
        self.CL3 = lens.GetCL3()


    def get_duration(self) -> None:
        """
        Gets the conditions for the beam shower simulation from the GUI inputs.
        
        Returns:
        None
        """
        self.time = int(self.time_spinbox.get(), 10) * 60 * 1000
        return
    
    
    def set_conditions(self) -> None:
        """
        Sets the conditions for the beam shower.
        
        Returns:
        None
        """
        print("setting up conditions")
        
        # blank beam
        blank_beam(True)
        # lower screen
        lower_screen()

        # Create a pop-up window with a message
        popup = tk.Toplevel(self)
        popup.title("Warning")
        popup.geometry("500x100")
        popup.configure(bg="yellow")
        message = ttk.Label(popup, text="Make sure EDX detector is retracted!",
                            font=("Helvetica", 12, "bold"), justify=tk.CENTER,
                            background="yellow", foreground="black")
        message.pack(pady=10)
        ok_button = tk.Button(popup, text="OK", width=20, command=popup.destroy)
        ok_button.pack(pady=10)

        # Display the pop-up window and wait for it to be closed
        popup.wait_window()

        # set CL values
        self.status_bar_message('Set CL Lenses')

        # Ideally would have access to the cFEG A2 to change the brightness
        # and the energy filter to change the defocus
        # without destroying the alignment
        # maybe in a future version of PyJEM?

        eos.SelectSpotSize(3) # choose the spot size to run the beam shower at
        lens.SetFLCAbs(0,CL1_val) # CL1
        lens.SetFLCAbs(1,CL2_val) # CL2 Need to find the right values
        lens.SetFLCAbs(2,CL3_val)  # CL3 Needs testing on F200 !

        # remove detectors
        self.status_bar_message('Removing Detectors')
        remove_detectors()

        # insert apertures
        self.status_bar_message('Inserting SA and OL Apertures')
        insert_aperture(2, 0)
        insert_aperture(4, 0)


        #unblank beam
        blank_beam(False)


    def reset_conditions(self) -> None:
        """
        Resets the conditions following the beam shower.

        Returns:
        None
        """

        print("resetting conditions")
        blank_beam(True)

        self.status_bar_message('Resetting Lenses')
        lens.SetFLCSwAllLens(0)
        eos.SelectSpotSize(self.probesize)
        self.after(1000, lambda: None)

        self.status_bar_message('Inserting Detectors')
        insert_detectors()

        self.status_bar_message('Removing SA and OL Apertures')
        remove_aperture(2, 0)
        remove_aperture(4, 0)

        blank_beam(False)

        self.stop_beam_shower_flag = False
        self.start_button.config(text="Start Beam Shower")
        self.start_button.config(command=self.start_beam_shower)

        self.status_bar_message('Beam Shower Finished')

    def status_bar_message(self, message) -> None:
        self.status_bar.config(text=message)
        self.update_idletasks()

    def __del__(self)  -> None:
        self.stop_beam_shower()
        self.reset_conditions()

if __name__ == '__main__':
    BeamShower = BeamShowerApp()
    BeamShower.mainloop()

