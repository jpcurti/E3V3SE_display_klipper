import serial

class SerialPortManager:
    """
    A manager class for handling and sharing a serial port.
    It mirrors the serial port API, but adds a context manager.
    """
    def __init__(self, port, baud_rate, timeout=1):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_port = None
        self.is_open = False
        self.serial_port = serial.Serial(port, baud_rate, timeout=timeout)
    def __enter__(self):
        """
        Enter the context manager.

        Returns:
        - SerialPortManager: The instance of the SerialPortManager.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the context manager. Closes the serial port.

        Parameters:
        - exc_type: Type of the exception.
        - exc_value: Value of the exception.
        - traceback: Traceback information.
        """
        self.close()

    def open(self):
        """
        Open the serial port if it is not already open.
        """
        if not self.serial_port.is_open:
            self.serial_port.open()

    def close(self):
        """
        Close the serial port if it is open.
        """
        if self.serial_port.is_open:
            self.serial_port.close()

    def write(self, data):
        """
        Write data to the serial port.

        Parameters:
        - data (bytes): The data to be written to the serial port.
        """
        self.serial_port.write(data)

    def read(self, size=1):
        """
        Read data from the serial port.

        Parameters:
        - size (int, optional): The number of bytes to read. Defaults to 1.

        Returns:
        - bytes: The read data.
        """
        return self.serial_port.read(size)
    
    @property
    def in_waiting(self):
        """
        Get the number of bytes in the receive buffer.

        Returns:
        - int: The number of bytes waiting in the receive buffer.
        """
        return self.serial_port.in_waiting