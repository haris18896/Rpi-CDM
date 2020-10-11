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

enrol = 31
delet = 32
inc = 39
dec = 40
led = 18

HIGH = 1
LOW = 0

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

#####################################################################################################

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
                overwrite = input("Overwite (Y/N)? ")

                if overwrite[0] == 'Y' or overwrite[0] == 'y':
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

            database.commit()

            lcd.clear()
            lcd.message("User " + new_name + "\nSaved")
            time.sleep(2)
    finally:
        GPIO.cleanup()

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
                db.commit()
            else:
                lcd.message("User does not exist.")
            time.sleep(2)
    finally:
        GPIO.cleanup()

#########################################   Fingerprint   ###############################################################

# Finger Print
GPIO.setup(enrol, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(delet, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(inc, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(dec, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(led, GPIO.OUT)

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
        print('Template already exists at position #' + str(positionNumber))
        lcd.clear()
        lcd.message("Finger already Exist")
        time.sleep(2)
        return
    print("Remove Finger")
    lcd.clear()
    lcd.message("Remove Finger")
    time.sleep(2)
    print('Waiting for same finger again...')
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


def deleteFinger():
    positionNumber = 0
    count = 0
    lcd.clear()
    lcd.message("Delete Finger" + str(count))
    while GPIO.input(enrol) == True:  # here enrol key means ok
        if GPIO.input(inc) == False:
            count = count + 1
            if count > 1000:
                count = 1000
            lcd.clear()
            lcd.message(str(count))
            time.sleep(0.2)
        elif GPIO.input(dec) == False:
            count = count - 1
            if count < 0:
                count = 0
                lcd.clear()
                lcd.message(str(count))
                time.sleep(0.2)
        positionNumber = count
        if f.deleteTemplate(positionNumber) == True:
            lcd.clear()
            lcd.message("Fingerprint deleted")
            time.sleep(2)



########################################### Keyboard ########################################
# Keyboard
""" Keyboard allows user to enter a password for reconfirmaton, and a code,
    If the C-button is pressed on keypad, the input is reset, and if A-button is pressed
    the input is checked """


keypadPressed = -1
# TODO: Make a Database model for secretCode
secretCode = "4789"
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
def checkSpecialKeys():
    global input
    pressed = False

    GPIO.output(L3, GPIO.HIGH)

    if (GPIO.input(C4) == 1):
        lcd.clear()
        lcd.message("Input reset!")
        pressed = True

    GPIO.output(L3, GPIO.LOW)
    GPIO.output(L1, GPIO.HIGH)

    if (not pressed and GPIO.input(C4) == 1):
        lcd.clear()
        lcd.message("Enter the Secret code")

        if input == secretCode:
            lcd.clear()
            lcd.message("Code Correct! ")
            # TODO: Access to the Account
        else:
            lcd.clear()
            lcd.message("Code Incorrect! ")
            # TODO: Sending a 4 digit pin to user phone usiing GSM
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


#########################################   Sending Message   ###############################################################

def setup():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(P_BUTTON, GPIO.IN, GPIO.PUD_UP)

SERIAL_PORT = "/dev/ttyS0"    # Raspberry Pi 3

ser = serial.Serial(SERIAL_PORT, baudrate = 9600, timeout = 5)
setup()
ser.write("AT+CMGF=1\r") # set to text mode
time.sleep(3)
ser.write('AT+CMGDA="DEL ALL"\r') # delete all SMS
time.sleep(3)
reply = ser.read(ser.inWaiting()) # Clean buf
print ("Listening for incomming SMS...")
while True:
    reply = ser.read(ser.inWaiting())
    if reply != "":
        ser.write("AT+CMGR=1\r") 
        time.sleep(3)
        reply = ser.read(ser.inWaiting())
        print ("SMS received. Content:")
        print (reply)
        if "getStatus" in reply:
            t = str(datetime.datetime.now())
            if GPIO.input(P_BUTTON) == GPIO.HIGH:
                state = "Button released"
            else:
                state = "Button pressed"
            ser.write('AT+CMGS="{{user_phone}}"\r',)
            time.sleep(3)
            msg = "Sending status at " + t + ":--" + state
            print ("Sending SMS with status info:" + msg)
            ser.write(msg + chr(26))
        time.sleep(3)
        ser.write('AT+CMGDA="DEL ALL"\r') # delete all
        time.sleep(3)
        ser.read(ser.inWaiting()) # Clear buf
    time.sleep(5)

#########################################   MAIN   ###############################################################

def main():
    print("working")
    keypadPressed = -1
    # main.fingerprint
    while 1:
        GPIO.output(led, HIGH)
        lcd.clear()
        lcd.message("Place Finger")
        if GPIO.input(enrol) == 0:
            GPIO.output(led, LOW)
            enrollFinger()
        elif GPIO.input(delet) == 0:
            GPIO.output(led, LOW)
            while GPIO.input(delet) == 0:
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


