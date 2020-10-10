def mdb_check_crc(_lstring):
    if len(_lstring) == 1:
        if (_lstring[0] == 0x00) | (_lstring[0] == 0xFF):
            return True
        else:
            return False
    if _lstring[0] == 0xFD:
        return False

    _mdb_crc = 0
    for _li in range(0,len(_lstring) - 1):
        _mdb_crc += _lstring[_li]
    _mdb_crc = _mdb_crc & 0xFF
    if _mdb_crc == _lstring[len(_lstring)-1]:
        return True
    else:
        return False

# **************************************************
def mdb_add_crc(_linput):
    _lcrc = 0
    for _li in range(0,len(_linput)):
        _lcrc += _linput[_li]
    _lcrc_lo = _lcrc & 0xFF
    return _lcrc_lo

# ***********************************************
def mdb_hex_dump(_psir):
    _lstring = ""
    for _li in range(0,len(_psir)):
        _ltmp_hex = hex(_psir[_li])[2:]
        if len(_ltmp_hex) == 1:
            _ltmp_hex = "0x0" + _ltmp_hex
        else:
            _ltmp_hex = "0x" + _ltmp_hex
        _lstring += _ltmp_hex + " "
    print(_lstring)

# *************************************************
def mdb_bill_send_ack():
    # sending ACK
    _ltmp_string = [0x00]
    _result,_response = mdb_send_command(_ltmp_string,g.bill_timeout,40)

# *************************************************
def mdb_bill_send_nack():
    # sending NACK
    _ltmp_string = [0xFF]
    _result,_response = mdb_send_command(_ltmp_string,g.bill_timeout,40)

# ***************************************************
def mdb_bill_timeout(_lstring):
    # extracting timeout value
    _start = _lstring.find("(",1)
    _end = _lstring.find(")",1)
    if (_start == -1) | (_end == -1):
        print("Syntax error")
        g.sock.send('{"MDBBillTimeout": -1}'.encode()+b"\r\n")
        return False
    try:
        g.bill_timeout = float(_lstring[_start + 1:_end])
        g.sock.send('{"MDBBillTimeout": 0}'.encode()+b"\r\n")
        return True
    except:
        print("Non-numeric timeout")
        g.sock.send('{"MDBBillTimeout": -1}'.encode()+b"\r\n")
        return False

#send command to the MDB interface uC and get the answer if any
def mdb_send_command(_lcommand,_ltimeout,_llength):
    g.ser.baudrate = 115200
    _ltmp_string=_lcommand
    g.ser.timeout = _ltimeout
    #g.ser.flush()
    _now = time.time()
    _timeout = _now + 1.5
    g.ser.rts = True
    while (g.ser.cts == False) & (_now < _timeout):
        time.sleep(0.05)
        _now = time.time()
        pass
    if g.ser.cts == False:
        return False,[0xFF]
    g.ser.write(_ltmp_string)
    g.ser.rts = False
    while (g.ser.cts == True):
        #time.sleep(0.005)
        pass
    time.sleep(_ltimeout)
    _ltmp_string=g.ser.read(g.ser.in_waiting)
    if len(_ltmp_string)==0:
        return False,[0xFF]
    return True,_ltmp_string

# MDB bill validator INIT
def mdb_bill_init():

    # checking for JUST RESET
    _ltmp_string=[0x33,0x33]
    _result,_response = mdb_send_command(_ltmp_string,g.bill_timeout,40)
    _lretry = 0
    while (_response[0] != 0x06) & (_lretry <10):
        time.sleep(0.2)
        _result,_response = mdb_send_command(_ltmp_string,g.bill_timeout,40)
        _lretry += 1
    if _result:
        if mdb_check_crc(_response):
            mdb_bill_send_ack()
            print("Message from device")
            mdb_hex_dump(_response)
            if _response[0] == 0x06:
                print("Got BILL JUST RESET")
            else:
                g.sock.send('{"MDBBIllInit": -1}'.encode()+b"\r\n")
                return False
        else:
            mdb_bill_send_nack()
            print("Message from device")
            mdb_hex_dump(_response)
            print("CRC failed on JUST RESET poll")
            g.sock.send('{"MDBBIllInit": -1}'.encode()+b"\r\n")
            return False

    else:
        g.sock.send('{"MDBBIllInit": -1}'.encode()+b"\r\n")
        return False

    # checking for level and configuration
    time.sleep(0.2)
    _ltmp_string=[0x31,0x31]
    print("Message to device")
    mdb_hex_dump(_ltmp_string)
    _result,_response = mdb_send_command(_ltmp_string,g.bill_timeout,40)
    _lretry = 0
    while (_result == False) & (_lretry <10):
        time.sleep(0.2)
        _result,_response = mdb_send_command(_ltmp_string,g.bill_timeout,40)
        _lretry += 1
    if _result:
        if mdb_check_crc(_response):
            mdb_bill_send_ack()
            print("Message from device")
            mdb_hex_dump(_response)
            g.bill_settings = _response
            for _li in range(11,len(_response) - 2 ):
                g.bill_value[_li - 11] = _response[_li]
            print("Got bill level and configuration")
        else:
            mdb_bill_send_nack()
            print("Message from device")
            mdb_hex_dump(_response)
            print("CRC failed on BILLL LEVEL AND CONFIG poll")
            g.sock.send('{"MDBBIllInit": -1}'.encode()+b"\r\n")
            return False
    else:
        g.sock.send('{"MDBBIllInit": -1}'.encode()+b"\r\n")
        return False

    # check expansion identification
    time.sleep(0.2)
    if g.bill_settings[0] == 0x01:
        _ltmp_string=[0x37,0x00,0x37]
    else:
        _ltmp_string=[0x37,0x02,0x39]
    print("Message to device")
    mdb_hex_dump(_ltmp_string)
    _result,_response = mdb_send_command(_ltmp_string,g.bill_timeout,40)
    _lretry = 0
    while (_result == False) & (_lretry <10):
        time.sleep(0.2)
        _result,_response = mdb_send_command(_ltmp_string,g.bill_timeout,40)
        _lretry += 1
    if _result:
        if mdb_check_crc(_response):
            mdb_bill_send_ack()
            print("Message from device")
            mdb_hex_dump(_response)
            g.bill_expansion = _response
        else:
            mdb_bill_send_nack()
            print("Message from device")
            mdb_hex_dump(_response)
            print("CRC failed on EXPANSION IDENTIFICATION poll")
            g.sock.send('{"MDBBIllInit": -1}'.encode()+b"\r\n")
            return False
    else:
        g.sock.send('{"MDBBIllInit": -1}'.encode()+b"\r\n")
        return False

    # enabling options for level 2+
    if g.bill_settings[0] > 0x01:
        time.sleep(0.2)
        _ltmp_string=[0x37,0x01,0x00,0x00,0x00,0x00,0x38]
        print("Message to device")
        mdb_hex_dump(_ltmp_string)
        _result,_response = mdb_send_command(_ltmp_string,g.bill_timeout,40)
        _lretry = 0
        while (_result == False) & (_lretry <10):
            time.sleep(0.2)
            _result,_response = mdb_send_command(_ltmp_string,g.bill_timeout,40)
            _lretry += 1
        if _result:
            print("Message from device")
            mdb_hex_dump(_response)
            if len(_response) > 1:
                _tmp = []
                _tmp.append(_response[len(_response)-1])
                _response = _tmp
            if mdb_check_crc(_response):
                if _response[0] == 0x00:
                    pass
                else:
                    print("Unable to enable bill expation options options")
                    g.sock.send('{"MDBBIllInit": -1}'.encode()+b"\r\n")
                    return False
            else:
                print("CRC failed on EXPANSION IDENTIFICATION poll")
                g.sock.send('{"MDBBIllInit": -1}'.encode()+b"\r\n")
                return False
        else:
            g.sock.send('{"MDBBIllInit": -1'.encode()+b"\r\n")
            return False
    else:
        print("Level 1 - no options to enable")

    # if reaches this point, the bill init = done
    g.sock.send('{"MDBBIllInit": 0}'.encode()+b"\r\n")
    g.bill_inited = True
    return True


