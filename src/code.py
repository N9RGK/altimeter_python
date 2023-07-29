import board
import time
from digitalio import DigitalInOut, Direction, Pull
import analogio
import busio
import storage
import adafruit_bmp280
import supervisor
import microcontroller
import os
import gc

# define the Hardware for the board
sda1_pin = board.GP18
scl1_pin = board.GP19
sda0_pin = board.GP20
scl0_pin = board.GP21

sense1_pin = board.A0
sense2_pin = board.A1
pixel_pin = board.GP1
fire1_pin = board.GP9
fire2_pin = board.GP11
pyro_low_pin = board.GP10
led_pin = board.GP25

tx_pin = board.GP0
rx_pin = board.GP1

# configure the system
flying = False

sense1 = analogio.AnalogIn(sense1_pin)
sense2 = analogio.AnalogIn(sense2_pin)

pyro_low = DigitalInOut(pyro_low_pin)
pyro_low.switch_to_output(value=False)

fire1 = DigitalInOut(fire1_pin)
fire1.switch_to_output(value=False)

fire2 = DigitalInOut(fire2_pin)
fire2.switch_to_output(value=False)

i2c = busio.I2C(scl0_pin, sda0_pin)
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, 0x77)

bmp280.sea_level_pressure = 1013.25
bmp280.mode = adafruit_bmp280.MODE_NORMAL
bmp280.standby_period = adafruit_bmp280.STANDBY_TC_500
bmp280.iir_filter = adafruit_bmp280.IIR_FILTER_X16
bmp280.overscan_pressure = adafruit_bmp280.OVERSCAN_X16
bmp280.overscan_temperature = adafruit_bmp280.OVERSCAN_X2

time.sleep(2)

altitude = (
    bmp280.altitude * 3.28084
)  # initialize altitude to current measurement and convert to feet

launchSiteAltitude = (
    altitude  # set launch site altitude to start athte current measurement
)

filename = "data.csv"

agl = 0
newAltitude = bmp280.altitude * 3.28084
agl = newAltitude - altitude
waitToLog = 15

usb_status = supervisor.runtime.serial_connected

# Setup LED
led_pin = board.GP25
led = DigitalInOut(led_pin)
led.switch_to_output()


# simple function to test if a file is present
def exists(f):
    os.sync()
    print(os.listdir("/"))
    if f in os.listdir("/"):
        print("found " + f)
        return True
    else:
        return False


if exists(filename):
    print("Standing by for file transfer. To fly and log, remove USB cable.")
    while True:
        led.value = True
        time.sleep(0.1)
        led.value = False
        time.sleep(0.1)

loopTime = 0

print("Starting Ground Phase")
while loopTime < waitToLog:
    newAltitude = bmp280.altitude * 3.28084
    launchSiteAltitude = newAltitude
    agl = newAltitude - launchSiteAltitude
    deltaAlt = newAltitude - altitude
    altitude = newAltitude
    print(loopTime, ", ", agl, ", ", usb_status, ", Waiting to log")
    loopTime = loopTime + 1
    led.value = True
    time.sleep(0.25)
    led.value = False
    time.sleep(0.25)
    time.sleep(0.1)

# open the file
# capture the time of the launch so we can subtract
launchTime = supervisor.ticks_ms()
print("Launch Time Set To: ", launchTime / 1000)
logging = True

previous_sample_time = 0

led.value = True  # turn on LED solid for the durration of the logging

gc.collect()  # garbage collect the memory
print(gc.mem_free())

mission_data = []
print(len(mission_data))

print("flying")
while logging == True:
    mission_time = (supervisor.ticks_ms() - launchTime) / 1000

    if mission_time - previous_sample_time > 0.050:  # sample every 50ms
        previous_sample_time = mission_time
        newAltitude = bmp280.altitude * 3.28084
        pressure = bmp280.pressure
        agl = newAltitude - launchSiteAltitude
        altitude = newAltitude
        try:
            mission_data.append((mission_time, agl, pressure))
        except Exception as e:
            logging = False

    if mission_time > 28:
        logging = False

print("saving the data")
file = open(filename, "wt")
print("Log File Created")
for d in mission_data:
    data_string = str(d[0]) + "," + str(d[1]) + "," + str(d[2])
    print("saving: " + data_string)
    file.write(data_string + "\n")
file.close()
time.sleep(1)
os.sync()

led.value = False  # Turn off LED to indicate logging is complete


print("Finished")
#while True:
#    led.value = True
#    time.sleep(0.5)
#    led.value = False
#    time.sleep(0.5)
