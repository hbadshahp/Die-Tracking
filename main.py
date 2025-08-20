# Connect to WiFi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    
    while not wlan.isconnected():
        print("Connecting to WiFi...")
        time.sleep(1)
    
    print("WiFi connected, IP address:", wlan.ifconfig()[0])

# MQTT callback function
def mqtt_callback(topic, msg):
    print(f"Message received: Topic: {topic}, Msg: {msg}")
    message = msg.decode('utf-8')
    print(message)
    
    if message == "up":
        
        RELAY_UP_PIN.on()  # Activate the relay
        #time.sleep(0.550)
        time.sleep(0.750)
        
        RELAY_UP_PIN.off()  # Deactivate the relay
    elif message == "down":
        
        RELAY_DOWN_PIN.on()  # Activate the relay
        #time.sleep(0.550)
        time.sleep(0.750)
        RELAY_DOWN_PIN.off()  # Deactivate the relay
    else:
        die_signal = float(message)
        #if die_signal < 250.0 or die_signal > 350.0:
        if die_signal < 450.0 or die_signal > 600.0:
            print("Invalid input: Out of range")
            return
        
        success, current_height = readCurrentDieHeight()
        if not success:
            print("Failed to read Modbus registers")
            return
        
        difference = current_height - die_signal
        #threshold1 = 0.1 # precision threshold for height adjustment 0.02
        #threshold2 =0.79
        threshold = 0.1
        # Activation of relay for 0.125 difference
        if difference > threshold:
            print("Operating down relay")
            operateRelay(RELAY_DOWN_PIN, die_signal, threshold, False)
        elif difference < -threshold:
            print("Operating up relay")
            operateRelay(RELAY_UP_PIN, die_signal, threshold, True)
        else:
            print("Height is within acceptable range")

# Connect to MQTT broker
def connect_mqtt():
    global client
    client = MQTTClient(client_id, mqtt_server, port=mqtt_port, user=mqtt_user, password=mqtt_password)
    client.set_callback(mqtt_callback)
    client.connect()
    client.subscribe(mqtt_subscribe_topic)
    print(f"Connected to MQTT broker at {mqtt_server}")
    return client


# Function to read current die height
def readCurrentDieHeight():
    slave_addr = const(0x08)  # Modbus slave address (updated to 8)
    starting_address = const(0x00)  # Start reading from address 0x0000
    register_quantity = const(2)  # Read two registers (32-bit value)

    # Try reading the holding registers
    try:
        #time.sleep(0.2)  # Small delay to give slave time to respond
        #print("Read")
        register_values = m.read_holding_registers(slave_addr, starting_address, register_quantity, signed=False)
        
        if register_values is None or len(register_values) != register_quantity:
            print("Failed to read Modbus registers")
            return False, 0.0
        
        # Combine the two 16-bit registers into a 32-bit unsigned integer
        register1 = register_values[0]
        register2 = register_values[1]

        combined_value = (register1 << 16) | register2

        # Convert to floating-point
        die_height = combined_value / 100000.0

        #print(f"Current Die Height: {die_height:.2f}")
        return True, die_height

    except Exception as e:
        print(f"Error reading Modbus registers: {e}")
        return False, 0.0    
    

def main():
    while True:
        try:
            connect_wifi()
            mqtt_client = connect_mqtt()

            baudrate = 115200
            uhf = UHF(baudrate)

            card = ""
            curr_card = ""
            same_tag_counter = 0
            no_tag_counter = 0
            NA_SENT = False  # Avoid spamming "NA"

            while True:
                rev = uhf.single_read()

                if rev is not None:
                    curr_card = str("".join(rev[7:19]))

                    if curr_card == card:
                        same_tag_counter += 1
                        no_tag_counter = 0  # Reset NA counter
                    else:
                        same_tag_counter = 1
                        no_tag_counter = 0
                        card = curr_card

                    if same_tag_counter == 8:
                        success, die_height = readCurrentDieHeight()
                        if success:
                            msg_str = f"{die_height:.2f}"
                        else:
                            print("Failed to read die height")
                            msg_str = "Failed"
                            
                        card_id_json = {
                            "card": curr_card,
                            "client_id": client_id,
                            "die_height": msg_str
                        }
                        json_msg = ujson.dumps(card_id_json)
                        print(json_msg)
                        mqtt_client.publish(topic_pub3, json_msg)

                        NA_SENT = False  # reset flag since valid card was detected
                        same_tag_counter = 0  # reset after successful publish

                else:
                    no_tag_counter += 1
                    same_tag_counter = 0
                    success, die_height = readCurrentDieHeight()
                    if success:
                        msg_str = f"{die_height:.2f}"
                        card_id_json = {
                            "card": "NA",
                            "client_id": client_id,
                            "die_height": msg_str
                        }
                        json_msg = ujson.dumps(card_id_json)
                        print(json_msg)
                        mqtt_client.publish(topic_pub3, json_msg)
                    else:
                        print("Failed to read die height")
                    if no_tag_counter == 50 and not NA_SENT:
                        success, die_height = readCurrentDieHeight()
                        if success:
                            msg_str = f"{die_height:.2f}"
                            card_id_json = {
                                "card": "NA",
                                "client_id": client_id,
                                "die_height": msg_str
                            }
                            json_msg = ujson.dumps(card_id_json)
                            print(json_msg)
                            mqtt_client.publish(topic_pub3, json_msg)
                        else:
                            print("Failed to read die height")

                        NA_SENT = True
                        card = ""  # reset stored card to allow new detection
                        no_tag_counter = 0

        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(5)

# Execute the main loop
if __name__ == "__main__":
    main()
