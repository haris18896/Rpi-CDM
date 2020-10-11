enrol = 31
delet = 32
inc = 39
dec = 40
led = 18

HIGH = 1
LOW = 0



GPIO.setup(enrol, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(delet, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(inc, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(dec, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(led, GPIO.OUT)


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
        elif GPIO.input(C1) == 1:
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

