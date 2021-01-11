import RPi.GPIO as GPIO
import board
import adafrout_dht
from csv import writer
import time as t
import os.path

GPIO.setmode(GPIO.BCM)
TEMP = board.D18
# Sonar Gpio set to 23 for trig, 24 for echo
TRIG = 23 # GPIO PIN number, NOT THE PLUGIN NUMBER OF THE PI
ECHO = 24 # GPIO PIN NUMBER

DHTSensor = adafruit_dht.DHT11(TEMP)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)
GPIO.setup(TEMP, GPIO.IN)
data_filename = 'TempHumid_sonar_data.csv'
print('bootup check')
# sound_constant = 34300 / 2 # cm/s


if not os.path.exists(data_filename):
    print('creating new file')
    columns = ['Date','Hour', 'Time From Epoch(S)','Sound Velocity(cm/s)', 
                'Distance(CM)', 'Deltatime(S)', "Temperature(C)", 
                "Temperature(F)", "Humidity(%)"]
    
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

    # use d = v * t, when v is half the speed of sound at sea level @ 343 m/s
    distance = delta_time * sound_velocity / 2 # cm
    return [distance, delta_time]

def compute_sound_velocity(temp_reading, humidity_reading):
    """Uses the Sound Velocity formula to improve the accuracy of detecting distance
        Vsound[m/s] = 331.4 + (0.606 * TempC) + (0.0124 * Humidity)"""
    vsound = 331.4 + (0.606 * temp_reading) + (0.0124 * humidity_reading)
    return vsound * 100 # cm

def temp_sensor():
    tempC = DHTSensor.temperature
    humidity = DHTSensor.humidity
    return [tempC, humidity]

def get_tempF(celsius_temp):
    return celsius_temp * 9 / 5 + 32
 
def display_values(header, row):
    readings = zip(header, row)
    for label, value in readings:
        print(label, row, "\t", end=" ")


# time_trackerA = t.localtime()[5]
dht_readings = temp_sensor()
t.sleep(2)
compromised_dht_reading = []
compromised_dht_reading.append(dht_readings)

try:
    while True:
  #      time_trackerB = t.localtime()[5]
  #      time_count = time_trackerB - time_trackerA
  #      if time_count >= 2: # every 2 seconds update temperature readings
        
        dht_readings = temp_sensor()
        if dht_readings[0] is not None or dht_readings[1] is not None:
            compromised_dht_reading.pop()
            # t.sleep(2)
            # dht_readings = temp_sensor()
            #continue
        
        elif dht_readings[0] is None or dht_readings[1] is None:
            dht_readings = temp_sensor()
            dht_readings = compromised_dht_reading[0] # use previous reading
            # t.sleep(1) or 2 sec
            #continue

      #  dht_readings = compromised_dht_reading  
        vel_sound  = compute_sound_velocity(dht_readings[0], dht_readings[1])
        sonar_values = compute_distance(vel_sound)
        distance, sonar_deltatime = sonar_values[0], sonar_values[1]
        tempC, humidity_perc = dht_readings[0], dht_readings[1]
        tempF = get_tempF(dht_readings[0]) 
        local_time = t.asctime()
        hour_time = t.localtime()[3]

# ['Date','Hour', 'Time From Epoch(S)',  "Sound Velocity(cm/s)"
#    "Distance(CM)', 'Deltatime(S)', "Temperature(C)", "Temperature(F)", 
#                "Humidity(%)"]
    

        data_row_values = [local_time, hour_time, t.time(), vel_sound, 
                            distance, sonar_deltatime, tempC, tempF, 
                            humidity_perc]
                        
        append_file(data_row_values)
        display_values(header, row)
           
        #print("Time: {0}     Distance: {1}cm.".format(local_time, values[0]))
        if compromised_dht_reading:
            compromised_dht_reading.pop()
            
        compromised_dht_reading.append(dht_readings)
        t.sleep(0.5) # allows a second for the user to cancel the loop
        
except KeyboardInterrupt:
    print("User interuption")
    GPIO.cleanup()
    DHTSensor.exit()
    #close('sonar_sensor.csv')

finally:
    GPIO.cleanup()
    DHTSensor.exit()
    # <file>.close()
    
