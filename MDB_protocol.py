from Adafruit_Python_CharLCD import adafruit_Charlcd as LCD
import socket

import serial
import cctalk_hopper_init
import cctalk_hopper_dispense_normal
import cctal
import time
import sys

host = "0.0.0.0"
port = 5127
conn = socket.socket()
conn.bind((host, port))
conn.listen(1)
sock, addr = conn.accept()

lcd = LCD.Adafruit_CharLCD(2, 24, 35, 36, 37, 38, 16, 2, 4)
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


def rtc_set(_psir):
    # rtc: Real time clock
    # extracting hour
    _tmp_string = _psir
    _start = _tmp_string.find("(")
    _end = _tmp_string.find(",", _start)
    if (_start == -1) | (_end == -1):
        _json_string = '{"RTCSet": -1}\r\n'
        sock.send(_json_string.encode())
        return False
    try:
        _hour = int(_tmp_string[_start + 1:_end]) & 0b01111111
        _hour = int(str(_hour), 16)
    except:
        _json_string = '{"RTCSet": -1}\r\n'
        sock.send(_json_string.encode())
        return False

    # extracting minutes
    _start = _tmp_string.find(",", _end)
    _end = _tmp_string.find(",", _start + 1)
    if (_start == -1) | (_end == -1):
        _json_string = '{"RTCSet": -1}\r\n'
        sock.send(_json_string.encode())
        return False
    try:
        _minutes = int(_tmp_string[_start + 1:_end]) & 0xFF
        _minutes = int(str(_minutes), 16)
    except:
        _json_string = '{"RTCSet": -1}\r\n'
        sock.send(_json_string.encode())
        return False

    # extracting seconds
    _start = _tmp_string.find(",", _end)
    _end = _tmp_string.find(",", _start + 1)
    if (_start == -1) | (_end == -1):
        _json_string = '{"RTCSet": -1}\r\n'
        sock.send(_json_string.encode())
        return False
    try:
        _seconds = int(_tmp_string[_start + 1:_end]) & 0xFF
        _seconds = int(str(_seconds), 16)
    except:
        _json_string = '{"RTCSet": -1}\r\n'
        sock.send(_json_string.encode())
        return False

    # extracting day in month
    _start = _tmp_string.find(",", _end)
    _end = _tmp_string.find(",", _start + 1)
    if (_start == -1) | (_end == -1):
        _json_string = '{"RTCSet": -1}\r\n'
        sock.send(_json_string.encode())
        return False
    try:
        _day = int(_tmp_string[_start + 1:_end]) & 0xFF
        _day = int(str(_day), 16)
    except:
        _json_string = '{"RTCSet": -1}\r\n'
        g.sock.send(_json_string.encode())
        return False

    # extracting month
    _start = _tmp_string.find(",", _end)
    _end = _tmp_string.find(",", _start + 1)
    if (_start == -1) | (_end == -1):
        _json_string = '{"RTCSet": -1}\r\n'
        sock.send(_json_string.encode())
        return False
    try:
        _month = int(_tmp_string[_start + 1:_end]) & 0xFF
        _month = int(str(_month), 16)
    except:
        _json_string = '{"RTCSet": -1}\r\n'
        sock.send(_json_string.encode())
        return False

    # extracting year
    _start = _tmp_string.find(",", _end)
    _end = _tmp_string.find(",", _start + 1)
    if (_start == -1) | (_end == -1):
        _json_string = '{"RTCSet": -1}\r\n'
        sock.send(_json_string.encode())
        return False
    try:
        _year = int(_tmp_string[_start + 1:_end]) & 0xFF
        _year = int(str(_year), 16)

    except:
        _json_string = '{"RTCSet": -1}\r\n'
        sock.send(_json_string.encode())
        return False

    # extracting day of week
    _start = _tmp_string.find(",", _end)
    _end = _tmp_string.find(")", _start + 1)
    if (_start == -1) | (_end == -1):
        _json_string = '{"RTCSet": -1}\r\n'
        sock.send(_json_string.encode())
        return False
    try:
        _weekday = int(_tmp_string[_start + 1:_end]) & 0xFF
        _weekday = int(str(_weekday), 16)
    except:
        _json_string = '{"RTCSet": -1}\r\n'
        sock.send(_json_string.encode())
        return False

    _serial_string = [0xFE, 0x01]
    _serial_string.append(_seconds)
    _serial_string.append(_minutes)
    _serial_string.append(_hour)
    _serial_string.append(_weekday)
    _serial_string.append(_day)
    _serial_string.append(_month)
    _serial_string.append(_year)
    # crc: Cyclic Redundancy check
    _crc = 0
    for _i in range(0, len(_serial_string)):
        _crc = _crc + _serial_string[_i]
    #    _crc = _crc & 0x00FF
    _serial_string.append(mdb_add_crc(_serial_string))
    _result, _str = mdb_send_command(_serial_string, 0.2, 40)
    if (len(_str) > 4) & (_result):
        if _str[1] == 0xFC:
            _json_string = '{"RTCSet": 0}\r\n'
        else:
            _json_string = '{"RTCSet": -1}\r\n'
            sock.send(_json_string.encode())
            return False
    else:
        _json_string = '{"RTCSet": -1}\r\n'  # no answer from the interface
        return False
    sock.send(_json_string.encode())
    return True

