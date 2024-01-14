# ender3_v3_se_display_klipper
## Interface for the Creality Ender 3 V3 SE display running Klipper 

This project allows you to use the original Creality E3V3SE (Ender 3 V3 SE) display with Klipper when connected directly to the host (atm a Raspberry pi only) via UART and GPIOs. It fetches the information from Klipper via the moonraker API and is able to send basic commands back, so that you can re-use the printer original display for some basic functionality.

As the E3V3SE communication protocol  with the display is (at the moment) not public, this repository also contains a guide on how to reverse engineer the communication protocol, so that the same can be done for any other 3d printer. Feel free to modify it to your specific model and, most important, have fun doing it :).


**Important points**:
-  This repository is heavily based on the [DWIN_T5UIC1_LCD](https://github.com/odwdinc/DWIN_T5UIC1_LCD) repository for the E3V2 display and makes use of most of the available classes and methods implemented there, with the necessary modifications for the E3V3SE display. All credits goes to the [author of the DWIN_T5UIC1_LCD project](https://github.com/odwdinc) for making the version which this repository is based on.
  
-  This project is based on the **E3V3SE display firmware 1.0.6**. Any changes in the firmware version, such as a new version from Creality, can change the assets locations within the display memory and a new mapping would be necessary. A list of available firmware can be found [on Creality website](https://www.creality.com/pages/download-ender-3-v3-se) and a detailed instruction on how to update your display is available on [youtube](https://www.youtube.com/watch?v=8oRuCusCyUM&ab_channel=CrealityAfter-sale).


## Useful links

https://www.klipper3d.org

https://octoprint.org/

https://github.com/arksine/moonraker

https://github.com/odwdinc/DWIN_T5UIC1_LCD


