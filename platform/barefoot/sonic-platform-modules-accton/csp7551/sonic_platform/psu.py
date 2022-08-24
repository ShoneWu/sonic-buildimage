#############################################################################
# Edgecore
#
# Module contains an implementation of SONiC Platform Base API and
# provides the PSUs status which are available in the platform
#
#############################################################################


import logging
import subprocess
import math
try:
    from sonic_platform_base.psu_base import PsuBase
    #from .helper import APIHelper
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")



IPMI_FRU_CMD="ipmitool fru print {0}"
IPMI_SENSOR_CMD="ipmitool raw 0x4 0x2d {0}"
IPMI_SENSOR_THRESHOLD_CMD="ipmitool raw 0x4 0x27 {0}"
IPMI_SENSOR_PARAM_CMD="ipmitool raw 0x4 0x21 0x00 0x00 {0} 0x00 24 6"
IPMI_PSU_PRESENT_GOOD_CMD="ipmitool raw 0x36 0x10"
PSU_NAME_LIST = ["PSU1", "PSU2"]
PSU_NUM_FAN = [1, 1]

PSU_FRU_INDEX={
    0:9,
    1:10
}
PSU_SENSOR_INDEX={
    0:{
        "vin" : 203,
        "vout" : 204,
        "pin" : 205,
        "iin" : 206,
        "ambi_temp" : 207,
        "second_temp" :208,
        "iout" : 209,
        "pout" : 217,
        "fan" : 219
    },
    1:{
        "vin" : 211,
        "vout" : 212,
        "pin" : 213,
        "iin" : 214,
        "ambi_temp" : 215,
        "second_temp" :216,
        "iout" : 210,
        "pout" : 218,
        "fan" : 220        
    },
}