def rtc_get(_psir):
    # extracting hour
    _serial_string = [0xFE, 0x02]
    _crc = 0
    for _i in range(0, len(_serial_string)):
        _crc = _crc + _serial_string[_i]
    #    _crc = _crc & 0x00FF
    _serial_string.append(mdb_add_crc(_serial_string))
    print("Trimite")
    _result, _str = mdb_send_command(_serial_string, 0.5, 40)
    if (len(_str) > 4) & (_result):
        if (_str[0] == 0xFE) & (_str[1] == 0x02):
            # if here, then it has received the RTC timestamp
            # extracting seconds
            _seconds = ((_str[2] & 0b01110000) >> 4) * 10
            _seconds += _str[2] & 0b00001111
            # extracting day of week
            _day_of_week = _str[5] & 0b00000111
            if _day_of_week > 7:
                _day_of_week = 0x00
            # extracting minutes
            _minutes = ((_str[3] & 0b01110000) >> 4) * 10
            _minutes += _str[3] & 0b00001111
            if _minutes > 59:
                _day_of_week = 0x00
            # extracting hours
            _hours = ((_str[4] & 0b00110000) >> 4) * 10
            _hours += _str[4] & 0b00001111
            # extracting day of month
            _day_of_month = ((_str[6] & 0b00110000) >> 4) * 10
            _day_of_month += _str[6] & 0b00001111
            # extracting month
            _month = ((_str[7] & 0b00010000) >> 4) * 10
            _month += _str[7] & 0b00001111
            # extracting year
            _year = ((_str[8] & 0b11110000) >> 4) * 10
            _year += _str[8] & 0b00001111

            _timestamp_human = str(_hours).zfill(2) + ":" + str(_minutes).zfill(2) + ":" + str(_seconds).zfill(2)
            _timestamp_human += " " + str(_day_of_month).zfill(2) + "-" + str(_month).zfill(2) + "-" + str(
                _year + 2000)
            _timestamp_human += " " + day_of_week[_day_of_week]
            print("Board date/time " + _timestamp_human)

            _json_string = '{"RTCGet": ['
            _json_string += str(_hours) + ","
            _json_string += str(_minutes) + ","
            _json_string += str(_seconds) + ","
            _json_string += str(_day_of_month) + ","
            _json_string += str(_month) + ","
            _json_string += str(_year) + ","
            _json_string += str(_day_of_week) + "]"
            _json_string += '}\r\n'
        else:
            _json_string = '{"RTCGet": -1}\r\n'
            sock.send(_json_string.encode())
            return False
    else:
        _json_string = '{"RTCGet": -1}\r\n'  # no answer from the interface
        return False
    sock.send(_json_string.encode())
    return True


# MDB check for CRC: Cyclic redundancy check
def mdb_check_crc(_string):
    if len(_string) == 1:
        if (_string[0] == 0x00) | (_string[0] == 0xFF):
            return True
        else:
            return False
    
    if _string[0] == 0xFD:
        return False

    _mdb_crc = 0
    for _i in range(0,len(_string),-1):
        _mdb_crc += _string[_i]
    _mdb_crc = _mdb_crc & 0xFE
    if _mdb_crc == _string[len(_string)-1]:
        return True
    else:
        return False
    
# add MDB_CRC 
def mdb_add_crc(_input):
    _crc = 0
    for _i in range(0,len(_input)):
        _crc  += _input[_i]
    _crc_o = _crc & 0xFF    # crcc output
    return _crc_o

# MDB hexa decimal Masking function
def mdb_hex_dump(_str):
    _string =""
    for _i in range(0, len(_str)):
        _tmp_hex = hex(_str[_i])[2:]
        if len(_tmp_hex) == 1:
            _tmp_hex = "0x0" + _tmp_hex
        else:
            _tmp_hex = "0x" + _tmp_hex
        _string += _tmp_hex + ""
    lcd.clear()
    lcd.message(_string)

# Sending Acknowledge command
def mdb_bill_send_ack():
    _tmp_string = [0x00]
    _result,_response = mdb_send_command(_tmp_string,bill_timeout,40)

# Sending not-Acknowledge command
def mdb_bill_send_nack():
    _tmp_string = [0xFF]
    _result,_response = mdb_send_command(_tmp_string, bill_timeout,40)

# Bill Timeout
def mdb_bill_timeout(_string):
    _start = _string.find("(", 1)
    _end = _string.find(")", 1)
    if (_start == -1) | (_end == -1):
        lcd.clear()
        lcd.message("syntax Error")
        sock.send('{"MDBBillTimeout": 0}'.encode()+b"\r\n")
        return False
    try:
        bill_timeout = float(_string[_start + 1:_end])
        sock.send('{"MDBBillTimeout": 0}'.encode()+b"\r\n")
        return True
    except:
        lcd.clear()
        lcd.message("Non-Numeric Timeout")
        sock.send('{"MDBBillTimeout": -1}'.encode()+b"\r\n")
        return False

def mdb_bill_accept():
    _tmp_string=[0x35,0x01]
    _tmp_string.append(mdb_add_crc(_tmp_string))
    lcd.clear()
    lcd.message("Message to device")
    mdb_hex_dump(_tmp_string)
    _result,_response = mdb_send_command(_tmp_string,bill_timeout,40)
    if _result:
        lcd.clear()
        lcd.message("Message from device")
        mdb_hex_dump(_response)
        if _response[0]==0x00:
            sock.send('{"MDBBIllAcceptBillInEscrow": 0}'.encode()+b"\r\n")
            return True
        else:
            sock.send('{"MDBBIllAcceptBillInEscrow": -1}'.encode()+b"\r\n")
            return False
    else:
        sock.send('{"MDBBIllAcceptBillInEscrow": -1}'.encode()+b"\r\n")
        return False

def mdb_bill_reject():
    tmp_string=[0x35,0x00,0x35]
    print("Message to device")
    lcd.clear()
    lcd.message("Message to device")
    mdb_hex_dump(_tmp_string)
    _result,_response = mdb_send_command(_tmp_string,bill_timeout,40)
    if _result:
        lcd.clear()
        lcd.message("Message from device")
        mdb_hex_dump(_response)
        if _response[0]==0x00:
            sock.send('{"MDBBIllRejectBillInEscrow": 0}'.encode()+b"\r\n")
            return True
        else:
            sock.send('{"MDBBIllRejectBillInEscrow": -1}'.encode()+b"\r\n")
            return False
    else:
        sock.send('{"MDBBIllRejectBillInEscrow": -1}'.encode()+b"\r\n")
        return False


