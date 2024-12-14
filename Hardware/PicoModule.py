import network # for Wi-Fi
import urequests # for POST, GET
import time
import dht # to read sensor output
import ntptime # to get current time
from mfrc522 import MFRC522 # for reading rfid tag and will learn how to write in block
import uasyncio as asyncio

dht_module = dht.DHT11(15)
rfid_reader = MFRC522(spi_id=0,sck=2,miso=4,mosi=7,cs=5,rst=18)

url_w = 'http://52.251.41.188:7898/warehouse'
url_m = 'http://52.251.41.188:7898/manufacturer'
url_m_rfid = 'http://52.251.41.188:7898/rfid'
url_m_collector = 'http://52.251.41.188:7898/rfid/collect?rfid={}'

def connect_to_internet():
    ssid = 'Synthesis Ion'
    password = 'atv50a80'
#     ssid = 'Galaxy A34 5G AF63'
#     password = 'hariesh5'
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid,password)
    print("Connecting to Wifi...", end='')
    while wlan.isconnected()== False:
        print('.',end='')
        time.sleep(1)
        
    print()
    print("Connected to Wi-Fi")
    print(wlan.ifconfig()[0])

def send_msg(url, data):
    response = urequests.post(url,json=data)
    return response.json()
    

def read_dht(id):
    while True:
        try:
            dht_module.measure()
            temp = dht_module.temperature()
            humidity = dht_module.humidity()
            print(f"DHT Readings - Temperature: {temp}, Humidity: {humidity}")
            await send_msg("http://52.251.41.188:7898/warehouse", {"wid":id,"temp": temp, "humidity": humidity})
        except Exception as e:
            print("Error reading DHT module:", e)
       

def get_time():    
    ist_time = time.localtime()
    formatted_time = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        ist_time[0], ist_time[1], ist_time[2], ist_time[3], ist_time[4], ist_time[5]
    )
    return formatted_time        
    
def read_rfid():
    while True:
        rfid_reader.init()
        (card_status, tag_type) = rfid_reader.request(rfid_reader.REQIDL)
        if card_status == rfid_reader.OK:
            (card_status, card_id) = rfid_reader.SelectTagSN()
            if card_status == rfid_reader.OK:
                rfid_card = int.from_bytes(bytes(card_id),"little",False)
                print("Detected Card : "+ str(rfid_card))
                return str(rfid_card)


connect_to_internet()
while True:
        
        print("Main Menu")
        print("1. Manufacturing Mode")
        print("2. Warehouse Mode")
        print("3. Retailer Mode")
        print("4. Exit")
        ch = int(input("What mode do you choose(1-4): "))
        
        if ch == 1:
            # For the manufacturer
            m_id = '1000'
            my_addr = "Manufacturer Address"
            # create 2 options one to create product & to assign rfid
            
            while True:
                print("a. Start Production")
                print("b. Dispatch Produced Products")
                print("c. Back")
                option = input("Choose an option(a-c): ")
                if option=='a':
                    
                    datetime = get_time()
                    order_id = input("Product ID to manufacture: ")
                    order_count = int(input("How many pieces to manufacture: "))               
                    data = {
                        'ppid':order_id,
                        'date': datetime,
                        'count': order_count}
                    response = send_msg(url_m, data) # return the starting and ending product id's
                    print("Product ID created: ", response["PLIS"])
                elif option=='b':
                    
                    warehouse_id = input("Enter the warehouse ID to send: ")
                    prod_id = input("Product ID to transmit: ")
                    prod_qty_start = input("Starting Piece ID: ") # change something else so easy to access.
                    prod_qty_end = input("Ending Piece ID: ")
                    plis = '{{"start": "{}", "end": "{}"}}'.format(prod_qty_start, prod_qty_end)

                    print("Place your RFID tag/card to link it with the current order...")
                    rfid = read_rfid()
                    
                    data = {
                        'twid': warehouse_id, #to
                        'fwid': m_id, # from
                        'rfid': rfid,
                        'plis': plis,
                        'loc': my_addr,
                        } # 0 for new rfid, 1 for consequent change and last time 2
                    response = send_msg(url_m_rfid, data)
                    print(response)
                else:
                    break
                                   
       
        if ch == 2:
            my_addr = "Distributor Address"
            m_id = '1001' # distributor Id as of now
            # create 2 options one to create product & to assign rfid
            
            while True:
                print("a. Scan Incoming batches")
                print("b. Dispatch to Retailer")
                print("c. Back")
                option = input("Choose an option(a-c):")
                
                if option == 'a':
                    m_id = input("Enter the Warehouse Id: ")
                    print("Scan Incoming Parcel: ")
                    rfid_prev = read_rfid()
                    response = urequests.get(url_m_collector.format(rfid_prev))
                    print(response.text)
                    
                elif option=='b':
                    retailer_id = input("Enter the Retailer ID to send: ")
                    prod_id = input("Product ID to transmit: ")
                    prod_qty_start = input("Batch ID starting: ") # change something else so easy to access.
                    prod_qty_end = input("Batch ID ending: ")
                    plis = '{{"start": "{}", "end": "{}"}}'.format(prod_qty_start, prod_qty_end)
                
                    print("Place your RFID tag/card to link it with the current order...")
                    rfid = read_rfid()
                    
                    if rfid_prev != rfid:
                        data = {
                        'twid': retailer_id,
                        'fwid': m_id,
                        'rfid': rfid,
                        'plis': plis,
                        'loc': my_addr,
                        'prfid':rfid_prev,
                        } # 0 for new rfid, 1 for consequent change and last time
                    else:
                        data = {
                        'twid': retailer_id,
                        'fwid': m_id,
                        'rfid': rfid,
                        'plis': plis,
                        'loc': my_addr,
                        } 
                    response = send_msg(url_m_rfid, data)
                    print(response)
                     ## prepare order for retailer (specify product type, count) get it from server and assign rfid to it accordingly.
                elif option =="c":
                    break
        
        # finally at the retailer the order should be scanned again to know if it is delivered or not( confirm receipt, record timestamp update the inventory)
        if ch==3:
            #my_addr = "Retailer Address"
#             m_id = input("Enter the Retailer Id: ")
            m_id = '1101'
            print("Scan Incoming Parcel: ")
            rfid = read_rfid()
            response = urequests.get(url_m_collector.format(rfid))
            print(response.text)
            #collector function
            
        if ch==4:
            print("Program Halted!")
            break
        
        else:
            continue
