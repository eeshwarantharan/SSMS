import time
import urequests
import dht
from machine import Pin

# Initialize the DHT11 sensor
dht_module = dht.DHT11(Pin(15))

def send_msg(url, data):
    try:
        response = urequests.post(url, json=data)
        print("Server Response:", response.text)
        response.close()
    except Exception as e:
        print("Error while sending message:", e)

def read_and_send_dht(id):
    while True:
        try:
            # Read temperature and humidity from DHT11
            dht_module.measure()
            temp = dht_module.temperature()
            humidity = dht_module.humidity()
            print(f"DHT Readings - Temperature: {temp}, Humidity: {humidity}")

            send_msg("http://52.251.41.188:7898/warehouse", {"wid": id, "temp": temp, "humidity": humidity})
        except Exception as e:
            print("Error reading DHT module:", e)
        
        # Wait for 10 seconds before the next reading
        time.sleep(5)

# Start reading and sending DHT values
# wid = input("Enter the place ID to send sensor values: ")
read_and_send_dht(1001)