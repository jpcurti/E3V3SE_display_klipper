#!/usr/bin/env python3
import sys
import os
import argparse
import configparser

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from e3v3se_display.display_interface import E3V3SE_DISPLAY

languages = {
    'chinese': 2,
    'english': 4,
    'german': 6,
    'russian': 9,
    'french': 12,
    'turkish': 15,
    'spanish': 17,
    'italian': 19,
    'portuguese': 21,
    'japanese': 23,
    'korean': 25
}

def load_config(config_file):
    if not os.path.isfile(config_file):
        print(f"Error: {config_file} is not a valid file.")
        return None
    config = configparser.ConfigParser()
    config.read(config_file)
    return config

def main():
    parser = argparse.ArgumentParser(description="Ender 3 V3 SE Display Interface for Klipper")
    parser.add_argument('--config', help='Configuration file location', default= 'config.ini')
    parser.add_argument('--com_port', help='COM Port that the display is connected to')
    parser.add_argument('--baud', type=int, help='Baudrate')
    parser.add_argument('--klipper_api_key', help='Klipper API key')
    parser.add_argument('--klipper_socket', help='Klipper socket on host')
    parser.add_argument('--language', help='Language, see docs for available languages')
   
    
    args = parser.parse_args()
    
    if args.config :
        config = load_config(args.config)
        if config:
            if not args.com_port:
                args.com_port = config.get('Display', 'com_port')
            if not args.baud:
                args.baud = config.get('Display', 'baud')
            if not args.klipper_api_key:
                args.klipper_api_key = config.get('Klipper', 'klipper_api_key')
            if not args.klipper_socket:
                args.klipper_socket = config.get('Klipper', 'klipper_socket')
            if not args.language:
                args.language = config.get('General', 'language', fallback='english')
        else:
            parser.error("When using config file as parameter, make sure the file path is correct.")
    else:
        if not args.com_port or not args.baud or not args.gpio_wheel_button_left or not args.gpio_wheel_button_right or not args.gpio_wheel_button_click or not args.klipper_api_key or not args.klipper_socket:
            parser.error("When using command-line parameters, all other parameters are required.")

    display = E3V3SE_DISPLAY(
        args.com_port,
        args.baud,
        args.klipper_api_key,
        args.klipper_socket,
        languages.get(args.language)
    )

if __name__ == "__main__":
    main()
    

