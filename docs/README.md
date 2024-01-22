[![PyPI version](https://badge.fury.io/py/e3v3se-display-klipper.svg)](https://pypi.org/project/e3v3se-display-klipper)
[![Documentation](https://github.com/jpcurti/E3V3SE_display_klipper/actions/workflows/documentation.yml/badge.svg)](https://jpcurti.github.io/E3V3SE_display_klipper/)
# Interface for the Creality Ender 3 V3 SE display running Klipper 

This project allows you to use the original Creality E3V3SE (Ender 3 V3 SE) display with Klipper when connected directly to the host (at the moment a Raspberry pi only) via UART and GPIOs. It fetches the information from Klipper via the moonraker API and is able to send basic commands back, so that you can re-use the printer original display for some basic functionality.

Considering that the communication protocol between E3V3SE and the display is presently undisclosed, the repository includes a [comprehensive guide on reverse engineering the communication protocol of such printers](/docs/tjc3224_reverse_engineering.md). This resource is invaluable for extending this capability to other 3D printers. Users are encouraged to customize the project to suit their specific printer models.


## Installation
### Via pip
``` sh
pip install e3v3se-display-klipper
e3v3se_display_klipper 
```
### By cloning the project
```sh
git clone https://github.com/jpcurti/E3V3SE_display_klipper.git
cd E3V3SE_display_klipper
```

## Configuration and Running
Parameters can be set as arguments or in a `config.ini` file in the project root. Run `python3 run.py --help` (for project cloning) or `e3v3se_display --help` for a complete list of parameters.
- Example of configuration file:  Check the file `config-example.ini`
- Example when running as arguments:
```sh
python run.py --com_port '/dev/ttyAMA0' --baud 115200 --gpio_wheel_button_left 26 --gpio_wheel_button_right 19 --gpio_wheel_button_click 13 --klipper_api_key 'yourapikey' --klipper_socket '/home/youruser/printer_data/comms/klippy.sock' 

or 

e3v3se_display_klipper --com_port '/dev/ttyAMA0' --baud 115200 --gpio_wheel_button_left 26 --gpio_wheel_button_right 19 --gpio_wheel_button_click 13 --klipper_api_key 'yourapikey' --klipper_socket '/home/youruser/printer_data/comms/klippy.sock' 

```

## Wiring

### Using a Rpi as a host
If you want to follow the same wiring as the default configuration, make sure to [configure the primary UART on the raspberry!](https://www.raspberrypi.com/documentation/computers/configuration.html#configuring-uarts).

Then, wire the raspberry pi and display according to the image below:
![Wiring diagram between display and raspberry pi](https://github.com/jpcurti/E3V3SE_display_klipper/blob/main/docs/img/wiring.png?raw=true)
 
|Display    |   RPi |
|-----------|-------|
|VCC (5V)   | 2     |
|GND        |6      |
|TX         |10 (RX)|
|RX         |8 (TX) |
|A          |19     |
|B          |26     |
|ENTER      |13     |

**Important - Credits**:
-  This repository is heavily based on the [DWIN_T5UIC1_LCD](https://github.com/odwdinc/DWIN_T5UIC1_LCD) repository for the E3V2 display and makes use of most of the available classes and methods implemented there, with the necessary modifications for the E3V3SE display. All credits goes to the [author of the DWIN_T5UIC1_LCD project](https://github.com/odwdinc) for making the version which this repository is based on.
  
-  This project is based on the **E3V3SE display firmware 1.0.6**. Any changes in the firmware version, such as a new version from Creality, can change the assets locations within the display memory and a new mapping would be necessary. A list of available firmware can be found [on Creality website](https://www.creality.com/pages/download-ender-3-v3-se) and a detailed instruction on how to update your display is available on [youtube](https://www.youtube.com/watch?v=8oRuCusCyUM&ab_channel=CrealityAfter-sale).

## Useful links

https://www.klipper3d.org

https://octoprint.org/

https://github.com/arksine/moonraker

https://github.com/odwdinc/DWIN_T5UIC1_LCD


