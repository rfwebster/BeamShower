# JEOLBeamShower
PyJEM script to run a beam shower (to remove/fix contamination) for a given time on the TEM (running in STEM mode)

**Tested on an F200 at UNSW, but not sure about other microoscopes so proceed with caution**

## Simple UI:

![beam shower ui screenshot](doc/screenshot.png)

For now the lens settings are changed in the main.py file set up in configuration.

## Configuration
The microscope configuration information is in the [microscopes.py](microscopes.py) file. For Each microscope you intend to run this on you can creat a new class (with the same methods as in the example) and edit to suit the particular configuration, but I have tried to make it quite general so hopefully this will work without major modifications necessary.

The code has several flags to set to make 

    '''python
    # User Configurable variables
    CL1_VALUE = 20000  # CL1 value to set during Beam Shower
    CL2_VALUE = 20000  # CL2 value to set during Beam Shower
    CL3_VALUE = 20000  # CL3 value to set during Beam Shower
    BS_METHOD = "CL" # options: "CL" or "ENG"
    IL_BLANK = False # options: True or False
    IL_BLANK_TYPE = "IS" # options: "IS" or "FLA"
    '''

In the "CL" method wich uses free lens control to alter the brightness and defocus, these need to be changed to suit your microscope. And the easier to configure "ENG" method which works on the F200 using the energy filter to defocus the beam and the spot size to increase the current. I don't know if this will work on other microscope models.

There are two methods for blanking the beam below the sample (to protect the screen) Can either insert smallest OL and SA apertures to block the path of the beam or can use the IL lens deflectors or Image Shift deflectors to blank the beam use. 


## Usage 
To Run either open in Sypder (provided with PyJEM) and click the play button or create a batch (.bat) file and run from that, example batch file: 

    '''
    @echo off
    REM Activate the Python environment (replace "env" with the name of your environment)
    call activate env

    REM Run the Python script
    python main.py

    REM Pause the batch file so that the user can see the output before the window closes
    pause
    '''

Once running the progamme first blanks the beam this ensures that the beam is not visible during the beam shower setup.

Next, the programme lowers the screen so that the detecotors and cameras below the screen are not damaged.

The programme then creates a pop-up window with a message to remind the user to retract the EDX detector before starting the beam shower. After the pop-up window is closed, the method removes any inserted STEM detectors using the remove_detectors method of the microscope object. 

Then the spotsize is increased and the CL aperture is removed to increase the electron fluence and depending on the method chosen either the CL lenses are set up or the energy filter is turned on.

Finally the beam blank is released to start the beam shower for the  time chosen in the UI.

When finished the original lens settings are restored, the apertures are removed and  the programme is returned to the starting condition. 

It is recommended to do the Ronchigram Alignment following the beam shower.
