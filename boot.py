# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()
# Libraries and Dependencies
import machine
from machine import Pin
from machine import UART

import time
import utime

import network

from umqttsimple import MQTTClient

from uhf import UHF

import webrepl

import ubinascii
import ujson  # Add this at the top with your other imports

from umodbus.serial import Serial

import micropython
import json
import esp
esp.osdebug(None)
import gc
gc.collect()

# Wifi-Setting
#ssid  = "raspi4-iiot"
#password = "iota2024"

# Wifi-Setting
ssid  = "wifi2-iiot"
password = "iota2024"

# server ip address & MQTT Information
#mqtt_server = "10.42.0.1"
mqtt_server = "10.10.10.248"
mqtt_port = 1883
#mqtt_user = "npdtom"
#mqtt_password = "npd@tom"
mqtt_user = "npdAtom"
mqtt_password = "npd@Atom"
mqtt_topic = "die_height"


#mqtt_subscribe_topic = "die_signal"
mqtt_subscribe_topic = "die_signal01"
topic_sub = b'control'
topic_pub1 = b'UHFRFID'
topic_pub2 = b'COUNT4'
topic_pub3 = b'J5'

#Client information
client_id = "246"

# Define the pins for Modbus communication and relay pins
# rtu_pins = (Pin(10), Pin(11))
rtu_pins = (Pin(14), Pin(15))
#rtu_pins = (Pin(3), Pin(1))
RELAY_UP_PIN = Pin(12, Pin.OUT)
RELAY_DOWN_PIN = Pin(10, Pin.OUT)

# Initialize the Modbus object
# m = Serial(baudrate=9600, data_bits=8, stop_bits=1, parity=None, pins=rtu_pins, ctrl_pin=Pin(15), uart_id=2)
m = Serial(baudrate=9600, data_bits=8, stop_bits=1, parity=None, pins=rtu_pins, ctrl_pin=Pin(6), uart_id=2)
#m = Serial(baudrate=9600, data_bits=8, stop_bits=1, parity=None, pins=rtu_pins, ctrl_pin=Pin(5), uart_id=2)


# Increase timeout for Modbus response
m._uart.init(timeout=300)  # Set UART timeout to 2000 ms (2 seconds)
#m._uart.init()


