# send command to the MDB interface and get the answer if any 
def mdb_send_command(_command, _timeout, _length):
    ser = serial.Serial(port=sys.argv[1], baudrate=115200, timeout=0.3, rtscts=False)
    ser.baudrate = 115200
    _tmp_string=_command
    ser.timeout = _timeout
    _now = time.time()
    _timeout = _now + 1.5
    ser.rts = True
    while (ser.cts == False) & (_now < _timeout):
        time.sleep(0.05)
        _now = time.time()
        pass
    if ser.cts == False:
        return False,[0xFF]
    ser.write(_tmp_string)
    ser.rts = False
    while (ser.cts == True):
        #time.sleep(0.005)
        pass
    time.sleep(_timeout)
    _tmp_string=ser.read(ser.in_waiting)
    if len(_tmp_string)==0:
        return False,[0xFF]
    return True,_tmp_string

# MDB bill initiates
def mdb_bill_init():

    # checking for JUST RESET
    _tmp_string=[0x33,0x33]
    _result,_response = mdb_send_command(_tmp_string,bill_timeout,40)
    _retry = 0
    while (_response[0] != 0x06) & (_retry <10):
        time.sleep(0.2)
        _result,_response = mdb_send_command(_tmp_string,bill_timeout,40)
        _retry += 1
    if _result:
        if mdb_check_crc(_response):
            mdb_bill_send_ack()
            lcd.clear()
            lcd.message("Message from device...")
            mdb_hex_dump(_response)
            if _response[0] == 0x06:
                lcd.clear()
                lcd.message("Got Bill Just Reset")
            else:
                sock.send('{"MDBBIllInit": -1}'.encode()+b"\r\n")
                return False
        else:
            mdb_bill_send_nack()
            lcd.clear()
            lcd.message("Message from device...")
            mdb_hex_dump(_response)
            lcd.clear()
            lcd.message("CRC failed on Just Reset poll")
            sock.send('{"MDBBIllInit": -1}'.encode()+b"\r\n")
            return False

    else:
        sock.send('{"MDBBIllInit": -1}'.encode()+b"\r\n")
        return False

    # checking for level and configuration
    time.sleep(0.2)
    _tmp_string=[0x31,0x31]
    lcd.clear()
    lcd.message("Message from device...")
    mdb_hex_dump(_tmp_string)
    _result,_response = mdb_send_command(_tmp_string,bill_timeout,40)
    _retry = 0
    while (_result == False) & (_retry <10):
        time.sleep(0.2)
        _result,_response = mdb_send_command(_tmp_string,bill_timeout,40)
        _retry += 1
    if _result:
        if mdb_check_crc(_response):
            mdb_bill_send_ack()
            lcd.clear()
            lcd.message("Message from device")
            mdb_hex_dump(_response)
            bill_settings = _response
            for _i in range(11,len(_response) - 2 ):
                bill_value[_i - 11] = _response[_i]
            lcd.clear()
            lcd.message("Got bill level and configuration")
        else:
            mdb_bill_send_nack()
            lcd.clear()
            lcd.message("Message from device")
            mdb_hex_dump(_response)
            lcd.clear()
            lcd.message("CRC failed on BILL LEVEL and CONFIG poll")
            sock.send('{"MDBBIllInit": -1}'.encode()+b"\r\n")
            return False
    else:
        sock.send('{"MDBBIllInit": -1}'.encode()+b"\r\n")
        return False

    # check expansion identification
    time.sleep(0.2)
    if bill_settings[0] == 0x01:
        _tmp_string=[0x37,0x00,0x37]
    else:
        _tmp_string=[0x37,0x02,0x39]
    lcd.clear()
    lcd.message("message to device")
    mdb_hex_dump(_tmp_string)
    _result,_response = mdb_send_command(_tmp_string,bill_timeout,40)
    _retry = 0
    while (_result == False) & (_retry <10):
        time.sleep(0.2)
        _result,_response = mdb_send_command(_tmp_string, bill_timeout,40)
        _retry += 1
    if _result:
        if mdb_check_crc(_response):
            mdb_bill_send_ack()
            lcd.clear()
            lcd.message("message to device")
            mdb_hex_dump(_response)
            bill_expansion = _response
        else:
            mdb_bill_send_nack()
            lcd.clear()
            lcd.message("message from device")
            mdb_hex_dump(_response)
            lcd.clear()
            lcd.message("CRC failed on EXPANSION IDENTIFICATION poll")
            sock.send('{"MDBBIllInit": -1}'.encode()+b"\r\n")
            return False
    else:
        sock.send('{"MDBBIllInit": -1}'.encode()+b"\r\n")
        return False

    # enabling options for level 2+
    if bill_settings[0] > 0x01:
        time.sleep(0.2)
        _tmp_string=[0x37,0x01,0x00,0x00,0x00,0x00,0x38]
        lcd.clear()
        lcd.message("message to device")
        mdb_hex_dump(_tmp_string)
        _result,_response = mdb_send_command(_tmp_string, bill_timeout,40)
        _retry = 0
        while (_result == False) & (_retry <10):
            time.sleep(0.2)
            _result,_response = mdb_send_command(_tmp_string, bill_timeout,40)
            _retry += 1
        if _result:
            lcd.clear()
            lcd.message("message from device")
            mdb_hex_dump(_response)
            if len(_response) > 1:
                _tmp = []
                _tmp.append(_response[len(_response)-1])
                _response = _tmp
            if mdb_check_crc(_response):
                if _response[0] == 0x00:
                    pass
                else:
                    lcd.clear()
                    lcd.message("Unable to enable bill expation options options")
                    sock.send('{"MDBBIllInit": -1}'.encode()+b"\r\n")
                    return False
            else:
                lcd.clear()
                lcd.message("CRC failed on EXPANSION IDENTIFICATION poll")
                sock.send('{"MDBBIllInit": -1}'.encode()+b"\r\n")
                return False
        else:
            sock.send('{"MDBBIllInit": -1'.encode()+b"\r\n")
            return False
    else:
        lcd.clear()
        lcd.message("Level 1 - no options to enable")

    # if reaches this point, the bill init = done
    sock.send('{"MDBBIllInit": 0}'.encode()+b"\r\n")
    bill_inited = True
    return True

