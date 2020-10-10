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
                server_prel_messages(_str)
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
                prel_serial_number(_str)
            # MDB poolling , if previously iniated
            if bill_inited:
                time.sleep(0.01)
                _result, bill_poll_response = mdb_bill_silent_poll()
                if _result:
                    mdb_bill_prel_messages()
    conn.close()