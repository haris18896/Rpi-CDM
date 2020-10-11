from Adafruit_Python_CharLCD import adafruit_Charlcd as LCD
from PyFingerprint import PyFingerprint

from mfrc522 import SimpleMFRC522
import Rpi.GPIO as GPIO
import smbus
import serial
import adafruit_fingerprint
import select
import string
import socket
import sys
import os
import json
import socket
import sqlite3
import time
import datetime
import MDB_protocol
import random


# from MDB_protocol import server_prel_messages, prel_serial_number, mdb_bill_silent_poll, mdb_bill_prel_messages

# GPIO pins and variables
lcd = LCD.Adafruit_CharLCD(2, 24, 35, 36, 37, 38, 16, 2, 4)

L1 = 5
L2 = 6
L3 = 10
L4 = 32
C1 = 12
C2 = 16
C3 = 20
C4 = 33


P_BUTTON = 24 # Button, adapt to your wiring

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


########################################### Keyboard ########################################
# Keyboard
""" Keyboard allows user to enter a password for reconfirmaton, and a code,
    If the C-button is pressed on keypad, the input is reset, and if A-button is pressed
    the input is checked """

conn = sqlite3.connect("database.sql")
cursor = conn.cursor()
lcd.clear()
lcd.message("Database connected successfully")

keypadPressed = -1
cursor.execute("SELECT id FROM users WHERE PIN=" + str(id))
#SecretCode = "4789"
input = ""


# Setup GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)  # Broadcom SOC channel

GPIO.setup(L1, GPIO.OUT)
GPIO.setup(L2, GPIO.OUT)
GPIO.setup(L3, GPIO.OUT)
GPIO.setup(L4, GPIO.OUT)

