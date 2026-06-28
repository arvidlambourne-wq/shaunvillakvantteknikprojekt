

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


# average altitude value for stabilty
def get_altitude_avg(samples):
    return sum(bmp280.altitude for _ in range(samples)) / samples
    
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
start_x, start_y, start_z = accelerometer.raw_x, accelerometer.raw_y, accelerometer.raw_z
print("Calibration complete!")

print(f"Offset: {start_x}, Y: {start_y}, Z: {start_z}")

base_altitude = bmp280.altitude
base_time = time.monotonic()


while True:
    current_altitude = get_altitude_avg(3)
    distance_traveled = current_altitude - base_altitude
    time_elapsed = time.monotonic()-base_time
    speed= distance_traveled/time_elapsed

    if speed > -2: 
        try:
            carbondioxide = ccs811.eco2
            
            print(f"Carbondioxide {carbondioxide} ppm")
        except RuntimeError:
            print("No air quality data")

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
            current_x, current_y, current_z = accelerometer.raw_x, accelerometer.raw_y, accelerometer.raw_z
            relative_x = current_x - start_x
            relative_y = current_y - start_y
            relative_z = current_z - start_z

            print(f"X: {relative_x:.2f}, Y: {relative_y:.2f}, Z: {relative_z:.2f}, ")
            print(accelerometer.acceleration)
        except RuntimeError:
            print("No acceleration data")
        print(speed)
        print("slow")
        time.sleep(0.1)
    elif speed <= -2:
        try:
            pressure_hpa = bmp280.pressure
            altitude_m = bmp280.altitude - altitude_m_start

            print(f"Air Pressure: {pressure_hpa:.2f} hPa")
            print(f"Altitude: {altitude_m:.1f} meters")
            print(f"Speed: {speed} m/s")
        except RuntimeError:
            print("No airpressure or altitude data")

        try:
            current_x, current_y, current_z = accelerometer.raw_x, accelerometer.raw_y, accelerometer.raw_z
            relative_x = current_x - start_x
            relative_y = current_y - start_y
            relative_z = current_z - start_z

            print(f"X: {relative_x:.2f}, Y: {relative_y:.2f}, Z: {relative_z:.2f}, ")
            print(accelerometer.acceleration)
        except RuntimeError:
            print("No acceleration data")
        print(speed)
        print("fast")
        time.sleep(0.01)
        time.sleep(0.01)

    base_altitude = current_altitude
    base_time = time.monotonic()

       

