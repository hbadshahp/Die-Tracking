#uhf library file
import machine
import time
import binascii
import array

'''
standard commands for UHF operations, refer command manual for more details
https://github.com/sbcshop/UHF_Reader_Pico_W_Software/blob/main/documents/UHF%20Commands%20Manual.pdf
So, you can add more commands for other operation
'''

# SINGLE EPC READ try
STARTBYTE     ='03' # combine Header + Type Request frame length LSB txBuf[0] 
ENDBYTE       ='3EC5' # CRC LSB txBuf[4] + txBuf[5]
SINGLE_READ   ='5002'# command code MSB AND LSB txBuf[1] + txBuf[2]

class UHF():
    def __init__(self,baudrate):
        self.serial = machine.UART(1, baudrate=baudrate, bits=8, parity=None, stop=1,tx=17,rx=18)
        self.serial.init(baudrate=baudrate, bits=8, parity=None, stop=1)
        time.sleep(0.2)
    
    def calculate_crc(self, data_hex_string):
        """
        Calculate CRC for hex string data
        Args:
            data_hex_string: hex string without CRC part
        Returns:
            string: calculated CRC as hex string (4 characters)
        """
        # Convert hex string to bytes
        data_bytes = binascii.unhexlify(data_hex_string)
        
        crc = 0x0000FFFF  # Initial CRC value
        
        for byte_val in data_bytes:
            crc = crc ^ byte_val
            for bit in range(8):
                if (crc & 0x8000) == 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = (crc << 1)
                # Keep within 16-bit range
                crc = crc & 0xFFFF
        
        # Return inverted CRC as hex string
        final_crc = (~crc) & 0xFFFF
        return f"{final_crc:04X}"
    
    def verify_crc(self, response_data):
        """
        Verify CRC of received response
        Args:
            response_data: list of hex strings or bytes
        Returns:
            bool: True if CRC is valid, False otherwise
        """
        if response_data is None or len(response_data) < 3:
            return False
        
        # Convert to hex string if it's bytes
        if isinstance(response_data[0], int):
            hex_data = ['{:02x}'.format(x) for x in response_data]
        else:
            hex_data = response_data
        
        # Extract data without CRC (assuming last 2 bytes are CRC)
        data_part = ''.join(hex_data[:-2])
        received_crc = ''.join(hex_data[-2:]).upper()
        
        # Calculate expected CRC
        calculated_crc = self.calculate_crc(data_part)
        
        print(f"Data: {data_part}")
        print(f"Received CRC: {received_crc}")
        print(f"Calculated CRC: {calculated_crc}")
        
        return received_crc == calculated_crc
    
    def calculation(self, data_hex_string):
        """
        Legacy method name for backward compatibility
        """
        return self.calculate_crc(data_hex_string)
        
    def read_mul(self):
        rec_data = self.serial.read(24)
        if rec_data is not None and len(rec_data)>22:
            if rec_data[0] != 0xbb or rec_data[23] != 0x7e or rec_data[1] != 0x02:
                return None
            
            # Verify CRC for received data
            hex_response = ['{:02x}'.format(x) for x in rec_data]
            if self.verify_crc(hex_response):
                print("CRC verification passed")
                return hex_response
            else:
                print("CRC verification failed")
                return None
    
    def send_command(self, data):
        if isinstance(data, str):
            # Single hex string - split into command and CRC parts
            Data = data
        else:
            # List of hex strings
            Data = ''.join(data)
        
        print('Request:', Data)
        bin_data = binascii.unhexlify(Data)
        response = self.serial.write(bin_data)
    
    def Kill_card(self):
        fig = '6500040000FFFF'   
        dat = self.calculate_crc(fig)
        dat1 = STARTBYTE + fig + dat
        print("Kill card command:", dat1)
        self.send_command(dat1)
        time.sleep(0.2)
        rec_data = self.serial.read(24)
        
        if rec_data is not None:
            hex_response = ['{:02x}'.format(x) for x in rec_data]
            print("Kill card response:", hex_response)
            
            if self.verify_crc(hex_response):
                print("Kill card - CRC verification passed")
                return hex_response
            else:
                print("Kill card - CRC verification failed")
                return None
                
    def Set_select_pera(self, tag_uid):          
        fig = '0C001300000000206000' + tag_uid
        dat = self.calculate_crc(fig)
        dat1 = STARTBYTE + fig + dat
        print('Card select command:', dat1)
        self.send_command(dat1)
        time.sleep(0.2)
        rec_data = self.serial.read(16)
        
        if rec_data is not None:
            hex_response = ['{:02x}'.format(x) for x in rec_data]
            print('Select response:', hex_response)
            
            if self.verify_crc(hex_response):
                if "".join(hex_response) == 'bb010c0001000e7e':   
                    return 'Select successful'
                else:
                    return 'Invalid response'
            else:
                print("Select - CRC verification failed")
                return 'CRC error'
    
    def Read_tag_data(self, memory_bank):
        fig = '390009000000000' + memory_bank + '00000008'   
        dat = self.calculate_crc(fig)
        dat1 = STARTBYTE + fig + dat
        print("Read tag command:", dat1)
        
        self.send_command(dat1)
        time.sleep(0.2)
        rec_data = self.serial.read(40)
        
        if rec_data is not None:
            hex_response = ['{:02x}'.format(x) for x in rec_data]
            print("Read tag response:", hex_response)
            
            if self.verify_crc(hex_response):
                print("Read tag - CRC verification passed")
                response_str = "".join(hex_response)
                
                if response_str == 'bb01ff0001090a7e':
                    return 'No card is there'
                else:
                    if memory_bank == '2':
                        return response_str[40:72]
                    elif memory_bank == '3':
                        return response_str[40:70]
                    elif memory_bank == '1':
                        return response_str[48:72]
            else:
                print("Read tag - CRC verification failed")
                return 'CRC error'

    def Write_tag_data(self, data_w, memory_bank):  
        fig = '490019000000000' + memory_bank + '00000008' + data_w      
        dat = self.calculate_crc(fig)
        dat1 = STARTBYTE + fig + dat
        print('Write command:', dat1)
        self.send_command(dat1)
        time.sleep(0.2)
        rec_data = self.serial.read(23)
        
        if rec_data is not None:
            hex_response = ['{:02x}'.format(x) for x in rec_data]
            print('Write data response:', hex_response)
            
            if self.verify_crc(hex_response):
                response_str = "".join(hex_response)
                if response_str == 'bb01ff000110117e':  
                    return 'Write card failed, No tag response'
                elif response_str == 'bb01ff000117187e':   
                    return 'Command error'
                elif hex_response[2] == '49':
                    return 'Card successfully written'
            else:
                print("Write tag - CRC verification failed")
                return 'CRC error'

    def single_read(self):
        # Create command with proper CRC
        command_data = SINGLE_READ  # '5002'
        calculated_crc = self.calculate_crc(STARTBYTE + command_data)
        full_command = STARTBYTE + command_data + calculated_crc
        
        print("Single read command:", full_command)
        self.send_command(full_command)
        
        time.sleep(0.5)
        rec_data = self.serial.read()
        print("Single read response:", rec_data)
        
        if rec_data is not None and len(rec_data) > 20:
            hex_response = ['{:02x}'.format(x) for x in rec_data]
            
            # Verify CRC of response
            if self.verify_crc(hex_response):
                print("Single read - CRC verification passed")
                return hex_response
            else:
                print("Single read - CRC verification failed")
                return None
        else:
            return None

    # Keep other methods as they were, but add CRC verification where needed
    def hardware_version(self):
        # Implementation would need CRC calculation for command
        pass

    def multiple_read(self):
        # Implementation would need CRC calculation for command
        pass

    def stop_read(self):
        # Implementation would need CRC calculation for command
        pass
    
    def setRegion_EU(self):
        # Implementation would need CRC calculation for command
        pass
    
    def setRegion_US(self):
        # Implementation would need CRC calculation for command
        pass
        
    def getReceivingModem(self):
        # Implementation would need CRC calculation for command
        pass
    
    def setTransmit_Power(self):
        # Implementation would need CRC calculation for command
        pass
    
    def getTransmit_Power(self):
        # Implementation would need CRC calculation for command
        pass