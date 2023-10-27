# Connect to the TEM3
_status = 0  # Online
try:
    from PyJEM import detector, TEM3
    TEM3.connect()
except ImportError:
    from PyJEM.offline import detector, TEM3
    _status = 1  # Offline
    
import time

PAUSE_DET = 1.8
PAUSE_APT = 1.8


class F200:
    def __init__(self):

        self.lens = TEM3.Lens3()
        self.defl = TEM3.Def3()
        self.eos = TEM3.EOS3()
        self.det = TEM3.Detector3()
        self.apt = TEM3.Apt3()
        self.filt = TEM3.Filter3()

        self.connect()

        self.detectors = []

        self.FLA_backup = None
        self.IS2_backup = None

    def connect(self):
        self.status = _status
        # velow for offline testing
        if self.status == 1:
            self.eos.SelectTemStem(1)  # Set to STEM mode
            self.det.SetPosition(0, 1)
            self.det.SetPosition(1, 0)

        self.probesize_backup = self.eos.GetSpotSize()
        self.CL1_backup = self.lens.GetCL1()
        self.CL2_backup = self.lens.GetCL2()
        self.CL3_backup = self.lens.GetCL3()
        self.FLA_backup = self.defl.GetFLA2()
        self.IS2_backup = self.defl.GetIS2()

    def get_attached_detectors(self):
        self.attached_detectors = detector.get_attached_detector()        
        for i, attached in enumerate(self.attached_detectors):
            if self.det.GetPosition(i):
                print(f"{attached} is inserted")
                self.inserted_detectors.append(i)

    def blank_beam(self, blank):
        if blank:
            self.defl.SetBeamBlank(1)
            print("beam blanked")
        else:
            self.defl.SetBeamBlank(0)
            print("beam unblanked")

    def IL_blanker(self, blank, deflector_type="FLA"):
        if blank:
            if deflector_type == "FLA":
                self.FLA_backup = self.defl.GetFLA2()
                self.defl.SetFLA2(65535, 65535)
            else:
                self.IS2_backup = self.defl.GetIS2()
                self.defl.SetIS2(65535, 65535)
            print("IL blanked")
        else:
            if deflector_type == "FLA":
                self.defl.SetFLA2(*self.FLA_backup)
            else:
                self.defl.SetIS2(*self.IS2_backup)
            print("IL unblanked")

    def lower_screen(self):
        self.det.SetScreen(0)
        time.sleep(2)

    def insert_aperture(self, k, s):
        """
        Inserts an aperture of kind k and size s.
        """
        print("inserting aperture {} with size {}".format(k, s))
        try:
            self.apt.SelectKind(k)
            self.apt.SetSize(s)
            time.sleep(PAUSE_APT)
        except Exception as e:
            print("Error: {}\n".format(e))
        else: return

        try:
            print("Trying extended apertures")
            self.apt.SelectExpKind(k)
            self.apt.SetExpSize(s)
            time.sleep(PAUSE_APT)
        except Exception as e:
            print("Error: {}".format(e))
        else: return

    def remove_aperture(self, k):
        """
        Removes an aperture of kind k and size s.
        """
        print("removing aperture {}".format(k))

        try:
            self.apt.SelectKind(k)
            self.apt.SetSize(0)
            time.sleep(PAUSE_APT)
        except Exception as e:
            print("Error: {}\n".format(e))
        else: return

        try:
            print("Trying extended apertures")
            self.apt.SelectExpKind(k)
            self.apt.SetExpSize(0)
            time.sleep(PAUSE_APT)
        except Exception as e:
            print("Error: {}".format(e))
        else: return


    def insert_detectors(self):
        """
        Inserts all detectors.
        """
        for d in self.detectors:
            self.det.SetPosition(d, 1)
            print("inserting detector {}".format(d))
            time.sleep(PAUSE_DET)

    def remove_detectors(self):
        """
        Removes all detectors.
        """
        for d in self.detectors:
            self.det.SetPosition(d, 0)
            print("removing detector {}".format(d))
            time.sleep(PAUSE_DET) # 
            
            