# MDB bill validator RESET
def mdb_bill_reset():
    g.bill_inited = False
    _ltmp_string=[0x30,0x30]
    print("Send to device")
    mdb_hex_dump(_ltmp_string)
    _result,_response = mdb_send_command(_ltmp_string,g.bill_timeout + 0.2,40)
    if _result:
        mdb_hex_dump(_response)
        if _response[0]==0x00:
            g.sock.send('{"MDBBIllReset": 0}'.encode()+b"\r\n")
            g.bill_inited = False
            return True
        else:
            g.sock.send('{"MDBBIllReset": -1}'.encode()+b"\r\n")
            return False
    else:
        g.sock.send('{"MDBBIllReset": -1}'.encode()+b"\r\n")
        return False

# MDB bill validator ENABLE
def mdb_bill_enable():
    _ltmp_string=[0x34,0xFF,0xFF,0xFF,0xFF]
    _ltmp_string.append(mdb_add_crc(_ltmp_string))
    print("Message to device")
    mdb_hex_dump(_ltmp_string)
    _result,_response = mdb_send_command(_ltmp_string,g.bill_timeout,40)
    if _result:
        print("Message from device")
        mdb_hex_dump(_response)
        if _response[0]==0x00:
            g.sock.send('{"MDBBIllEnable": 0}'.encode()+b"\r\n")
            return True
        else:
            g.sock.send('{"MDBBIllEnable": -1}'.encode()+b"\r\n")
            return False
    else:
        g.sock.send('{"MDBBIllEnable": -1}'.encode()+b"\r\n")
        return False


# MDB bill validator DISABLE
def mdb_bill_disable():
    _ltmp_string=[0x34,0x00,0x00,0x00,0x00]
    _ltmp_string.append(mdb_add_crc(_ltmp_string))
    print("Message to device")
    mdb_hex_dump(_ltmp_string)
    _result,_response = mdb_send_command(_ltmp_string,g.bill_timeout,40)
    if _result:
        print("Message from device")
        mdb_hex_dump(_response)
        if _response[0]==0x00:
            g.sock.send('{"MDBBIllDisable": 0}'.encode()+b"\r\n")
            return True
        else:
            g.sock.send('{"MDBBIllDisable": -1}'.encode()+b"\r\n")
            return False
    else:
        g.sock.send('{"MDBBIllDisable": -1}'.encode()+b"\r\n")
        return False

# MDB bill validator stacker
def mdb_bill_stacker():
    _ltmp_string=[0x36,0x36]
    print("Message to device")
    mdb_hex_dump(_ltmp_string)
    _result,_response = mdb_send_command(_ltmp_string,g.bill_timeout,40)
    if _result:
        if mdb_check_crc(_response):
            mdb_bill_send_ack()
            print("Message from device")
            mdb_hex_dump(_response)
            _lvalue = _response[0]
            _lvalue = _lvalue << 8
            _lvalue += _response[1]
#            _ltmp_string = [0x00]
#            _result,_response = mdb_send_command(_ltmp_string,g.bill_timeout,40)
            _lstacker_full = _lvalue & 0b1000000000000000
            if _lstacker_full != 0:
                _lstacker_full_string = "true"
            else:
                _lstacker_full_string = "false"
            _lvalue = _lvalue & 0b0111111111111111
            _ljson_string = ('{"MDBBIllStacker": '+str(_lvalue)+',"StackerFull": '+_lstacker_full_string+' }\r\n')
            g.sock.send(_ljson_string.encode())
            return True,_lvalue
        else:
            mdb_bill_send_nack()
            print("Message from device")
            mdb_hex_dump(_response)
            g.sock.send('{"MDBBIllStacker": -1}'.encode()+b"\r\n")
            return False,0
    else:
        g.sock.send('{"MDBBIllStacker": -1}'.encode()+b"\r\n")
        return False,0


# MDB bill validator poll
def mdb_bill_poll():
    _ltmp_string=[0x33,0x33]
    print("Message to device")
    mdb_hex_dump(_ltmp_string)
    _result,_response = mdb_send_command(_ltmp_string,g.bill_timeout,40)
    if _result:
        if len(_result) == 1:
            return True,_result
        print("Message from device")
        mdb_hex_dump(_response)
        if mdb_check_crc(_response):
            mdb_bill_send_ack()
            _ljson_string = ('{"MDBBIllPoll": 0}\r\n')
            g.sock.send(_ljson_string.encode())
            return True,_response
        else:
            mdb_bill_send_nack()
            g.sock.send('{"MDBBIllPoll": -1}'.encode()+b"\r\n")
            return False,[]
    else:
        g.sock.send('{"MDBBIllPoll": -1}'.encode()+b"\r\n")
        return False,[]

