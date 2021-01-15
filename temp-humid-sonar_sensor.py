import RPi.GPIO as GPIO
import board
import adafruit_dht
from csv import writer
import time as t
import os.path

GPIO.setmode(GPIO.BCM)
TEMP = board.D18 # Adafruit library GPIO PIN NUMBER
TRIG = 23 # GPIO PIN number, NOT THE PLUGIN NUMBER OF THE PI
ECHO = 24 # GPIO PIN NUMBER; voltage division for pi

DHTSensor = adafruit_dht.DHT11(TEMP)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

print('Bootup check')
# sound_constant = 34300 / 2 # cm/s
data_filename = 'TempHumSon_data.csv'
columns = ['Date','Hour', 'Time(MS)','Time From Epoch(S)','Sound Velocity(cm/s)', 
                'Distance(CM)', 'Deltatime(S)', "Temperature(C)", 
                "Temperature(F)", "Humidity(%)"]
    


if not os.path.exists(data_filename):
    print('Creating new file') 
    with open(data_filename, 'a+', newline='') as csvfile:
        csvwriter = writer(csvfile)
        csvwriter.writerow(columns)

def append_file(data, filename = data_filename):
    with open(filename, 'a+', newline='') as csvfile:
        csvwriter = writer(csvfile)
        csvwriter.writerow(data)
    return

# finding distance
def compute_distance(sound_velocity):
    """Use d = v * t, when v is half the speed of sound at sea level @ 343 m/s.
        Increases accuracy of Sound Velocity with Temperature and Humidity taken
        into account."""

    GPIO.output(TRIG, True)
    t.sleep(0.00001) #0.01ms to set trigger to low

    GPIO.output(TRIG, False)
    pulse_start = t.time()# are these required?
    pulse_end = t.time()

    while GPIO.input(ECHO) == 0:
        pulse_start = t.time()

    while GPIO.input(ECHO) == 1:
        pulse_end = t.time()

    delta_time = pulse_end - pulse_start # the time it took to read the sound wave

    distance = delta_time * sound_velocity / 2 # cm
    return [distance, delta_time]

def compute_sound_velocity(temp_reading, humidity_reading):
    """Uses the Sound Velocity formula to improve the accuracy of detecting 
    distance: Vsound[m/s] = 331.4 + (0.606 * TempC) + (0.0124 * Humidity)."""
    vsound = 333.4 + (0.606 * temp_reading) + (0.0124 * humidity_reading)
    return vsound * 100 # cm

def temp_sensor():
    try:
        tempC = DHTSensor.temperature
        humidity = DHTSensor.humidity
        return [tempC, humidity]
    
    except RuntimeError as noreading:
        # print("Temp Sensor reached RuntimeError")
        return None

def get_tempF(celsius_temp):
    return celsius_temp * 9 / 5 + 32
 
def display_values(header, row):
    readings = zip(header, row)
    for label, value in readings:
        print(label, row, "\t", end=" ")


# dht_readings = temp_sensor()
compromised_dht_reading = []

while not compromised_dht_reading:
    dht_readings = temp_sensor()
    if dht_readings is not None:
        print("Initial temp reading has been found and saved")
        compromised_dht_reading.append(dht_readings)
    t.sleep(2)

try:
    while True:      
        dht_readings = temp_sensor()
        if dht_readings is not None:
          #  print("New DHT readings was succesful")
            compromised_dht_reading.pop()
               
        elif dht_readings is None:
          #  print("New DHT readings was None")
            dht_readings = temp_sensor()
            if dht_readings is None:
          #      print("Second attempt at dht reading is none. Continue in the loop with previous reading")
                dht_readings = compromised_dht_reading[0] # use previous reading
        
        vel_sound  = compute_sound_velocity(dht_readings[0], dht_readings[1])
        sonar_values = compute_distance(vel_sound)
        distance, sonar_deltatime = sonar_values[0], sonar_values[1]
        tempC, humidity_perc = dht_readings[0], dht_readings[1]
        tempF = get_tempF(dht_readings[0]) 
        full_date = t.asctime()
        milisec_time = t.perf_counter_ns() // 100000 #time in milis
        hour_time = t.localtime()[3]

        data_row_values = [full_date, hour_time, milisec_time, t.time(), 
                            vel_sound, distance, sonar_deltatime, tempC, tempF, 
                            humidity_perc]
                        
        append_file(data_row_values) # update csvfile
         # display_values(columns, data_row_values)
        if distance < 400:   
            print("Time: {0}     Distance: {1}cm.".format(full_date, distance))
        if compromised_dht_reading:
            # print("Theres an extra Temp reading in COMP array. COMPDHT array poped")
            compromised_dht_reading.pop()
        
        compromised_dht_reading.append(dht_readings)
        # print("End of writing data", compromised_dht_reading)    
        t.sleep(0.5) # allows a 0.5 second for the user to cancel the loop
        
except KeyboardInterrupt:
    print("User interuption")
    GPIO.cleanup()
    DHTSensor.exit()
    
finally:
    GPIO.cleanup()
    print("GPIO.cleanup() was successful!")
    DHTSensor.exit()

