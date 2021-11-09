#!/usr/bin/env python
import sys
try:
    import os
    import time
    import re
    import subprocess
    from sonic_sfp.sfputilbase import SfpUtilBase
except ImportError as e:
    raise ImportError (str(e) + "- required module not found")


class SfpUtil(SfpUtilBase):
    """Platform specific SfpUtill class"""
    
    _port_start = 1
    _port_end = 0
    _qsfp_port_start = 1
    _qsfp_port_end = 0
    ports_in_block = 0
    QSFP_CHECK_INTERVAL = 4
         
    _port_to_eeprom_mapping = {}
    #i2c-0 is i801 SMBUS
    #i2c-1~i2c-32are smbus 1-32 that map into port 1-32
    port_to_i2c_mapping = {}
       
    _cpld_mapping = {
       1:  "33-0062",
       2:  "34-0064",
           }
        
    def __init__(self):
        self.ready = True
        self.phy_port_dict = {'-1': 'system_not_ready'}
        self.phy_port_cur_state = {}
        self.qsfp_interval = self.QSFP_CHECK_INTERVAL
        eeprom_path = '/sys/bus/i2c/devices/{0}-0050/sfp_eeprom'
        
        self.set_i2cmap()
                   
        for x in range(0, self._port_end):
            port_eeprom_path = eeprom_path.format(self.port_to_i2c_mapping[x+1])
            self._port_to_eeprom_mapping[x+1] = port_eeprom_path
        SfpUtilBase.__init__(self)
        
    def set_i2cmap(self):
        fp_port_index = 0
        number = 0
        
        if os.path.isfile("/usr/share/sonic/platform/Accton-CSP7551/port_config.ini"):
            porttabfile = "/usr/share/sonic/platform/Accton-CSP7551/port_config.ini"
        else:
            porttabfile = "/usr/share/sonic/device/x86_64-accton_csp7551-r0/Accton-CSP7551/port_config.ini"
                            
        try:
          f = open(porttabfile)
        except:
          raise
                        
        title = []
        for line in f:
            line.strip()
            if re.search("^#", line) is not None:
                # The current format is: # name lanes alias index speed
                # Where the ordering of the columns can vary
                title = line.split()[1:]
                continue
                     
            portname = line.split()[0]             
            fp_port_index = int(line.split()[title.index("index")])               
            number = portname[8:] 
            self.port_to_i2c_mapping.setdefault(fp_port_index,int((int(number)-1)/4+1))
            
        
        self._port_end = fp_port_index
        self._qsfp_port_end = fp_port_index
        self.ports_in_block = fp_port_index
             
        #for x in range(0, self._port_end):
            #print("%d : %s " % (x+1,self.port_to_i2c_mapping[x+1]))
            
        return 0
      
    # For 1~16 are at cpld1, others are at cpld2.
    def get_cpld_num(self, port_num):             
        cpld_i = 1
        if (self.port_to_i2c_mapping[port_num] > 16 and self.port_to_i2c_mapping[port_num] < 33):
            cpld_i = 2

        return cpld_i

    '''
    def get_eeprom_raw(self, port_num):
        # Read interface id EEPROM at addr 0x50
        eeprom_raw = []

        for i in range(0, 256):
            eeprom_raw.append("0x00")
            
        raw_info_func="docker exec -it syncd python /opt/bfn/install_msdc_profile/lib/python2.7/site-packages/sfputil.py sfp_dump_raw_port %d" % port_num

        st, raw = commands.getstatusoutput(raw_info_func)
        if st != 0:
            raise 'error on syscmd'

        try:
            for i in range(256):
                eeprom_raw[i]  = raw[i*2] + raw[(i*2)+1]

        except:
            return None
        
        return eeprom_raw

    def get_eeprom_dom_raw(self, port_num):
        if port_num in self.qsfp_ports:
            # QSFP DOM EEPROM is also at addr 0x50 and thus also stored in eeprom_ifraw
            return None
        else:
            # Read dom eeprom at addr 0x51
            eeprom_raw = []
            for i in range(0, 256):
                eeprom_raw.append("0x00")

            raw_info_func = "docker exec -it syncd python /opt/bfn/install_msdc_profile/lib/python2.7/site-packages/sfputil.py sfp_dump_dom_port %d" % port_num

            st, dom_raw = commands.getstatusoutput(raw_info_func)
            if st != 0:
                raise 'error on syscmd'

            try:
                for i in range(256):
                    eeprom_raw[i] = dom_raw[i*2] + dom_raw[(i*2)+1]

            except:
                return None
        
            return eeprom_raw
    '''

    def reset(self, port_num):
        # Check for invalid port_num
        if port_num < self._qsfp_port_start or port_num > self._qsfp_port_end:
            return False

        path = "/sys/bus/i2c/devices/{0}-0050/sfp_mod_rst"
        port_ps = path.format(self.port_to_i2c_mapping[port_num])
 
        try:
            reg_file = open(port_ps, 'w')
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        #HW will clear reset after set.
        reg_file.seek(0)
        reg_file.write('1')
        reg_file.close()
        return True

    def set_low_power_mode(self, port_num, lpmode):
        # Check for invalid port_num
        if port_num < self.port_start or port_num > self.port_end:
            return False

        path = "/sys/bus/i2c/devices/{0}-0050/sfp_lp_mod_sel"
        port_ps = path.format(self.port_to_i2c_mapping[port_num])

        try:
            reg_file = open(port_ps, "r+")
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        reg_value = int(reg_file.readline().rstrip())

        # LPMode is active high; set or clear the bit accordingly
        if lpmode is True:
            reg_value = 1
        else:
            reg_value = 0

        reg_file.write(str(reg_value))
        reg_file.close()

        return True

        
    def get_low_power_mode(self, port_num):
        # Check for invalid port_num
        if port_num < self._port_start or port_num > self._port_end:
            return False

        path = "/sys/bus/i2c/devices/{0}-0050/sfp_lp_mod_sel"
        port_ps = path.format(self.port_to_i2c_mapping[port_num])
          
        try:
            reg_file = open(port_ps)
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        reg_value = reg_file.readline().rstrip()
        if reg_value == '1':
            return True

        return False
                  
    def get_presence(self, port_num):
        # Check for invalid port_num
        if port_num < self._port_start or port_num > self._port_end:
            return False

        path = "/sys/bus/i2c/devices/{}-0050/sfp_is_present"
        port_ps = path.format(self.port_to_i2c_mapping[port_num])
        
        try:
            reg_file = open(port_ps)
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        reg_value = reg_file.readline().rstrip()
        if reg_value == '1':
            return True

        return False

    def tx_disable(self, port_num, disable):
        # Check for invalid port_num
        if port_num < self.port_start or port_num > self.port_end:
            return False

        presence = self.get_presence(port_num)
        if not presence:
            return True

        path = "/sys/bus/i2c/devices/{0}-0050/sfp_tx_disable"
        port_ps = path.format(self.port_to_i2c_mapping[port_num])

        try:
            reg_file = open(port_ps, "r+")
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        reg_value = int(reg_file.readline().rstrip())

        # tx_disable is active high; set or clear the bit accordingly
        if disable is True:
            reg_value = 1
            #print("reg_value=1")
        else:
            reg_value = 0
            #print("reg_value=0")

        reg_file.write(str(reg_value))
        reg_file.close()

        return True
    @property
    def port_start(self):
        return self._port_start

    @property
    def port_end(self):
        return self._port_end
	
    @property
    def qsfp_ports(self):
        return range(self._qsfp_port_start, self.ports_in_block + 1)

    @property 
    def port_to_eeprom_mapping(self):
         return self._port_to_eeprom_mapping
         
    def check_transceiver_change(self):
        if not self.ready:
            return

        self.phy_port_dict = {}

        # Get presence of each SFP
        for port in range(self.port_start, self.port_end+1):
            try:
                sfp_resent = self.get_presence(port)
            except:
                sfp_resent = False
            sfp_state = '1' if sfp_resent else '0'

            if port in self.phy_port_cur_state:
                if self.phy_port_cur_state[port] != sfp_state:
                    self.phy_port_dict[port] = sfp_state
            else:
                self.phy_port_dict[port] = sfp_state

            # Update port current state
            self.phy_port_cur_state[port] = sfp_state

    def get_transceiver_change_event(self, timeout=0):
        forever = False
        if timeout == 0:
            forever = True
        elif timeout > 0:
            timeout = timeout / float(1000) # Convert to secs
        else:
            print("get_transceiver_change_event:Invalid timeout value", timeout)
            return False, {}

        while forever or timeout > 0:
            if self.qsfp_interval == 0:
                self.qsfp_interval = self.QSFP_CHECK_INTERVAL

                # Process transceiver plug-in/out event
                self.check_transceiver_change()

                # Break if tranceiver state has changed
                if bool(self.phy_port_dict):
                    break

            if timeout:
                timeout -= 1

            if self.qsfp_interval:
                self.qsfp_interval -= 1

            time.sleep(1)

        return self.ready, self.phy_port_dict

'''        
    def get_transceiver_change_event(self):
        """
        TODO: This function need to be implemented
        when decide to support monitoring SFP(Xcvrd)
        on this platform.
        """
        raise NotImplementedError
'''

def main():
    sfp = SfpUtil()
    if sys.argv[1] == "1":
        sfp.tx_disable(int(sys.argv[2]),True)
        print("port %d disable TX" %(int(sys.argv[2])))
    else:
        sfp.tx_disable(int(sys.argv[2]),False)
        print("port %d enable TX" %(int(sys.argv[2])))
        
if __name__ == '__main__':
    if len(sys.argv) > 1:
        main()