# Use the internal pull-down resistors
GPIO.setup(C1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(C2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(C3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(C4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


# This callback registers the key that was pressed, if no other key is currently pressed
def keypadCallback(channel):
    global keypadPressed
    if keypadPressed == -1:
        keypadPressed = channel


# Detecting the Rising edges on the column lines of the keypad, this way we can detect if the user presses a button, when we send a pulse.
GPIO.add_event_detect(C1, GPIO.RISING, callback=keypadCallback)
GPIO.add_event_detect(C2, GPIO.RISING, callback=keypadCallback)
GPIO.add_event_detect(C3, GPIO.RISING, callback=keypadCallback)
GPIO.add_event_detect(C4, GPIO.RISING, callback=keypadCallback)


# sets all the lines to a specific state. this is helper for detecting when the user releases a button
def setAllLines(state):
    GPIO.output(L1, state)
    GPIO.output(L2, state)
    GPIO.output(L3, state)
    GPIO.output(L4, state)



# Checking Special characters , C-button to reset, A-button to check input
def checkSpecialKeys(_pin):
    global input
    pressed = False
    lcd.clear()
    lcd.message("Enter the Secret code")
    cursor.execute("SELECT id FROM users WHERE PIN=" +str(id))
    secretcode = cursor.fetchone()
    # using fingerprint or RFID
    lcd.clear()
    fp_or_rfid = lcd.message("Press A for using Fingerprint and B for RFID (A/B)")
    if cursor.rowcount >= 1:
        lcd.clear()
        lcd.message("Code Correct! ")
        time.sleep(.5)
        if fp_or_rfid[0] == 'A' or fp_or_rfid[0] == 'a':
            lcd.clear()
            lcd.message("place your finger")
            searchFinger()
            if searchFinger:
                pass
            else:
                return False
        elif fp_or_rfid[0] == 'B' or fp_or_rfid[0] == 'b':
            lcd.clear()
            lcd.message("place your card Tag")
            RFID_Read()
            if RFID_Read:
                pass
            else:
                return False
    else:
        lcd.clear()
        lcd.message("Code Incorrect! ")
        GSM()
        if GSM:
            pass
        else:
            return False
    pressed = True

    GPIO.output(L3, GPIO.LOW)

    if pressed:
        input = ""

    return pressed


# reads the columns and appends the value , that corresponds to the buttoon , to a variable
def readLine(line, characters):
    global input
    # Sending a pulse on each line to detect the button pressed
    GPIO.output(line, GPIO.HIGH)
    if (GPIO.input(C1) == 1):
        input = input + characters[0]
    if (GPIO.input(C2) == 1):
        input = input + characters[1]
    if (GPIO.input(C3) == 1):
        input = input + characters[2]
    if (GPIO.input(C4) == 1):
        input = input + characters[3]
    GPIO.output(line, GPIO.LOW)



####################################    RFID  read and Write  #####################################################

def RFID_Read():
    conn = sqlite3.connect("database.sql")
    cursor = conn.cursor()
    reader = SimpleMFRC522()

    try:
        while True:
            lcd.clear()
            lcd.message('Place Card to\nregister')
            id, text = reader.read()

            cursor.execute("SELECT id FROM users WHERE rfid_uid=" + str(id))
            result = cursor.fetchone()

            if cursor.rowcount >= 1:
                lcd.clear()
                lcd.message("Overwrite\nexisting user?")
                overwrite = input("Overwite (A/C)? ")

                if overwrite[0] == 'A' or overwrite[0] == 'a':
                    lcd.clear()
                    lcd.message("Overwriting user.")
                    time.sleep(1)
                    sql_insert = "UPDATE users SET name = %s WHERE rfid_uid=%s"
                    lcd.message("User Overwritten")
                else:
                    continue
            else:
                sql_insert = "INSERT INTO users (name, rfid_uid) VALUES (%s, %s)"
            lcd.clear()
            lcd.message('Enter new name')
            new_name = input("Name: ")

            cursor.execute(sql_insert, (new_name, id))

            conn.commit()

            lcd.clear()
            lcd.message("User " + new_name + "\nSaved")
            time.sleep(2)
    finally:
        GPIO.cleanup()
        conn.close()

        # RFID Write
def RFID_Write():
    conn = sqlite3.connect("database.sql")
    cursor = conn.cursor()
    reader = SimpleMFRC522()

    try:
        while True:
            lcd.clear()
            lcd.message('Place Card to\ngrant Access')
            id, text = reader.read()

            cursor.execute("Select id, name FROM users WHERE rfid_uid=" + str(id))
            result = cursor.fetchone()

            lcd.clear()

            if cursor.rowcount >= 1:
                lcd.message("Welcome " + result[1])
                cursor.execute("INSERT INTO Reading_card (user_id) VALUES (%s)", (result[0],))
                conn.commit()
            else:
                lcd.message("User does not exist.")
            time.sleep(2)
    finally:
        GPIO.cleanup()
        conn.close()

#########################################   Fingerprint   ###############################################################

# Finger Print

# USB/serial converter
try:
    f = PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000)

    if (f.verifyPassword() == False):
        lcd.clear()
        lcd.message("fingerprint error")
        raise ValueError('The given fingerprint sensor password is wrong!')

except Exception as e:
    lcd.clear()
    lcd.message("Exception message" + str(e))
    print('Exception message: ' + str(e))
    exit(1)


def searchFinger():
    try:
        print('Waiting for finger...')
        while (f.readImage() == False):
            # pass
            time.sleep(.5)
            return
        f.convertImage(0x01)
        result = f.searchTemplate()
        positionNumber = result[0]
        accuracyScore = result[1]

        if positionNumber == -1:
            lcd.clear()
            lcd.message("No match found !")
            time.sleep(2)
        else:
            lcd.clear()
            lcd.message("Found Template at postion #" + str(positionNumber))
            time.sleep(2)
    except Exception as e:
        lcd.clear()
        lcd.message("Operation Failed")
        time.sleep(0.5)
        lcd.clear()
        lcd.message("Exception message: " + str(e))
        exit(1)


def enrollFinger():
    lcd.clear()
    lcd.message("Enrolling Finger...")
    time.sleep(2)
    print("waiting for finger....")
    lcd.clear()
    lcd.message("Place Finger")
    while (f.readImage() == False):
        pass
    f.convertImage(0x01)  # convert to hexa decimal

    result = f.searchTemplate()
    positionNumber = result[0]
    if (positionNumber >= 0):
        lcd.clear()
        lcd.message("Finger already Exist #" + str(positionNumber))
        time.sleep(2)
        return
    lcd.clear()
    lcd.message("Remove Finger")
    time.sleep(2)
    lcd.clear()
    lcd.message("Place Finger again")
    while (f.readImage() == False):
        pass
    f.convertImage(0x02)

    if (f.compareCharacteristics() == 0):
        print("Fingers not match")
        lcd.clear()
        lcd.message("Finger not Matched")
        time.sleep(2)
        return
    f.createTemplate()
    positionNumber = f.storeTemplate()
    print('Finger enrolled successfully!')
    lcd.clear()
    lcd.message("Fnger enrolled successfuly !")
    lcd.clear()
    lcd.message("stored at pos: " + str(positionNumber) + "successfully")
    time.sleep(2)

#########################################   GSM   ###############################################################
def GSM():
    OTP = str(random.randit(0,9))
    conn = sqlite3.connect("database.sql")
    cursor = conn.cursor()
    phone = cursor.execute("SELECT id from users WHERE phone_number=" + str(id))
    GPIO.setmode(GPIO.BOARD)
    port = serial.Serial(“/dev/ttyS0”, baudrate=9600, timeout=1)

    port.write(b’AT\r’)
    rcv = port.read(10)
    print(rcv)
    time.sleep(1)

    port.write(b”AT+CMGF=1\r”)
    print(“Text Mode Enabled…”)
    time.sleep(3)

    port.write(b’AT+CMGS=phone″\r’)
    msg = “Your new PIN is ....$s ” % OTP 
    lcd.clear()
    lcd.message("sending message....")
    time.sleep(3)
    port.reset_output_buffer()      # clear the output buffer
    time.sleep(1)
    port.write(str.encode(msg+chr(26))) #concatenate the message
    time.sleep(3)
    lcd.clear()
    lcd.message("Message sent,....")
    sql_insert = "UPDATE users SET PIN = %s WHERE phone_number = %s"
    cursor.execute(sql_insert,(OTP, phone))
    conn.commit()
    lcd.clear()
    lcd.message("Password updated, check you phone")

#########################################   MAIN   ###############################################################

def main():
    print("Fingerprint....")
    keypadPressed = -1
    # main.fingerprint
    while 1:
        lcd.clear()
        enroll = lcd.message('enroll finger (D/d)')
        time.sleep(0.5)
        lcd.message("Place Finger")
        if keypadPressed('A'):
            enrollFinger()
        elif keypadPressed('D'):
            while keypadPressed('D'):
                time.sleep(0.1)
                deleteFinger()
        else:
            searchFinger()


    # main.keyboard
    try:
        while True:
            # if a button was previously pressed, check, wheather the user has released it yet
            if keypadPressed != -1:
                setAllLines(GPIO.HIGH)
                if GPIO.input(keypadPressed) == 0:
                    keypadPressed = -1
                else:
                    time.sleep(0.1)
            # otherwise just read the input
            else:
                if not checkSpecialKeys():
                    readLine(L1, ["1", "2", "3", "A"])
                    readLine(L2, ["4", "5", "6", "B"])
                    readLine(L3, ["7", "8", "9", "C"])
                    readLine(L4, ["*", "0", "#", "D"])
                    time.sleep(0.1)
                else:
                    time.sleep(0.1)
    except KeyboardInterrupt:
        lcd.clear()
        lcd.message("Application Stopped")



##########################################    Main Procedure of Bill Acceptor usinf MDB protocol  #####################################################

def MainProcedure():
    if len(sys.argv) < 2:
        lcd.clear()
        lcd.message("You have to give me the serial port as a parameter :-)")
        sys.exit(1)
    host = "0.0.0.0"
    port = 5127
    _first_loop = True
    lcd.clear()
    lcd.message("GPIO initiated....")
    #raspigpio_raspivend_init()
    #raspigpio_set_value(raspigpio_mdb_rts(),raspigpio_off())
    try:
        lcd.clear()
        lcd.message("Opening Serial port...")
        ser = serial.Serial(port=sys.argv[1], baudrate=115200, timeout=0.3, rtscts=False)
        if ser.isOpen() == False:
            lcd.clear()
            lcd.message("cannot open serial port...")
            sys.exit(2)
        else:
            ser.rts = False
            lcd.clear()
            lcd.message("Serial port opened")
    except:
        lcd.clear()
        lcd.message("Error opening serial port")
        sys.exit(3)
    try:
        conn = socket.socket()
        conn.bind((host, port))
        conn.listen(1)
        lcd.clear()
        lcd.message("Listening on port " + str(port))
        sock, addr = conn.accept()
        time.sleep(1)

        sock.send('{"AppName" : "Rpi_CDM", "version" : "1.0", "createdBy" : "UET Abbottabad campus"}\r\n'.encode())

    except:
        lcd.clear()
        lcd.message("Cannot open socket for listen port.")
        lcd.clear()
        lcd.message("may be the port is in use")
        sys.exit(4)

    while True:
        _str = ""
        ser.flush()
        _sock_ready = select.select([sock], [], [], 0.01)
        # if something on scoket executed do this
        if _sock_ready[0]:
            _str = sock.recv(128)
            if len(_str) > 3:
                #parse and exceute received command
                MDB_protocol.server_prel_messages(_str)
            else:
                lcd.clear()
                lcd.message("command too short")
                if len(_str) == 0:
                    lcd.clear()
                    lcd.message("Listening again....")
                    conn.listen(1)
                    sock, addr = conn.accept()
                    sock.setblocking(0)
                    lcd.clear()
                    lcd.message("connection opend...")
                    sock.send(json.dumps({"AppName": "Rpi_CDM", "version" : "1.0", "createdBy" : "UET Abbottabad campus"}).encode() + b"\r\n")
                else:
                    _json_string = '{"Error":"Syntax error","ErrorCode","1001"}\r\n'
                    sock.send(_json_string.encode())
                    
            _str = ser.read(128)
            if len(_str) > 0 and (_str[0] == 0xFE) & (_str[1] == 0x0E):
                MDB_protocol.prel_serial_number(_str)
            # MDB poolling , if previously iniated
            if bill_inited:
                time.sleep(0.01)
                _result, bill_poll_response = MDB_protocol.mdb_bill_silent_poll()
                if _result:
                    MDB_protocol.mdb_bill_prel_messages()
    conn.close()
        
        
if __name__ == '__main__':
    MainProcedure()
    main()


