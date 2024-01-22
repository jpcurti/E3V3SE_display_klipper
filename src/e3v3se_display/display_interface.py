import time
import multitimer
import atexit

from e3v3se_display.encoder import Encoder
from e3v3se_display.printerInterface import PrinterData
from e3v3se_display.TJC3224 import TJC3224_LCD


from RPi import GPIO


def current_milli_time():
    return round(time.time() * 1000)


def _MAX(lhs, rhs):
    if lhs > rhs:
        return lhs
    else:
        return rhs


def _MIN(lhs, rhs):
    if lhs < rhs:
        return lhs
    else:
        return rhs


class select_t:
    now = 0
    last = 0

    def set(self, v):
        self.now = self.last = v

    def reset(self):
        self.set(0)

    def changed(self):
        c = self.now != self.last
        if c:
            self.last = self.now
            return c

    def dec(self):
        if self.now:
            self.now -= 1
        return self.changed()

    def inc(self, v):
        if self.now < (v - 1):
            self.now += 1
        else:
            self.now = v - 1
        return self.changed()


class E3V3SE_DISPLAY:
    """
    Class that interfaces with the the E3V3SE display.

    This class is based on the DWIN_LCD class from the DWIN_T5UIC1_LCD
    repository available on (https://github.com/odwdinc/DWIN_T5UIC1_LCD),
    adapted for the Creality Ender 3 V3 SE display and GUI
    """

    TROWS = 6
    MROWS = TROWS - 1  # Total rows, and other-than-Back
    HEADER_HEIGHT = 24  # Title bar height
    STATUS_Y = 260  # Y position of status area
    MLINE = 39  # Menu line height
    LBLX = 45  # Menu item label X
    MENU_CHR_W = 8
    STAT_CHR_W = 10

    dwin_abort_flag = False  # Flag to reset feedrate, return to Home

    MSG_STOP_PRINT = "Stop Print"
    MSG_PAUSE_PRINT = "Pausing..."

    scroll_up = 2
    scroll_down = 3

    select_page = select_t()
    select_file = select_t()
    select_print = select_t()
    select_prepare = select_t()

    select_control = select_t()
    select_axis = select_t()
    select_temp = select_t()
    select_motion = select_t()
    select_tune = select_t()
    select_PLA = select_t()
    select_TPU = select_t()

    index_file = MROWS
    index_prepare = MROWS
    index_control = MROWS
    index_leveling = MROWS
    index_tune = MROWS

    MainMenu = 0
    SelectFile = 1
    Prepare = 2
    Control = 3
    Leveling = 4
    PrintProcess = 5
    AxisMove = 6
    TemperatureID = 7
    Motion = 8
    Info = 9
    Tune = 10
    PLAPreheat = 11
    TPUPreheat = 12
    MaxSpeed = 13
    MaxSpeed_value = 14
    MaxAcceleration = 15
    MaxAcceleration_value = 16
    MaxJerk = 17
    MaxJerk_value = 18
    Step = 19
    Step_value = 20
    FeatureNotAvailable = 21

    # Last Process ID
    Last_Prepare = 21
    last_status = ""

    # Back Process ID
    Back_Main = 22
    Back_Print = 23

    # Date variable ID
    Move_X = 24
    Move_Y = 25
    Move_Z = 26
    Extruder = 27
    ETemp = 28
    Homeoffset = 29
    BedTemp = 30
    FanSpeed = 31
    PrintSpeed = 32

    Print_window = 33
    Popup_Window = 34

    MINUNITMULT = 10

    ENCODER_DIFF_NO = 0  # no state
    ENCODER_DIFF_CW = 1  # clockwise rotation
    ENCODER_DIFF_CCW = 2  # counterclockwise rotation
    ENCODER_DIFF_ENTER = 3  # click
    ENCODER_WAIT = 80
    ENCODER_WAIT_ENTER = 300
    EncoderRateLimit = True

    dwin_zoffset = 0.0
    last_zoffset = 0.0

    # Picture ID
    Start_Process = 0

    # IMAGE LIBRARIES ID
    ICON = 0
    GIF_ICON = 27
    LANGUAGE_Chinese = 2
    LANGUAGE_English = 4
    LANGUAGE_German = 6
    LANGUAGE_Russian = 9
    LANGUAGE_French = 12
    LANGUAGE_Turkish = 15
    LANGUAGE_Spanish = 17
    LANGUAGE_Italian = 19
    LANGUAGE_Portuguese = 21
    LANGUAGE_Japanese = 23
    LANGUAGE_Korean = 25

    # Language
    selected_language = LANGUAGE_English

    # ICON ID
    icon_logo = 0
    icon_print = 1
    icon_print_selected = 2
    icon_prepare = 3
    icon_prepare_selected = 4
    icon_control = 5
    icon_control_selected = 6
    icon_leveling = 7
    icon_leveling_selected = 8
    icon_hotend_temp = 9
    icon_bedtemp = 10
    icon_speed = 11
    icon_z_offset = 12
    icon_back = 13
    icon_file = 14
    icon_print_time = 15
    icon_remain_time = 16
    icon_tune = 17
    icon_tune_selected = 18
    icon_pause = 19
    icon_pause_selected = 20
    icon_continue = 21
    icon_continue_selected = 22
    icon_stop = 23
    icon_stop_selected = 24
    icon_bar = 25
    icon_more = 26

    icon_axis = 27
    icon_close_motor = 28
    icon_homing = 29
    icon_set_home = 30
    icon_preheat_pla = 31
    icon_preheat_tpu = 32
    icon_cool = 33
    icon_language = 34

    icon_move_x = 35
    icon_move_y = 36
    icon_move_z = 37
    icon_move_e = 38

    icon_temperature = 40
    icon_motion = 41
    icon_write_eeprom = 42
    icon_read_eeprom = 43
    icon_resume_eeprom = 44
    icon_info = 45

    icon_SetEndTemp = 46
    icon_SetBedTemp = 47
    icon_FanSpeed = 48
    icon_SetPLAPreheat = 49
    icon_SetTPUPreheat = 50

    icon_MaxSpeed = 51
    icon_MaxAccelerated = 52
    icon_MaxJerk = 53
    icon_Step = 54
    icon_PrintSize = 55
    icon_Version = 56
    icon_Contact = 57
    icon_StockConfiguraton = 58
    icon_MaxSpeedX = 59
    icon_MaxSpeedY = 60
    icon_MaxSpeedZ = 61
    icon_MaxSpeedE = 62
    icon_MaxAccX = 63
    icon_MaxAccY = 64
    icon_MaxAccZ = 65
    icon_MaxAccE = 66
    icon_MaxSpeedJerkX = 67
    icon_MaxSpeedJerkY = 68
    icon_MaxSpeedJerkZ = 69
    icon_MaxSpeedJerkE = 70
    icon_StepX = 71
    icon_StepY = 72
    icon_StepZ = 73
    icon_StepE = 74
    icon_Setspeed = 75
    icon_SetZOffset = 76
    icon_Rectangle = 77
    icon_BLTouch = 78
    icon_TempTooLow = 79
    icon_AutoLeveling = 80
    icon_TempTooHigh = 81
    icon_NoTips_C = 82
    icon_NoTips_E = 83
    icon_continue_button = 96
    icon_continue_button_hovered = 96
    icon_cancel_button = 72
    icon_cancel_button_hovered = 72
    icon_confirm_button = 73
    icon_confim_button_hovered = 73
    icon_Info_0 = 90
    icon_Info_1 = 91

    icon_progress_0 = 145

    # TEXT ICON ID
    icon_TEXT_header_main = 1
    icon_TEXT_header_printing = 20
    icon_TEXT_header_tune = 17
    icon_TEXT_header_file_selection = 26
    icon_TEXT_header_motion = 33
    icon_TEXT_header_move = 39
    icon_TEXT_header_prepare = 40
    icon_TEXT_header_pause = 27
    icon_TEXT_header_temperature = 49
    icon_TEXT_header_control = 80
    icon_TEXT_header_print_finish = 81
    icon_TEXT_header_leveling = 85
    icon_TEXT_header_max_speed = 88
    icon_TEXT_header_language_selection = 106
    icon_TEXT_header_info = 61
    icon_TEXT_header_PLA_settings = 62
    icon_TEXT_header_TPU_settings = 64

    icon_popup_nozzle_temp_too_high = 71
    icon_popup_nozzle_temp_too_low = 69
    icon_popup_bed_temp_too_low = 140
    icon_popup_bed_temp_too_high = 141
    icon_popup_unexpected_stoppage = 70
    icon_popup_filament_reloaded = 67
    icon_popup_filament_runout = 68
    icon_popup_pause_print = 76
    icon_popup_stop_print = 77
    icon_popup_homing = 84

    icon_TEXT_Print = 2
    icon_TEXT_Print_selected = 8
    icon_TEXT_Prepare = 3
    icon_TEXT_Prepare_selected = 9
    icon_TEXT_Control = 4
    icon_TEXT_Control_selected = 10
    icon_TEXT_Leveling = 14
    icon_TEXT_Leveling_selected = 15
    icon_TEXT_Info = 5
    icon_TEXT_Info_selected = 11
    icon_TEXT_Stop = 6
    icon_TEXT_Stop_selected = 12
    icon_TEXT_Pause = 7
    icon_TEXT_Pause_selected = 13
    icon_TEXT_Z_Offset = 16
    icon_TEXT_Tune = 78
    icon_TEXT_Tune_selected = 79
    icon_TEXT_Printing_Speed = 19
    icon_TEXT_continue = 96
    icon_TEXT_nozzle_temperature = 23
    icon_TEXT_fan_speed = 22
    icon_TEXT_back = 21
    icon_TEXT_bed_temperature = 24
    icon_TEXT_remain = 25
    icon_TEXT_store_configuration = 28
    icon_TEXT_read_configuration = 29
    icon_TEXT_reset_configuration = 30
    icon_TEXT_temperature = 31
    icon_TEXT_motion = 32
    # icon_TEXT_ =33
    icon_TEXT_preheat_tpu = 34
    icon_TEXT_preheat_pla = 35
    icon_TEXT_auto_home = 36
    icon_TEXT_Info = 37
    icon_TEXT_disable_stepper = 38
    icon_TEXT_cooldown = 41
    icon_TEXT_move_x = 42
    icon_TEXT_move_y = 43
    icon_TEXT_move_z = 44
    icon_TEXT_move_e = 45
    icon_TEXT_move_axis = 46
    icon_TEXT_preheat_pla_settings = 47
    icon_TEXT_preheat_tpu_settings = 48
    icon_TEXT_steps_per_mm = 54
    icon_TEXT_max_acceleration = 55
    icon_TEXT_max_corner = 56
    icon_TEXT_max_speed = 57
    icon_TEXT_save_pla_parameters = 63
    icon_TEXT_save_tpu_parameters = 65
    icon_TEXT_language_selection = 66
    icon_TEXT_pla_fan_speed = 100
    icon_TEXT_pla_nozzle_temperature = 101
    icon_TEXT_pla_bed_temperature = 102
    icon_TEXT_tpu_nozzle_temperature = 103
    icon_TEXT_tpu_bed_temperature = 104
    icon_TEXT_tpu_fan_speed = 105
    icon_TEXT_max_speed_x = 107
    icon_TEXT_max_speed_y = 108
    icon_TEXT_max_speed_z = 109
    icon_TEXT_max_speed_e = 110
    icon_TEXT_max_acceleration_x = 112
    icon_TEXT_max_acceleration_y = 113
    icon_TEXT_max_acceleration_z = 114
    icon_TEXT_max_acceleration_e = 115
    icon_TEXT_hardware_version = 156
    icon_TEXT_bed_size = 59
    icon_TEXT_contact = 60

    icon_text_printing_time = 18
    icon_text_remain_time = 25

    # Color Palette
    color_white = 0xFFFF
    color_yellow = 0xFF0F
    color_popup_background = 0x31E8  # Popup background color
    color_background_grey = 0x1145  # Dark grey background color
    color_background_black = 0x0841  # Black background color
    color_background_red = 0xF00F  # Red background color
    color_popup_text = 0xD6BA  # Popup font_ background color
    color_line = 0x3A6A  # Split line color
    Rectangle_color = 0xEE2F  # Blue square cursor color
    Percent_color = 0xFE29  # Percentage color
    BarFill_color = 0x10E4  # Fill color of progress bar
    Selected_color = 0x33BB  # Selected color

    MENU_CHAR_LIMIT = 24

    MOTION_CASE_RATE = 1
    MOTION_CASE_ACCEL = 2
    MOTION_CASE_JERK = MOTION_CASE_ACCEL + 0
    MOTION_CASE_STEPS = MOTION_CASE_JERK + 1
    MOTION_CASE_TOTAL = MOTION_CASE_STEPS

    PREPARE_CASE_MOVE = 1
    PREPARE_CASE_DISA = 2
    PREPARE_CASE_HOME = 3
    PREPARE_CASE_ZOFF = PREPARE_CASE_HOME + 1
    PREPARE_CASE_PLA = PREPARE_CASE_ZOFF + 1
    PREPARE_CASE_TPU = PREPARE_CASE_PLA + 1
    PREPARE_CASE_COOL = PREPARE_CASE_TPU + 1
    PREPARE_CASE_LANG = PREPARE_CASE_COOL + 0
    PREPARE_CASE_TOTAL = PREPARE_CASE_LANG

    CONTROL_CASE_TEMP = 1
    CONTROL_CASE_MOVE = 2
    CONTROL_CASE_INFO = 3
    CONTROL_CASE_TOTAL = 3

    TUNE_CASE_SPEED = 1
    TUNE_CASE_TEMP = TUNE_CASE_SPEED + 1
    TUNE_CASE_BED = TUNE_CASE_TEMP + 1
    TUNE_CASE_FAN = TUNE_CASE_BED + 0
    TUNE_CASE_ZOFF = TUNE_CASE_FAN + 1
    TUNE_CASE_TOTAL = TUNE_CASE_ZOFF

    TEMP_CASE_TEMP = 0 + 1
    TEMP_CASE_BED = TEMP_CASE_TEMP + 1
    TEMP_CASE_FAN = TEMP_CASE_BED + 0
    TEMP_CASE_PLA = TEMP_CASE_FAN + 1
    TEMP_CASE_TPU = TEMP_CASE_PLA + 1
    TEMP_CASE_TOTAL = TEMP_CASE_TPU

    PREHEAT_CASE_TEMP = 0 + 1
    PREHEAT_CASE_BED = PREHEAT_CASE_TEMP + 1
    PREHEAT_CASE_FAN = PREHEAT_CASE_BED + 0
    PREHEAT_CASE_SAVE = PREHEAT_CASE_FAN + 1
    PREHEAT_CASE_TOTAL = PREHEAT_CASE_SAVE

    def __init__(
        self, USARTx, baudrate, encoder_pins, button_pin, octoPrint_API_Key, Klipper_Socket
    ):
        GPIO.setmode(GPIO.BCM)
        self.encoder = Encoder(encoder_pins[0], encoder_pins[1])
        self.button_pin = button_pin
        GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(
            self.button_pin, GPIO.BOTH, callback=self.encoder_has_data
        )
        self.encoder.callback = self.encoder_has_data
        self.EncodeLast = 0
        self.EncodeMS = current_milli_time() + self.ENCODER_WAIT
        self.EncodeEnter = current_milli_time() + self.ENCODER_WAIT_ENTER
        self.next_rts_update_ms = 0
        self.last_cardpercentValue = 101
        self.lcd = TJC3224_LCD(USARTx, baudrate)
        self.checkkey = self.MainMenu
        self.pd = PrinterData(octoPrint_API_Key, Klipper_Socket)
        print("Testing Web-services")
        self.pd.init_Webservices()
        while self.pd.status is None:
            print("No Web-services")
            self.pd.init_Webservices()
        self.timer = multitimer.MultiTimer(interval=2, function=self.EachMomentUpdate)
        self.HMI_Init()
        self.HMI_ShowBoot(3)
        self.HMI_StartFrame(True)

    def lcdExit(self):
        print("Shutting down the LCD")
        self.lcd.set_backlight_brightness(0)
        self.timer.stop()

    def MBASE(self, L):
        return 45 + self.MLINE * L

    def HMI_ShowBoot(self, sleep_time=0):
        self.lcd.clear_screen(self.color_background_black)

        self.lcd.draw_string(
            False,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            55,
            20,
            "E3V3SE display ",
        )
        self.lcd.draw_string(
            False,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            70,
            50,
            "for klipper",
        )
        # Todo: QR
        self.lcd.draw_string(
            False,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            80,
            250,
            "Github: ",
        )
        self.lcd.draw_string(
            False,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            0,
            280,
            "jpcurti/E3V3SE_display_klipper",
        )
        time.sleep(sleep_time)

    def HMI_Init(self):
        self.timer.start()
        self.lcd.set_backlight_brightness(100)
        atexit.register(self.lcdExit)

    def HMI_StartFrame(self, with_update):
        self.Clear_Screen()
        self.last_status = self.pd.status
        if self.pd.status == "printing":
            self.Goto_PrintProcess()
            self.Draw_Status_Area(with_update)
        elif self.pd.status in ["operational", "complete", "standby", "cancelled"]:
            self.Goto_MainMenu()
        else:
            self.Goto_MainMenu()

    def HMI_MainMenu(self):
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return
        if encoder_diffState == self.ENCODER_DIFF_CW:
            if self.select_page.inc(4):
                if self.select_page.now == 0:
                    self.icon_Print()
                if self.select_page.now == 1:
                    self.icon_Print()
                    self.icon_Prepare()
                if self.select_page.now == 2:
                    self.icon_Prepare()
                    self.icon_Control()
                if self.select_page.now == 3:
                    self.icon_Control()
                    if self.pd.HAS_ONESTEP_LEVELING:
                        self.icon_Leveling(True)
                    else:
                        self.icon_StartInfo(True)
        elif encoder_diffState == self.ENCODER_DIFF_CCW:
            if self.select_page.dec():
                if self.select_page.now == 0:
                    self.icon_Print()
                    self.icon_Prepare()
                elif self.select_page.now == 1:
                    self.icon_Prepare()
                    self.icon_Control()
                elif self.select_page.now == 2:
                    self.icon_Control()
                    if self.pd.HAS_ONESTEP_LEVELING:
                        self.icon_Leveling(False)
                    else:
                        self.icon_StartInfo(False)
                elif self.select_page.now == 3:
                    if self.pd.HAS_ONESTEP_LEVELING:
                        self.icon_Leveling(True)
                    else:
                        self.icon_StartInfo(True)
        elif encoder_diffState == self.ENCODER_DIFF_ENTER:
            if self.select_page.now == 0:  # Print File
                self.checkkey = self.SelectFile
                self.Draw_Print_File_Menu()
            if self.select_page.now == 1:  # Prepare
                self.checkkey = self.Prepare
                self.select_prepare.reset()
                self.index_prepare = self.MROWS
                self.Draw_Prepare_Menu()
            if self.select_page.now == 2:  # Control
                self.checkkey = self.Control
                self.select_control.reset()
                self.index_control = self.MROWS
                self.Draw_Control_Menu()
            if self.select_page.now == 3:  # Leveling or Info
                if self.pd.HAS_ONESTEP_LEVELING:
                    # The leveling menu is not implemented yet, therefore it popups
                    # a "feature not available" window
                    self.popup_caller = self.MainMenu
                    self.checkkey = self.FeatureNotAvailable
                    self.Draw_FeatureNotAvailable_Popup()

                else:
                    self.checkkey = self.Info
                    self.Draw_Info_Menu()

    def HMI_SelectFile(self):
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return

        fullCnt = len(self.pd.GetFiles(refresh=True))

        if encoder_diffState == self.ENCODER_DIFF_CW and fullCnt:
            if self.select_file.inc(1 + fullCnt):
                itemnum = self.select_file.now - 1  # -1 for "Back"
                if (
                    self.select_file.now > self.MROWS
                    and self.select_file.now > self.index_file
                ):  # Cursor past the bottom
                    self.index_file = self.select_file.now  # New bottom line
                    self.Scroll_Menu(self.scroll_up)
                    self.Draw_SDItem(
                        itemnum, self.MROWS
                    )  # Draw and init the shift name
                else:
                    self.Move_Highlight(
                        1, self.select_file.now + self.MROWS - self.index_file
                    )  # Just move highlight
        elif encoder_diffState == self.ENCODER_DIFF_CCW and fullCnt:
            if self.select_file.dec():
                itemnum = self.select_file.now - 1  # -1 for "Back"
                if (
                    self.select_file.now < self.index_file - self.MROWS
                ):  # Cursor past the top
                    self.index_file -= 1  # New bottom line
                    self.Scroll_Menu(self.scroll_down)
                    if self.index_file == self.MROWS:
                        self.Draw_Back_First()
                    else:
                        self.Draw_SDItem(
                            itemnum, 0
                        )  # Draw the item (and init shift name)
                else:
                    self.Move_Highlight(
                        -1, self.select_file.now + self.MROWS - self.index_file
                    )  # Just move highlight
        elif encoder_diffState == self.ENCODER_DIFF_ENTER:
            if self.select_file.now == 0:  # Back
                self.select_page.set(0)
                self.Goto_MainMenu()
            else:
                filenum = self.select_file.now - 1
                # Reset highlight for next entry
                self.select_print.reset()
                self.select_file.reset()

                # // Start choice and print SD file
                self.pd.HMI_flag.heat_flag = True
                self.pd.HMI_flag.print_finish = False
                self.pd.HMI_ValueStruct.show_mode = 0

                self.pd.openAndPrintFile(filenum)
                self.Goto_PrintProcess()

    def HMI_Prepare(self):
        """
        This function handles the logic for scrolling through the prepare menu options,
        selecting different actions, and executing the corresponding actions based on user input.
        """
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return

        if encoder_diffState == self.ENCODER_DIFF_CW:
            if self.select_prepare.inc(1 + self.PREPARE_CASE_TOTAL):
                if (
                    self.select_prepare.now > self.MROWS
                    and self.select_prepare.now > self.index_prepare
                ):
                    self.index_prepare = self.select_prepare.now

                    # Scroll up and draw a blank bottom line
                    self.Scroll_Menu(self.scroll_up)
                    self.Draw_Menu_Icon(
                        self.MROWS, self.icon_axis + self.select_prepare.now - 1
                    )

                    # Draw "More" icon for sub-menus
                    if self.index_prepare < 7:
                        self.Draw_More_Icon(self.MROWS - self.index_prepare + 1)

                    if self.pd.HAS_HOTEND:
                        if self.index_prepare == self.PREPARE_CASE_TPU:
                            self.Item_Prepare_TPU(self.MROWS)
                    if self.pd.HAS_PREHEAT:
                        if self.index_prepare == self.PREPARE_CASE_COOL:
                            self.Item_Prepare_Cool(self.MROWS)
                else:
                    self.Move_Highlight(
                        1, self.select_prepare.now + self.MROWS - self.index_prepare
                    )

        elif encoder_diffState == self.ENCODER_DIFF_CCW:
            if self.select_prepare.dec():
                if self.select_prepare.now < self.index_prepare - self.MROWS:
                    self.index_prepare -= 1
                    self.Scroll_Menu(self.scroll_down)

                    if self.index_prepare == self.MROWS:
                        self.Draw_Back_First()
                    else:
                        self.Draw_Menu_Line(
                            0, self.icon_axis + self.select_prepare.now - 1
                        )

                    if self.index_prepare < 7:
                        self.Draw_More_Icon(self.MROWS - self.index_prepare + 1)

                    if self.index_prepare == 6:
                        self.Item_Prepare_Move(0)
                    elif self.index_prepare == 7:
                        self.Item_Prepare_Disable(0)
                    elif self.index_prepare == 8:
                        self.Item_Prepare_Home(0)
                else:
                    self.Move_Highlight(
                        -1, self.select_prepare.now + self.MROWS - self.index_prepare
                    )

        elif encoder_diffState == self.ENCODER_DIFF_ENTER:
            if self.select_prepare.now == 0:  # Back
                self.select_page.set(1)
                self.Goto_MainMenu()

            elif self.select_prepare.now == self.PREPARE_CASE_MOVE:  # Axis move
                self.checkkey = self.AxisMove
                self.select_axis.reset()
                self.Draw_Move_Menu()
                self.pd.sendGCode("G92 E0")
                self.pd.current_position.e = self.pd.HMI_ValueStruct.Move_E_scale = 0
            elif self.select_prepare.now == self.PREPARE_CASE_DISA:  # Disable steppers
                self.pd.sendGCode("M84")
            elif self.select_prepare.now == self.PREPARE_CASE_HOME:  # Homing
                self.checkkey = self.Last_Prepare
                self.index_prepare = self.MROWS
                self.pd.current_position.homing()
                self.pd.HMI_flag.home_flag = True
                self.Popup_Window_Home()
                self.pd.sendGCode("G28")
            elif self.select_prepare.now == self.PREPARE_CASE_ZOFF:  # Z-offset
                self.checkkey = self.Homeoffset
                if self.pd.HAS_BED_PROBE:
                    self.pd.probe_calibrate()

                self.pd.HMI_ValueStruct.show_mode = -4

                self.lcd.draw_signed_float(
                    True,
                    self.lcd.font_8x8,
                    self.color_white,
                    self.color_background_black,
                    2,
                    3,
                    175,
                    self.MBASE(self.PREPARE_CASE_ZOFF + self.MROWS - self.index_prepare)
                    - 10,
                    self.pd.HMI_ValueStruct.offset_value,
                )

                self.EncoderRateLimit = False

            elif self.select_prepare.now == self.PREPARE_CASE_PLA:  # PLA preheat
                self.pd.preheat("PLA")

            elif self.select_prepare.now == self.PREPARE_CASE_TPU:  # TPU preheat
                self.pd.preheat("TPU")

            elif self.select_prepare.now == self.PREPARE_CASE_COOL:  # Cool
                if self.pd.HAS_FAN:
                    self.pd.zero_fan_speeds()
                self.pd.disable_all_heaters()

            elif self.select_prepare.now == self.PREPARE_CASE_LANG:  # Toggle Language
                self.HMI_ToggleLanguage()
                self.Draw_Prepare_Menu()

    def HMI_Control(self):
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return

        if encoder_diffState == self.ENCODER_DIFF_CW:
            if self.select_control.inc(1 + self.CONTROL_CASE_TOTAL):
                if (
                    self.select_control.now > self.MROWS
                    and self.select_control.now > self.index_control
                ):
                    self.index_control = self.select_control.now
                    self.Scroll_Menu(self.scroll_up)
                    self.Draw_Menu_Icon(
                        self.MROWS, self.icon_temperature + self.index_control - 1
                    )
                    self.Draw_More_Icon(
                        self.CONTROL_CASE_TEMP + self.MROWS - self.index_control
                    )  # Temperature >
                    self.Draw_More_Icon(
                        self.CONTROL_CASE_MOVE + self.MROWS - self.index_control
                    )  # Motion >
                    if self.index_control > self.MROWS:
                        self.Draw_More_Icon(
                            self.CONTROL_CASE_INFO + self.MROWS - self.index_control
                        )  # Info >
                        self.lcd.move_screen_area(
                            1,
                            0,
                            104,
                            24,
                            114,
                            self.LBLX,
                            self.MBASE(self.CONTROL_CASE_INFO - 1),
                        )
                else:
                    self.Move_Highlight(
                        1, self.select_control.now + self.MROWS - self.index_control
                    )
        elif encoder_diffState == self.ENCODER_DIFF_CCW:
            if self.select_control.dec():
                if self.select_control.now < self.index_control - self.MROWS:
                    self.index_control -= 1
                    self.Scroll_Menu(self.scroll_down)
                    if self.index_control == self.MROWS:
                        self.Draw_Back_First()
                    else:
                        self.Draw_Menu_Line(
                            0, self.icon_temperature + self.select_control.now - 1
                        )
                    self.Draw_More_Icon(
                        0 + self.MROWS - self.index_control + 1
                    )  # Temperature >
                    self.Draw_More_Icon(
                        1 + self.MROWS - self.index_control + 1
                    )  # Motion >
                else:
                    self.Move_Highlight(
                        -1, self.select_control.now + self.MROWS - self.index_control
                    )
        elif encoder_diffState == self.ENCODER_DIFF_ENTER:
            if self.select_control.now == 0:  # Back
                self.select_page.set(2)
                self.Goto_MainMenu()
            if self.select_control.now == self.CONTROL_CASE_TEMP:  # Temperature
                self.checkkey = self.TemperatureID
                self.pd.HMI_ValueStruct.show_mode = -1
                self.select_temp.reset()
                self.Draw_Temperature_Menu()
            if self.select_control.now == self.CONTROL_CASE_MOVE:  # Motion
                self.checkkey = self.Motion
                self.select_motion.reset()
                self.Draw_Motion_Menu()
            if self.select_control.now == self.CONTROL_CASE_INFO:  # Info
                self.checkkey = self.Info
                self.Draw_Info_Menu()

    def HMI_FeatureNotAvailable(self):
        """
        Handles the "feature not available" popup.
        This method is called when the user enters a menu that
        is not implemented yet in the display interface. After
        the user presses the confirmation, he needs to go back to
        where he came from.
        """
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return
        if encoder_diffState == self.ENCODER_DIFF_ENTER:
            self.checkkey = self.popup_caller
            if self.popup_caller == self.MainMenu:
                self.Goto_MainMenu()
            if self.popup_caller == self.Motion:
                self.Draw_Motion_Menu()

    def HMI_Info(self):
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return
        if encoder_diffState == self.ENCODER_DIFF_ENTER:
            if self.pd.HAS_ONESTEP_LEVELING:
                self.checkkey = self.Control
                self.select_control.set(self.CONTROL_CASE_INFO)
                self.Draw_Control_Menu()
            else:
                self.select_page.set(3)
                self.Goto_MainMenu()

    def HMI_Printing(self):
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return
        if self.pd.HMI_flag.done_confirm_flag:
            if encoder_diffState == self.ENCODER_DIFF_ENTER:
                self.pd.HMI_flag.done_confirm_flag = False
                self.dwin_abort_flag = True  # Reset feedrate, return to Home
            return

        if encoder_diffState == self.ENCODER_DIFF_CW:
            if self.select_print.inc(3):
                if self.select_print.now == 0:
                    self.show_tune()
                elif self.select_print.now == 1:
                    self.show_tune()
                    if self.pd.printingIsPaused():
                        self.show_continue()
                    else:
                        self.show_pause()
                elif self.select_print.now == 2:
                    if self.pd.printingIsPaused():
                        self.show_continue()
                    else:
                        self.show_pause()
                    self.show_stop()
        elif encoder_diffState == self.ENCODER_DIFF_CCW:
            if self.select_print.dec():
                if self.select_print.now == 0:
                    self.show_tune()
                    if self.pd.printingIsPaused():
                        self.show_continue()
                    else:
                        self.show_pause()
                elif self.select_print.now == 1:
                    if self.pd.printingIsPaused():
                        self.show_continue()
                    else:
                        self.show_pause()
                    self.show_stop()
                elif self.select_print.now == 2:
                    self.show_stop()
        elif encoder_diffState == self.ENCODER_DIFF_ENTER:
            if self.select_print.now == 0:  # Tune
                self.checkkey = self.Tune
                self.pd.HMI_ValueStruct.show_mode = 0
                self.select_tune.reset()
                self.index_tune = self.MROWS
                self.Draw_Tune_Menu()
            elif self.select_print.now == 1:  # Pause
                if self.pd.HMI_flag.pause_flag:
                    self.show_pause()
                    self.pd.resume_job()
                else:
                    self.pd.HMI_flag.select_flag = True
                    self.checkkey = self.Print_window
                    self.Popup_window_PauseOrStop()
            elif self.select_print.now == 2:  # Stop
                self.pd.HMI_flag.select_flag = True
                self.checkkey = self.Print_window
                self.Popup_window_PauseOrStop()

    # Pause and Stop window */
    def HMI_PauseOrStop(self):
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return
        if encoder_diffState == self.ENCODER_DIFF_CW:
            self.Draw_Select_Highlight(False)
        elif encoder_diffState == self.ENCODER_DIFF_CCW:
            self.Draw_Select_Highlight(True)
        elif encoder_diffState == self.ENCODER_DIFF_ENTER:
            if self.select_print.now == 1:  # pause window
                if self.pd.HMI_flag.select_flag:
                    self.pd.HMI_flag.pause_action = True
                    self.show_continue()
                    self.pd.pause_job()
                self.Goto_PrintProcess()
            elif self.select_print.now == 2:  # stop window
                if self.pd.HMI_flag.select_flag:
                    self.dwin_abort_flag = True  # Reset feedrate, return to Home
                    self.pd.cancel_job()
                    self.Goto_MainMenu()
                else:
                    self.Goto_PrintProcess()  # cancel stop

    # Tune  */
    def HMI_Tune(self):
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return
        if encoder_diffState == self.ENCODER_DIFF_CW:
            if self.select_tune.inc(1 + self.TUNE_CASE_TOTAL):
                if (
                    self.select_tune.now > self.MROWS
                    and self.select_tune.now > self.index_tune
                ):
                    self.index_tune = self.select_tune.now
                    self.Scroll_Menu(self.scroll_up)
                else:
                    self.Move_Highlight(
                        1, self.select_tune.now + self.MROWS - self.index_tune
                    )
        elif encoder_diffState == self.ENCODER_DIFF_CCW:
            if self.select_tune.dec():
                if self.select_tune.now < self.index_tune - self.MROWS:
                    self.index_tune -= 1
                    self.Scroll_Menu(self.scroll_down)
                    if self.index_tune == self.MROWS:
                        self.Draw_Back_First()
                else:
                    self.Move_Highlight(
                        -1, self.select_tune.now + self.MROWS - self.index_tune
                    )
        elif encoder_diffState == self.ENCODER_DIFF_ENTER:
            if self.select_tune.now == 0:  # Back
                self.select_print.set(0)
                self.Goto_PrintProcess()
            elif self.select_tune.now == self.TUNE_CASE_SPEED:  # Print speed
                self.checkkey = self.PrintSpeed
                self.pd.HMI_ValueStruct.print_speed = self.pd.feedrate_percentage
                self.lcd.draw_int_value(
                    True,
                    True,
                    0,
                    self.lcd.font_8x8,
                    self.color_white,
                    self.color_background_black,
                    3,
                    200,
                    self.MBASE(self.TUNE_CASE_SPEED + self.MROWS - self.index_tune) - 8,
                    self.pd.feedrate_percentage,
                )
                self.EncoderRateLimit = False
            elif self.select_tune.now == self.TUNE_CASE_ZOFF:  # z offset
                self.checkkey = self.Homeoffset
                self.lcd.draw_signed_float(
                    True,
                    self.lcd.font_8x8,
                    self.color_white,
                    self.color_background_black,
                    2,
                    3,
                    175,
                    self.MBASE(self.TUNE_CASE_ZOFF) - 10,
                    self.pd.HMI_ValueStruct.offset_value,
                )

    def HMI_PrintSpeed(self):
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return

        if encoder_diffState == self.ENCODER_DIFF_CW:
            self.pd.HMI_ValueStruct.print_speed += 1

        elif encoder_diffState == self.ENCODER_DIFF_CCW:
            self.pd.HMI_ValueStruct.print_speed -= 1

        elif encoder_diffState == self.ENCODER_DIFF_ENTER:
            self.checkkey = self.Tune
            self.encoderRate = True
            self.pd.set_feedrate(self.pd.HMI_ValueStruct.print_speed)

        self.lcd.draw_int_value(
            True,
            True,
            0,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            3,
            200,
            self.MBASE(self.select_tune.now + self.MROWS - self.index_tune) - 8,
            self.pd.HMI_ValueStruct.print_speed,
        )

    def HMI_AxisMove(self):
        """
        Handles the axis movement in the HMI (Human Machine Interface).

        This function checks the encoder state and performs the corresponding action based on the state.
        It updates the display and handles the movement of the X, Y, Z axes, and the extruder.
        """
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return

        # In case of "nozzle too cold" popup is on the screen
        if self.pd.PREVENT_COLD_EXTRUSION:
            if self.pd.HMI_flag.ETempTooLow_flag:
                # Resuming after "nozzle too cold" popup should clear the flag and draw move menu again
                if encoder_diffState == self.ENCODER_DIFF_ENTER:
                    self.pd.HMI_flag.ETempTooLow_flag = False
                    self.pd.current_position.e = (
                        self.pd.HMI_ValueStruct.Move_E_scale
                    ) = 0
                    self.Draw_Move_Menu()
                return

        # Avoid flicker by updating only the previous menu
        if encoder_diffState == self.ENCODER_DIFF_CW:
            if self.select_axis.inc(1 + 4):
                self.Move_Highlight(1, self.select_axis.now)
        elif encoder_diffState == self.ENCODER_DIFF_CCW:
            if self.select_axis.dec():
                self.Move_Highlight(-1, self.select_axis.now)
        elif encoder_diffState == self.ENCODER_DIFF_ENTER:
            selected_line = self.select_axis.now
            if selected_line == 0:  # Back
                self.checkkey = self.Prepare
                self.select_prepare.set(1)
                self.index_prepare = self.MROWS
                self.Draw_Prepare_Menu()
            elif selected_line == 1:  # X axis move
                self.checkkey = self.Move_X
                self.pd.HMI_ValueStruct.Move_X_scale = (
                    self.pd.current_position.x * self.MINUNITMULT
                )
                self.lcd.draw_float_value(
                    True,
                    True,
                    0,
                    self.lcd.font_8x8,
                    self.color_yellow,
                    self.color_background_black,
                    3,
                    1,
                    175,
                    self.MBASE(selected_line) - 10,
                    self.pd.HMI_ValueStruct.Move_X_scale,
                )
                self.EncoderRateLimit = False
            elif selected_line == 2:  # Y axis move
                self.checkkey = self.Move_Y
                self.pd.HMI_ValueStruct.Move_Y_scale = (
                    self.pd.current_position.y * self.MINUNITMULT
                )
                self.lcd.draw_float_value(
                    True,
                    True,
                    0,
                    self.lcd.font_8x8,
                    self.color_yellow,
                    self.color_background_black,
                    3,
                    1,
                    175,
                    self.MBASE(selected_line) - 10,
                    self.pd.HMI_ValueStruct.Move_Y_scale,
                )
                self.EncoderRateLimit = False
            elif selected_line == 3:  # Z axis move
                self.checkkey = self.Move_Z
                self.pd.HMI_ValueStruct.Move_Z_scale = (
                    self.pd.current_position.z * self.MINUNITMULT
                )
                self.lcd.draw_float_value(
                    True,
                    True,
                    0,
                    self.lcd.font_8x8,
                    self.color_yellow,
                    self.color_background_black,
                    3,
                    1,
                    175,
                    self.MBASE(selected_line) - 10,
                    self.pd.HMI_ValueStruct.Move_Z_scale,
                )
                self.EncoderRateLimit = False
            elif selected_line == 4:  # Extruder
                # Check if nozzle is too cold and don't allow extrusion. Popup warning instead
                if self.pd.PREVENT_COLD_EXTRUSION:
                    if (
                        self.pd.thermalManager["temp_hotend"][0]["celsius"]
                        < self.pd.EXTRUDE_MINTEMP
                    ):
                        self.pd.HMI_flag.ETempTooLow_flag = True
                        self.Popup_Window_ETempTooLow()
                        return
                self.checkkey = self.Extruder
                self.pd.HMI_ValueStruct.Move_E_scale = (
                    self.pd.current_position.e * self.MINUNITMULT
                )
                self.lcd.draw_signed_float(
                    False,
                    self.lcd.font_8x8,
                    self.color_yellow,
                    self.color_background_black,
                    3,
                    1,
                    175,
                    self.MBASE(selected_line) - 10,
                    self.pd.HMI_ValueStruct.Move_E_scale,
                )
                self.EncoderRateLimit = False

    def HMI_Move_X(self):
        """
        Handles the X axis move logic based on the encoder input.
        """
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return
        elif encoder_diffState == self.ENCODER_DIFF_ENTER:
            # Enable change in Move X value, draw text as yellow
            self.checkkey = self.AxisMove
            self.EncoderRateLimit = True
            self.lcd.draw_float_value(
                True,
                True,
                0,
                self.lcd.font_8x8,
                self.color_yellow,
                self.color_background_black,
                3,
                1,
                175,
                self.MBASE(1) - 10,
                self.pd.HMI_ValueStruct.Move_X_scale,
            )
            self.pd.moveAbsolute("X", self.pd.current_position.x, 5000)

            return
        elif encoder_diffState == self.ENCODER_DIFF_CW:
            self.pd.HMI_ValueStruct.Move_X_scale += 1
        elif encoder_diffState == self.ENCODER_DIFF_CCW:
            self.pd.HMI_ValueStruct.Move_X_scale -= 1

        if (
            self.pd.HMI_ValueStruct.Move_X_scale
            < (self.pd.X_MIN_POS) * self.MINUNITMULT
        ):
            self.pd.HMI_ValueStruct.Move_X_scale = (
                self.pd.X_MIN_POS
            ) * self.MINUNITMULT

        if (
            self.pd.HMI_ValueStruct.Move_X_scale
            > (self.pd.X_MAX_POS) * self.MINUNITMULT
        ):
            self.pd.HMI_ValueStruct.Move_X_scale = (
                self.pd.X_MAX_POS
            ) * self.MINUNITMULT

        self.pd.current_position.x = self.pd.HMI_ValueStruct.Move_X_scale / 10
        self.lcd.draw_float_value(
            True,
            True,
            0,
            self.lcd.font_8x8,
            self.color_yellow,
            self.color_background_black,
            3,
            1,
            175,
            self.MBASE(1) - 10,
            self.pd.HMI_ValueStruct.Move_X_scale,
        )

    def HMI_Move_Y(self):
        """
        Handles the Y axis move logic based on the encoder input.
        """
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return
        elif encoder_diffState == self.ENCODER_DIFF_ENTER:
            self.checkkey = self.AxisMove
            self.EncoderRateLimit = True
            self.lcd.draw_float_value(
                True,
                True,
                0,
                self.lcd.font_8x8,
                self.color_yellow,
                self.color_background_black,
                3,
                1,
                175,
                self.MBASE(2) - 10,
                self.pd.HMI_ValueStruct.Move_Y_scale,
            )

            self.pd.moveAbsolute("Y", self.pd.current_position.y, 5000)

            return
        elif encoder_diffState == self.ENCODER_DIFF_CW:
            self.pd.HMI_ValueStruct.Move_Y_scale += 1
        elif encoder_diffState == self.ENCODER_DIFF_CCW:
            self.pd.HMI_ValueStruct.Move_Y_scale -= 1

        if (
            self.pd.HMI_ValueStruct.Move_Y_scale
            < (self.pd.Y_MIN_POS) * self.MINUNITMULT
        ):
            self.pd.HMI_ValueStruct.Move_Y_scale = (
                self.pd.Y_MIN_POS
            ) * self.MINUNITMULT

        if (
            self.pd.HMI_ValueStruct.Move_Y_scale
            > (self.pd.Y_MAX_POS) * self.MINUNITMULT
        ):
            self.pd.HMI_ValueStruct.Move_Y_scale = (
                self.pd.Y_MAX_POS
            ) * self.MINUNITMULT

        self.pd.current_position.y = self.pd.HMI_ValueStruct.Move_Y_scale / 10
        self.lcd.draw_float_value(
            True,
            True,
            0,
            self.lcd.font_8x8,
            self.color_yellow,
            self.color_background_black,
            3,
            1,
            175,
            self.MBASE(2) - 10,
            self.pd.HMI_ValueStruct.Move_Y_scale,
        )

    def HMI_Move_Z(self):
        """
        Handles the Z axis move logic based on the encoder input.
        """
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return
        elif encoder_diffState == self.ENCODER_DIFF_ENTER:
            self.checkkey = self.AxisMove
            self.EncoderRateLimit = True
            self.lcd.draw_float_value(
                True,
                True,
                0,
                self.lcd.font_8x8,
                self.color_yellow,
                self.color_background_black,
                3,
                1,
                175,
                self.MBASE(3) - 10,
                self.pd.HMI_ValueStruct.Move_Z_scale,
            )
            self.pd.moveAbsolute("Z", self.pd.current_position.z, 600)

            return
        elif encoder_diffState == self.ENCODER_DIFF_CW:
            self.pd.HMI_ValueStruct.Move_Z_scale += 1
        elif encoder_diffState == self.ENCODER_DIFF_CCW:
            self.pd.HMI_ValueStruct.Move_Z_scale -= 1

        if (
            self.pd.HMI_ValueStruct.Move_Z_scale
            < (self.pd.Z_MIN_POS) * self.MINUNITMULT
        ):
            self.pd.HMI_ValueStruct.Move_Z_scale = (
                self.pd.Z_MIN_POS
            ) * self.MINUNITMULT

        if (
            self.pd.HMI_ValueStruct.Move_Z_scale
            > (self.pd.Z_MAX_POS) * self.MINUNITMULT
        ):
            self.pd.HMI_ValueStruct.Move_Z_scale = (
                self.pd.Z_MAX_POS
            ) * self.MINUNITMULT

        self.pd.current_position.z = self.pd.HMI_ValueStruct.Move_Z_scale / 10
        self.lcd.draw_float_value(
            True,
            True,
            0,
            self.lcd.font_8x8,
            self.color_yellow,
            self.color_background_black,
            3,
            1,
            175,
            self.MBASE(3) - 10,
            self.pd.HMI_ValueStruct.Move_Z_scale,
        )

    def HMI_Move_E(self):
        """
        Handles the Extruder move logic based on the encoder input.
        """
        self.pd.last_E_scale = 0
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return

        elif encoder_diffState == self.ENCODER_DIFF_ENTER:
            self.checkkey = self.AxisMove
            self.EncoderRateLimit = True
            self.pd.last_E_scale = self.pd.HMI_ValueStruct.Move_E_scale
            self.lcd.draw_signed_float(
                True,
                self.lcd.font_8x8,
                self.color_white,
                self.color_background_black,
                3,
                1,
                175,
                self.MBASE(4) - 10,
                self.pd.HMI_ValueStruct.Move_E_scale,
            )
            self.pd.moveAbsolute("E", self.pd.current_position.e, 300)

        elif encoder_diffState == self.ENCODER_DIFF_CW:
            self.pd.HMI_ValueStruct.Move_E_scale += 1
        elif encoder_diffState == self.ENCODER_DIFF_CCW:
            self.pd.HMI_ValueStruct.Move_E_scale -= 1

        if (self.pd.HMI_ValueStruct.Move_E_scale - self.pd.last_E_scale) > (
            self.pd.EXTRUDE_MAXLENGTH
        ) * self.MINUNITMULT:
            self.pd.HMI_ValueStruct.Move_E_scale = (
                self.pd.last_E_scale + (self.pd.EXTRUDE_MAXLENGTH) * self.MINUNITMULT
            )
        elif (self.pd.last_E_scale - self.pd.HMI_ValueStruct.Move_E_scale) > (
            self.pd.EXTRUDE_MAXLENGTH
        ) * self.MINUNITMULT:
            self.pd.HMI_ValueStruct.Move_E_scale = (
                self.pd.last_E_scale - (self.pd.EXTRUDE_MAXLENGTH) * self.MINUNITMULT
            )
        self.pd.current_position.e = self.pd.HMI_ValueStruct.Move_E_scale / 10
        self.lcd.draw_signed_float(
            True,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            3,
            1,
            175,
            self.MBASE(4) - 10,
            self.pd.HMI_ValueStruct.Move_E_scale,
        )

    def HMI_Temperature(self):
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return

        if encoder_diffState == self.ENCODER_DIFF_CW:
            if self.select_temp.inc(1 + self.TEMP_CASE_TOTAL):
                self.Move_Highlight(1, self.select_temp.now)
        elif encoder_diffState == self.ENCODER_DIFF_CCW:
            if self.select_temp.dec():
                self.Move_Highlight(-1, self.select_temp.now)
        elif encoder_diffState == self.ENCODER_DIFF_ENTER:
            if self.select_temp.now == 0:  # back
                self.checkkey = self.Control
                self.select_control.set(1)
                self.index_control = self.MROWS
                self.Draw_Control_Menu()
            elif self.select_temp.now == self.TEMP_CASE_TEMP:  # Nozzle temperature
                self.checkkey = self.ETemp
                self.pd.HMI_ValueStruct.E_Temp = self.pd.thermalManager["temp_hotend"][
                    0
                ]["target"]
                self.lcd.draw_int_value(
                    True,
                    True,
                    0,
                    self.lcd.font_8x8,
                    self.color_yellow,
                    self.color_background_black,
                    3,
                    200,
                    self.MBASE(1) - 8,
                    self.pd.thermalManager["temp_hotend"][0]["target"],
                )
                self.EncoderRateLimit = False
            elif self.select_temp.now == self.TEMP_CASE_BED:  # Bed temperature
                self.checkkey = self.BedTemp
                self.pd.HMI_ValueStruct.Bed_Temp = self.pd.thermalManager["temp_bed"][
                    "target"
                ]
                self.lcd.draw_int_value(
                    True,
                    True,
                    0,
                    self.lcd.font_8x8,
                    self.color_yellow,
                    self.color_background_black,
                    3,
                    200,
                    self.MBASE(2) - 8,
                    self.pd.thermalManager["temp_bed"]["target"],
                )
                self.EncoderRateLimit = False
            elif self.select_temp.now == self.TEMP_CASE_FAN:  # Fan speed
                self.checkkey = self.FanSpeed
                self.pd.HMI_ValueStruct.Fan_speed = self.pd.thermalManager["fan_speed"][
                    0
                ]
                self.lcd.draw_int_value(
                    True,
                    True,
                    0,
                    self.lcd.font_8x8,
                    self.color_yellow,
                    self.color_background_black,
                    3,
                    200,
                    self.MBASE(3) - 8,
                    self.pd.thermalManager["fan_speed"][0],
                )
                self.EncoderRateLimit = False

            elif self.select_temp.now == self.TEMP_CASE_PLA:  # PLA preheat setting
                self.checkkey = self.PLAPreheat
                self.select_PLA.reset()
                self.pd.HMI_ValueStruct.show_mode = -2

                self.Clear_Main_Window()
                self.lcd.draw_icon(
                    False,
                    self.selected_language,
                    self.icon_TEXT_header_PLA_settings,
                    self.HEADER_HEIGHT,
                    1,
                )

                self.Draw_Back_First()
                i = 1
                self.Draw_Menu_Line_With_Only_Icons(
                    i, self.icon_SetEndTemp, self.icon_TEXT_pla_nozzle_temperature
                )  # PLA nozzle temp
                self.lcd.draw_int_value(
                    True,
                    True,
                    0,
                    self.lcd.font_8x8,
                    self.color_white,
                    self.color_background_black,
                    3,
                    200,
                    self.MBASE(i) - 8,
                    self.pd.material_preset[0].hotend_temp,
                )
                if self.pd.HAS_HEATED_BED:
                    i += 1
                    self.Draw_Menu_Line_With_Only_Icons(
                        i, self.icon_SetBedTemp, self.icon_TEXT_pla_bed_temperature
                    )  # PLA bed temp
                    self.lcd.draw_int_value(
                        True,
                        True,
                        0,
                        self.lcd.font_8x8,
                        self.color_white,
                        self.color_background_black,
                        3,
                        200,
                        self.MBASE(i) - 8,
                        self.pd.material_preset[0].bed_temp,
                    )
                if self.pd.HAS_FAN:
                    i += 1
                    self.Draw_Menu_Line_With_Only_Icons(
                        i, self.icon_FanSpeed, self.icon_TEXT_pla_fan_speed
                    )  # PLA fan speed
                    self.lcd.draw_int_value(
                        True,
                        True,
                        0,
                        self.lcd.font_8x8,
                        self.color_white,
                        self.color_background_black,
                        3,
                        200,
                        self.MBASE(i) - 8,
                        self.pd.material_preset[0].fan_speed,
                    )
                i += 1
                self.Draw_Menu_Line_With_Only_Icons(
                    i, self.icon_write_eeprom, self.icon_TEXT_save_pla_parameters
                )  # Save PLA configuration
            elif self.select_temp.now == self.TEMP_CASE_TPU:  # TPU preheat setting
                self.checkkey = self.TPUPreheat
                self.select_TPU.reset()
                self.pd.HMI_ValueStruct.show_mode = -3
                self.Clear_Main_Window()
                self.lcd.draw_icon(
                    False,
                    self.selected_language,
                    self.icon_TEXT_header_TPU_settings,
                    self.HEADER_HEIGHT,
                    1,
                )

                self.Draw_Back_First()
                i = 1
                self.Draw_Menu_Line_With_Only_Icons(
                    i, self.icon_SetEndTemp, self.icon_TEXT_tpu_nozzle_temperature
                )  # TPU nozzle temp
                self.lcd.draw_int_value(
                    True,
                    True,
                    0,
                    self.lcd.font_8x8,
                    self.color_white,
                    self.color_background_black,
                    3,
                    200,
                    self.MBASE(i) - 8,
                    self.pd.material_preset[1].hotend_temp,
                )
                if self.pd.HAS_HEATED_BED:
                    i += 1
                    self.Draw_Menu_Line_With_Only_Icons(
                        i, self.icon_SetBedTemp, self.icon_TEXT_tpu_bed_temperature
                    )  # TPU bed temp
                    self.lcd.draw_int_value(
                        True,
                        True,
                        0,
                        self.lcd.font_8x8,
                        self.color_white,
                        self.color_background_black,
                        3,
                        200,
                        self.MBASE(i) - 8,
                        self.pd.material_preset[1].bed_temp,
                    )
                if self.pd.HAS_FAN:
                    i += 1
                    self.Draw_Menu_Line_With_Only_Icons(
                        i, self.icon_FanSpeed, self.icon_TEXT_tpu_fan_speed
                    )  # TPU fan speed
                    self.lcd.draw_int_value(
                        True,
                        True,
                        0,
                        self.lcd.font_8x8,
                        self.color_white,
                        self.color_background_black,
                        3,
                        200,
                        self.MBASE(i) - 8,
                        self.pd.material_preset[1].fan_speed,
                    )
                i += 1
                self.Draw_Menu_Line_With_Only_Icons(
                    i, self.icon_write_eeprom, self.icon_TEXT_save_tpu_parameters
                )  # Save TPU configuration

    def HMI_PLAPreheatSetting(self):
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return
        # Avoid flicker by updating only the previous menu
        elif encoder_diffState == self.ENCODER_DIFF_CW:
            if self.select_PLA.inc(1 + self.PREHEAT_CASE_TOTAL):
                self.Move_Highlight(1, self.select_PLA.now)
        elif encoder_diffState == self.ENCODER_DIFF_CCW:
            if self.select_PLA.dec():
                self.Move_Highlight(-1, self.select_PLA.now)
        elif encoder_diffState == self.ENCODER_DIFF_ENTER:
            if self.select_PLA.now == 0:  # Back
                self.checkkey = self.TemperatureID
                self.select_temp.now = self.TEMP_CASE_PLA
                self.pd.HMI_ValueStruct.show_mode = -1
                self.Draw_Temperature_Menu()
            elif self.select_PLA.now == self.PREHEAT_CASE_TEMP:  # Nozzle temperature
                self.checkkey = self.ETemp
                self.pd.HMI_ValueStruct.E_Temp = self.pd.material_preset[0].hotend_temp
                self.lcd.draw_int_value(
                    True,
                    True,
                    0,
                    self.lcd.font_8x8,
                    self.color_yellow,
                    self.color_background_black,
                    3,
                    200,
                    self.MBASE(self.PREHEAT_CASE_TEMP) - 8,
                    self.pd.material_preset[0].hotend_temp,
                )
                self.EncoderRateLimit = False
            elif self.select_PLA.now == self.PREHEAT_CASE_BED:  # Bed temperature
                self.checkkey = self.BedTemp
                self.pd.HMI_ValueStruct.Bed_Temp = self.pd.material_preset[0].bed_temp
                self.lcd.draw_int_value(
                    True,
                    True,
                    0,
                    self.lcd.font_8x8,
                    self.color_yellow,
                    self.color_background_black,
                    3,
                    200,
                    self.MBASE(self.PREHEAT_CASE_BED) - 8,
                    self.pd.material_preset[0].bed_temp,
                )
                self.EncoderRateLimit = False
            elif self.select_PLA.now == self.PREHEAT_CASE_FAN:  # Fan speed
                self.checkkey = self.FanSpeed
                self.pd.HMI_ValueStruct.Fan_speed = self.pd.material_preset[0].fan_speed
                self.lcd.draw_int_value(
                    True,
                    True,
                    0,
                    self.lcd.font_8x8,
                    self.color_yellow,
                    self.color_background_black,
                    3,
                    200,
                    self.MBASE(self.PREHEAT_CASE_FAN) - 8,
                    self.pd.material_preset[0].fan_speed,
                )
                self.EncoderRateLimit = False
            elif (
                self.select_PLA.now == self.PREHEAT_CASE_SAVE
            ):  # Save PLA configuration
                success = self.pd.save_settings()
                self.HMI_AudioFeedback(success)

    def HMI_TPUPreheatSetting(self):
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return
        # Avoid flicker by updating only the previous menu
        elif encoder_diffState == self.ENCODER_DIFF_CW:
            if self.select_TPU.inc(1 + self.PREHEAT_CASE_TOTAL):
                self.Move_Highlight(1, self.select_TPU.now)
        elif encoder_diffState == self.ENCODER_DIFF_CCW:
            if self.select_TPU.dec():
                self.Move_Highlight(-1, self.select_TPU.now)
        elif encoder_diffState == self.ENCODER_DIFF_ENTER:
            if self.select_TPU.now == 0:  # Back
                self.checkkey = self.TemperatureID
                self.select_temp.now = self.TEMP_CASE_TPU
                self.pd.HMI_ValueStruct.show_mode = -1
                self.Draw_Temperature_Menu()

            elif self.select_TPU.now == self.PREHEAT_CASE_TEMP:  # Nozzle temperature
                self.checkkey = self.ETemp
                self.pd.HMI_ValueStruct.E_Temp = self.pd.material_preset[1].hotend_temp
                print(self.pd.HMI_ValueStruct.E_Temp)
                self.lcd.draw_int_value(
                    True,
                    True,
                    0,
                    self.lcd.font_8x8,
                    self.color_yellow,
                    self.color_background_black,
                    3,
                    200,
                    self.MBASE(self.PREHEAT_CASE_TEMP) - 8,
                    self.pd.material_preset[1].hotend_temp,
                )
                self.EncoderRateLimit = False
            elif self.select_TPU.now == self.PREHEAT_CASE_BED:  # Bed temperature
                self.checkkey = self.BedTemp
                self.pd.HMI_ValueStruct.Bed_Temp = self.pd.material_preset[1].bed_temp
                self.lcd.draw_int_value(
                    True,
                    True,
                    0,
                    self.lcd.font_8x8,
                    self.color_yellow,
                    self.color_background_black,
                    3,
                    200,
                    self.MBASE(self.PREHEAT_CASE_BED) - 8,
                    self.pd.material_preset[1].bed_temp,
                )
                self.EncoderRateLimit = False
            elif self.select_TPU.now == self.PREHEAT_CASE_FAN:  # Fan speed
                self.checkkey = self.FanSpeed
                self.pd.HMI_ValueStruct.Fan_speed = self.pd.material_preset[1].fan_speed
                self.lcd.draw_int_value(
                    True,
                    True,
                    0,
                    self.lcd.font_8x8,
                    self.color_yellow,
                    self.color_background_black,
                    3,
                    200,
                    self.MBASE(self.PREHEAT_CASE_FAN) - 8,
                    self.pd.material_preset[1].fan_speed,
                )
                self.EncoderRateLimit = False
            elif (
                self.select_TPU.now == self.PREHEAT_CASE_SAVE
            ):  # Save PLA configuration
                success = self.pd.save_settings()
                self.HMI_AudioFeedback(success)

    def HMI_ETemp(self):
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return

        if self.pd.HMI_ValueStruct.show_mode == -1:
            temp_line = self.TEMP_CASE_TEMP
        elif self.pd.HMI_ValueStruct.show_mode == -2:
            temp_line = self.PREHEAT_CASE_TEMP
        elif self.pd.HMI_ValueStruct.show_mode == -3:
            temp_line = self.PREHEAT_CASE_TEMP
        else:
            temp_line = self.TUNE_CASE_TEMP + self.MROWS - self.index_tune

        if encoder_diffState == self.ENCODER_DIFF_ENTER:
            self.EncoderRateLimit = True
            if self.pd.HMI_ValueStruct.show_mode == -1:  # temperature
                self.checkkey = self.TemperatureID
                self.lcd.draw_int_value(
                    True,
                    True,
                    0,
                    self.lcd.font_8x8,
                    self.color_yellow,
                    self.color_background_black,
                    3,
                    200,
                    self.MBASE(temp_line) - 8,
                    self.pd.HMI_ValueStruct.E_Temp,
                )
            elif self.pd.HMI_ValueStruct.show_mode == -2:
                self.checkkey = self.PLAPreheat
                self.pd.material_preset[0].hotend_temp = self.pd.HMI_ValueStruct.E_Temp
                self.lcd.draw_int_value(
                    True,
                    True,
                    0,
                    self.lcd.font_8x8,
                    self.color_yellow,
                    self.color_background_black,
                    3,
                    200,
                    self.MBASE(temp_line) - 8,
                    self.pd.material_preset[0].hotend_temp,
                )
                return
            elif self.pd.HMI_ValueStruct.show_mode == -3:
                self.checkkey = self.TPUPreheat
                self.pd.material_preset[1].hotend_temp = self.pd.HMI_ValueStruct.E_Temp
                self.lcd.draw_int_value(
                    True,
                    True,
                    0,
                    self.lcd.font_8x8,
                    self.color_yellow,
                    self.color_background_black,
                    3,
                    200,
                    self.MBASE(temp_line) - 8,
                    self.pd.material_preset[1].hotend_temp,
                )
                return
            else:  # tune
                self.checkkey = self.Tune
                self.lcd.draw_int_value(
                    True,
                    True,
                    0,
                    self.lcd.font_8x8,
                    self.color_yellow,
                    self.color_background_black,
                    3,
                    200,
                    self.MBASE(temp_line) - 8,
                    self.pd.HMI_ValueStruct.E_Temp,
                )
                self.pd.setTargetHotend(self.pd.HMI_ValueStruct.E_Temp, 0)
            return

        elif encoder_diffState == self.ENCODER_DIFF_CW:
            self.pd.HMI_ValueStruct.E_Temp += 1

        elif encoder_diffState == self.ENCODER_DIFF_CCW:
            self.pd.HMI_ValueStruct.E_Temp -= 1

        # E_Temp limit
        if self.pd.HMI_ValueStruct.E_Temp > self.pd.MAX_E_TEMP:
            self.pd.HMI_ValueStruct.E_Temp = self.pd.MAX_E_TEMP
        if self.pd.HMI_ValueStruct.E_Temp < self.pd.MIN_E_TEMP:
            self.pd.HMI_ValueStruct.E_Temp = self.pd.MIN_E_TEMP
        # E_Temp value
        self.lcd.draw_int_value(
            True,
            True,
            0,
            self.lcd.font_8x8,
            self.color_yellow,
            self.color_background_black,
            3,
            200,
            self.MBASE(temp_line) - 8,
            self.pd.HMI_ValueStruct.E_Temp,
        )

    def HMI_BedTemp(self):
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return

        if self.pd.HMI_ValueStruct.show_mode == -1:
            bed_line = self.TEMP_CASE_BED
        elif self.pd.HMI_ValueStruct.show_mode == -2:
            bed_line = self.PREHEAT_CASE_BED
        elif self.pd.HMI_ValueStruct.show_mode == -3:
            bed_line = self.PREHEAT_CASE_BED
        else:
            bed_line = self.TUNE_CASE_TEMP + self.MROWS - self.index_tune

        if encoder_diffState == self.ENCODER_DIFF_ENTER:
            self.EncoderRateLimit = True
            if self.pd.HMI_ValueStruct.show_mode == -1:  # temperature
                self.checkkey = self.TemperatureID
                self.lcd.draw_int_value(
                    True,
                    True,
                    0,
                    self.lcd.font_8x8,
                    self.color_yellow,
                    self.color_background_black,
                    3,
                    200,
                    self.MBASE(bed_line) - 8,
                    self.pd.HMI_ValueStruct.Bed_Temp,
                )
            elif self.pd.HMI_ValueStruct.show_mode == -2:
                self.checkkey = self.PLAPreheat
                self.pd.material_preset[0].bed_temp = self.pd.HMI_ValueStruct.Bed_Temp
                self.lcd.draw_int_value(
                    True,
                    True,
                    0,
                    self.lcd.font_8x8,
                    self.color_yellow,
                    self.color_background_black,
                    3,
                    200,
                    self.MBASE(bed_line) - 8,
                    self.pd.material_preset[0].bed_temp,
                )
                return
            elif self.pd.HMI_ValueStruct.show_mode == -3:
                self.checkkey = self.TPUPreheat
                self.pd.material_preset[1].bed_temp = self.pd.HMI_ValueStruct.Bed_Temp
                self.lcd.draw_int_value(
                    True,
                    True,
                    0,
                    self.lcd.font_8x8,
                    self.color_yellow,
                    self.color_background_black,
                    3,
                    200,
                    self.MBASE(bed_line) - 8,
                    self.pd.material_preset[1].bed_temp,
                )
                return
            else:  # tune
                self.checkkey = self.Tune
                self.lcd.draw_int_value(
                    True,
                    True,
                    0,
                    self.lcd.font_8x8,
                    self.color_yellow,
                    self.color_background_black,
                    3,
                    200,
                    self.MBASE(bed_line) - 8,
                    self.pd.HMI_ValueStruct.Bed_Temp,
                )
                self.pd.setTargetHotend(self.pd.HMI_ValueStruct.Bed_Temp, 0)
            return

        elif encoder_diffState == self.ENCODER_DIFF_CW:
            self.pd.HMI_ValueStruct.Bed_Temp += 1

        elif encoder_diffState == self.ENCODER_DIFF_CCW:
            self.pd.HMI_ValueStruct.Bed_Temp -= 1

        # Bed_Temp limit
        if self.pd.HMI_ValueStruct.Bed_Temp > self.pd.BED_MAX_TARGET:
            self.pd.HMI_ValueStruct.Bed_Temp = self.pd.BED_MAX_TARGET
        if self.pd.HMI_ValueStruct.Bed_Temp < self.pd.MIN_BED_TEMP:
            self.pd.HMI_ValueStruct.Bed_Temp = self.pd.MIN_BED_TEMP
        # Bed_Temp value
        self.lcd.draw_int_value(
            True,
            True,
            0,
            self.lcd.font_8x8,
            self.color_yellow,
            self.color_background_black,
            3,
            200,
            self.MBASE(bed_line) - 8,
            self.pd.HMI_ValueStruct.Bed_Temp,
        )

    # ---------------------Todo--------------------------------#

    def HMI_Motion(self):
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return
        if encoder_diffState == self.ENCODER_DIFF_CW:
            if self.select_motion.inc(1 + self.MOTION_CASE_TOTAL):
                self.Move_Highlight(1, self.select_motion.now)
        elif encoder_diffState == self.ENCODER_DIFF_CCW:
            if self.select_motion.dec():
                self.Move_Highlight(-1, self.select_motion.now)
        elif encoder_diffState == self.ENCODER_DIFF_ENTER:
            if self.select_motion.now == 0:  # back
                self.checkkey = self.Control
                self.select_control.set(self.CONTROL_CASE_MOVE)
                self.index_control = self.MROWS
                self.Draw_Control_Menu()
            else:
                # Max speed, acceleration and steps per mm menu
                # are not implemented yet. Popup a "feature not
                # available" window and return to motion menu
                # when confirm is pressed.
                self.popup_caller = self.Motion
                self.checkkey = self.FeatureNotAvailable
                self.Draw_FeatureNotAvailable_Popup()

    def HMI_Zoffset(self):
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return
        zoff_line = 0
        if self.pd.HMI_ValueStruct.show_mode == -4:
            zoff_line = self.PREPARE_CASE_ZOFF + self.MROWS - self.index_prepare
        else:
            zoff_line = self.TUNE_CASE_ZOFF + self.MROWS - self.index_tune

        if (
            encoder_diffState == self.ENCODER_DIFF_ENTER
        ):  # if (applyencoder(encoder_diffstate, offset_value))
            self.EncoderRateLimit = True
            if self.pd.HAS_BED_PROBE:
                self.pd.offset_z(self.dwin_zoffset)
            else:
                self.pd.setZOffset(self.dwin_zoffset)  # manually set

            self.checkkey = (
                self.Prepare if self.pd.HMI_ValueStruct.show_mode == -4 else self.Tune
            )
            self.lcd.draw_signed_float(
                True,
                self.lcd.font_8x8,
                self.color_yellow,
                self.color_background_black,
                2,
                3,
                175,
                self.MBASE(zoff_line) - 10,
                self.pd.HMI_ValueStruct.offset_value,
            )

            return

        elif encoder_diffState == self.ENCODER_DIFF_CW:
            self.pd.HMI_ValueStruct.offset_value += 1
        elif encoder_diffState == self.ENCODER_DIFF_CCW:
            self.pd.HMI_ValueStruct.offset_value -= 1

        if (
            self.pd.HMI_ValueStruct.offset_value
            < (self.pd.Z_PROBE_OFFSET_RANGE_MIN) * 100
        ):
            self.pd.HMI_ValueStruct.offset_value = (
                self.pd.Z_PROBE_OFFSET_RANGE_MIN * 100
            )
        elif (
            self.pd.HMI_ValueStruct.offset_value
            > (self.pd.Z_PROBE_OFFSET_RANGE_MAX) * 100
        ):
            self.pd.HMI_ValueStruct.offset_value = (
                self.pd.Z_PROBE_OFFSET_RANGE_MAX * 100
            )

        self.last_zoffset = self.dwin_zoffset
        self.dwin_zoffset = self.pd.HMI_ValueStruct.offset_value / 100.0
        if self.pd.HAS_BED_PROBE:
            self.pd.add_mm("Z", self.dwin_zoffset - self.last_zoffset)

        self.lcd.draw_signed_float(
            True,
            self.lcd.font_8x8,
            self.color_yellow,
            self.color_background_black,
            2,
            3,
            175,
            self.MBASE(zoff_line) - 10,
            self.pd.HMI_ValueStruct.offset_value,
        )

    def HMI_MaxSpeed(self):
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return

    def HMI_MaxAcceleration(self):
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return

    def HMI_MaxJerk(self):
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return

    def HMI_Step(self):
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return

    def HMI_MaxFeedspeedXYZE(self):
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return

    def HMI_MaxAccelerationXYZE(self):
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return

    def HMI_MaxJerkXYZE(self):
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return

    def HMI_StepXYZE(self):
        encoder_diffState = self.get_encoder_state()
        if encoder_diffState == self.ENCODER_DIFF_NO:
            return

    # --------------------------------------------------------------#

    def Draw_Status_Area(self, with_update=True):
        #  Clear the bottom area of the screen
        self.lcd.draw_rectangle(
            1,
            self.color_background_black,
            0,
            self.STATUS_Y,
            self.lcd.screen_width,
            self.lcd.screen_height - 1,
        )

        # nozzle temp area

        self.lcd.draw_icon(True, self.ICON, self.icon_hotend_temp, 6, 262)
        self.lcd.draw_int_value(
            True,
            True,
            0,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            3,
            26,
            268,
            self.pd.thermalManager["temp_hotend"][0]["celsius"],
        )
        self.lcd.draw_string(
            False,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            26 + 3 * self.STAT_CHR_W + 4,
            268,
            "/",
        )
        self.lcd.draw_int_value(
            False,
            True,
            0,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            3,
            26 + 3 * self.STAT_CHR_W + 5,
            268,
            self.pd.thermalManager["temp_hotend"][0]["target"],
        )

        # bed temp area
        self.lcd.draw_icon(True, self.ICON, self.icon_bedtemp, 6, 294)
        self.lcd.draw_int_value(
            True,
            True,
            0,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            3,
            26,
            300,
            self.pd.thermalManager["temp_bed"]["celsius"],
        )
        self.lcd.draw_string(
            False,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            26 + 3 * self.STAT_CHR_W + 4,
            300,
            "/",
        )
        self.lcd.draw_int_value(
            False,
            True,
            0,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            3,
            26 + 3 * self.STAT_CHR_W + 5,
            300,
            self.pd.thermalManager["temp_bed"]["target"],
        )

        # speed area
        self.lcd.draw_icon(True, self.ICON, self.icon_speed, 99, 262)
        self.lcd.draw_int_value(
            True,
            True,
            0,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            3,
            99 + 2 * self.STAT_CHR_W,
            268,
            self.pd.feedrate_percentage,
        )
        self.lcd.draw_string(
            False,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            99 + 5 * self.STAT_CHR_W + 2,
            268,
            "%",
        )

        # extrude area
        self.lcd.draw_icon(True, self.ICON, self.icon_MaxSpeedE, 99, 294)
        self.lcd.draw_int_value(
            True,
            True,
            0,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            3,
            99 + 2 * self.STAT_CHR_W,
            300,
            self.pd.feedrate_percentage,
        )
        self.lcd.draw_string(
            False,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            99 + 5 * self.STAT_CHR_W + 2,
            300,
            "%",
        )

        # fan speed area
        self.lcd.draw_icon(True, self.ICON, self.icon_FanSpeed, 165, 262)
        self.lcd.draw_int_value(
            True,
            True,
            0,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            3,
            165 + 2 * self.STAT_CHR_W,
            268,
            self.pd.feedrate_percentage,
        )
        self.lcd.draw_string(
            False,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            165 + 5 * self.STAT_CHR_W + 2,
            268,
            "%",
        )

        # Z offset area
        self.lcd.draw_icon(True, self.ICON, self.icon_z_offset, 165, 294)
        self.lcd.draw_signed_float(
            True,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            1,
            3,
            191,
            300,
            self.pd.BABY_Z_VAR * 100,
        )

        if with_update:
            time.sleep(0.005)

    def Draw_Title(self, title):
        self.lcd.draw_string(
            False,
            self.lcd.font_12x24,
            self.color_white,
            self.color_background_grey,
            14,
            4,
            title,
        )

    def Draw_Popup_Bkgd_105(self):
        self.lcd.draw_rectangle(
            1,
            self.color_popup_background,
            6,
            self.HEADER_HEIGHT + 6,
            self.lcd.screen_width - 6,
            self.STATUS_Y + 78,
        )

    def Draw_More_Icon(self, line):
        self.lcd.draw_icon(True, self.ICON, self.icon_more, 206, self.MBASE(line) - 14)

    def Draw_Menu_Cursor(self, line):
        self.lcd.draw_rectangle(
            1,
            self.Rectangle_color,
            0,
            self.MBASE(line) - 18,
            10,
            self.MBASE(line + 1) - 20,
        )

    def Draw_Menu_Icon(self, line, icon):
        self.lcd.draw_icon(True, self.ICON, icon, 20, self.MBASE(line) - 14)

    def Draw_Menu_Text_Icon(self, line, text_icon):
        self.lcd.draw_icon(
            True, self.selected_language, text_icon, self.LBLX, self.MBASE(line) - 16
        )

    def Draw_Menu_Line(self, line, icon=False, label=False):
        if label:
            self.lcd.draw_rectangle(
                1,
                self.color_background_black,
                self.LBLX,
                self.MBASE(line) - 5,
                self.lcd.screen_width,
                self.MBASE(line + 1) - 22,
            )
            self.lcd.draw_string(
                True,
                self.lcd.font_8x8,
                self.color_white,
                self.color_background_black,
                self.LBLX,
                self.MBASE(line) - 5,
                label,
            )
        if icon:
            self.Draw_Menu_Icon(line, icon)
        self.lcd.draw_line(
            self.color_line,
            15,
            self.MBASE(line + 1) - 22,
            235,
            self.MBASE(line + 1) - 22,
        )

    def Draw_Menu_Line_With_Only_Icons(
        self, line, icon_left=False, text_icon=False, dividing_line=True
    ):
        if icon_left:
            self.Draw_Menu_Icon(line, icon_left)
        if text_icon:
            self.lcd.draw_rectangle(
                1,
                self.color_background_black,
                self.LBLX,
                self.MBASE(line) - 5,
                self.lcd.screen_width,
                self.MBASE(line + 1) - 22,
            )
            self.Draw_Menu_Text_Icon(line, text_icon)
        if dividing_line:
            self.lcd.draw_line(
                self.color_line,
                15,
                self.MBASE(line + 1) - 22,
                235,
                self.MBASE(line + 1) - 22,
            )

    # Draw "Back" line at the top
    def Draw_Back_First(self, is_sel=True):
        self.Draw_Menu_Line_With_Only_Icons(0, self.icon_back, self.icon_TEXT_back)

        if is_sel:
            self.Draw_Menu_Cursor(0)

    def draw_move_en(self, line):
        self.lcd.move_screen_area(1, 69, 61, 102, 71, self.LBLX, line)  # "Move"

    def draw_max_en(self, line):
        self.lcd.move_screen_area(1, 245, 119, 269, 129, self.LBLX, line)  # "Max"

    def draw_max_accel_en(self, line):
        self.draw_max_en(line)
        self.lcd.move_screen_area(
            1, 1, 135, 79, 145, self.LBLX + 27, line
        )  # "Acceleration"

    def draw_speed_en(self, inset, line):
        self.lcd.move_screen_area(
            1, 184, 119, 224, 132, self.LBLX + inset, line
        )  # "Speed"

    def draw_jerk_en(self, line):
        self.lcd.move_screen_area(1, 64, 119, 106, 129, self.LBLX + 27, line)  # "Jerk"

    def draw_steps_per_mm(self, line):
        self.lcd.move_screen_area(
            1, 1, 151, 101, 161, self.LBLX, line
        )  # "Steps-per-mm"

    # Display an SD item
    def Draw_SDItem(self, item, row=0):
        fl = self.pd.GetFiles()[item]
        self.Draw_Menu_Line(row, self.icon_file, fl)

    def Draw_Select_Highlight(self, sel):
        self.pd.HMI_flag.select_flag = sel
        if sel:
            c1 = self.color_background_black
            c2 = self.color_popup_background
        else:
            c1 = self.color_popup_background
            c2 = self.color_background_black
        self.lcd.draw_rectangle(0, c1, 30, 154, 111, 185)
        self.lcd.draw_rectangle(0, c2, 129, 154, 211, 186)

    def Draw_Printing_Screen(self):
        # Tune
        self.lcd.draw_icon(True, self.ICON, self.icon_tune, 12, 191)
        self.lcd.draw_icon(False, self.selected_language, self.icon_TEXT_Tune, 12, 225)
        # Pause
        self.lcd.draw_icon(True, self.ICON, self.icon_pause, 86, 191)
        self.lcd.draw_icon(False, self.selected_language, self.icon_TEXT_Pause, 86, 225)
        # Stop
        self.lcd.draw_icon(True, self.ICON, self.icon_stop, 160, 191)
        self.lcd.draw_icon(False, self.selected_language, self.icon_TEXT_Stop, 160, 225)
        # Print elapsed time
        self.lcd.draw_icon(True, self.ICON, self.icon_print_time, 117, 77)
        self.lcd.draw_icon(
            True, self.selected_language, self.icon_text_printing_time, 170, 61
        )
        # Print remain time
        self.lcd.draw_icon(True, self.ICON, self.icon_remain_time, 117, 138)
        self.lcd.draw_icon(
            True, self.selected_language, self.icon_text_remain_time, 170, 122
        )

    def Draw_Print_ProgressBar(self, Percentrecord=None):
        if not Percentrecord:
            Percentrecord = self.pd.getPercent()
        progress_icon_id = self.icon_progress_0 + Percentrecord
        self.lcd.draw_icon(True, self.GIF_ICON, progress_icon_id, 12, 75)

    def Draw_Print_ProgressElapsed(self):
        elapsed = self.pd.duration()  # print timer
        self.lcd.draw_int_value(
            False,
            True,
            1,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            2,
            160,
            100,
            elapsed / 3600,
        )
        self.lcd.draw_string(
            False,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            183,
            100,
            ":",
        )
        self.lcd.draw_int_value(
            False,
            True,
            1,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            2,
            190,
            100,
            (elapsed % 3600) / 60,
        )

    def Draw_Print_ProgressRemain(self):
        remain_time = self.pd.remain()
        if not remain_time:
            return  # time remaining is None during warmup.
        self.lcd.draw_int_value(
            False,
            True,
            1,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            2,
            160,
            166,
            remain_time / 3600,
        )
        self.lcd.draw_string(
            False,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            183,
            166,
            ":",
        )
        self.lcd.draw_int_value(
            False,
            True,
            1,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            2,
            190,
            166,
            (remain_time % 3600) / 60,
        )

    def Draw_Print_File_Menu(self):
        self.Clear_Title_Bar()
        # Draw "File Selection" on header
        self.lcd.draw_icon(
            False,
            self.selected_language,
            self.icon_TEXT_header_file_selection,
            self.HEADER_HEIGHT,
            1,
        )
        self.Redraw_SD_List()
        self.Draw_Status_Area()

    def Draw_Prepare_Menu(self):
        self.Clear_Main_Window()
        # Draw "Prepare" on header
        self.lcd.draw_icon(
            False,
            self.selected_language,
            self.icon_TEXT_header_prepare,
            self.HEADER_HEIGHT,
            1,
        )

        scroll = self.MROWS - self.index_prepare
        # self.Frame_TitleCopy(1, 178, 2, 229, 14)  # "Prepare"
        self.Draw_Back_First(self.select_prepare.now == 0)  # < Back
        if scroll + self.PREPARE_CASE_MOVE <= self.MROWS:
            self.Item_Prepare_Move(self.PREPARE_CASE_MOVE)  # Move >
        if scroll + self.PREPARE_CASE_DISA <= self.MROWS:
            self.Item_Prepare_Disable(self.PREPARE_CASE_DISA)  # Disable Stepper
        if scroll + self.PREPARE_CASE_HOME <= self.MROWS:
            self.Item_Prepare_Home(self.PREPARE_CASE_HOME)  # Auto Home
        if self.pd.HAS_ZOFFSET_ITEM:
            if scroll + self.PREPARE_CASE_ZOFF <= self.MROWS:
                self.Item_Prepare_Offset(
                    self.PREPARE_CASE_ZOFF
                )  # Edit Z-Offset / Babystep / Set Home Offset
        if self.pd.HAS_HOTEND:
            if scroll + self.PREPARE_CASE_PLA <= self.MROWS:
                self.Item_Prepare_PLA(self.PREPARE_CASE_PLA)  # Preheat PLA
            if scroll + self.PREPARE_CASE_TPU <= self.MROWS:
                self.Item_Prepare_TPU(self.PREPARE_CASE_TPU)  # Preheat TPU
        if self.pd.HAS_PREHEAT:
            if scroll + self.PREPARE_CASE_COOL <= self.MROWS:
                self.Item_Prepare_Cool(self.PREPARE_CASE_COOL)  # Cooldown
        if self.select_prepare.now:
            self.Draw_Menu_Cursor(self.select_prepare.now)
        self.Draw_Status_Area()

    def Draw_Control_Menu(self):
        self.Clear_Main_Window()
        # Draw "Control" on header
        self.lcd.draw_icon(
            False,
            self.selected_language,
            self.icon_TEXT_header_control,
            self.HEADER_HEIGHT,
            1,
        )

        self.Draw_Back_First(self.select_control.now == 0)

        # self.Frame_TitleCopy(1, 128, 2, 176, 12)
        # self.lcd.move_screen_area(1, 1, 89, 83, 101, self.LBLX, self.MBASE(self.CONTROL_CASE_TEMP))  # Temperature >
        # self.lcd.move_screen_area(1, 84, 89, 128, 99, self.LBLX, self.MBASE(self.CONTROL_CASE_MOVE))  # Motion >
        # self.lcd.move_screen_area(1, 0, 104, 25, 115, self.LBLX, self.MBASE(self.CONTROL_CASE_INFO))  # Info >

        if self.select_control.now and self.select_control.now < self.MROWS:
            self.Draw_Menu_Cursor(self.select_control.now)

        # # Draw icons and lines
        self.Draw_Menu_Line_With_Only_Icons(
            1, self.icon_temperature, self.icon_TEXT_temperature
        )
        self.Draw_More_Icon(1)
        self.Draw_Menu_Line_With_Only_Icons(2, self.icon_motion, self.icon_TEXT_motion)
        self.Draw_More_Icon(2)
        self.Draw_Menu_Line_With_Only_Icons(3, self.icon_info, self.icon_TEXT_Info)
        self.Draw_More_Icon(3)
        self.Draw_Status_Area()

    def Draw_Leveling_Menu(self):
        self.Clear_Main_Window()

    def Draw_Info_Menu(self):
        """
        Draws the "Info" menu on the display.
        As the text stays on the bottom of each line instead of
        a normal menu item, this is manually drawn.
        """
        self.Clear_Main_Window()
        # Draw "Info" on header
        self.lcd.draw_icon(
            False,
            self.selected_language,
            self.icon_TEXT_header_info,
            self.HEADER_HEIGHT,
            1,
        )

        self.Draw_Back_First()

        # Bed size 80,95,110,140,155,170,200,215,230,260
        self.lcd.draw_icon(
            True, self.selected_language, self.icon_TEXT_bed_size, self.LBLX, 75
        )
        self.lcd.draw_icon(True, self.ICON, self.icon_PrintSize, 20, 90)
        self.lcd.draw_string(
            False,
            self.lcd.font_6x12,
            self.color_white,
            self.color_background_black,
            70,
            105,
            self.pd.MACHINE_SIZE,
        )

        # Klipper version
        self.lcd.draw_icon(
            True,
            self.selected_language,
            self.icon_TEXT_hardware_version,
            self.LBLX,
            135,
        )
        self.lcd.draw_icon(True, self.ICON, self.icon_Version, 20, 140)
        self.lcd.draw_string(
            False,
            self.lcd.font_6x12,
            self.color_white,
            self.color_background_black,
            50,
            155,
            "Klipper " + self.pd.SHORT_BUILD_VERSION,
        )

        # Contact details
        self.lcd.draw_icon(
            True, self.selected_language, self.icon_TEXT_contact, self.LBLX, 185
        )
        self.lcd.draw_icon(True, self.ICON, self.icon_Contact, 20, 200)
        self.lcd.draw_string(
            False,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            50,
            215,
            "github.com/jpcurti/",
        )
        self.lcd.draw_string(
            False,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            30,
            230,
            "E3V3SE_display_klipper",
        )
        self.Draw_Status_Area()

    def Draw_Tune_Menu(self):
        self.Clear_Main_Window()
        # Draw "Tune" on header
        self.lcd.draw_icon(
            False,
            self.selected_language,
            self.icon_TEXT_header_tune,
            self.HEADER_HEIGHT,
            1,
        )
        self.lcd.move_screen_area(1, 94, 2, 126, 12, 14, 9)
        self.lcd.move_screen_area(
            1, 1, 179, 92, 190, self.LBLX, self.MBASE(self.TUNE_CASE_SPEED)
        )  # Print speed
        if self.pd.HAS_HOTEND:
            self.lcd.move_screen_area(
                1, 197, 104, 238, 114, self.LBLX, self.MBASE(self.TUNE_CASE_TEMP)
            )  # Hotend...
            self.lcd.move_screen_area(
                1, 1, 89, 83, 101, self.LBLX + 44, self.MBASE(self.TUNE_CASE_TEMP)
            )  # Temperature
        if self.pd.HAS_HEATED_BED:
            self.lcd.move_screen_area(
                1, 240, 104, 264, 114, self.LBLX, self.MBASE(self.TUNE_CASE_BED)
            )  # Bed...
            self.lcd.move_screen_area(
                1, 1, 89, 83, 101, self.LBLX + 27, self.MBASE(self.TUNE_CASE_BED)
            )  # ...Temperature
        if self.pd.HAS_FAN:
            self.lcd.move_screen_area(
                1, 0, 119, 64, 132, self.LBLX, self.MBASE(self.TUNE_CASE_FAN)
            )  # Fan speed
        if self.pd.HAS_ZOFFSET_ITEM:
            self.lcd.move_screen_area(
                1, 93, 179, 141, 189, self.LBLX, self.MBASE(self.TUNE_CASE_ZOFF)
            )  # Z-offset
        self.Draw_Back_First(self.select_tune.now == 0)
        if self.select_tune.now:
            self.Draw_Menu_Cursor(self.select_tune.now)

        self.Draw_Menu_Line_With_Only_Icons(
            self.TUNE_CASE_SPEED, self.icon_speed, self.icon_TEXT_Printing_Speed
        )
        self.lcd.draw_int_value(
            True,
            True,
            0,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            3,
            200,
            self.MBASE(self.TUNE_CASE_SPEED) - 8,
            self.pd.feedrate_percentage,
        )

        if self.pd.HAS_HOTEND:
            self.Draw_Menu_Line_With_Only_Icons(
                self.TUNE_CASE_TEMP,
                self.icon_hotend_temp,
                self.icon_TEXT_nozzle_temperature,
            )
            self.lcd.draw_int_value(
                True,
                True,
                0,
                self.lcd.font_8x8,
                self.color_white,
                self.color_background_black,
                3,
                200,
                self.MBASE(self.TUNE_CASE_TEMP) - 8,
                self.pd.thermalManager["temp_hotend"][0]["target"],
            )

        if self.pd.HAS_HEATED_BED:
            self.Draw_Menu_Line_With_Only_Icons(
                self.TUNE_CASE_BED, self.icon_bedtemp, self.icon_TEXT_bed_temperature
            )
            self.lcd.draw_int_value(
                True,
                True,
                0,
                self.lcd.font_8x8,
                self.color_white,
                self.color_background_black,
                3,
                200,
                self.MBASE(self.TUNE_CASE_BED) - 8,
                self.pd.thermalManager["temp_bed"]["target"],
            )

        if self.pd.HAS_FAN:
            self.Draw_Menu_Line_With_Only_Icons(
                self.TUNE_CASE_FAN, self.icon_FanSpeed, self.icon_TEXT_fan_speed
            )
            self.lcd.draw_int_value(
                True,
                True,
                0,
                self.lcd.font_8x8,
                self.color_white,
                self.color_background_black,
                3,
                200,
                self.MBASE(self.TUNE_CASE_FAN) - 8,
                self.pd.thermalManager["fan_speed"][0],
            )
        if self.pd.HAS_ZOFFSET_ITEM:
            self.Draw_Menu_Line_With_Only_Icons(
                self.TUNE_CASE_ZOFF, self.icon_z_offset, self.icon_TEXT_Z_Offset
            )
            self.lcd.draw_signed_float(
                True,
                self.lcd.font_8x8,
                self.color_white,
                self.color_background_black,
                2,
                3,
                175,
                self.MBASE(self.TUNE_CASE_ZOFF) - 10,
                self.pd.BABY_Z_VAR * 100,
            )

    def Draw_Temperature_Menu(self):
        self.Clear_Main_Window()
        # Draw "Temperature" on header
        self.lcd.draw_icon(
            False,
            self.selected_language,
            self.icon_TEXT_header_temperature,
            self.HEADER_HEIGHT,
            1,
        )

        self.Draw_Back_First(self.select_temp.now == 0)
        if self.select_temp.now:
            self.Draw_Menu_Cursor(self.select_temp.now)

        # Draw icons and lines
        i = 0
        if self.pd.HAS_HOTEND:
            i += 1
            # self.Draw_Menu_Line( self.TEMP_CASE_TEMP, self.icon_SetEndTemp, "Nozzle Temperature")
            self.Draw_Menu_Line_With_Only_Icons(
                self.TEMP_CASE_TEMP,
                self.icon_SetEndTemp,
                self.icon_TEXT_nozzle_temperature,
            )
            self.lcd.draw_int_value(
                True,
                True,
                0,
                self.lcd.font_8x8,
                self.color_white,
                self.color_background_black,
                3,
                200,
                self.MBASE(i) - 8,
                self.pd.thermalManager["temp_hotend"][0]["target"],
            )
        if self.pd.HAS_HEATED_BED:
            i += 1
            # self.Draw_Menu_Line( (self.TEMP_CASE_BED), self.icon_SetEndTemp, "Bed Temperature")
            self.Draw_Menu_Line_With_Only_Icons(
                self.TEMP_CASE_BED, self.icon_SetEndTemp, self.icon_TEXT_bed_temperature
            )
            self.lcd.draw_int_value(
                True,
                True,
                0,
                self.lcd.font_8x8,
                self.color_white,
                self.color_background_black,
                3,
                200,
                self.MBASE(i) - 8,
                self.pd.thermalManager["temp_bed"]["target"],
            )
        if self.pd.HAS_FAN:
            i += 1
            self.Draw_Menu_Line_With_Only_Icons(
                (self.TEMP_CASE_FAN),
                self.icon_SetEndTemp,
                self.icon_TEXT_nozzle_temperature,
            )
            self.lcd.draw_int_value(
                True,
                True,
                0,
                self.lcd.font_8x8,
                self.color_white,
                self.color_background_black,
                3,
                200,
                self.MBASE(i) - 8,
                self.pd.thermalManager["fan_speed"][0],
            )
        if self.pd.HAS_HOTEND:
            # PLA/TPU items have submenus
            i += 1
            self.Draw_Menu_Line_With_Only_Icons(
                self.TEMP_CASE_PLA,
                self.icon_SetEndTemp,
                self.icon_TEXT_preheat_pla_settings,
            )
            self.Draw_More_Icon(i)
            i += 1
            self.Draw_Menu_Line_With_Only_Icons(
                self.TEMP_CASE_TPU,
                self.icon_SetEndTemp,
                self.icon_TEXT_preheat_tpu_settings,
            )
            self.Draw_More_Icon(i)

    def Draw_Motion_Menu(self):
        self.Clear_Main_Window()
        # Draw "Motion" on header
        self.lcd.draw_icon(
            False,
            self.selected_language,
            self.icon_TEXT_header_motion,
            self.HEADER_HEIGHT,
            1,
        )
        self.draw_max_en(self.MBASE(self.MOTION_CASE_RATE))
        self.draw_speed_en(27, self.MBASE(self.MOTION_CASE_RATE))  # "Max Speed"
        self.draw_max_accel_en(self.MBASE(self.MOTION_CASE_ACCEL))  # "Max Acceleration"
        self.draw_steps_per_mm(self.MBASE(self.MOTION_CASE_STEPS))  # "Steps-per-mm"

        self.Draw_Back_First(self.select_motion.now == 0)
        if self.select_motion.now:
            self.Draw_Menu_Cursor(self.select_motion.now)

        self.Draw_Menu_Line_With_Only_Icons(
            self.MOTION_CASE_RATE, self.icon_MaxSpeed, self.icon_TEXT_max_speed
        )
        self.Draw_More_Icon(self.MOTION_CASE_RATE)

        self.Draw_Menu_Line_With_Only_Icons(
            self.MOTION_CASE_ACCEL,
            self.icon_MaxAccelerated,
            self.icon_TEXT_max_acceleration,
        )
        self.Draw_More_Icon(self.MOTION_CASE_ACCEL)

        self.Draw_Menu_Line_With_Only_Icons(
            self.MOTION_CASE_STEPS, self.icon_Step, self.icon_TEXT_steps_per_mm
        )
        self.Draw_More_Icon(self.MOTION_CASE_STEPS)

    def Draw_Move_Menu(self):
        """
        Only visual: Draws the "Move" menu on the display.

        This method clears the main window and then proceeds to draw the "Move" header.
        It also draws the options for moving the X, Y, and Z axes, as well as the extruder
        option if available. It also handles drawing the menu cursor and separators.
        """
        self.Clear_Main_Window()
        # Draw "Move" on header
        self.lcd.draw_icon(
            False,
            self.selected_language,
            self.icon_TEXT_header_move,
            self.HEADER_HEIGHT,
            1,
        )

        self.Draw_Back_First(self.select_axis.now == 0)
        if self.select_axis.now:
            self.Draw_Menu_Cursor(self.select_axis.now)

        line_count = 1
        self.Draw_Menu_Line_With_Only_Icons(
            line_count, self.icon_move_x, self.icon_TEXT_move_x
        )
        self.lcd.draw_float_value(
            True,
            True,
            0,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            3,
            1,
            175,
            self.MBASE(line_count) - 10,
            self.pd.current_position.x * self.MINUNITMULT,
        )

        line_count += 1
        self.Draw_Menu_Line_With_Only_Icons(
            line_count, self.icon_move_y, self.icon_TEXT_move_y
        )
        self.lcd.draw_float_value(
            True,
            True,
            0,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            3,
            1,
            175,
            self.MBASE(line_count) - 10,
            self.pd.current_position.y * self.MINUNITMULT,
        )

        line_count += 1
        self.Draw_Menu_Line_With_Only_Icons(
            line_count, self.icon_move_z, self.icon_TEXT_move_z
        )
        self.lcd.draw_float_value(
            True,
            True,
            0,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            3,
            1,
            175,
            self.MBASE(line_count) - 10,
            self.pd.current_position.z * self.MINUNITMULT,
        )

        line_count += 1
        self.Draw_Menu_Line_With_Only_Icons(
            line_count, self.icon_move_e, self.icon_TEXT_move_e
        )
        self.lcd.draw_float_value(
            True,
            True,
            0,
            self.lcd.font_8x8,
            self.color_white,
            self.color_background_black,
            3,
            1,
            175,
            self.MBASE(line_count) - 10,
            self.pd.current_position.e * self.MINUNITMULT,
        )

    def Goto_MainMenu(self):
        self.checkkey = self.MainMenu
        self.Clear_Screen()
        # Draw "Main" on header
        self.lcd.draw_icon(
            True, self.selected_language, self.icon_TEXT_header_main, 29, 1
        )

        self.icon_Print()
        self.icon_Prepare()
        self.icon_Control()
        if self.pd.HAS_ONESTEP_LEVELING:
            self.icon_Leveling(self.select_page.now == 3)
        else:
            self.icon_StartInfo(self.select_page.now == 3)

    def Goto_PrintProcess(self):
        self.checkkey = self.PrintProcess
        self.Clear_Main_Window()
        # Draw "Printing" on header
        self.lcd.draw_icon(
            True, self.selected_language, self.icon_TEXT_header_printing, 29, 1
        )
        self.Draw_Printing_Screen()

        self.show_tune()
        if self.pd.printingIsPaused():
            self.show_continue()
        else:
            self.show_pause()
        self.show_stop()

        # Copy into filebuf string before entry
        name = self.pd.file_name
        if name:
            npos = _MAX(0, self.lcd.screen_width - len(name) * self.MENU_CHR_W) / 2
            self.lcd.draw_string(
                False,
                self.lcd.font_6x12,
                self.color_white,
                self.color_background_black,
                npos,
                40,
                name,
            )

        self.Draw_Print_ProgressBar()
        self.Draw_Print_ProgressElapsed()
        self.Draw_Print_ProgressRemain()
        self.Draw_Status_Area()

    # --------------------------------------------------------------#
    # --------------------------------------------------------------#

    def Clear_Title_Bar(self):
        self.lcd.draw_rectangle(
            1,
            self.color_background_grey,
            0,
            0,
            self.lcd.screen_width,
            self.HEADER_HEIGHT,
        )

    def Clear_Menu_Area(self):
        self.lcd.draw_rectangle(
            1,
            self.color_background_black,
            0,
            self.HEADER_HEIGHT,
            self.lcd.screen_width,
            self.STATUS_Y,
        )

    def Clear_Status_Area(self):
        self.lcd.draw_rectangle(
            1,
            self.color_background_black,
            0,
            self.STATUS_Y,
            self.lcd.screen_width,
            self.lcd.screen_height,
        )

    def Clear_Main_Window(self):
        self.Clear_Title_Bar()
        self.Clear_Menu_Area()

    def Clear_Screen(self):
        self.Clear_Title_Bar()
        self.Clear_Menu_Area()
        self.Clear_Status_Area()

    def Clear_Popup_Area(self):
        self.Clear_Title_Bar()
        self.lcd.draw_rectangle(
            1,
            self.color_background_black,
            0,
            31,
            self.lcd.screen_width,
            self.lcd.screen_height,
        )

    def Popup_window_PauseOrStop(self):
        self.Clear_Main_Window()
        if self.select_print.now == 1:
            self.lcd.draw_icon(
                True,
                self.selected_language,
                self.icon_popup_pause_print,
                15,
                self.HEADER_HEIGHT + 50,
            )

        elif self.select_print.now == 2:
            self.lcd.draw_icon(
                True,
                self.selected_language,
                self.icon_popup_stop_print,
                15,
                self.HEADER_HEIGHT + 50,
            )
        self.lcd.draw_rectangle(
            0, self.color_white, 15, self.HEADER_HEIGHT + 50, 225, 195
        )
        self.lcd.draw_icon(
            True,
            self.selected_language,
            self.icon_confim_button_hovered,
            30,
            self.HEADER_HEIGHT + 130,
        )
        self.lcd.draw_icon(
            True,
            self.selected_language,
            self.icon_cancel_button_hovered,
            130,
            self.HEADER_HEIGHT + 130,
        )
        self.Draw_Select_Highlight(True)

    def Popup_Window_Home(self):
        """
        Displays a popup window indicating that the printer is homing.
        """
        self.Clear_Main_Window()
        self.lcd.draw_icon(
            True,
            self.selected_language,
            self.icon_popup_homing,
            18,
            self.HEADER_HEIGHT + 60,
        )

    def Popup_Window_ETempTooLow(self):
        """
        Displays a popup window indicating that the extruder temperature is too low.
        """
        self.Clear_Main_Window()
        self.lcd.draw_rectangle(
            1, self.color_popup_background, 15, self.HEADER_HEIGHT + 50, 225, 195
        )
        self.lcd.draw_icon(
            True,
            self.selected_language,
            self.icon_popup_nozzle_temp_too_low,
            15,
            self.HEADER_HEIGHT + 50,
        )
        self.lcd.draw_rectangle(
            0, self.color_white, 15, self.HEADER_HEIGHT + 50, 225, 195
        )

        # Draw ok button
        self.lcd.draw_icon(
            True, self.selected_language, self.icon_confim_button_hovered, 80, 154
        )
        self.lcd.draw_rectangle(0, self.color_white, 80, 154, 160, 185)

    def Draw_FeatureNotAvailable_Popup(self):
        """
        Displays a popup window indicating that this feature is not available.
        """
        # self.Clear_Main_Window()
        self.lcd.draw_rectangle(
            1, self.color_popup_background, 15, self.HEADER_HEIGHT + 50, 225, 195
        )
        self.lcd.draw_rectangle(
            0, self.color_white, 15, self.HEADER_HEIGHT + 50, 225, 195
        )
        # Draw text with "Feature not available on the screen. Please use klipper"
        self.lcd.draw_string(
            False,
            self.lcd.font_8x8,
            self.color_white,
            self.color_popup_background,
            20,
            self.HEADER_HEIGHT + 55,
            "Feature not available on",
        )
        self.lcd.draw_string(
            False,
            self.lcd.font_8x8,
            self.color_white,
            self.color_popup_background,
            20,
            self.HEADER_HEIGHT + 75,
            "the screen yet, please",
        )
        self.lcd.draw_string(
            False,
            self.lcd.font_8x8,
            self.color_white,
            self.color_popup_background,
            20,
            self.HEADER_HEIGHT + 95,
            "use the klipper interface.",
        )
        # Draw ok button
        self.lcd.draw_icon(
            True, self.selected_language, self.icon_confim_button_hovered, 80, 154
        )
        self.lcd.draw_rectangle(0, self.color_white, 80, 154, 160, 185)

    def Erase_Menu_Cursor(self, line):
        self.lcd.draw_rectangle(
            1,
            self.color_background_black,
            0,
            self.MBASE(line) - 18,
            14,
            self.MBASE(line + 1) - 20,
        )

    def Erase_Menu_Text(self, line):
        self.lcd.draw_rectangle(
            1,
            self.color_background_black,
            self.LBLX,
            self.MBASE(line) - 14,
            271,
            self.MBASE(line) + 28,
        )

    def Move_Highlight(self, ffrom, newline):
        self.Erase_Menu_Cursor(newline - ffrom)
        self.Draw_Menu_Cursor(newline)

    def Add_Menu_Line(self):
        self.Move_Highlight(1, self.MROWS)
        self.lcd.draw_line(
            self.color_line,
            18,
            self.MBASE(self.MROWS + 1) - 22,
            238,
            self.MBASE(self.MROWS + 1) - 22,
        )

    def Scroll_Menu(self, dir):
        self.lcd.move_screen_area(
            dir,
            self.MLINE,
            self.color_background_grey,
            12,
            self.HEADER_HEIGHT,
            self.lcd.screen_width - 1,
            self.STATUS_Y,
        )
        if dir == self.scroll_down:
            self.Move_Highlight(-1, 0)
        elif dir == self.scroll_up:
            self.Add_Menu_Line()

    # Redraw the first set of SD Files
    def Redraw_SD_List(self):
        self.select_file.reset()
        self.index_file = self.MROWS
        self.Clear_Menu_Area()  # Leave title bar unchanged, clear only middle of screen
        self.Draw_Back_First()
        fl = self.pd.GetFiles()
        ed = len(fl)
        if ed > 0:
            if ed > self.MROWS:
                ed = self.MROWS
            for i in range(ed):
                self.Draw_SDItem(i, i + 1)
        else:
            self.lcd.draw_rectangle(
                1,
                self.color_Bg_Red,
                11,
                25,
                self.MBASE(3) - 10,
                self.lcd.screen_width - 10,
                self.MBASE(4),
            )
            self.lcd.draw_string(
                False,
                self.lcd.font_16x32,
                self.color_yellow,
                self.color_Bg_Red,
                ((self.lcd.screen_width) - 8 * 16) / 2,
                self.MBASE(3),
                "No Media",
            )

    def CompletedHoming(self):
        self.pd.HMI_flag.home_flag = False
        if self.checkkey == self.Last_Prepare:
            self.checkkey = self.Prepare
            self.select_prepare.now = self.PREPARE_CASE_HOME
            self.index_prepare = self.MROWS
            self.Draw_Prepare_Menu()
        elif self.checkkey == self.Back_Main:
            self.pd.HMI_ValueStruct.print_speed = self.pd.feedrate_percentage = 100
            # dwin_zoffset = TERN0(HAS_BED_PROBE, probe.offset.z)
            # planner.finish_and_disable()
            self.Goto_MainMenu()

    # --------------------------------------------------------------#
    # --------------------------------------------------------------#

    def icon_Print(self):
        if self.select_page.now == 0:
            self.lcd.draw_icon(True, self.ICON, self.icon_print_selected, 12, 51)
            self.lcd.draw_icon(
                True, self.selected_language, self.icon_TEXT_Print_selected, 13, 120
            )
            self.lcd.draw_rectangle(0, self.color_white, 12, 51, 112, 165)
            # self.lcd.move_screen_area(1, 1, 451, 31, 463, 57, 201)
        else:
            self.lcd.draw_icon(True, self.ICON, self.icon_print, 12, 51)
            self.lcd.draw_icon(
                True, self.selected_language, self.icon_TEXT_Print, 13, 120
            )
            # self.lcd.move_screen_area(1, 1, 423, 31, 435, 57, 201)

    def icon_Prepare(self):
        if self.select_page.now == 1:
            self.lcd.draw_icon(True, self.ICON, self.icon_prepare_selected, 126, 51)
            self.lcd.draw_icon(
                True, self.selected_language, self.icon_TEXT_Prepare_selected, 127, 120
            )
            self.lcd.draw_rectangle(0, self.color_white, 126, 51, 226, 165)
            # self.lcd.move_screen_area(1, 33, 451, 82, 466, 175, 201)
        else:
            self.lcd.draw_icon(True, self.ICON, self.icon_prepare, 126, 51)
            self.lcd.draw_icon(
                True, self.selected_language, self.icon_TEXT_Prepare, 127, 120
            )
            # self.lcd.move_screen_area(1, 33, 423, 82, 438, 175, 201)

    def icon_Control(self):
        if self.select_page.now == 2:
            self.lcd.draw_icon(True, self.ICON, self.icon_control_selected, 12, 178)
            self.lcd.draw_icon(
                True, self.selected_language, self.icon_TEXT_Control_selected, 13, 247
            )
            self.lcd.draw_rectangle(0, self.color_white, 12, 178, 112, 292)
            # self.lcd.move_screen_area(1, 85, 451, 132, 463, 48, 318)
        else:
            self.lcd.draw_icon(True, self.ICON, self.icon_control, 12, 178)
            self.lcd.draw_icon(
                True, self.selected_language, self.icon_TEXT_Control, 13, 247
            )
            # self.lcd.move_screen_area(1, 85, 423, 132, 434, 48, 318)

    def icon_Leveling(self, show):
        if show:
            self.lcd.draw_icon(True, self.ICON, self.icon_leveling_selected, 126, 178)
            self.lcd.draw_icon(
                True, self.selected_language, self.icon_TEXT_Leveling_selected, 126, 247
            )
            self.lcd.draw_rectangle(0, self.color_white, 126, 178, 226, 292)
            # self.lcd.move_screen_area(1, 84, 437, 120, 449, 182, 318)
        else:
            self.lcd.draw_icon(True, self.ICON, self.icon_leveling, 126, 178)
            self.lcd.draw_icon(
                True, self.selected_language, self.icon_TEXT_Leveling, 126, 247
            )
            # self.lcd.move_screen_area(1, 84, 465, 120, 478, 182, 318)

    def icon_StartInfo(self, show):
        if show:
            self.lcd.draw_icon(True, self.ICON, self.icon_Info_1, 145, 246)
            self.lcd.draw_rectangle(0, self.color_white, 126, 178, 226, 292)
            # self.lcd.move_screen_area(1, 132, 451, 159, 466, 186, 318)
        else:
            self.lcd.draw_icon(True, self.ICON, self.icon_Info_0, 145, 246)
            # self.lcd.move_screen_area(1, 132, 423, 159, 435, 186, 318)

    def show_tune(self):
        if self.select_print.now == 0:
            self.lcd.draw_icon(True, self.ICON, self.icon_tune_selected, 12, 191)
            self.lcd.draw_icon(
                False, self.selected_language, self.icon_TEXT_Tune_selected, 12, 225
            )
            self.lcd.draw_rectangle(0, self.color_white, 12, 191, 78, 251)
        else:
            self.lcd.draw_icon(True, self.ICON, self.icon_tune, 12, 191)
            self.lcd.draw_icon(
                False, self.selected_language, self.icon_TEXT_Tune, 12, 225
            )

    def show_continue(self):
        # Todo: Where is icon for continue text? replace for text if not found
        if self.select_print.now == 1:
            self.lcd.draw_icon(True, self.ICON, self.icon_continue_selected, 86, 191)
            self.lcd.draw_icon(
                False, self.selected_language, self.icon_TEXT_Pause_selected, 86, 225
            )
            self.lcd.draw_rectangle(0, self.color_white, 86, 191, 151, 251)
        else:
            self.lcd.draw_icon(True, self.ICON, self.icon_continue, 86, 191)
            self.lcd.draw_icon(
                False, self.selected_language, self.icon_TEXT_Pause, 86, 225
            )
            # self.lcd.move_screen_area(1, 1, 424, 31, 434, 121, 325)

    def show_pause(self):
        if self.select_print.now == 1:
            self.lcd.draw_icon(True, self.ICON, self.icon_pause_selected, 86, 191)
            self.lcd.draw_icon(
                False, self.selected_language, self.icon_TEXT_Pause_selected, 86, 225
            )
            self.lcd.draw_rectangle(0, self.color_white, 86, 191, 151, 251)
        else:
            self.lcd.draw_icon(True, self.ICON, self.icon_pause, 86, 191)
            self.lcd.draw_icon(
                False, self.selected_language, self.icon_TEXT_Pause, 86, 225
            )

    def show_stop(self):
        if self.select_print.now == 2:
            self.lcd.draw_icon(True, self.ICON, self.icon_stop_selected, 160, 191)
            self.lcd.draw_icon(
                False, self.selected_language, self.icon_TEXT_Stop_selected, 160, 225
            )
            self.lcd.draw_rectangle(0, self.color_white, 160, 191, 225, 251)

        else:
            self.lcd.draw_icon(True, self.ICON, self.icon_stop, 160, 191)
            self.lcd.draw_icon(
                False, self.selected_language, self.icon_TEXT_Stop, 160, 225
            )

    def Item_Prepare_Move(self, row):
        # Draw Move icon and text
        self.draw_move_en(self.MBASE(row))
        self.Draw_Menu_Line_With_Only_Icons(
            row, self.icon_axis, self.icon_TEXT_move_axis
        )
        self.Draw_More_Icon(row)

    def Item_Prepare_Disable(self, row):
        # Draw Disable Stepper icon and text
        self.Draw_Menu_Line_With_Only_Icons(
            row, self.icon_close_motor, self.icon_TEXT_disable_stepper
        )

    def Item_Prepare_Home(self, row):
        # Draw auto home icon and text
        self.Draw_Menu_Line_With_Only_Icons(
            row, self.icon_homing, self.icon_TEXT_auto_home
        )

    def Item_Prepare_Offset(self, row):
        if self.pd.HAS_BED_PROBE:
            # Draw Z-offset icon and text, iv available
            self.Draw_Menu_Line_With_Only_Icons(
                row, self.icon_z_offset, self.icon_TEXT_Z_Offset
            )
            self.lcd.draw_signed_float(
                True,
                self.lcd.font_8x8,
                self.color_white,
                self.color_background_black,
                2,
                3,
                175,
                self.MBASE(row) - 10,
                self.pd.BABY_Z_VAR * 100,
            )
        else:
            # If not, dont write text, only icon
            self.Draw_Menu_Line(row, self.icon_set_home, "...")

    def Item_Prepare_PLA(self, row):
        # Draw preheat pla icon and text
        self.Draw_Menu_Line_With_Only_Icons(
            row, self.icon_preheat_pla, self.icon_TEXT_preheat_pla
        )

    def Item_Prepare_TPU(self, row):
        # Draw preheat tpu icon and text
        self.Draw_Menu_Line_With_Only_Icons(
            row, self.icon_preheat_tpu, self.icon_TEXT_preheat_tpu
        )

    def Item_Prepare_Cool(self, row):
        # Draw cooldown icon and text
        self.Draw_Menu_Line_With_Only_Icons(
            row, self.icon_cool, self.icon_TEXT_cooldown
        )

    # --------------------------------------------------------------#
    # --------------------------------------------------------------#

    def EachMomentUpdate(self):
        # variable update
        update = self.pd.update_variable()
        if self.last_status != self.pd.status:
            self.last_status = self.pd.status
            print(self.pd.status)
            if self.pd.status == "printing":
                self.Goto_PrintProcess()
            elif self.pd.status in ["operational", "complete", "standby", "cancelled"]:
                self.Goto_MainMenu()

        if self.checkkey == self.PrintProcess:
            if self.pd.HMI_flag.print_finish and not self.pd.HMI_flag.done_confirm_flag:
                self.pd.HMI_flag.print_finish = False
                self.pd.HMI_flag.done_confirm_flag = True
                # show percent bar and value
                self.Draw_Print_ProgressBar(0)
                # show print done confirm
                self.lcd.draw_rectangle(
                    1,
                    self.color_background_black,
                    0,
                    250,
                    self.lcd.screen_width - 1,
                    self.STATUS_Y,
                )
                self.lcd.draw_icon(
                    True,
                    self.selected_language,
                    self.icon_confim_button_hovered,
                    86,
                    283,
                )
            elif self.pd.HMI_flag.pause_flag != self.pd.printingIsPaused():
                # print status update
                self.pd.HMI_flag.pause_flag = self.pd.printingIsPaused()
                if self.pd.HMI_flag.pause_flag:
                    self.show_continue()
                else:
                    self.show_pause()
            self.Draw_Print_ProgressBar()
            self.Draw_Print_ProgressElapsed()
            self.Draw_Print_ProgressRemain()

        if self.pd.HMI_flag.home_flag:
            if self.pd.ishomed():
                self.CompletedHoming()

        if update and self.checkkey != self.MainMenu:
            self.Draw_Status_Area(update)

    def encoder_has_data(self, val):
        if self.checkkey == self.MainMenu:
            self.HMI_MainMenu()
        elif self.checkkey == self.SelectFile:
            self.HMI_SelectFile()
        elif self.checkkey == self.Prepare:
            self.HMI_Prepare()
        elif self.checkkey == self.Control:
            self.HMI_Control()
        elif self.checkkey == self.PrintProcess:
            self.HMI_Printing()
        elif self.checkkey == self.Print_window:
            self.HMI_PauseOrStop()
        elif self.checkkey == self.AxisMove:
            self.HMI_AxisMove()
        elif self.checkkey == self.TemperatureID:
            self.HMI_Temperature()
        elif self.checkkey == self.Motion:
            self.HMI_Motion()
        elif self.checkkey == self.Info:
            self.HMI_Info()
        elif self.checkkey == self.Tune:
            self.HMI_Tune()
        elif self.checkkey == self.PLAPreheat:
            self.HMI_PLAPreheatSetting()
        elif self.checkkey == self.TPUPreheat:
            self.HMI_TPUPreheatSetting()
        elif self.checkkey == self.MaxSpeed:
            self.HMI_MaxSpeed()
        elif self.checkkey == self.MaxAcceleration:
            self.HMI_MaxAcceleration()
        elif self.checkkey == self.MaxJerk:
            self.HMI_MaxJerk()
        elif self.checkkey == self.Step:
            self.HMI_Step()
        elif self.checkkey == self.Move_X:
            self.HMI_Move_X()
        elif self.checkkey == self.Move_Y:
            self.HMI_Move_Y()
        elif self.checkkey == self.Move_Z:
            self.HMI_Move_Z()
        elif self.checkkey == self.Extruder:
            self.HMI_Move_E()
        elif self.checkkey == self.ETemp:
            self.HMI_ETemp()
        elif self.checkkey == self.Homeoffset:
            self.HMI_Zoffset()
        elif self.checkkey == self.BedTemp:
            self.HMI_BedTemp()
        # elif self.checkkey == self.FanSpeed:
        #     self.HMI_FanSpeed()
        elif self.checkkey == self.PrintSpeed:
            self.HMI_PrintSpeed()
        elif self.checkkey == self.MaxSpeed_value:
            self.HMI_MaxFeedspeedXYZE()
        elif self.checkkey == self.MaxAcceleration_value:
            self.HMI_MaxAccelerationXYZE()
        elif self.checkkey == self.MaxJerk_value:
            self.HMI_MaxJerkXYZE()
        elif self.checkkey == self.Step_value:
            self.HMI_StepXYZE()
        elif self.checkkey == self.FeatureNotAvailable:
            self.HMI_FeatureNotAvailable()

    def get_encoder_state(self):
        if self.EncoderRateLimit:
            if self.EncodeMS > current_milli_time():
                return self.ENCODER_DIFF_NO
            self.EncodeMS = current_milli_time() + self.ENCODER_WAIT

        if self.encoder.value < self.EncodeLast:
            self.EncodeLast = self.encoder.value
            return self.ENCODER_DIFF_CW
        elif self.encoder.value > self.EncodeLast:
            self.EncodeLast = self.encoder.value
            return self.ENCODER_DIFF_CCW
        elif not GPIO.input(self.button_pin):
            if self.EncodeEnter > current_milli_time():  # prevent double clicks
                return self.ENCODER_DIFF_NO
            self.EncodeEnter = current_milli_time() + self.ENCODER_WAIT_ENTER
            return self.ENCODER_DIFF_ENTER
        else:
            return self.ENCODER_DIFF_NO

    def HMI_AudioFeedback(self, success=True):
        if success:
            self.pd.buzzer.tone(100, 659)
            self.pd.buzzer.tone(10, 0)
            self.pd.buzzer.tone(100, 698)
        else:
            self.pd.buzzer.tone(40, 440)
