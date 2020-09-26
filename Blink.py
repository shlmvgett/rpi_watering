#!/usr/bin/env python

import RPi.GPIO as GPIO
import logging
import datetime
import time
import configparser


# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
    if (adcnum > 7) or (adcnum < 0):
        return -1
    GPIO.output(cspin, True)

    GPIO.output(clockpin, False)  # start clock low
    GPIO.output(cspin, False)  # bring CS low

    commandout = adcnum
    commandout |= 0x18  # start bit + single-ended bit
    commandout <<= 3  # we only need to send 5 bits here
    for i in range(5):
        if commandout & 0x80:
            GPIO.output(mosipin, True)
        else:
            GPIO.output(mosipin, False)
        commandout <<= 1
        GPIO.output(clockpin, True)
        GPIO.output(clockpin, False)

    adcout = 0
    # read in one empty bit, one null bit and 10 ADC bits
    for i in range(12):
        GPIO.output(clockpin, True)
        GPIO.output(clockpin, False)
        adcout <<= 1
        if GPIO.input(misopin):
            adcout |= 0x1

    GPIO.output(cspin, True)

    adcout >>= 1  # first bit is 'null' so drop it
    return adcout


HUMIDITY_LEVEL = 685
PUMP_DURATION = 3  # 3sec == 100ml

SPICLK = 23
SPIMISO = 21
SPIMOSI = 19
SPICS = 24
RELAY = 11

# set up the SPI interface pins
GPIO.setmode(GPIO.BOARD)
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)
GPIO.setup(RELAY, GPIO.OUT)

# 10k trim pot connected to adc #0
potentiometer_adc = 0
logging.basicConfig(filename="test.log", level=logging.DEBUG)
config = configparser.ConfigParser()

while True:
    try:
        config.read("config.properties")
        current_humidity = readadc(potentiometer_adc, SPICLK, SPIMOSI, SPIMISO, SPICS)

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        logging.debug("%s, value = %s. dry_level: %s", now, str(current_humidity), config["DEFAULT"]["DRY_LEVEL"])
        print("Humidity: ", current_humidity)
        print("Dry level: ", config["DEFAULT"]["DRY_LEVEL"], "\n")

        if current_humidity > int(config["DEFAULT"]["DRY_LEVEL"]):
            logging.debug(">>>>> Watering")
            print(">>>>> Watering \n")
            GPIO.output(RELAY, GPIO.HIGH)
            time.sleep(int(config["DEFAULT"]["PUMP_DURATION"]))
            GPIO.output(RELAY, GPIO.LOW)

        # wait 60 min
        time.sleep(3600)
    except KeyboardInterrupt:
        print("Program close...")
        GPIO.output(RELAY, GPIO.LOW)
        GPIO.cleanup()
