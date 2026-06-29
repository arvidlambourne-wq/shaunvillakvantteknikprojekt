#Import all needed libraries
import time
import random
import board
import digitalio
from adafruit_onewire.bus import OneWireBus
from adafruit_ds18x20 import DS18X20
import adafruit_dht
import busio
import adafruit_bmp280
import adafruit_adxl34x
import adafruit_ccs811

switch = digitalio.DigitalInOut(board.D24)
switch.switch_to_input(pull=digitalio.Pull.DOWN)
DEBUG = switch.value

# average altitude value for stabilty
def get_altitude_avg(samples):
    return sum(bmp280.altitude for _ in range(samples)) / samples
    
#Define sensors and protocols
i2c = busio.I2C(board.SCL, board.SDA)
ow_bus = OneWireBus(board.D12)
dht_sensor = adafruit_dht.DHT11(board.D5) #Air moisture sensor
devices = ow_bus.scan()
ds18b20_sensors = [DS18X20(ow_bus, device) for device in devices] #thermometer


# Define i2c addresses
try:
    ccs811 = adafruit_ccs811.CCS811(i2c, address=0x5a) #air quality sensor
except:
    ccs811 = None
accelerometer = adafruit_adxl34x.ADXL345(i2c, address=0x53)
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x77)

bmp280.sea_level_pressure = 1013.25

altitude_m_start = bmp280.altitude


# calibrating step
readings = []

# Calibration wait
led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT
led.value = False

calibration_start = time.monotonic()
now = time.monotonic()
while now - calibration_start < 5:
    if now % 1 < 0.5:
        led.value = True
    else:
        led.value = False

    now = time.monotonic()

CALIBRATION_TIME = 2 # s
READING_INTERVAL = .2 # s

led.value = True
for _ in range(CALIBRATION_TIME // READING_INTERVAL):
    readings.append(accelerometer.acceleration)
    time.sleep(READING_INTERVAL)
led.value = False


num_elements = len(readings)

offset_x_acc = sum(read[0] for read in readings) / num_elements
offset_y_acc = sum(read[1] for read in readings) / num_elements
offset_z_acc = sum(read[2] for read in readings) / num_elements


if DEBUG:
    print(f"Offset: {offset_x_acc}, Y: {offset_y_acc}, Z: {offset_z_acc}")


base_altitude = get_altitude_avg(10)
base_time = time.monotonic()

try:
    f = open(f"/{random.randint(10000,99999)}.csv", "a")
except OSError as e:
    f = None
    print(f"File error!: {e}")

while True:
    carbondioxide = None
    pressure_hpa = None
    altitude_m = None
    humidity = None
    compensated_x = None 
    compensated_y = None
    compensated_z = None
    temperature = None
    
    try:
        carbondioxide = ccs811.eco2
        if DEBUG:
            print(f"Carbondioxide {carbondioxide} ppm")
    except:
        if DEBUG:
            print("No air quality data")

    try:
        pressure_hpa = bmp280.pressure
        if DEBUG:
            print(f"Air Pressure: {pressure_hpa} hPa")
    except:
        if DEBUG:
            print("No airpressure")

    try:
        altitude_m = bmp280.altitude - altitude_m_start
        if DEBUG:
            print(f"Altitude: {altitude_m} meters")
    except:
        if DEBUG:
            print("No airpressure or altitude data")

    try:
        if not ds18b20_sensors:
            devices = ow_bus.scan()
            ds18b20_sensors = [DS18X20(ow_bus, device) for device in devices]
        
        for sensor in ds18b20_sensors:
            temperature = sensor.temperature
            if DEBUG:
                print(f"Temperature: {temperature}°C")     
    except:
        if DEBUG:
            print("No temperature data")
        ds18b20_sensors = []

    try:
        humidity = dht_sensor.humidity
        if DEBUG:
            print(f"Humidity: {humidity}%")
    except:
        if DEBUG:
            print("OBS: Unreliable humidity data")

    try:
        current_x, current_y, current_z = accelerometer.acceleration
        compensated_x = current_x - offset_x_acc
        compensated_y = current_y - offset_y_acc
        compensated_z = current_z - offset_z_acc
        if DEBUG:
            print(f"X: {compensated_x}, Y: {compensated_y}, Z: {compensated_z}, ")
            print(accelerometer.acceleration)
    except:
        if DEBUG:
            print("No acceleration data")

    time_elapsed = time.monotonic() - base_time

    values_to_output = [
        time_elapsed,
        compensated_x,
        compensated_y,
        compensated_z,
        pressure_hpa,
        altitude_m,
        temperature,
        humidity,
        carbondioxide
    ]

    if f is not None:
        f.write(",".join(str(value) for value in values_to_output) + "\n")
        f.flush()
        # print("Wrote file!")
    else:
        print("f is None!")
