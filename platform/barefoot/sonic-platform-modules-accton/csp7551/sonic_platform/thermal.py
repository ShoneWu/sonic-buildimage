#############################################################################
# Edgecore
#
# Thermal contains an implementation of SONiC Platform Base API and
# provides the thermal device status which are available in the platform
#
#############################################################################


import subprocess
import math
try:
    from sonic_platform_base.thermal_base import ThermalBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

IPMI_SENSOR_CMD="ipmitool raw 0x4 0x2d {0}"
IPMI_SENSOR_THRESHOLD_CMD="ipmitool raw 0x4 0x27 {0}"
IPMI_SENSOR_PARAM_CMD="ipmitool raw 0x4 0x21 0x00 0x00 {0} 0x00 24 6"

THERMAL_SENSOR_INDEX={
    0:{"name" : "CPU0_around_temp", "index" : 1},
    1:{"name" : "CPU1_around_temp", "index" : 2},
    2:{"name" : "PCH_around_temp", "index" : 3},
    3:{"name" : "air_inlet1_temp", "index" : 4},
    4:{"name" : "air_inlet2_temp", "index" : 5},
    5:{"name" : "switch_MAC_temp", "index" : 6},
    6:{"name" : "FAN_outlet1_temp", "index" : 7},
    7:{"name" : "FAN_outlet2_temp", "index" : 8},
    8:{"name" : "CPU0_die_temp", "index" : 9},
    9:{"name" : "CPU0_core0_temp", "index" : 10},
    10:{"name" : "CPU0_core1_temp", "index" : 11},
    11:{"name" : "CPU0_core2_temp", "index" : 12},
    12:{"name" : "CPU0_core3_temp", "index" : 13},
    13:{"name" : "CPU0_core4_temp", "index" : 14},
    14:{"name" : "CPU0_core5_temp", "index" : 15},
    15:{"name" : "CPU0_core6_temp", "index" : 16},
    16:{"name" : "CPU0_core7_temp", "index" : 17},
    17:{"name" : "CPU0_DIMM0_temp", "index" : 18},
    18:{"name" : "CPU0_DIMM1_temp", "index" : 19},
    19:{"name" : "CPU0_DIMM2_temp", "index" : 20},
    20:{"name" : "CPU0_DIMM3_temp", "index" : 21},
    21:{"name" : "CPU0_DIMM4_temp", "index" : 22},
    22:{"name" : "CPU0_DIMM5_temp", "index" : 23},
    23:{"name" : "CPU0_DIMM6_temp", "index" : 24},
    24:{"name" : "CPU0_DIMM7_temp", "index" : 25},
    25:{"name" : "CPU1_die_temp", "index" : 26},
    26:{"name" : "CPU1_core0_temp", "index" : 27},
    27:{"name" : "CPU1_core1_temp", "index" : 28},
    28:{"name" : "CPU1_core2_temp", "index" : 29},
    29:{"name" : "CPU1_core3_temp", "index" : 30},
    30:{"name" : "CPU1_core4_temp", "index" : 31},
    31:{"name" : "CPU1_core5_temp", "index" : 32},
    32:{"name" : "CPU1_core6_temp", "index" : 33},
    33:{"name" : "CPU1_core7_temp", "index" : 34},
    34:{"name" : "CPU1_DIMM0_temp", "index" : 35},
    35:{"name" : "CPU1_DIMM1_temp", "index" : 36},
    36:{"name" : "CPU1_DIMM2_temp", "index" : 37},
    37:{"name" : "CPU1_DIMM3_temp", "index" : 38},
    38:{"name" : "CPU1_DIMM4_temp", "index" : 39},
    39:{"name" : "CPU1_DIMM5_temp", "index" : 40},
    40:{"name" : "CPU1_DIMM6_temp", "index" : 41},
    41:{"name" : "CPU1_DIMM7_temp", "index" : 42},
    42:{"name" : "PSU1_ambi_temp", "index" : 43},
    43:{"name" : "PSU1_second_temp", "index" : 44},
    44:{"name" : "PSU2_ambi_temp", "index" : 45},
    45:{"name" : "PSU2_second_temp", "index" : 46},
    46:{"name" : "FPGA1_CF_temp", "index" : 47},
    47:{"name" : "FPGA2_CF_temp", "index" : 48},
    48:{"name" : "FPGA3_CF_temp", "index" : 49},
    49:{"name" : "FPGA4_CF_temp", "index" : 50}

}

