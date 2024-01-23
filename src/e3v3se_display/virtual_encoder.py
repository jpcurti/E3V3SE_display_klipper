import threading
import time

class Encoder:
    """
    This class replaces the GPIO encoder class from the first version 
    by a virtual encoder class that uses the serial communication. This 
    will be used together with a modified version from klipper firmware 
    to communicate the host with the display through the USB port that 
    is already being used.
    """
    
    state_null = 0  # no state
    state_rotation_left = 1  # clockwise rotation
    state_rotation_right = 2  # counterclockwise rotation
    state_click = 4  # click
    
    def __init__(self, serial_manager, callback=None):
        """
        Initialize the virtual encoder object.

        Parameters:
        - serial_obj: Reference to a Serial object for communication.
        - callback: Optional callback function to be called on value change.
        """
        self.value = 0
        self.callback = callback
        self.serial = serial_manager
        self.lock = threading.Lock()
        self.valid_values = {b"\x01": 1, b"\x02": 2, b"\x04": 4}
        self.startInterruptHandler()
        
    def transitionOccurred(self, data):
        """
        Handle transition events based on received data.

        Parameters:
        - data: Byte array containing the received data.
        """
        if data in self.valid_values:  
            self.value = self.valid_values[data]
            with self.lock:
                if self.callback is not None:
                    self.callback(self.value)
                    
        else:
            self.value = self.state_null
                
    def interruptHandler(self):
        """
        Continuously listen for UART messages and handle transitions.
        """
        while True:
            if self.serial.in_waiting > 0:
                header = self.serial.read(1)
                if header == b"\xAA":
                    command = self.serial.read(1)
                    if command == b"\xBC":
                        data = self.serial.read(1)
                        checksum = self.serial.read(4)
                        if checksum == b"\xCC\x33\xC3\x3C":
                            self.transitionOccurred(data)
            time.sleep(0.01)  # Adjust sleep time as needed

    def getValue(self):
        """
        Get the current value of the Encoder.

        Returns:
        - int: Current value of the Encoder.
        """
        return_value = self.value
        #self.value = 0
        return return_value
    
    def startInterruptHandler(self):
        """
        Start the interrupt handling thread.
        """
        threading.Thread(target=self.interruptHandler, daemon=True).start()