class Psu(PsuBase):
    def _syscmd(self,cmd):        
        proc = subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=True,stderr=subprocess.PIPE)
        data, _ = proc.communicate()
        status=proc.returncode
        data=data.decode(errors="ignore")
        return status , data


    def get_param(self,type):
        command=IPMI_SENSOR_PARAM_CMD.format(PSU_SENSOR_INDEX[self.index][type])
        st1, log1 = self._syscmd(command)
        if st1 != 0:
            print('error on syscmd')
        m1 = log1.split()[2].strip()
        m2 = log1.split()[3].strip()
        m2 = (int(m2,16)&0xc0) <<2
        m3=int(m1,16)+m2
        if (m3 & 0x200 != 0):
            m3 = m3-1024
        b1 = log1.split()[4].strip()
        b2 = log1.split()[5].strip()
        b2 = (int(b2,16)&0xc0) <<2
        b3=int(b1,16)+b2
        if (b3 & 0x200 != 0):
            b3 = b3-1024
        rb_exp = log1.split()[7].strip()
        r_exp = (int(rb_exp,16) & 0xf0)>>4
        if(r_exp & 0x8 !=0 ):
            r_exp = r_exp -16
        b_exp =  (int(rb_exp,16) & 0x0f)
        if(b_exp & 0x8 !=0 ):
            b_exp = b_exp -16
        
        return m3,b3,r_exp,b_exp

    def convert_ipmi(self,val,type):
        m,b,r_exp,b_exp=self.get_param(type)
        offset=b*math.pow(10,b_exp)
        rex=math.pow(10,r_exp)
        val2=(int(val,16)*m+offset)*rex
        return val2

    def get_sensor_command(self,type):
        index=PSU_SENSOR_INDEX[self.index][type]        
        return  IPMI_SENSOR_CMD.format(index)

    def get_sensor_threshold_command(self,type):
        index=PSU_SENSOR_INDEX[self.index][type]        
        return  IPMI_SENSOR_THRESHOLD_CMD.format(index)

    def get_fru_command(self):
        index=PSU_FRU_INDEX[self.index]        
        return  IPMI_FRU_CMD.format(index)

    """Platform-specific Psu class"""
    def __init__(self, psu_index=0):
        PsuBase.__init__(self)
        self.index = psu_index
        #self._api_helper = APIHelper()   

        #self.__initialize_fan()

        logging.basicConfig(level=logging.DEBUG)

    def __initialize_fan(self):
        from sonic_platform.fan import Fan
        for fan_index in range(0, PSU_NUM_FAN[self.index]):
            fan = Fan(fan_index, 0, is_psu_fan=True, psu_index=self.index)
            self._fan_list.append(fan)

    def get_voltage(self):
        """
        Retrieves current PSU voltage output
        Returns:
            A float number, the output voltage in volts,
            e.g. 12.1
        """
        cmd = self.get_sensor_command("vout")
        st1, log1 = self._syscmd(cmd)
        if st1 != 0:
            return 0
        status=log1.split()[1].strip()
        if(int(status,16) & 1<<5 ==0):
            val=log1.split()[0].strip()
            val2=self.convert_ipmi(val,"vout")
            return round(val2,3)
        else:
            return 0

    def get_current(self):
        """
        Retrieves present electric current supplied by PSU
        Returns:
            A float number, the electric current in amperes, e.g 15.4
        """
        cmd = self.get_sensor_command("iout")
        st1, log1 = self._syscmd(cmd)
        if st1 != 0:
            return 0
        status=log1.split()[1].strip()
        if(int(status,16) & 1<<5 ==0):
            val=log1.split()[0].strip()
            val2=self.convert_ipmi(val,"iout")
            return round(val2,3)
        else:
            return 0

    def get_power(self):
        """
        Retrieves current energy supplied by PSU
        Returns:
            A float number, the power in watts, e.g. 302.6
        """
        cmd = self.get_sensor_command("pout")
        st1, log1 = self._syscmd(cmd)
        if st1 != 0:
            return 0
        status=log1.split()[1].strip()
        if(int(status,16) & 1<<5 ==0):
            val=log1.split()[0].strip()
            val2=self.convert_ipmi(val,"pout")
            return round(val2,3)
        else:
            return 0

    def get_powergood_status(self):
        """
        Retrieves the powergood status of PSU
        Returns:
            A boolean, True if PSU has stablized its output voltages and passed all
            its internal self-tests, False if not.
        """
        return self.get_status()

    def set_status_led(self, color):
        """
        Sets the state of the PSU status LED
        Args:
            color: A string representing the color with which to set the PSU status LED
                   Note: Only support green and off
        Returns:
            bool: True if status LED state is set successfully, False if not
        """

        return False  #Controlled by HW

    def get_status_led(self):
        """
        Gets the state of the PSU status LED
        Returns:
            A string, one of the predefined STATUS_LED_COLOR_* strings above
        """
        status=self.get_status()
        if status is None:
            return  self.STATUS_LED_COLOR_OFF
        
        return {
            1: self.STATUS_LED_COLOR_GREEN,
            0: self.STATUS_LED_COLOR_RED            
        }.get(status, self.STATUS_LED_COLOR_OFF)

    def get_temperature(self):
        """
        Retrieves current temperature reading from PSU
        Returns:
            A float number of current temperature in Celsius up to nearest thousandth
            of one degree Celsius, e.g. 30.125 
        """
        cmd = self.get_sensor_command("ambi_temp")
        st1, log1 = self._syscmd(cmd)
        if st1 != 0:
            return 0
        status=log1.split()[1].strip()
        if(int(status,16) & 1<<5 ==0):
            val=log1.split()[0].strip()
            val2=self.convert_ipmi(val,"ambi_temp")
            return round(val2,3)
        else:
            return 0

    def get_temperature_high_threshold(self):
        """
        Retrieves the high threshold temperature of PSU
        Returns:
            A float number, the high threshold temperature of PSU in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        cmd = self.get_sensor_threshold_command("ambi_temp")
        st1, log1 = self._syscmd(cmd)
        if st1 != 0:
            return 0
        status=log1.split()[0].strip()
        if(int(status,16) & 1<<4 !=0):
            val=log1.split()[5].strip()
            val2=self.convert_ipmi(val,"ambi_temp")
            return round(val2,3)
        else:
            return 0

    def get_voltage_high_threshold(self):
        """
        Retrieves the high threshold PSU voltage output
        Returns:
            A float number, the high threshold output voltage in volts, 
            e.g. 12.1 
        """
        cmd = self.get_sensor_threshold_command("vout")
        st1, log1 = self._syscmd(cmd)
        if st1 != 0:
            return 0
        status=log1.split()[0].strip()
        if(int(status,16) & 1<<4 !=0):
            val=log1.split()[5].strip()
            val2=self.convert_ipmi(val,"vout")
            return round(val2,3)
        else:
            return 0


    def get_voltage_low_threshold(self):
        """
        Retrieves the low threshold PSU voltage output
        Returns:
            A float number, the low threshold output voltage in volts, 
            e.g. 12.1 
        """
        cmd = self.get_sensor_threshold_command("vout")
        st1, log1 = self._syscmd(cmd)
        if st1 != 0:
            return 0
        status=log1.split()[0].strip()
        if(int(status,16) & 1<<1 !=0):
            val=log1.split()[2].strip()
            val2=self.convert_ipmi(val,"vout")
            return round(val2,3)
        else:
            return 0

    def get_name(self):
        """
        Retrieves the name of the device
            Returns:
            string: The name of the device
        """
        return PSU_NAME_LIST[self.index]

    def get_presence(self):
        """
        Retrieves the presence of the PSU
        Returns:
            bool: True if PSU is present, False if not
        """        
        st1, log1 = self._syscmd(IPMI_PSU_PRESENT_GOOD_CMD)
        if st1 != 0:
            return 0
        index=self.index
        ps=log1.split()[index].strip()
        if(int(ps,16) & 1 ==1):
            return 1
        else:
            return 0



    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        st1, log1 = self._syscmd(IPMI_PSU_PRESENT_GOOD_CMD)
        if st1 != 0:            
            return 0
        index=self.index + 2
        ps=log1.split()[index].strip()
        if(int(ps,16) & 1 ==1):
            return 1
        else:
            return 0

    def get_model(self):
        """
        Retrieves the model number (or part number) of the device
        Returns:
            string: Model/part number of device
        """
        cmd = self.get_fru_command()
        st1, log1 = self._syscmd(cmd + "|grep Part")
        if st1 != 0:
            return "N/A"
        model = log1.split(":")[1].strip()       
        if model is None:
            return "N/A"
        return model

    def get_serial(self):
        """
        Retrieves the serial number of the device
        Returns:
            string: Serial number of device
        """
        cmd = self.get_fru_command()
        st1, log1 = self._syscmd(cmd + "|grep Serial")
        if st1 != 0:
            return "N/A"
        serial = log1.split(":")[1].strip()
        if serial is None:
            return "N/A"
        return serial