# MDB bill validator Reset
def mdb_bill_reset():
    bill_inited = False
    _tmp_string=[0x30,0x30]
    lcd.clear()
    lcd.message("Send to device")
    mdb_hex_dump(_tmp_string)
    _result,_response = mdb_send_command(_tmp_string,bill_timeout + 0.2,40)
    if _result:
        mdb_hex_dump(_response)
        if _response[0]==0x00:
            sock.send('{"MDBBIllReset": 0}'.encode()+b"\r\n")
            bill_inited = False
            return True
        else:
            sock.send('{"MDBBIllReset": -1}'.encode()+b"\r\n")
            return False
    else:
        sock.send('{"MDBBIllReset": -1}'.encode()+b"\r\n")
        return False

# MDB bill validator enabled
def mdb_bill_enable():
    _tmp_string=[0x34,0xFF,0xFF,0xFF,0xFF]
    _tmp_string.append(mdb_add_crc(_tmp_string))
    lcd.clear()
    lcd.message("message to device")
    mdb_hex_dump(_tmp_string)
    _result,_response = mdb_send_command(_tmp_string,bill_timeout,40)
    if _result:
        print("Message from device")
        mdb_hex_dump(_response)
        if _response[0]==0x00:
            sock.send('{"MDBBIllEnable": 0}'.encode()+b"\r\n")
            return True
        else:
            sock.send('{"MDBBIllEnable": -1}'.encode()+b"\r\n")
            return False
    else:
        sock.send('{"MDBBIllEnable": -1}'.encode()+b"\r\n")
        return False

# MDB bill validator DISABLE
def mdb_bill_disable():
    _tmp_string=[0x34,0x00,0x00,0x00,0x00]
    _tmp_string.append(mdb_add_crc(_tmp_string))
    lcd.clear()
    lcd.message("Message to device")
    mdb_hex_dump(_tmp_string)
    _result,_response = mdb_send_command(_tmp_string,bill_timeout,40)
    if _result:
        lcd.clear()
        lcd.message("Message from device")
        mdb_hex_dump(_response)
        if _response[0]==0x00:
            sock.send('{"MDBBIllDisable": 0}'.encode()+b"\r\n")
            return True
        else:
            sock.send('{"MDBBIllDisable": -1}'.encode()+b"\r\n")
            return False
    else:
        sock.send('{"MDBBIllDisable": -1}'.encode()+b"\r\n")
        return False


# MDB bill validator stacker
def mdb_bill_stacker():
    _tmp_string=[0x36,0x36]
    lcd.clear()
    lcd.message("Message to device")
    mdb_hex_dump(_tmp_string)
    _result,_response = mdb_send_command(_tmp_string,bill_timeout,40)
    if _result:
        if mdb_check_crc(_response):
            mdb_bill_send_ack()
            lcd.clear()
            lcd.message("Message from device")
            mdb_hex_dump(_response)
            _value = _response[0]
            _value = _value << 8
            _value += _response[1]
            # _tmp_string = [0x00]
            # _result,_response = mdb_send_command(_tmp_string,bill_timeout,40)
            _stacker_full = _value & 0b1000000000000000
            if _stacker_full != 0:
                _stacker_full_string = "true"
            else:
                _stacker_full_string = "false"
            _value = _value & 0b0111111111111111
            _json_string = ('{"MDBBIllStacker": '+str(_value)+',"StackerFull": '+_stacker_full_string+' }\r\n')
            sock.send(_json_string.encode())
            return True,_value
        else:
            mdb_bill_send_nack()
            lcd.clear()
            lcd.message("Message from device")
            mdb_hex_dump(_response)
            sock.send('{"MDBBIllStacker": -1}'.encode()+b"\r\n")
            return False,0
    else:
        sock.send('{"MDBBIllStacker": -1}'.encode()+b"\r\n")
        return False,0

def mdb_bill_poll():
    _tmp_string=[0x33,0x33]
    lcd.clear()
    lcd.message("message from device")
    mdb_hex_dump(_tmp_string)
    _result,_response = mdb_send_command(_tmp_string,bill_timeout,40)
    if _result:
        if len(_result) == 1:
            return True,_result
        print("Message from device")
        mdb_hex_dump(_response)
        if mdb_check_crc(_response):
            mdb_bill_send_ack()
            _json_string = ('{"MDBBIllPoll": 0}\r\n')
            sock.send(_json_string.encode())
            return True,_response
        else:
            mdb_bill_send_nack()
            sock.send('{"MDBBIllPoll": -1}'.encode()+b"\r\n")
            return False,[]
    else:
        sock.send('{"MDBBIllPoll": -1}'.encode()+b"\r\n")
        return False,[]