# MDB bill validator silent poll
def mdb_bill_silent_poll():
    _ltmp_string=[0x33,0x33]
    _result,_response = mdb_send_command(_ltmp_string,g.bill_timeout,40)
    if _result:
        if len(_response) == 1:
            return True,_response

        if mdb_check_crc(_response):
            mdb_bill_send_ack()
            return True,_response
        else:
            mdb_bill_send_nack()
            print("CRC error on silent bill poll")
            return False,[]
    else:
        print("No response on silent bill poll")
        return False,[]

# MDB bill validator accept bill in escrow
def mdb_bill_accept():
    _ltmp_string=[0x35,0x01]
    _ltmp_string.append(mdb_add_crc(_ltmp_string))
    print("Message to device")
    mdb_hex_dump(_ltmp_string)
    _result,_response = mdb_send_command(_ltmp_string,g.bill_timeout,40)
    if _result:
        print("Message from device")
        mdb_hex_dump(_response)
        if _response[0]==0x00:
            g.sock.send('{"MDBBIllAcceptBillInEscrow": 0}'.encode()+b"\r\n")
            return True
        else:
            g.sock.send('{"MDBBIllAcceptBillInEscrow": -1}'.encode()+b"\r\n")
            return False
    else:
        g.sock.send('{"MDBBIllAcceptBillInEscrow": -1}'.encode()+b"\r\n")
        return False

# MDB bill validator reject bill in escrow
def mdb_bill_reject():
    _ltmp_string=[0x35,0x00,0x35]
    print("Message to device")
    mdb_hex_dump(_ltmp_string)
    _result,_response = mdb_send_command(_ltmp_string,g.bill_timeout,40)
    if _result:
        print("Message from device")
        mdb_hex_dump(_response)
        if _response[0]==0x00:
            g.sock.send('{"MDBBIllRejectBillInEscrow": 0}'.encode()+b"\r\n")
            return True
        else:
            g.sock.send('{"MDBBIllRejectBillInEscrow": -1}'.encode()+b"\r\n")
            return False
    else:
        g.sock.send('{"MDBBIllRejectBillInEscrow": -1}'.encode()+b"\r\n")
        return False


# MDB get INTERNAL SETTINGS from bill validator
def mdb_bill_get_settings():
    if len(g.bill_settings) == 0:
        g.sock.send('{"MDBBIllSettings": -1}'.encode()+b"\r\n")
        return False
    # calculate various values
    # level
    _llevel = str(g.bill_settings[0])
    g.bill_level = g.bill_settings[0]
    # country code
    _lcountry_code = "586"
    _tmp_string = hex(g.bill_settings[1])[2:]
    if len(_tmp_string) == 1:
        _lcountry_code = _lcountry_code + "0" +_tmp_string
    else::
        _lcountry_code += _tmp_string
    _tmp_string = hex(g.bill_settings[2])[2:]
    if len(_tmp_string) == 1:
        _lcountry_code = _lcountry_code + "0" +_tmp_string
    else:
        _lcountry_code += _tmp_string
    # scaling factor
    _lscaling_factor = g.bill_settings[3]
    _lscaling_factor = _lscaling_factor << 8
    _lscaling_factor += g.bill_settings[4]
    g.bill_scaling_factor = _lscaling_factor
    # decimal places
    _ldecimal_places = g.bill_settings[5]
    g.bill_decimal_places = _ldecimal_places
    # stacker cappacity
    # scaling factor
    _lstacker_cappacity = g.bill_settings[6]
    _lstacker_cappacity = _lstacker_cappacity << 8
    _lstacker_cappacity += g.bill_settings[7]
    g.bill_stacker_cappacity = _lstacker_cappacity
    # escrow capability
    if g.bill_settings[10] == 0xFF:
        _lescrow = "true"
    else:
        _lescrow = "false"
    _ljson_string = '{"MDBBillSettings": "Current",'
    _ljson_string += '"Level": ' + _llevel + ','
    _ljson_string += '"CountryCode": ' + _lcountry_code + ','
    _ljson_string += '"ScalingFactor": ' + str(_lscaling_factor) + ','
    _ljson_string += '"StackerCappacity": ' + str(_lstacker_cappacity) + ','
    _ljson_string += '"EscrowAvailable": ' + _lescrow + ','
    _ljson_string += '"BillValues": ['
    for _li in range(0,15):
        _ljson_string += str(g.bill_value[_li]) + ','
    _ljson_string += str(g.bill_value[_li]) + '],'
    # manufacturer code
    _lmanufact = ""
    for _li in range(0,3):
        _lmanufact += chr(g.bill_expansion[_li])
#    if _lmanufact == "CCD":
#        g.bill_timeout = 0.001
    # serial number
    _lserial_number = ""
    for _li in range(3,15):
        _lserial_number += chr(g.bill_expansion[_li])
    # model number
    _lmodel_number = ""
    for _li in range(15,27):
        _lmodel_number += chr(g.bill_expansion[_li])
    # software version
    _lsoftware_version = ""
    _tmp_string = hex(g.bill_expansion[27])[2:]
    if len(_tmp_string) == 1:
        _lsoftware_version = _lsoftware_version + "0" +_tmp_string
    else:
        _lsoftware_version += _tmp_string
    _tmp_string = hex(g.bill_expansion[28])[2:]
    if len(_tmp_string) == 1:
        _lsoftware_version = _lsoftware_version + "0" +_tmp_string
    else:
        _lsoftware_version += _tmp_string
    # recycling option
    if g.bill_level > 1:
        _ltmp_byte = g.bill_expansion[32] & 0b00000010
        if _ltmp_byte != 0:
            _lrecycling_option = "true"
            g.bill_recycling_option = True
        else:
            _lrecycling_option = "false"
            g.bill_recycling_option = False
    else:
        _lrecycling_option = "false"
        g.bill_recycling_option = False

    _ljson_string += '"Manufacturer": "' + _lmanufact + '",'
    _ljson_string += '"SerialNumber": "' + _lserial_number + '",'
    _ljson_string += '"Model": "' + _lmodel_number + '",'
    _ljson_string += '"SoftwareVersion": "' + _lsoftware_version + '",'
    _ljson_string += '"RecyclingAvaliable": ' + _lrecycling_option
    _ljson_string += '}\r\n'
    g.sock.send(_ljson_string.encode())
    return True

