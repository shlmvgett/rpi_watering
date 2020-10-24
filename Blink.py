#!/usr/bin/env python

import RPi.GPIO as GPIO
import logging
import datetime
import time
import configparser
import SpiConnector


SPI_CLK = 23
SPI_MISO = 21
SPI_MOSI = 19
SPI_CS = 24
RELAY = 11
ALARM_LED = 32
ON_LED = 22

# set up the SPI interface pins
GPIO.setmode(GPIO.BOARD)
GPIO.setup(SPI_MOSI, GPIO.OUT)
GPIO.setup(SPI_MISO, GPIO.IN)
GPIO.setup(SPI_CLK, GPIO.OUT)
GPIO.setup(SPI_CS, GPIO.OUT)
GPIO.setup(RELAY, GPIO.OUT)
GPIO.setup(ALARM_LED, GPIO.OUT, GPIO.PUD_OFF, GPIO.LOW)
GPIO.setup(ON_LED, GPIO.OUT, GPIO.PUD_OFF, GPIO.HIGH)

# 10k trim pot connected to adc #0
potentiometer_adc = 0
logging.basicConfig(filename="test.log", level=logging.DEBUG)
config = configparser.ConfigParser()
previous_humidity = 0

while True:
    try:
        config.read("config.properties")
        current_humidity = SpiConnector.readadc(potentiometer_adc, SPI_CLK, SPI_MOSI, SPI_MISO, SPI_CS)

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
            if previous_humidity > int(config["DEFAULT"]["DRY_LEVEL"]):
                print(">>>>> WANRNIG: check system work \n")
                GPIO.output(ALARM_LED, GPIO.HIGH)
        else:
            GPIO.output(ALARM_LED, GPIO.LOW)

        previous_humidity = current_humidity
        # wait 60 min (3600)
        time.sleep(3600)
    except KeyboardInterrupt:
        print("Program close...")
        GPIO.output(RELAY, GPIO.LOW)
        GPIO.cleanup()