# MDB bill validator silent poll
def mdb_bill_silent_poll():
    _tmp_string=[0x33,0x33]
    _result,_response = mdb_send_command(_tmp_string,bill_timeout,40)
    if _result:
        if len(_response) == 1:
            return True,_response

        if mdb_check_crc(_response):
            mdb_bill_send_ack()
            return True,_response
        else:
            mdb_bill_send_nack()
            lcd.clear()
            lcd.message("CRC error on silent bill poll")
            return False,[]
    else:
        lcd.clear()
        lcd.message("Noo response on silent bill poll")
        return False,[]

# prel serial Number
def prel_serial_number(_str):
    _serial_number = ""
    for _i in range(2, 8):
        _tmp_hex = hex(_str[_i])[2:]
        if len(_tmp_hex) < 2:
            _tmp_hex = "0" + _tmp_hex
        else:
            pass
        _serial_number += _tmp_hex
    _json_string = '{"DeviceIdentification": "SerialNumber","DeviceID": "' + _serial_number + '"}\r\n'
    sock.send(_json_string.encode())


# MDB get INTERNAL SETTINGS from bill validator
def mdb_bill_get_settings():
    if len(bill_settings) == 0:
        sock.send('{"MDBBIllSettings": -1}'.encode()+b"\r\n")
        return False
    # calculate various values
    # level
    _level = str(bill_settings[0])
    bill_level = bill_settings[0]
    # country code
    _country_code = "586"       #for Pakistani currency
    _tmp_string = hex(bill_settings[1])[2:]
    if len(_tmp_string) == 1:
        _country_code = _country_code + "0" +_tmp_string
    else:
        _country_code += _tmp_string
    _tmp_string = hex(bill_settings[2])[2:]
    if len(_tmp_string) == 1:
        _country_code = _country_code + "0" +_tmp_string
    else:
        _country_code += _tmp_string
    # scaling factor
    _scaling_factor = bill_settings[3]
    _scaling_factor = _scaling_factor << 8
    _scaling_factor += bill_settings[4]
    bill_scaling_factor = _scaling_factor
    # decimal places
    _decimal_places = bill_settings[5]
    bill_decimal_places = _decimal_places
    # stacker cappacity
    # scaling factor
    _stacker_cappacity = bill_settings[6]
    _stacker_cappacity = _stacker_cappacity << 8
    _stacker_cappacity += bill_settings[7]
    bill_stacker_cappacity = _stacker_cappacity
    # escrow capability
    if bill_settings[10] == 0xFF:
        _escrow = "true"
    else:
        _escrow = "false"
    _json_string = '{"MDBBillSettings": "Current",'
    _json_string += '"Level": ' + _level + ','
    _json_string += '"CountryCode": ' + _country_code + ','
    _json_string += '"ScalingFactor": ' + str(_scaling_factor) + ','
    _json_string += '"StackerCappacity": ' + str(_stacker_cappacity) + ','
    _json_string += '"EscrowAvailable": ' + _escrow + ','
    _json_string += '"BillValues": ['
    for _i in range(0,15):
        _json_string += str(bill_value[_i]) + ','
    _json_string += str(bill_value[_i]) + '],'
    # manufacturer code
    _manufact = ""
    for _i in range(0,3):
        _manufact += chr(bill_expansion[_i])
    # if _manufact == "CCD":
    # bill_timeout = 0.001
    # serial number
    _serial_number = ""
    for _i in range(3,15):
        _serial_number += chr(bill_expansion[_i])
    # model number
    _model_number = ""
    for _i in range(15,27):
        _model_number += chr(bill_expansion[_i])
    # software version
    _software_version = ""
    _tmp_string = hex(bill_expansion[27])[2:]
    if len(_tmp_string) == 1:
        _software_version = _software_version + "0" +_tmp_string
    else:
        _software_version += _tmp_string
    _tmp_string = hex(bill_expansion[28])[2:]
    if len(_tmp_string) == 1:
        _software_version = _software_version + "0" +_tmp_string
    else:
        _software_version += _tmp_string
    # recycling option
    if bill_level > 1:
        _tmp_byte = bill_expansion[32] & 0b00000010
        if _tmp_byte != 0:
            _recycling_option = "true"
            bill_recycling_option = True
        else:
            _recycling_option = "false"
            bill_recycling_option = False
    else:
        _recycling_option = "false"
        bill_recycling_option = False

    _json_string += '"Manufacturer": "' + _manufact + '",'
    _json_string += '"SerialNumber": "' + _serial_number + '",'
    _json_string += '"Model": "' + _model_number + '",'
    _json_string += '"SoftwareVersion": "' + _software_version + '",'
    _json_string += '"RecyclingAvaliable": ' + _recycling_option
    _json_string += '}\r\n'
    sock.send(_json_string.encode())
    return True


# mdb bill prel message
def mdb_bill_prel_messages():
    # if it is ACK
    if bill_poll_response[0] == 0x00:
        if bill_previous_status != 0x00:
            _json_string = '{"BillStatus": "OK","BillStatusCode" : 0}\r\n'
            sock.send(_json_string.encode())
            bill_previous_status = 0x00
        return

    # if it is NACK
    if bill_poll_response[0] == 0xFF:
        return


    #if there is something about a bill action
    _tmp_byte = bill_poll_response[0] & 0b10000000
    if _tmp_byte == 0b10000000:
        _tmp_byte = bill_poll_response[0] & 0b01110000
        _tmp_byte = _tmp_byte >> 4
        # if it is stacked
        if _tmp_byte == 0b00000000:
            _bill_position = bill_poll_response[0] & 0b00001111
            _value = (bill_value[_bill_position] * bill_scaling_factor)
            _json_string = '{"BillStacked": ' + str(_bill_position) + ',"BillValue": ' + str(_value)
            _json_string +='}\r\n'
            sock.send(_json_string.encode())
            return
        #if it is escrow position
        if _tmp_byte == 0b00000001:
            _bill_position = bill_poll_response[0] & 0b00001111
            _value = (bill_value[_bill_position] * bill_scaling_factor)
            _json_string = '{"BillInEscrow": ' + str(_bill_position) + ',"BillValue": ' + str(_value)
            _json_string +='}\r\n'
            sock.send(_json_string.encode())
