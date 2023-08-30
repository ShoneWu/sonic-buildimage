# Name: sfp.py, version: 1.0
#
# Description: Module contains the definitions of SFP related APIs
# for Nokia IXR 7250 platform.
#
# Copyright (c) 2023, Nokia
# All rights reserved.
#

try:
    from sonic_platform_base.sonic_xcvr.sfp_optoe_base import SfpOptoeBase
    from sonic_py_common.logger import Logger
    from sonic_py_common import device_info

except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

import subprocess as cmd

smbus_present = 1

try:
    import smbus
except ImportError as e:
    smbus_present = 0

COPPER_TYPE = "COPPER"
SFP_TYPE = "SFP"

# SFP PORT numbers
SFP_PORT_START = 49
SFP_PORT_END = 52

logger = Logger()

class Sfp(SfpOptoeBase):
    """
    Nokia IXR-7215 Platform-specific Sfp refactor class
    """
    instances = []

    # Paths
    PLATFORM_ROOT_PATH = "/usr/share/sonic/device"
    PMON_HWSKU_PATH = "/usr/share/sonic/hwsku"
    HOST_CHK_CMD = "docker > /dev/null 2>&1"

    PLATFORM = "armhf-nokia_ixs7215_52x-r0"
    HWSKU = "Nokia-7215"

    port_to_i2c_mapping = 0

    # def __init__(self, index, sfp_type, stub):
    def __init__(self, index, sfp_type, eeprom_path, port_i2c_map):
        SfpOptoeBase.__init__(self)

        self.index = index
        self.port_num = index
        self.sfp_type = sfp_type
        self.eeprom_path = eeprom_path
        self.port_to_i2c_mapping = port_i2c_map
        self.name = sfp_type + str(index-1)
        self.port_name = sfp_type + str(index)
        self.port_to_eeprom_mapping = {}

        self.port_to_eeprom_mapping[index] = eeprom_path

        self._version_info = device_info.get_sonic_version_info()
        self.lastPresence = False

        logger.log_debug("Sfp __init__ index {} setting name to {} and eeprom_path to {}".format(index, self.name, self.eeprom_path))

        Sfp.instances.append(self)
        
    def get_eeprom_path(self):
        return self.eeprom_path

    def get_presence(self):
        """
        Retrieves the presence
        Returns:
            bool: True if is present, False if not
        """
        if self.sfp_type == COPPER_TYPE:
            return False

        if smbus_present == 0:  # if called from sfputil outside of pmon
            cmdstatus, sfpstatus = cmd.getstatusoutput('sudo i2cget -y 0 0x41 0x3')
            sfpstatus = int(sfpstatus, 16)
        else:
            bus = smbus.SMBus(0)
            DEVICE_ADDRESS = 0x41
            DEVICE_REG = 0x3
            sfpstatus = bus.read_byte_data(DEVICE_ADDRESS, DEVICE_REG)

        pos = [1, 2, 4, 8]
        bit_pos = pos[self.index-SFP_PORT_START]
        sfpstatus = sfpstatus & (bit_pos)

        if sfpstatus == 0:
            return True

        return False

    def get_name(self):
        """
        Retrieves the name of the device
            Returns:
            string: The name of the device
        """
        return self.name

    def get_position_in_parent(self):
        """
        Retrieves 1-based relative physical position in parent device.
        Returns:
            integer: The 1-based relative physical position in parent device or
                     -1 if cannot determine the position
        """
        return -1

    def is_replaceable(self):
        """
        Indicate whether this device is replaceable.
        Returns:
            bool: True if it is replaceable.
        """

        if self.sfp_type == "SFP":
            return True
        else:
            return False

    def _get_error_code(self):
        """
        Get error code of the SFP module

        Returns:
            The error code
        """
        return NotImplementedError

    def get_error_description(self):
        """
        Get error description

        Args:
            error_code: The error code returned by _get_error_code

        Returns:
            The error description
        """
        if not self.get_presence():
            error_description = self.SFP_STATUS_UNPLUGGED
        else:
            error_description = self.SFP_STATUS_OK

        return error_description
        # return NotImplementedError

    def get_reset_status(self):
        """
        Retrieves the reset status of SFP
        Returns:
            A Boolean, True if reset enabled, False if disabled
        """
        if self.sfp_type == COPPER_TYPE:
            return False
        if self.sfp_type == SFP_TYPE:
            return False

    def get_status(self):
        """
        Retrieves the operational status of the device
        """
        reset = self.get_reset_status()

        if reset is True:
            status = False
        else:
            status = True

        return status

    def reset(self):
        """
        Reset SFP.
        Returns:
            A boolean, True if successful, False if not
        """
        # RJ45 and SFP ports not resettable
        return False

    def set_lpmode(self, lpmode):
        """
        Sets the lpmode (low power mode) of SFP
        Args:
            lpmode: A Boolean, True to enable lpmode, False to disable it
            Note  : lpmode can be overridden by set_power_override
        Returns:
            A boolean, True if lpmode is set successfully, False if not
        """
        if self.sfp_type == COPPER_TYPE:
            return False
        if self.sfp_type == SFP_TYPE:
            return False

    def get_lpmode(self):
        """
        Retrieves the lpmode (low power mode) status of this SFP
        Returns:
            A Boolean, True if lpmode is enabled, False if disabled
        """
        if self.sfp_type == COPPER_TYPE:
            return False
        if self.sfp_type == SFP_TYPE:
            return False