# ********************************************************
def mdb_bill_prel_messages():
    # if it is ACK
    if g.bill_poll_response[0] == 0x00:
        if g.bill_previous_status != 0x00:
            _ljson_string = '{"BillStatus": "OK","BillStatusCode" : 0}\r\n'
            g.sock.send(_ljson_string.encode())
            g.bill_previous_status = 0x00
        return

    # if it is NACK
    if g.bill_poll_response[0] == 0xFF:
        return


    #if there is something about a bill action
    _tmp_byte = g.bill_poll_response[0] & 0b10000000
    if _tmp_byte == 0b10000000:
        _tmp_byte = g.bill_poll_response[0] & 0b01110000
        _tmp_byte = _tmp_byte >> 4
        # if it is stacked
        if _tmp_byte == 0b00000000:
            _lbill_position = g.bill_poll_response[0] & 0b00001111
            _lvalue = (g.bill_value[_lbill_position] * g.bill_scaling_factor)
            _ljson_string = '{"BillStacked": ' + str(_lbill_position) + ',"BillValue": ' + str(_lvalue)
            _ljson_string +='}\r\n'
            g.sock.send(_ljson_string.encode())
            return
        #if it is escrow position
        if _tmp_byte == 0b00000001:
            _lbill_position = g.bill_poll_response[0] & 0b00001111
            _lvalue = (g.bill_value[_lbill_position] * g.bill_scaling_factor)
            _ljson_string = '{"BillInEscrow": ' + str(_lbill_position) + ',"BillValue": ' + str(_lvalue)
            _ljson_string +='}\r\n'
            g.sock.send(_ljson_string.encode())
#            mdb_bill_accept()
            return
        #if it is returned to customer
        if _tmp_byte == 0b00000010:
            _lbill_position = g.bill_poll_response[0] & 0b00001111
            _lvalue = (g.bill_value[_lbill_position] * g.bill_scaling_factor)
            _ljson_string = '{"BillReturned": ' + str(_lbill_position) + ',"BillValue": ' + str(_lvalue)
            _ljson_string +='}\r\n'
            g.sock.send(_ljson_string.encode())
            return
        #if it is to recycler
        if _tmp_byte == 0b00000011:
            _lbill_position = g.bill_poll_response[0] & 0b00001111
            _lvalue = (g.bill_value[_lbill_position] * g.bill_scaling_factor)
            _ljson_string = '{"BillToRecycler": ' + str(_lbill_position) + ',"BillValue": ' + str(_lvalue)
            _ljson_string +='}\r\n'
            g.sock.send(_ljson_string.encode())
            return
        #if it is disabled bill rejected
        if _tmp_byte == 0b00000100:
            _lbill_position = g.bill_poll_response[0] & 0b00001111
            _lvalue = (g.bill_value[_lbill_position] * g.bill_scaling_factor)
            _ljson_string = '{"BillDisabledRejected": ' + str(_lbill_position) + ',"BillValue": ' + str(_lvalue)
            _ljson_string +='}\r\n'
            g.sock.send(_ljson_string.encode())
            return
        #if it is to recycler - manual fill
        if _tmp_byte == 0b00000101:
            _lbill_position = g.bill_poll_response[0] & 0b00001111
            _lvalue = (g.bill_value[_lbill_position] * g.bill_scaling_factor)
            _ljson_string = '{"BillToRecyclerManual": ' + str(_lbill_position) + ',"BillValue": ' + str(_lvalue)
            _ljson_string +='}\r\n'
            g.sock.send(_ljson_string.encode())
            return
        #if it is recycler manual dispense
        if _tmp_byte == 0b00000110:
            _lbill_position = g.bill_poll_response[0] & 0b00001111
            _lvalue = (g.bill_value[_lbill_position] * g.bill_scaling_factor)
            _ljson_string = '{"BillDispensedManual": ' + str(_lbill_position) + ',"BillValue": ' + str(_lvalue)
            _ljson_string +='}\r\n'
            g.sock.send(_ljson_string.encode())
            return
        #if it is recycler transfered tp cashbox
        if _tmp_byte == 0b00000111:
            _lbill_position = g.bill_poll_response[0] & 0b00001111
            _lvalue = (g.bill_value[_lbill_position] * g.bill_scaling_factor)
            _ljson_string = '{"BillTransferToCashbox": ' + str(_lbill_position) + ',"BillValue": ' + str(_lvalue)
            _ljson_string +='}\r\n'
            g.sock.send(_ljson_string.encode())
            return

    # if there is something about bill status
    _tmp_byte = g.bill_poll_response[0] & 0b11110000
    if _tmp_byte == 0x00:
        _tmp_byte = g.bill_poll_response[0] & 0b00001111
        if _tmp_byte == g.bill_previous_status:
            return
        # deffective motor
        if _tmp_byte ==0b00000001:
            _ljson_string = '{"BillStatus": "DeffectiveMotor","BillStatusCode" : '+str(_tmp_byte)
            _ljson_string += '}\r\n'
            g.sock.send(_ljson_string.encode())
            g.bill_previous_status = _tmp_byte
            return
        # sensor problem motor
        if _tmp_byte ==0b00000010:
            _ljson_string = '{"BillStatus": "SensorProblem","BillStatusCode" : '+str(_tmp_byte)
            _ljson_string += '}\r\n'
            g.sock.send(_ljson_string.encode())
            g.bill_previous_status = _tmp_byte
            return
        # validator busy
        if _tmp_byte ==0b00000011:
            _ljson_string = '{"BillStatus": "BusyDoingSomething","BillStatusCode" : '+str(_tmp_byte)
            _ljson_string += '}\r\n'
            g.sock.send(_ljson_string.encode())
            g.bill_previous_status = _tmp_byte
            return
        # ROM checksum error
        if _tmp_byte ==0b00000100:
            _ljson_string = '{"BillStatus": "ROMChecksumError","BillStatusCode" : '+str(_tmp_byte)
            _ljson_string += '}\r\n'
            g.sock.send(_ljson_string.encode())
            g.bill_previous_status = _tmp_byte
            return
        # Bill jammed
        if _tmp_byte ==0b00000101:
            _ljson_string = '{"BillStatus": "BillJammed","BillStatusCode" : '+str(_tmp_byte)
            _ljson_string += '}\r\n'
            g.sock.send(_ljson_string.encode())
            g.bill_previous_status = _tmp_byte
            return
        # Just reset
        if _tmp_byte ==0b00000110:
            _ljson_string = '{"BillStatus": "JustReset","BillStatusCode" : '+str(_tmp_byte)
            _ljson_string += '}\r\n'
            g.sock.send(_ljson_string.encode())
            g.bill_previous_status = _tmp_byte
            return
        # Bill removed
        if _tmp_byte ==0b00000111:
            _ljson_string = '{"BillStatus": "BillRemoved","BillStatusCode" : '+str(_tmp_byte)
            _ljson_string += '}\r\n'
            g.sock.send(_ljson_string.encode())
            g.bill_previous_status = _tmp_byte
            return
        # Cashbox removed
        if _tmp_byte ==0b00001000:
            _ljson_string = '{"BillStatus": "CashBoxRemoved","BillStatusCode" : '+str(_tmp_byte)
            _ljson_string += '}\r\n'
            g.sock.send(_ljson_string.encode())
            g.bill_previous_status = _tmp_byte
            return
        # Bill validator disabled
        if _tmp_byte ==0b00001001:
            _ljson_string = '{"BillStatus": "Disabled","BillStatusCode" : '+str(_tmp_byte)
            _ljson_string += '}\r\n'
            g.sock.send(_ljson_string.encode())
            g.bill_previous_status = _tmp_byte
            return
        # Bill invalid escrow request
        if _tmp_byte ==0b00001010:
            _ljson_string = '{"BillStatus": "InvalidEscrowRequest","BillStatusCode" : '+str(_tmp_byte)
            _ljson_string += '}\r\n'
            g.sock.send(_ljson_string.encode())
            g.bill_previous_status = _tmp_byte
            return
        # Bill rejected
        if _tmp_byte ==0b00001011:
            _ljson_string = '{"BillStatus": "UnknownBillRejected","BillStatusCode" : '+str(_tmp_byte)
            _ljson_string += '}\r\n'
            g.sock.send(_ljson_string.encode())
            g.bill_previous_status = _tmp_byte
            return
        # Bill credit removal
        if _tmp_byte ==0b00001100:
            _ljson_string = '{"BillStatus": "PossibleCreditRemoval","BillStatusCode" : '+str(_tmp_byte)
            _ljson_string += '}\r\n'
            g.sock.send(_ljson_string.encode())
            g.bill_previous_status = _tmp_byte
            return


    #if there is something about a bill try in disabled status
    _tmp_byte = g.bill_poll_response[0] & 0b11100000
    if _tmp_byte == 0b01000000:
        _lvalue = g.bill_poll_response[0] & 0b00011111
        _ljson_string = '{"BillDisabled": True,"BillPresented": ' + str(_lvalue)
        _ljson_string +='}\r\n'
        g.sock.send(_ljson_string.encode())

    return


