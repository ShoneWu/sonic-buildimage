#############################################################################
# Edgecore
#
# Thermal contains an implementation of SONiC Platform Base API and
# provides the thermal device status which are available in the platform
#
#############################################################################

import os
import os.path
import glob
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
    8:{"name" : "PCH_PVNN_temp", "index" : 35},
    9:{"name" : "PCH_P1V05_temp", "index" : 39},
    10:{"name" : "CPU0_VCCIN_temp", "index" : 55},
    11:{"name" : "CPU0_VCCIO_temp", "index" : 62},
    12:{"name" : "VDDQ_AB_temp", "index" : 66},
    13:{"name" : "VPP_AB_temp", "index" : 70},
    14:{"name" : "VDDQ_DE_temp", "index" : 74},
    15:{"name" : "VPP_DE_temp", "index" : 78},
    16:{"name" : "CPU1_VCCIN_temp", "index" : 82},
    17:{"name" : "CPU1_VCCIO_temp", "index" : 89},
    18:{"name" : "VDDQ_GH_temp", "index" : 93},
    19:{"name" : "VPP_GH_temp", "index" : 97},
    20:{"name" : "VDDQ_KL_temp", "index" : 101},
    21:{"name" : "VPP_KL_temp", "index" : 105},
    22:{"name" : "P12V_temp", "index" : 110},
    23:{"name" : "SLOT1_P12V_temp", "index" : 115},
    24:{"name" : "SLOT2_P12V_temp", "index" : 120},
    25:{"name" : "SLOT3_P12V_temp", "index" : 125},
    26:{"name" : "SLOT4_P12V_temp", "index" : 130},
    27:{"name" : "P12V_ATX1_temp", "index" : 135},
    28:{"name" : "P12V_ATX2_temp", "index" : 140},
    29:{"name" : "CPU0_die_temp", "index" : 169},
    30:{"name" : "CPU0_core0_temp", "index" : 170},
    31:{"name" : "CPU0_core1_temp", "index" : 171},
    32:{"name" : "CPU0_core2_temp", "index" : 172},
    33:{"name" : "CPU0_core3_temp", "index" : 173},
    34:{"name" : "CPU0_core4_temp", "index" : 174},
    35:{"name" : "CPU0_core5_temp", "index" : 175},
    36:{"name" : "CPU0_core6_temp", "index" : 176},
    37:{"name" : "CPU0_core7_temp", "index" : 177},
    38:{"name" : "CPU0_DIMM0_temp", "index" : 178},
    39:{"name" : "CPU0_DIMM1_temp", "index" : 179},
    40:{"name" : "CPU0_DIMM2_temp", "index" : 180},
    41:{"name" : "CPU0_DIMM3_temp", "index" : 181},
    42:{"name" : "CPU0_DIMM4_temp", "index" : 182},
    43:{"name" : "CPU0_DIMM5_temp", "index" : 183},
    44:{"name" : "CPU0_DIMM6_temp", "index" : 184},
    45:{"name" : "CPU0_DIMM7_temp", "index" : 185},
    46:{"name" : "CPU1_die_temp", "index" : 186},
    47:{"name" : "CPU1_core0_temp", "index" : 187},
    48:{"name" : "CPU1_core1_temp", "index" : 188},
    49:{"name" : "CPU1_core2_temp", "index" : 189},
    50:{"name" : "CPU1_core3_temp", "index" : 190},
    51:{"name" : "CPU1_core4_temp", "index" : 191},
    52:{"name" : "CPU1_core5_temp", "index" : 192},
    53:{"name" : "CPU1_core6_temp", "index" : 193},
    54:{"name" : "CPU1_core7_temp", "index" : 194},
    55:{"name" : "CPU1_DIMM0_temp", "index" : 195},
    56:{"name" : "CPU1_DIMM1_temp", "index" : 196},
    57:{"name" : "CPU1_DIMM2_temp", "index" : 197},
    58:{"name" : "CPU1_DIMM3_temp", "index" : 198},
    59:{"name" : "CPU1_DIMM4_temp", "index" : 199},
    60:{"name" : "CPU1_DIMM5_temp", "index" : 200},
    61:{"name" : "CPU1_DIMM6_temp", "index" : 201},
    62:{"name" : "CPU1_DIMM7_temp", "index" : 202},
    63:{"name" : "PSU1_ambi_temp", "index" : 207},
    64:{"name" : "PSU1_second_temp", "index" : 208},
    65:{"name" : "PSU2_ambi_temp", "index" : 215},
    66:{"name" : "PSU2_second_temp", "index" : 216}

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
            raise 'error on syscmd'
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