class Thermal(ThermalBase):
    """Platform-specific Thermal class"""


    def _syscmd(self,cmd):        
        proc = subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=True,stderr=subprocess.PIPE)
        data, _ = proc.communicate()
        status=proc.returncode
        data=data.decode(errors="ignore")
        return status , data


    def get_param(self):
        command=IPMI_SENSOR_PARAM_CMD.format(THERMAL_SENSOR_INDEX[self.index]["index"])
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

    def convert_ipmi(self,val):
        m,b,r_exp,b_exp=self.get_param()
        offset=b*math.pow(10,b_exp)
        rex=math.pow(10,r_exp)
        val2=(int(val,16)*m+offset)*rex
        return val2

    def get_sensor_command(self):
        index=THERMAL_SENSOR_INDEX[self.index]["index"]        
        return  IPMI_SENSOR_CMD.format(index)

    def get_sensor_threshold_command(self):
        index=THERMAL_SENSOR_INDEX[self.index]["index"]         
        return  IPMI_SENSOR_THRESHOLD_CMD.format(index)

    def __init__(self, thermal_index=0):
        self.index = thermal_index


    def get_temperature(self):
        """
        Retrieves current temperature reading from thermal
        Returns:
            A float number of current temperature in Celsius up to nearest thousandth
            of one degree Celsius, e.g. 30.125
        """
        cmd = self.get_sensor_command()
        st1, log1 = self._syscmd(cmd)
        if st1 != 0:
            return 0
        status=log1.split()[1].strip()
        if(int(status,16) & 1<<5 ==0):
            val=log1.split()[0].strip()
            val2=self.convert_ipmi(val)
            return round(val2,3)
        else:
            return 0


    def get_high_threshold(self):
        """
        Retrieves the high threshold temperature of thermal
        Returns:
            A float number, the high threshold temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        cmd = self.get_sensor_threshold_command()
        st1, log1 = self._syscmd(cmd)
        if st1 != 0:
            return 0
        status=log1.split()[0].strip()
        if(int(status,16) & 1<<3 !=0):
            val=log1.split()[4].strip()
            val2=self.convert_ipmi(val)
            return round(val2,3)
        else:
            return 0

    def get_low_threshold(self):
        """
        Retrieves the low threshold temperature of thermal

        Returns:
            A float number, the low threshold temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        cmd = self.get_sensor_threshold_command()
        st1, log1 = self._syscmd(cmd)
        if st1 != 0:
            return 0
        status=log1.split()[0].strip()
        if(int(status,16) & 1<<0 !=0):
            val=log1.split()[1].strip()
            val2=self.convert_ipmi(val)
            return round(val2,3)
        else:
            return 0

    def get_high_critical_threshold(self):
        """
        Retrieves the high critical threshold temperature of thermal

        Returns:
            A float number, the high critical threshold temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        cmd = self.get_sensor_threshold_command()
        st1, log1 = self._syscmd(cmd)
        if st1 != 0:
            return 0
        status=log1.split()[0].strip()
        if(int(status,16) & 1<<4 !=0):
            val=log1.split()[5].strip()
            val2=self.convert_ipmi(val)
            return round(val2,3)
        else:
            return 0
        
    def get_low_critical_threshold(self):
        """
        Retrieves the low critical threshold temperature of thermal

        Returns:
            A float number, the low critical threshold temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        cmd = self.get_sensor_threshold_command()
        st1, log1 = self._syscmd(cmd)
        if st1 != 0:
            return 0
        status=log1.split()[0].strip()
        if(int(status,16) & 1<<1 !=0):
            val=log1.split()[2].strip()
            val2=self.convert_ipmi(val)
            return round(val2,3)
        else:
            return 0

    def get_name(self):
        """
        Retrieves the name of the thermal device
            Returns:
            string: The name of the thermal device
        """
        return THERMAL_SENSOR_INDEX[self.index]["name"]

    def get_presence(self):
        """
        Retrieves the presence of the Thermal
        Returns:
            bool: True if Thermal is present, False if not
        """
        cmd = self.get_sensor_command()
        st1, log1 = self._syscmd(cmd)
        if st1 != 0:
            return False
        else:
            return True

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """

        cmd = self.get_sensor_command()
        st1, log1 = self._syscmd(cmd)
        if st1 != 0:
            return False
        status=log1.split()[1].strip()
        if(int(status,16) & 1<<5 ==0):
            return True
        else:
            return False
