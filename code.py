#Import all needed libraries
import time
import board
import digitalio
from adafruit_onewire.bus import OneWireBus
from adafruit_ds18x20 import DS18X20
import adafruit_dht
import busio
import adafruit_bmp280
import adafruit_adxl34x
import adafruit_ccs811

#Define sensors and protocols
i2c = busio.I2C(board.SCL, board.SDA)
ow_bus = OneWireBus(board.D13)
dht_sensor = adafruit_dht.DHT11(board.D5) #Air moisture sensor
devices = ow_bus.scan()
ds18b20_sensors = [DS18X20(ow_bus, device) for device in devices] #thermometer


# Define i2c addresses
ccs811 = adafruit_ccs811.CCS811(i2c, address=0x5a) #air quality sensor
accelerometer = adafruit_adxl34x.ADXL345(i2c, address=0x53)
bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=0x77)

bmp280.sea_level_pressure = 1013.25

altitude_m_start = bmp280.altitude
print("Calibrating: keep the CanSat still")
time.sleep(1.0) 


start_x, start_y, start_z = accelerometer.acceleration

print("Calibration complete!")
print(f"Offset: {start_x:.2f}, Y: {start_y:.2f}, Z: {start_z:.2f}")

base_altitude = bmp280.altitude
base_time = time.monotonic()


while True:

    try:
        carbondioxide = ccs811.eco2
        total_volatile_compounds = ccs811.tvoc
        
        print(f"Carbondioxide {carbondioxide} ppm")
        print(f"Total_volatile_compounds {total_volatile_compounds} ppb")
    except RuntimeError:
        print("No air quality data")

    distance_traveled = bmp280.altitude - base_altitude
    time_elapsed = time.monotonic()-base_time
    speed= distance_traveled/time_elapsed

    try:
        pressure_hpa = bmp280.pressure
        altitude_m = bmp280.altitude - altitude_m_start

        print(f"Air Pressure: {pressure_hpa:.2f} hPa")
        print(f"Altitude: {altitude_m:.1f} meters")
        print(f"Speed: {speed} m/s")

    except RuntimeError:
        print("No airpressure or altitude data")

    try:
        if not ds18b20_sensors:
            devices = ow_bus.scan()
            ds18b20_sensors = [DS18X20(ow_bus, device) for device in devices]
        for sensor in ds18b20_sensors:
            temperature = sensor.temperature
            print(f"Temperature: {temperature}°C")

            
    except RuntimeError:
        print("No temperature data")
        ds18b20_sensors = []
    try:
        humidity = dht_sensor.humidity
        print(f"Humidity: {humidity}%")
    except RuntimeError:
        print("OBS: Unreliable humidity data")

    try:
        current_x, current_y, current_z = accelerometer.acceleration
        relative_x = current_x - start_x
        relative_y = current_y - start_y
        relative_z = current_z - start_z

        print(f" {relative_x:.2f}, Y: {relative_y:.2f}, Z: {relative_z:.2f} m/s^2")
  

    except RuntimeError:
        print("No acceleration data")

    base_altitude = bmp280.altitude
    base_time = time.monotonic()
    time.sleep(1.0)