def mdb_send_raw(_lstring):
    _ltmp_string= []
    #extracting first byte
    _start = _lstring.find("(",1)
    _end = _lstring.find(",",1)
    if (_start == -1) | (_end == -1):
        print("Syntax error")
        g.sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
        return False
    _tmp_buff = _lstring[_start + 1:_end]
    #if it is hex value
    if _tmp_buff[0:2] == "0X":
        try:
            _tmp_byte = int(_tmp_buff,16)
        except:
            print("Non-numeric value")
            g.sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
            return False
    else:
        try:
            _tmp_byte = int(_tmp_buff)
        except:
            print("Non-numeric value")
            g.sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
            return False
    if _tmp_byte > 255:
        print("Overflow")
        g.sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
        return False
    _ltmp_string.append(_tmp_byte)


    #extracting all the rest except the last one
    _last_end = _end
    _start = _lstring.find(",",_last_end)
    _end = _lstring.find(",",_start + 1)
    while (_start != -1) & (_end != -1):
        _tmp_buff = _lstring[_start + 1:_end]
        #if it is hex value
        if _tmp_buff[0:2] == "0X":
            try:
                _tmp_byte = int(_tmp_buff,16)
            except:
                print("Non-numeric value")
                g.sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
                return False
        else:
            try:
                _tmp_byte = int(_tmp_buff)
            except:
                print("Non-numeric value")
                g.sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
                return False
        if _tmp_byte > 255:
            print("Overflow")
            g.sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
            return False
        _ltmp_string.append(_tmp_byte)
        _last_end = _end
        _start = _lstring.find(",",_end)
        _end = _lstring.find(",",_start + 1)


    #extracting the last one
    _start = _lstring.find(",",_last_end)
    _end = _lstring.find(")",_start + 1)
    if (_start == -1) | (_end == -1):
        print("Syntax error")
        g.sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
        return False
    _tmp_buff = _lstring[_start + 1:_end]
    #if it is hex value
    if _tmp_buff[0:2] == "0X":
        try:
            _tmp_byte = int(_tmp_buff,16)
        except:
            print("Non-numeric value")
            g.sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
            return False
    else:
        try:
            _tmp_byte = int(_tmp_buff)
        except:
            print("Non-numeric value")
            g.sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
            return False
    if _tmp_byte > 255:
        print("Overflow")
        g.sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
        return False
    _ltmp_string.append(_tmp_byte)
    print("Message to device")
    mdb_hex_dump(_ltmp_string)
    _result,_response = mdb_send_command(_ltmp_string,0.002,40)
    if _result:
        print("Message from device")
        mdb_hex_dump(_response)
        if _response[0]==0x00:
            g.sock.send('{"MDBCashlessSendRaw": 0}'.encode()+b"\r\n")
            return True
        elif _response[0]==0xFF:
            g.sock.send('{"MDBCashlessSendRaw": -1}'.encode()+b"\r\n")
            return True
        else:
            g.sock.send('{"MDBCashlessSendRaw": 0}'.encode()+b"\r\n")
            return True

    return True

