import network
import urequests
import time
from machine import Pin, I2C, PWM
import pn532

SSID = 'WiFiSSID'
PASSWORD = 'WiFiPassword'

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

while not wlan.isconnected():
    time.sleep(1)
print("Connected, IP:", wlan.ifconfig()[0])

i2c = I2C(1, scl=Pin(23), sda=Pin(22), freq=400000)
pn532_module = pn532.PN532_I2C(i2c, debug=False)

ic, ver, rev, support = pn532_module.get_firmware_version()
print('PN532 firmware: {0}.{1}'.format(ver, rev))
pn532_module.SAM_configuration()

btn1 = Pin(17, Pin.IN, Pin.PULL_UP)
btn2 = Pin(19, Pin.IN, Pin.PULL_UP)

led1 = Pin(2, Pin.OUT)
led2 = Pin(21, Pin.OUT)

servo1 = PWM(Pin(0), freq=50)
servo2 = PWM(Pin(1), freq=50)

speaker = PWM(Pin(16))
speaker.duty(0)

PC_IP = '192.168.x.x'
URL = f'http://{PC_IP}:5000/trigger'

def send_trigger():
    try:
        r = urequests.post(URL)
        print("Trigger sent:", r.text)
        r.close()
    except Exception as e:
        print("Trigger failed:", e)

def set_servo_speed(servo, speed):
    neutral = 77
    max_delta = 51
    duty = int(neutral + (speed / 100) * max_delta)
    servo.duty(duty)

def beep(freq=1000, dur=200):
    speaker.freq(freq)
    speaker.duty(512)
    time.sleep_ms(dur)
    speaker.duty(0)

def siren_step(step, max_step=50, base_freq=500, freq_range=1500):
    if step < max_step // 2:
        freq = base_freq + (freq_range * step * 2) / max_step
    else:
        freq = base_freq + (freq_range * (max_step - step) * 2) / max_step
    return int(freq)

last_uid = None
nfc_cooldown_end = 0

btn2_hold_start = None
btn2_reverse_pending = False
siren_pos = 0
siren_direction = 1
max_siren_steps = 50

set_servo_speed(servo1, 0)

while True:
    now = time.ticks_ms()

    if time.ticks_ms() > nfc_cooldown_end:
        uid = pn532_module.read_passive_target(timeout=0.5)
        if uid and uid != last_uid:
            print('NFC tag:', [hex(i) for i in uid])
            beep()
            send_trigger()
            last_uid = uid
            nfc_cooldown_end = now + 5000
        elif not uid:
            last_uid = None

    if not btn1.value():
        print("Button 1 pressed")
        beep(1200, 100)
        set_servo_speed(servo1, 100)
        time.sleep(1)
        set_servo_speed(servo1, 0)
        time.sleep(0.2)
        set_servo_speed(servo1, -100)
        time.sleep(1)
        set_servo_speed(servo1, 0)
        while not btn1.value():
            time.sleep_ms(10)

    if not btn2.value():
        if btn2_hold_start is None:
            btn2_hold_start = now
            siren_pos = 0
            siren_direction = 1

        freq = siren_step(siren_pos, max_siren_steps)
        speaker.freq(freq)
        speaker.duty(300)

        siren_pos += siren_direction
        if siren_pos >= max_siren_steps:
            siren_direction = -1
            siren_pos = max_siren_steps
        elif siren_pos <= 0:
            siren_direction = 1
            siren_pos = 0

        if not btn2_reverse_pending and time.ticks_diff(now, btn2_hold_start) > 5000:
            print("Button 2 held 5s, reversing servo")
            btn2_reverse_pending = True
    else:
        speaker.duty(0)
        btn2_hold_start = None
        siren_pos = 0
        siren_direction = 1

    if btn2_reverse_pending:
        set_servo_speed(servo1, -100)
        time.sleep(1)
        set_servo_speed(servo1, 0)
        btn2_reverse_pending = False

    time.sleep_ms(10)
