from pyfingerprint.pyfingerprint import PyFingerprint
from mfrc522 import SimpleMFRC522

import Adafruit_CharLCD as LCD
import Rpi.GPIO as gpio
import smbus
import adafruit_fingerprint
import select
import string
import socket
import serial
import sys
import os
import json
import socket
import sqlite3
import time


bill_settings = []
bill_expansion = []
bill_stacker = 0  # current number of bills in stacker
bill_poll_response = []
bill_inited = False
bill_level = 0
bill_scaling_factor = 0
bill_value = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
bill_decimal_places = 0
bill_stacker_cappacity = 0
bill_recycling_option = False
bill_timeout = 0.001
bill_previous_status = 0x00

day_of_week = [
    "Unset",
    "Sun",
    "Mon",
    "Tue",
    "Wed",
    "Thu",
    "Fri",
    "Sat"
]