#            mdb_bill_accept()
            return
        #if it is returned to customer
        if _tmp_byte == 0b00000010:
            _bill_position = bill_poll_response[0] & 0b00001111
            _value = (bill_value[_bill_position] * bill_scaling_factor)
            _json_string = '{"BillReturned": ' + str(_bill_position) + ',"BillValue": ' + str(_value)
            _json_string +='}\r\n'
            sock.send(_json_string.encode())
            return
        #if it is to recycler
        if _tmp_byte == 0b00000011:
            _bill_position = bill_poll_response[0] & 0b00001111
            _value = (bill_value[_bill_position] * bill_scaling_factor)
            _json_string = '{"BillToRecycler": ' + str(_bill_position) + ',"BillValue": ' + str(_value)
            _json_string +='}\r\n'
            sock.send(_json_string.encode())
            return
        #if it is disabled bill rejected
        if _tmp_byte == 0b00000100:
            _bill_position = bill_poll_response[0] & 0b00001111
            _value = (bill_value[_bill_position] * bill_scaling_factor)
            _json_string = '{"BillDisabledRejected": ' + str(_bill_position) + ',"BillValue": ' + str(_value)
            _json_string +='}\r\n'
            sock.send(_json_string.encode())
            return
        #if it is to recycler - manual fill
        if _tmp_byte == 0b00000101:
            _bill_position = bill_poll_response[0] & 0b00001111
            _value = (bill_value[_bill_position] * bill_scaling_factor)
            _json_string = '{"BillToRecyclerManual": ' + str(_bill_position) + ',"BillValue": ' + str(_value)
            _json_string +='}\r\n'
            sock.send(_json_string.encode())
            return
        #if it is recycler manual dispense
        if _tmp_byte == 0b00000110:
            _bill_position = bill_poll_response[0] & 0b00001111
            _value = (bill_value[_bill_position] * bill_scaling_factor)
            _json_string = '{"BillDispensedManual": ' + str(_bill_position) + ',"BillValue": ' + str(_value)
            _json_string +='}\r\n'
            sock.send(_json_string.encode())
            return
        #if it is recycler transfered tp cashbox
        if _tmp_byte == 0b00000111:
            _bill_position = bill_poll_response[0] & 0b00001111
            _value = (bill_value[_bill_position] * bill_scaling_factor)
            _json_string = '{"BillTransferToCashbox": ' + str(_bill_position) + ',"BillValue": ' + str(_value)
            _json_string +='}\r\n'
            sock.send(_json_string.encode())
            return

    # if there is something about bill status
    _tmp_byte = bill_poll_response[0] & 0b11110000
    if _tmp_byte == 0x00:
        _tmp_byte = bill_poll_response[0] & 0b00001111
        if _tmp_byte == bill_previous_status:
            return
        # deffective motor
        if _tmp_byte ==0b00000001:
            _json_string = '{"BillStatus": "DeffectiveMotor","BillStatusCode" : '+str(_tmp_byte)
            _json_string += '}\r\n'
            sock.send(_json_string.encode())
            bill_previous_status = _tmp_byte
            return
        # sensor problem motor
        if _tmp_byte ==0b00000010:
            _json_string = '{"BillStatus": "SensorProblem","BillStatusCode" : '+str(_tmp_byte)
            _json_string += '}\r\n'
            sock.send(_json_string.encode())
            bill_previous_status = _tmp_byte
            return
        # validator busy
        if _tmp_byte ==0b00000011:
            _json_string = '{"BillStatus": "BusyDoingSomething","BillStatusCode" : '+str(_tmp_byte)
            _json_string += '}\r\n'
            sock.send(_json_string.encode())
            bill_previous_status = _tmp_byte
            return
        # ROM checksum error
        if _tmp_byte ==0b00000100:
            _json_string = '{"BillStatus": "ROMChecksumError","BillStatusCode" : '+str(_tmp_byte)
            _json_string += '}\r\n'
            sock.send(_json_string.encode())
            bill_previous_status = _tmp_byte
            return
        # Bill jammed
        if _tmp_byte ==0b00000101:
            _json_string = '{"BillStatus": "BillJammed","BillStatusCode" : '+str(_tmp_byte)
            _json_string += '}\r\n'
            sock.send(_json_string.encode())
            bill_previous_status = _tmp_byte
            return
        # Just reset
        if _tmp_byte ==0b00000110:
            _json_string = '{"BillStatus": "JustReset","BillStatusCode" : '+str(_tmp_byte)
            _json_string += '}\r\n'
            sock.send(_json_string.encode())
            bill_previous_status = _tmp_byte
            return
        # Bill removed
        if _tmp_byte ==0b00000111:
            _json_string = '{"BillStatus": "BillRemoved","BillStatusCode" : '+str(_tmp_byte)
            _json_string += '}\r\n'
            sock.send(_json_string.encode())
            bill_previous_status = _tmp_byte
            return
        # Cashbox removed
        if _tmp_byte ==0b00001000:
            _json_string = '{"BillStatus": "CashBoxRemoved","BillStatusCode" : '+str(_tmp_byte)
            _json_string += '}\r\n'
            sock.send(_json_string.encode())
            bill_previous_status = _tmp_byte
            return
        # Bill validator disabled
        if _tmp_byte ==0b00001001:
            _json_string = '{"BillStatus": "Disabled","BillStatusCode" : '+str(_tmp_byte)
            _json_string += '}\r\n'
            sock.send(_json_string.encode())
            bill_previous_status = _tmp_byte
            return
        # Bill invalid escrow request
        if _tmp_byte ==0b00001010:
            _json_string = '{"BillStatus": "InvalidEscrowRequest","BillStatusCode" : '+str(_tmp_byte)
            _json_string += '}\r\n'
            sock.send(_json_string.encode())
            bill_previous_status = _tmp_byte
            return
        # Bill rejected
        if _tmp_byte ==0b00001011:
            _json_string = '{"BillStatus": "UnknownBillRejected","BillStatusCode" : '+str(_tmp_byte)
            _json_string += '}\r\n'
            sock.send(_json_string.encode())
            bill_previous_status = _tmp_byte
            return
        # Bill credit removal
        if _tmp_byte ==0b00001100:
            _json_string = '{"BillStatus": "PossibleCreditRemoval","BillStatusCode" : '+str(_tmp_byte)
            _json_string += '}\r\n'
            sock.send(_json_string.encode())
            bill_previous_status = _tmp_byte
            return


    #if there is something about a bill try in disabled status
    _tmp_byte = bill_poll_response[0] & 0b11100000
    if _tmp_byte == 0b01000000:
        _value = bill_poll_response[0] & 0b00011111
        _json_string = '{"BillDisabled": True,"BillPresented": ' + str(_value)
        _json_string +='}\r\n'
        sock.send(_json_string.encode())

    return



