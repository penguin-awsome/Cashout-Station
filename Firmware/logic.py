import network
import urequests
import time
from machine import Pin, I2C, PWM
import pn532

# --- Wi-Fi Setup ---
SSID = 'YourWiFiSSID' #add the stuff
PASSWORD = 'YourWiFiPassword' #and this stuff

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD) #and even more stuff

print("Connecting to Wi-Fi...")
while not wlan.isconnected():
    time.sleep(1)
print("Connected, IP:", wlan.ifconfig()[0])

# --- GPIO Setup ---

# I2C for NFC
i2c = I2C(1, scl=Pin(23), sda=Pin(22), freq=400000)
pn532_module = pn532.PN532_I2C(i2c, debug=False)

ic, ver, rev, support = pn532_module.get_firmware_version()
print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))

pn532_module.SAM_configuration()

# Buttons 
button1 = Pin(17, Pin.IN, Pin.PULL_UP)
button2 = Pin(19, Pin.IN, Pin.PULL_UP)

# LEDs 
led1 = Pin(2, Pin.OUT)
led2 = Pin(21, Pin.OUT)

# Servos on GPIO0 and GPIO1 
servo1 = PWM(Pin(0), freq=50)
servo2 = PWM(Pin(1), freq=50)

# Speaker on GPIO16 
speaker = PWM(Pin(16))

# PC trigger URL
PC_IP = '192.168.x.x'  # Replace with IP
URL = f'http://{PC_IP}:5000/trigger'

def send_trigger():
    try:
        response = urequests.post(URL)
        print("Trigger sent, response:", response.text)
        response.close()
    except Exception as e:
        print("Failed to send trigger:", e)

# Button 
def button1(pin):
    print("Button 1 pressed!")

def button2(pin):
    print("Button 2 pressed!")

button1.irq(trigger=Pin.IRQ_FALLING, handler=button1)
button2.irq(trigger=Pin.IRQ_FALLING, handler=button2)

# Servo control function
def set_servo_angle(servo, angle):
    min_duty = 26   # 0.5ms 
    max_duty = 128  # 2.5ms 
    duty = int(min_duty + (max_duty - min_duty) * (angle / 180))
    servo.duty(duty)

# Speaker beep
def beep(frequency=1000, duration=200):
    speaker.freq(frequency)
    speaker.duty(512)  
    time.sleep_ms(duration)
    speaker.duty(0)

# Main loop: check for NFC tags and handle
last_uid = None
while True:
    uid = pn532_module.read_passive_target(timeout=0.5)
    if uid:
        if uid != last_uid:
            print('NFC tag detected:', [hex(i) for i in uid])
            beep()
            send_trigger()
            last_uid = uid
    else:
        last_uid = None
    time.sleep(0.1)