def mdb_send_raw_crc(_lstring):
    _ltmp_string= []
    #extracting first byte
    _start = _lstring.find("(",1)
    _end = _lstring.find(",",1)
    if (_start == -1) | (_end == -1):
        print("Syntax error")
        g.sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
        return False
    _tmp_buff = _lstring[_start + 1:_end]
    #if it is hex value
    if _tmp_buff[0:2] == "0X":
        try:
            _tmp_byte = int(_tmp_buff,16)
        except:
            print("Non-numeric value")
            g.sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
            return False
    else:
        try:
            _tmp_byte = int(_tmp_buff)
        except:
            print("Non-numeric value")
            g.sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
            return False
    if _tmp_byte > 255:
        print("Overflow")
        g.sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
        return False
    _ltmp_string.append(_tmp_byte)


    #extracting all the rest except the last one
    _last_end = _end
    _start = _lstring.find(",",_last_end)
    _end = _lstring.find(",",_start + 1)
    while (_start != -1) & (_end != -1):
        _tmp_buff = _lstring[_start + 1:_end]
        #if it is hex value
        if _tmp_buff[0:2] == "0X":
            try:
                _tmp_byte = int(_tmp_buff,16)
            except:
                print("Non-numeric value")
                g.sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
                return False
        else:
            try:
                _tmp_byte = int(_tmp_buff)
            except:
                print("Non-numeric value")
                g.sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
                return False
        if _tmp_byte > 255:
            print("Overflow")
            g.sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
            return False
        _ltmp_string.append(_tmp_byte)
        _last_end = _end
        _start = _lstring.find(",",_end)
        _end = _lstring.find(",",_start + 1)


    #extracting the last one
    _start = _lstring.find(",",_last_end)
    _end = _lstring.find(")",_start + 1)
    if (_start == -1) | (_end == -1):
        print("Syntax error")
        g.sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
        return False
    _tmp_buff = _lstring[_start + 1:_end]
    #if it is hex value
    if _tmp_buff[0:2] == "0X":
        try:
            _tmp_byte = int(_tmp_buff,16)
        except:
            print("Non-numeric value")
            g.sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
            return False
    else:
        try:
            _tmp_byte = int(_tmp_buff)
        except:
            print("Non-numeric value")
            g.sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
            return False
    if _tmp_byte > 255:
        print("Overflow")
        g.sock.send('{"MDBSendRaw": -1}'.encode()+b"\r\n")
        return False
    _ltmp_string.append(_tmp_byte)
    _ltmp_string.append(mdb_add_crc(_ltmp_string))
    print("Message to device")
    mdb_hex_dump(_ltmp_string)
    _result,_response = mdb_send_command(_ltmp_string,0.002,40)
    if _result:
        print("Message from device")
        mdb_hex_dump(_response)
        if _response[0]==0x00:
            g.sock.send('{"MDBCashlessSendRaw": 0}'.encode()+b"\r\n")
            return True
        elif _response[0]==0xFF:
            g.sock.send('{"MDBCashlessSendRaw": -1}'.encode()+b"\r\n")
            return True
        else:
            g.sock.send('{"MDBCashlessSendRaw": 0}'.encode()+b"\r\n")
            return True

    return True





































def rtc_set(_psir):
    # rtc: Real time clock
    # extracting hour
    _tmp_string = _psir
    _start = _tmp_string.find("(")
    _end = _tmp_string.find(",", _start)
    if (_start == -1) | (_end == -1):
        _ljson_string = '{"RTCSet": -1}\r\n'
        g.sock.send(_ljson_string.encode())
        return False
    try:
        _lhour = int(_tmp_string[_start + 1:_end]) & 0b01111111
        _lhour = int(str(_lhour), 16)
    except:
        _ljson_string = '{"RTCSet": -1}\r\n'
        g.sock.send(_ljson_string.encode())
        return False

    # extracting minutes
    _start = _tmp_string.find(",", _end)
    _end = _tmp_string.find(",", _start + 1)
    if (_start == -1) | (_end == -1):
        _ljson_string = '{"RTCSet": -1}\r\n'
        g.sock.send(_ljson_string.encode())
        return False
    try:
        _lminutes = int(_tmp_string[_start + 1:_end]) & 0xFF
        _lminutes = int(str(_lminutes), 16)
    except:
        _ljson_string = '{"RTCSet": -1}\r\n'
        g.sock.send(_ljson_string.encode())
        return False

    # extracting seconds
    _start = _tmp_string.find(",", _end)
    _end = _tmp_string.find(",", _start + 1)
    if (_start == -1) | (_end == -1):
        _ljson_string = '{"RTCSet": -1}\r\n'
        g.sock.send(_ljson_string.encode())
        return False
    try:
        _lseconds = int(_tmp_string[_start + 1:_end]) & 0xFF
        _lseconds = int(str(_lseconds), 16)
    except:
        _ljson_string = '{"RTCSet": -1}\r\n'
        g.sock.send(_ljson_string.encode())
        return False

    # extracting day in month
    _start = _tmp_string.find(",", _end)
    _end = _tmp_string.find(",", _start + 1)
    if (_start == -1) | (_end == -1):
        _ljson_string = '{"RTCSet": -1}\r\n'
        g.sock.send(_ljson_string.encode())
        return False
    try:
        _lday = int(_tmp_string[_start + 1:_end]) & 0xFF
        _lday = int(str(_lday), 16)
    except:
        _ljson_string = '{"RTCSet": -1}\r\n'
        g.sock.send(_ljson_string.encode())
        return False

    # extracting month
    _start = _tmp_string.find(",", _end)
    _end = _tmp_string.find(",", _start + 1)
    if (_start == -1) | (_end == -1):
        _ljson_string = '{"RTCSet": -1}\r\n'
        g.sock.send(_ljson_string.encode())
        return False
    try:
        _lmonth = int(_tmp_string[_start + 1:_end]) & 0xFF
        _lmonth = int(str(_lmonth), 16)
    except:
        _ljson_string = '{"RTCSet": -1}\r\n'
        g.sock.send(_ljson_string.encode())
        return False

    # extracting year
    _start = _tmp_string.find(",", _end)
    _end = _tmp_string.find(",", _start + 1)
    if (_start == -1) | (_end == -1):
        _ljson_string = '{"RTCSet": -1}\r\n'
        g.sock.send(_ljson_string.encode())
        return False
    try:
        _lyear = int(_tmp_string[_start + 1:_end]) & 0xFF
        _lyear = int(str(_lyear), 16)

    except:
        _ljson_string = '{"RTCSet": -1}\r\n'
        g.sock.send(_ljson_string.encode())
        return False

    # extracting day of week
    _start = _tmp_string.find(",", _end)
    _end = _tmp_string.find(")", _start + 1)
    if (_start == -1) | (_end == -1):
        _ljson_string = '{"RTCSet": -1}\r\n'
        g.sock.send(_ljson_string.encode())
        return False
    try:
        _lweekday = int(_tmp_string[_start + 1:_end]) & 0xFF
        _lweekday = int(str(_lweekday), 16)
    except:
        _ljson_string = '{"RTCSet": -1}\r\n'
        g.sock.send(_ljson_string.encode())
        return False

    _lserial_string = [0xFE, 0x01]
    _lserial_string.append(_lseconds)
    _lserial_string.append(_lminutes)
    _lserial_string.append(_lhour)
    _lserial_string.append(_lweekday)
    _lserial_string.append(_lday)
    _lserial_string.append(_lmonth)
    _lserial_string.append(_lyear)