def mdb_send_raw(_string):
    _tmp_string= []
    #extracting first byte
    _start = _string.find("(",1)
    _end = _string.find(",",1)
    if (_start == -1) | (_end == -1):
        print("Syntax error")
        sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
        return False
    _tmp_buff = _string[_start + 1:_end]
    #if it is hex value
    if _tmp_buff[0:2] == "0X":
        try:
            _tmp_byte = int(_tmp_buff,16)
        except:
            print("Non-numeric value")
            sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
            return False
    else:
        try:
            _tmp_byte = int(_tmp_buff)
        except:
            print("Non-numeric value")
            sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
            return False
    if _tmp_byte > 255:
        print("Overflow")
        sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
        return False
    _tmp_string.append(_tmp_byte)


    #extracting all the rest except the last one
    _ast_end = _end
    _start = _string.find(",",_ast_end)
    _end = _string.find(",",_start + 1)
    while (_start != -1) & (_end != -1):
        _tmp_buff = _string[_start + 1:_end]
        #if it is hex value
        if _tmp_buff[0:2] == "0X":
            try:
                _tmp_byte = int(_tmp_buff,16)
            except:
                print("Non-numeric value")
                sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
                return False
        else:
            try:
                _tmp_byte = int(_tmp_buff)
            except:
                print("Non-numeric value")
                sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
                return False
        if _tmp_byte > 255:
            print("Overflow")
            sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
            return False
        _tmp_string.append(_tmp_byte)
        _ast_end = _end
        _start = _string.find(",",_end)
        _end = _string.find(",",_start + 1)


    #extracting the last one
    _start = _string.find(",",_ast_end)
    _end = _string.find(")",_start + 1)
    if (_start == -1) | (_end == -1):
        print("Syntax error")
        sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
        return False
    _tmp_buff = _string[_start + 1:_end]
    #if it is hex value
    if _tmp_buff[0:2] == "0X":
        try:
            _tmp_byte = int(_tmp_buff,16)
        except:
            print("Non-numeric value")
            sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
            return False
    else:
        try:
            _tmp_byte = int(_tmp_buff)
        except:
            print("Non-numeric value")
            sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
            return False
    if _tmp_byte > 255:
        print("Overflow")
        sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
        return False
    _tmp_string.append(_tmp_byte)
    print("Message to device")
    mdb_hex_dump(_tmp_string)
    _result,_response = mdb_send_command(_tmp_string,0.002,40)
    if _result:
        print("Message from device")
        mdb_hex_dump(_response)
        if _response[0]==0x00:
            sock.send('{"MDBCashlessSendRaw": 0}'.encode()+b"\r\n")
            return True
        elif _response[0]==0xFF:
            sock.send('{"MDBCashlessSendRaw": -1}'.encode()+b"\r\n")
            return True
        else:
            sock.send('{"MDBCashlessSendRaw": 0}'.encode()+b"\r\n")
            return True

    return True



def mdb_send_raw_crc(_string):
    _tmp_string= []
    #extracting first byte
    _start = _string.find("(",1)
    _end = _string.find(",",1)
    if (_start == -1) | (_end == -1):
        print("Syntax error")
        sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
        return False
    _tmp_buff = _string[_start + 1:_end]
    #if it is hex value
    if _tmp_buff[0:2] == "0X":
        try:
            _tmp_byte = int(_tmp_buff,16)
        except:
            print("Non-numeric value")
            sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
            return False
    else:
        try:
            _tmp_byte = int(_tmp_buff)
        except:
            print("Non-numeric value")
            sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
            return False
    if _tmp_byte > 255:
        print("Overflow")
        sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
        return False
    _tmp_string.append(_tmp_byte)


    #extracting all the rest except the last one
    _last_end = _end
    _start = _string.find(",",_last_end)
    _end = _string.find(",",_start + 1)
    while (_start != -1) & (_end != -1):
        _tmp_buff = _string[_start + 1:_end]
        #if it is hex value
        if _tmp_buff[0:2] == "0X":
            try:
                _tmp_byte = int(_tmp_buff,16)
            except:
                print("Non-numeric value")
                sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
                return False
        else:
            try:
                _tmp_byte = int(_tmp_buff)
            except:
                print("Non-numeric value")
                sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
                return False
        if _tmp_byte > 255:
            print("Overflow")
            sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
            return False
        _tmp_string.append(_tmp_byte)
        _last_end = _end
        _start = _string.find(",",_end)
        _end = _string.find(",",_start + 1)


    #extracting the last one
    _start = _string.find(",",_last_end)
    _end = _string.find(")",_start + 1)
    if (_start == -1) | (_end == -1):
        print("Syntax error")
        sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
        return False
    _tmp_buff = _string[_start + 1:_end]
    #if it is hex value
    if _tmp_buff[0:2] == "0X":
        try:
            _tmp_byte = int(_tmp_buff,16)
        except:
            print("Non-numeric value")
            sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
            return False
    else:
        try:
            _tmp_byte = int(_tmp_buff)
        except:
            print("Non-numeric value")
            sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
            return False
    if _tmp_byte > 255:
        print("Overflow")
        sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
        return False
    _tmp_string.append(_tmp_byte)
    _tmp_string.append(mdb_add_crc(_tmp_string))
    print("Message to device")
    mdb_hex_dump(_tmp_string)
    _result,_response = mdb_send_command(_mp_string,0.002,40)
    if _result:
        print("Message from device")
        mdb_hex_dump(_response)
        if _response[0]==0x00:
            sock.send('{"MDBCashlessSendRaw": 0}'.encode()+b"\r\n")
            return True
        elif _response[0]==0xFF:
            sock.send('{"MDBCashlessSendRaw": -1}'.encode()+b"\r\n")
            return True
        else:
            sock.send('{"MDBCashlessSendRaw": 0}'.encode()+b"\r\n")
            return True

    return True



