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

try:
    from sonic_platform_base.thermal_base import ThermalBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

SENSOR_NAME = ["CPU Core",
                "LM75-1-48",
                "LM75-2-49",
                "LM75-3-4A",
                "LM75-1-4B",
                "TMP43-INT(MAC)-4C",
                "TMP43-EXT(MAC)-4C",
                "LM75-2-4D",
                "LM75-3-4E",
                "LM75-3-4F",
                "PSU-1 Thermal Sensor 1",
                "PSU-1 Thermal Sensor 2",
                "PSU-1 Thermal Sensor 3",
                "PSU-2 Thermal Sensor 1",
                "PSU-2 Thermal Sensor 2",
                "PSU-2 Thermal Sensor 3"]

SENSOR_CRIT_HIGH_TEMP = [103000, 81000, 83000, 88000, 76000, 84000, 110000, 76000, 66000, 69000, 84000, 84000, 84000, 84000, 84000, 84000]
SENSOR_HIGH_TEMP = [83000, 71000, 73000, 78000, 66000, 64000, 90000, 66000, 56000, 59000, 74000, 74000, 74000, 74000, 74000, 74000]

HWMON_I2C_PATH = ["/sys/bus/i2c/devices/18-0048/hwmon/hwmon*/temp1_input",
                    "/sys/bus/i2c/devices/18-0049/hwmon/hwmon*/temp1_input",
                    "/sys/bus/i2c/devices/18-004a/hwmon/hwmon*/temp1_input",
                    "/sys/bus/i2c/devices/18-004b/hwmon/hwmon*/temp1_input",
                    "/sys/bus/i2c/devices/18-004c/hwmon/hwmon*/temp1_input",
                    "/sys/bus/i2c/devices/18-004c/hwmon/hwmon*/temp2_input",
                    "/sys/bus/i2c/devices/18-004d/hwmon/hwmon*/temp1_input",
                    "/sys/bus/i2c/devices/18-004e/hwmon/hwmon*/temp1_input",
                    "/sys/bus/i2c/devices/18-004f/hwmon/hwmon*/temp1_input",
                    "/sys/bus/i2c/devices/10-0059/psu_temp1_input",
                    "/sys/bus/i2c/devices/10-0059/psu_temp2_input",
                    "/sys/bus/i2c/devices/10-0059/psu_temp3_input",
                    "/sys/bus/i2c/devices/9-0058/psu_temp1_input",
                    "/sys/bus/i2c/devices/9-0058/psu_temp2_input",
                    "/sys/bus/i2c/devices/9-0058/psu_temp3_input"]

CPU_CORE_TEMP_PATH = ["/sys/devices/platform/coretemp.0/hwmon/hwmon*/temp1_input",
                        "/sys/devices/platform/coretemp.0/hwmon/hwmon*/temp2_input",
                        "/sys/devices/platform/coretemp.0/hwmon/hwmon*/temp3_input",
                        "/sys/devices/platform/coretemp.0/hwmon/hwmon*/temp4_input",
                        "/sys/devices/platform/coretemp.0/hwmon/hwmon*/temp5_input",
                        "/sys/devices/platform/coretemp.0/hwmon/hwmon*/temp6_input",
                        "/sys/devices/platform/coretemp.0/hwmon/hwmon*/temp7_input",
                        "/sys/devices/platform/coretemp.0/hwmon/hwmon*/temp8_input",
                        "/sys/devices/platform/coretemp.0/hwmon/hwmon*/temp9_input"]

class Thermal(ThermalBase):
    """Platform-specific Thermal class"""

    THERMAL_NAME_LIST = []

    def __init__(self, thermal_index=0):
        self.index = thermal_index
        # Add thermal name
        for name in SENSOR_NAME:
            self.THERMAL_NAME_LIST.append(name)

        if self.index == 0: # CPU Core
            self.hwmon_path = None
        else:
            self.hwmon_path = HWMON_I2C_PATH[self.index - 1]

        self.ss_key = self.THERMAL_NAME_LIST[self.index]
        self.ss_index = self.index + 1

    def __read_txt_file(self, file_path):
        for filename in glob.glob(file_path):
            try:
                with open(filename, 'r') as fd:
                    data =fd.readline().rstrip()
                    return data
            except IOError as e:
                pass

        return None

    def __get_max_cpu_core_temp(self):
        max_raw_temp = 0
        for path in CPU_CORE_TEMP_PATH:
            raw_temp = self.__read_txt_file(path)
            if raw_temp is not None:
                if float(raw_temp) > float(max_raw_temp):
                    max_raw_temp = raw_temp
        return max_raw_temp

    def get_temperature(self):
        """
        Retrieves current temperature reading from thermal
        Returns:
            A float number of current temperature in Celsius up to nearest thousandth
            of one degree Celsius, e.g. 30.125
        """
        if self.index == 0: # CPU Core
            raw_temp = self.__get_max_cpu_core_temp()
        else:
            raw_temp = self.__read_txt_file(self.hwmon_path)

        if (raw_temp is not None) and (raw_temp.isdigit()):
            return float(raw_temp)/1000
        else:
            return None

    def get_high_critical_threshold(self):
        """
        Retrieves the high critical threshold temperature of thermal
        Returns:
            A float number, the high critical threshold temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        return float(SENSOR_CRIT_HIGH_TEMP[self.index])/1000

    def get_high_threshold(self):
        """
        Retrieves the high threshold temperature of thermal
        Returns:
            A float number, the high threshold temperature of thermal in Celsius
            up to nearest thousandth of one degree Celsius, e.g. 30.125
        """
        return float(SENSOR_HIGH_TEMP[self.index])/1000

    def get_name(self):
        """
        Retrieves the name of the thermal device
            Returns:
            string: The name of the thermal device
        """
        return self.THERMAL_NAME_LIST[self.index]

    def get_presence(self):
        """
        Retrieves the presence of the Thermal
        Returns:
            bool: True if Thermal is present, False if not
        """
        if self.index == 0: # CPU Core
            raw_txt = self.__get_max_cpu_core_temp()
        else:
            raw_txt = self.__read_txt_file(self.hwmon_path)

        if raw_txt is not None:
            return True
        else:
            return False

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        if self.index == 0: # CPU Core
            raw_txt = self.__get_max_cpu_core_temp()
        else:
            raw_txt = self.__read_txt_file(self.hwmon_path)

        if raw_txt is None:
            return False
        else:
            return int(raw_txt) != 0