# crc: Cyclic Redundancy check
    _lcrc = 0
    for _li in range(0, len(_lserial_string)):
        _lcrc = _lcrc + _lserial_string[_li]
    #    _lcrc = _lcrc & 0x00FF
    _lserial_string.append(mdb_add_crc(_lserial_string))
    _lresult, _lsir = mdb_send_command(_lserial_string, 0.2, 40)
    if (len(_lsir) > 4) & (_lresult):
        if _lsir[1] == 0xFC:
            _ljson_string = '{"RTCSet": 0}\r\n'
        else:
            _ljson_string = '{"RTCSet": -1}\r\n'
            g.sock.send(_ljson_string.encode())
            return False
    else:
        _ljson_string = '{"RTCSet": -1}\r\n'  # no answer from the interface
        return False
    g.sock.send(_ljson_string.encode())
    return True


def rtc_get(_psir):
    # extracting hour
    _lserial_string = [0xFE, 0x02]
    _lcrc = 0
    for _li in range(0, len(_lserial_string)):
        _lcrc = _lcrc + _lserial_string[_li]
    #    _lcrc = _lcrc & 0x00FF
    _lserial_string.append(mdb_add_crc(_lserial_string))
    print("Trimite")
    _lresult, _lsir = mdb_send_command(_lserial_string, 0.5, 40)
    if (len(_lsir) > 4) & (_lresult):
        if (_lsir[0] == 0xFE) & (_lsir[1] == 0x02):
            # if here, then it has received the RTC timestamp
            # extracting seconds
            _lseconds = ((_lsir[2] & 0b01110000) >> 4) * 10
            _lseconds += _lsir[2] & 0b00001111
            # extracting day of week
            _lday_of_week = _lsir[5] & 0b00000111
            if _lday_of_week > 7:
                _lday_of_week = 0x00
            # extracting minutes
            _lminutes = ((_lsir[3] & 0b01110000) >> 4) * 10
            _lminutes += _lsir[3] & 0b00001111
            if _lminutes > 59:
                _lday_of_week = 0x00
            # extracting hours
            _lhours = ((_lsir[4] & 0b00110000) >> 4) * 10
            _lhours += _lsir[4] & 0b00001111
            # extracting day of month
            _lday_of_month = ((_lsir[6] & 0b00110000) >> 4) * 10
            _lday_of_month += _lsir[6] & 0b00001111
            # extracting month
            _lmonth = ((_lsir[7] & 0b00010000) >> 4) * 10
            _lmonth += _lsir[7] & 0b00001111
            # extracting year
            _lyear = ((_lsir[8] & 0b11110000) >> 4) * 10
            _lyear += _lsir[8] & 0b00001111

            _ltimestamp_human = str(_lhours).zfill(2) + ":" + str(_lminutes).zfill(2) + ":" + str(_lseconds).zfill(2)
            _ltimestamp_human += " " + str(_lday_of_month).zfill(2) + "-" + str(_lmonth).zfill(2) + "-" + str(
                _lyear + 2000)
            _ltimestamp_human += " " + g.day_of_week[_lday_of_week]
            print("Board date/time " + _ltimestamp_human)

            _ljson_string = '{"RTCGet": ['
            _ljson_string += str(_lhours) + ","
            _ljson_string += str(_lminutes) + ","
            _ljson_string += str(_lseconds) + ","
            _ljson_string += str(_lday_of_month) + ","
            _ljson_string += str(_lmonth) + ","
            _ljson_string += str(_lyear) + ","
            _ljson_string += str(_lday_of_week) + "]"
            _ljson_string += '}\r\n'
        else:
            _ljson_string = '{"RTCGet": -1}\r\n'
            g.sock.send(_ljson_string.encode())
            return False
    else:
        _ljson_string = '{"RTCGet": -1}\r\n'  # no answer from the interface
        return False
    g.sock.send(_ljson_string.encode())
    return True