# server parse and execute received message
def server_prel_messages(_lstr):
    try:
        _str = _lstr.decode()
    except:
        print("Malformated command")
        return
    _str = _str.upper()
    if _str.find("BILLINIT") != -1:
        print("Trying to INIT bill validator... ")
        if mdb_bill_init():
            print("SUCCESS")
        else:
            print("FAIL")
    elif _str.find("BILLENABLE") != -1:
        print("Trying to ENABLE bill validator... ")
        if mdb_bill_enable():
            print("SUCCESS")
        else:
            print("FAIL")
    elif _str.find("BILLRESET") != -1:
        print("Trying to RESET bill validator... ")
        if mdb_bill_reset():
            print("SUCCESS")
        else:
            print("FAIL")
    elif _str.find("BILLDISABLE") != -1:
        print("Trying to DISABLE bill validator... ")
        if mdb_bill_disable():
            print("SUCCESS")
        else:
            print("FAIL")
    elif _str.find("BILLSTACKER") != -1:
        print("Trying to check stacker status for bill validator... ")
        _result, bill_stacker = mdb_bill_stacker()
        if _result:
            print("SUCCESS")
        else:
            print("FAIL")
    elif _str.find("BILLPOLL") != -1:
        print("Trying to poll bill validator... ")
        _result, bill_poll_response = mdb_bill_poll()
        if _result:
            print("SUCCESS")
        else:
            print("FAIL")
    elif _str.find("BILLACCEPT") != -1:
        print("Trying to ACCEPT bill... ")
        if mdb_bill_accept():
            print("SUCCESS")
        else:
            print("FAIL")
    elif _str.find("BILLREJECT") != -1:
        print("Trying to REJECT bill... ")
        if mdb_bill_reject():
            print("SUCCESS")
        else:
            print("FAIL")
    elif _str.find("BILLTIMEOUT(") != -1:
        print("Setting bill validator timeout... ")
        if mdb_bill_timeout(_str):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _str.find("BILLSETTINGS") != -1:
        print("Trying to get INTERNAL SETTINGS from bill validator... ")
        if mdb_bill_get_settings():
            print("SUCCESS")
        else:
            print("FAIL")
    elif _str.find("MDBSENDRAW(") != -1:
        print("Trying to SEND RAW MESSAGE TO MDB... ")
        if mdb_send_raw(_str):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _str.find("MDBSENDRAWCRC(") != -1:
        print("Trying to SEND RAW MESSAGE TO MDB calculating CRC... ")
        if mdb_send_raw_crc(_str):
            print("SUCCESS")
        else:
            print("FAIL")
    #    elif _str.find("SETMUXCHANNEL(")!=-1:
    #        print("Trying to set multiplexer channel... ")
    #        if set_mux_channel(_str):
    #            print("SUCCESS")
    #        else:
    #            print("FAIL")
    elif _str.find("CCTHOPPERINIT(") != -1:
        print("Trying to init ccTalk hopper... ")
        if cctalk_hopper_init(_str):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _str.find("CCTHOPPERDISPENSE(") != -1:
        print("Trying to dispense coins from ccTalk hopper... ")
        if cctalk_hopper_dispense_normal(_str):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _str.find("CCTHOPPERCHECKDISPENSE(") != -1:
        print("Trying to dispense coins from ccTalk hopper... ")
        if cctalk_hopper_check_dispense_status(_str):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _str.find("CCTHOPPERDISPENSECIPHER(") != -1:
        print("Trying to dispense coins from ccTalk hopper... ")
        if cctalk_hopper_dispense_cipher(_str):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _str.find("CCTHI(") != -1:
        print("Trying to init ccTalk hopper... ")
        if cctalk_hopper_init(_str):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _str.find("RTCSET(") != -1:
        print("Trying to set RTC...")
        if rtc_set(_str):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _str.find("RTCGET") != -1:
        print("Trying to get RTC...")
        if rtc_get(_str):
            print("SUCCESS")
        else:
            print("FAIL")

    elif _str.find("KEYPRESS(") != -1:
        print("Sending KEYPRESS... ")
        if keyboard_sss_keypress(_str):
            print("SUCCESS")
        else:
            print("FAIL")


    elif _str.find("BYE") != -1:
        sys.exit(0)
    else:
        sock.send(json.dumps({"UnknownCommand": "failed"}).encode() + b"\n")