# server parse and execute received message
def server_prel_messages(_llsir):
    try:
        _lsir = _llsir.decode()
    except:
        print("Malformated command")
        return
    _lsir = _lsir.upper()
    if _lsir.find("BILLINIT") != -1:
        print("Trying to INIT bill validator... ")
        if mdb_bill_init():
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("BILLENABLE") != -1:
        print("Trying to ENABLE bill validator... ")
        if mdb_bill_enable():
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("BILLRESET") != -1:
        print("Trying to RESET bill validator... ")
        if mdb_bill_reset():
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("BILLDISABLE") != -1:
        print("Trying to DISABLE bill validator... ")
        if mdb_bill_disable():
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("BILLSTACKER") != -1:
        print("Trying to check stacker status for bill validator... ")
        _result, g.bill_stacker = mdb_bill_stacker()
        if _result:
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("BILLPOLL") != -1:
        print("Trying to poll bill validator... ")
        _result, g.bill_poll_response = mdb_bill_poll()
        if _result:
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("BILLACCEPT") != -1:
        print("Trying to ACCEPT bill... ")
        if mdb_bill_accept():
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("BILLREJECT") != -1:
        print("Trying to REJECT bill... ")
        if mdb_bill_reject():
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("BILLTIMEOUT(") != -1:
        print("Setting bill validator timeout... ")
        if mdb_bill_timeout(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("BILLSETTINGS") != -1:
        print("Trying to get INTERNAL SETTINGS from bill validator... ")
        if mdb_bill_get_settings():
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("COINRESET") != -1:
        print("Trying to RESET coin acceptor... ")
        if mdb_coin_reset():
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("COININIT") != -1:
        print("Trying to INIT coin acceptor... ")
        _result = mdb_coin_init()
        if _result:
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("COINPOLL") != -1:
        print("Trying to poll coin acceptor... ")
        _result, g.coin_poll_response = mdb_coin_poll()
        if _result:
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("COINENABLE") != -1:
        print("Trying to ENABLE coin acceptor... ")
        if mdb_coin_enable():
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("COINDISABLE") != -1:
        print("Trying to DISABLE coin acceptor... ")
        if mdb_coin_disable():
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("COINSETTINGS") != -1:
        print("Trying to get INTERNAL SETTINGS from coin acceptor... ")
        if mdb_coin_get_settings():
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("COINTUBESTATUS") != -1:
        print("Trying to check tube status for coin changer... ")
        _result, g.coin_tube_status = mdb_coin_tube_status()
        if _result:
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("COINCHANGE(") != -1:
        print("Trying to RETURN CHANGE... ")
        if mdb_coin_change(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("COINPAYSTATUS") != -1:
        print("Trying to get PAYOUT STATUS from coin acceptor... ")
        if mdb_coin_pay_status():
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("COINTIMEOUT(") != -1:
        print("Setting coin acceptor timeout... ")
        if mdb_coin_timeout(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("CASHLESSRESET(") != -1:
        print("Trying to reset cashless... ")
        if mdb_cashless_reset(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("CASHLESSINIT(") != -1:
        print("Trying to INIT cashless... ")
        if mdb_cashless_init(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("CASHLESSENABLE(") != -1:
        print("Trying to ENABLE cashless... ")
        if mdb_cashless_enable(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("CASHLESSPOLL(") != -1:
        print("Trying to POLL cashless... ")
        if mdb_cashless_poll(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("CASHLESSDISABLE(") != -1:
        print("Trying to DISABLE cashless... ")
        if mdb_cashless_disable(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("CASHLESSCANCEL(") != -1:
        print("Trying to send READER CANCEL on cashless... ")
        if mdb_cashless_reader_cancel(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("CASHLESSVENDREQUEST(") != -1:
        print("Trying to send VEND REQUEST to cashless... ")
        if mdb_cashless_vend_request(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("CASHLESSNEGATIVEVENDREQUEST(") != -1:
        print("Trying to send VEND REQUEST to cashless... ")
        if mdb_cashless_negative_vend_request(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("CASHLESSVENDCANCEL(") != -1:
        print("Trying to send VEND CANCEL to cashless... ")
        if mdb_cashless_vend_cancel(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("CASHLESSVENDSUCCESS(") != -1:
        print("Trying to send VEND SUCCESS to cashless... ")
        if mdb_cashless_vend_success(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("CASHLESSVENDFAILED(") != -1:
        print("Trying to send VEND FAILED to cashless... ")
        if mdb_cashless_vend_failed(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("CASHLESSSESSIONCOMPLETE(") != -1:
        print("Trying to send SESSION COMPLETE to cashless... ")
        if mdb_cashless_session_complete(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("CASHLESSCASHSALE(") != -1:
        print("Trying to send CASH SALE to cashless... ")
        if mdb_cashless_cash_sale(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("CASHLESSREVALUE(") != -1:
        print("Trying to send REVALUE to cashless... ")
        if mdb_cashless_revalue(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("CASHLESSREVALUELIMITREQUEST(") != -1:
        print("Trying to send REVALUE LIMIT REQUEST to cashless... ")
        if mdb_cashless_revalue_limit_request(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("CASHLESSSETTINGS(") != -1:
        print("Trying to get CASHLESS SETTINGS... ")
        if mdb_cashless_get_settings(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("MDBSENDRAW(") != -1:
        print("Trying to SEND RAW MESSAGE TO MDB... ")
        if mdb_send_raw(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("MDBSENDRAWCRC(") != -1:
        print("Trying to SEND RAW MESSAGE TO MDB calculating CRC... ")
        if mdb_send_raw_crc(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    #    elif _lsir.find("SETMUXCHANNEL(")!=-1:
    #        print("Trying to set multiplexer channel... ")
    #        if set_mux_channel(_lsir):
    #            print("SUCCESS")
    #        else:
    #            print("FAIL")
    elif _lsir.find("CCTHOPPERINIT(") != -1:
        print("Trying to init ccTalk hopper... ")
        if cctalk_hopper_init(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("CCTHOPPERDISPENSE(") != -1:
        print("Trying to dispense coins from ccTalk hopper... ")
        if cctalk_hopper_dispense_normal(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("CCTHOPPERCHECKDISPENSE(") != -1:
        print("Trying to dispense coins from ccTalk hopper... ")
        if cctalk_hopper_check_dispense_status(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("CCTHOPPERDISPENSECIPHER(") != -1:
        print("Trying to dispense coins from ccTalk hopper... ")
        if cctalk_hopper_dispense_cipher(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("CCTHI(") != -1:
        print("Trying to init ccTalk hopper... ")
        if cctalk_hopper_init(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("RTCSET(") != -1:
        print("Trying to set RTC...")
        if rtc_set(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")
    elif _lsir.find("RTCGET") != -1:
        print("Trying to get RTC...")
        if rtc_get(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")

    elif _lsir.find("KEYPRESS(") != -1:
        print("Sending KEYPRESS... ")
        if keyboard_sss_keypress(_lsir):
            print("SUCCESS")
        else:
            print("FAIL")


    elif _lsir.find("BYE") != -1:
        sys.exit(0)
    else:
        g.sock.send(json.dumps({"UnknownCommand": "failed"}).encode() + b"\n")


def prel_serial_number(_lsir):
    _lserial_number = ""
    for _li in range(2, 8):
        _ltmp_hex = hex(_lsir[_li])[2:]
        if len(_ltmp_hex) < 2:
            _ltmp_hex = "0" + _ltmp_hex
        else:
            pass
        _lserial_number += _ltmp_hex
    _ljson_string = '{"DeviceIdentification": "SerialNumber","DeviceID": "' + _lserial_number + '"}\r\n'
    g.sock.send(_ljson_string.encode())

