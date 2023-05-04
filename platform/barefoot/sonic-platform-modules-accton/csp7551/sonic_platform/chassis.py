#############################################################################
# Edgecore
#
# Module contains an implementation of SONiC Platform Base API and
# provides the Chassis information which are available in the platform
#
#############################################################################

import os
import sys

try:
    from sonic_platform_base.chassis_base import ChassisBase
    from .helper import APIHelper
    from .event import SfpEvent
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

NUM_FAN_TRAY = 6 #4FAN+2PSU
NUM_FAN = 2
NUM_PSU = 2
NUM_THERMAL = 50
NUM_PORT = 59
NUM_COMPONENT = 8
HOST_REBOOT_CAUSE_PATH = "/host/reboot-cause/"
PMON_REBOOT_CAUSE_PATH = "/usr/share/sonic/platform/api_files/reboot-cause/"
REBOOT_CAUSE_FILE = "reboot-cause.txt"
PREV_REBOOT_CAUSE_FILE = "previous-reboot-cause.txt"
HOST_CHK_CMD = "docker > /dev/null 2>&1"


class Chassis(ChassisBase):
    """Platform-specific Chassis class"""

    def __init__(self):
        ChassisBase.__init__(self)
        self._api_helper = APIHelper()
        self._api_helper = APIHelper()
        self.is_host = self._api_helper.is_host()
        self.config_data = {}
        self.__initialize_fan_drawers()
        self.__initialize_psu()
        self.__initialize_thermals()
        self.__initialize_components()
        self.__initialize_sfp()
        self.__initialize_eeprom()

    def __initialize_sfp(self):
        from sonic_platform.sfp import Sfp
        for index in range(0, NUM_PORT):
            sfp = Sfp(index)
            self._sfp_list.append(sfp)
        self.sfp_module_initialized = True
        
    def __initialize_fan_drawers(self):
        from sonic_platform.fan_drawers import FanDrawer
        for fant_index in range(0, NUM_FAN_TRAY):
            fan_drawer = FanDrawer(fant_index)
            self._fan_drawer_list.append(fan_drawer)

    def __initialize_psu(self):
        from sonic_platform.psu import Psu
        for index in range(0, NUM_PSU):
            psu = Psu(index)
            self._psu_list.append(psu)

    def __initialize_thermals(self):
        from sonic_platform.thermal import Thermal
        for index in range(0, NUM_THERMAL):
            thermal = Thermal(index)
            self._thermal_list.append(thermal)

    def __initialize_eeprom(self):
        from sonic_platform.eeprom import Tlv
        self._eeprom = Tlv()

    def __initialize_components(self):
        from sonic_platform.component import Component
        for index in range(0, NUM_COMPONENT):
            component = Component(index)
            self._component_list.append(component)

    def __initialize_watchdog(self):
        from sonic_platform.watchdog import Watchdog
        self._watchdog = Watchdog()


    def __is_host(self):
        return os.system(HOST_CHK_CMD) == 0

    def __read_txt_file(self, file_path):
        try:
            with open(file_path, 'r') as fd:
                data = fd.read()
                return data.strip()
        except IOError:
            pass
        return None

    def get_name(self):
        """
        Retrieves the name of the device
            Returns:
            string: The name of the device
        """
        return self._api_helper.hwsku

    def get_presence(self):
        """
        Retrieves the presence of the Chassis
        Returns:
            bool: True if Chassis is present, False if not
        """
        return True
    
    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        return True

    def get_base_mac(self):
        """
        Retrieves the base MAC address for the chassis
        Returns:
            A string containing the MAC address in the format
            'XX:XX:XX:XX:XX:XX'
        """
        return self._eeprom.get_mac()

    def get_model(self):
        """
        Retrieves the model number (or part number) of the device
        Returns:
            string: Model/part number of device
        """
        return self._eeprom.get_pn()
        
    def get_serial_number(self):
        """
        Retrieves the hardware serial number for the chassis
        Returns:
            A string containing the hardware serial number for this chassis.
        """
        return self._eeprom.get_serial()

    def get_system_eeprom_info(self):
        """
        Retrieves the full content of system EEPROM information for the chassis
        Returns:
            A dictionary where keys are the type code defined in
            OCP ONIE TlvInfo EEPROM format and values are their corresponding
            values.
        """
        return self._eeprom.get_eeprom()

    def get_reboot_cause(self):
        """
        Retrieves the cause of the previous reboot
        Returns:
            A tuple (string, string) where the first element is a string
            containing the cause of the previous reboot. This string must be
            one of the predefined strings in this class. If the first string
            is "REBOOT_CAUSE_HARDWARE_OTHER", the second string can be used
            to pass a description of the reboot cause.
        """
        reboot_cause_path = (HOST_REBOOT_CAUSE_PATH + REBOOT_CAUSE_FILE)
        sw_reboot_cause = self._api_helper.read_txt_file(reboot_cause_path) or "Unknown"
        return ('REBOOT_CAUSE_NON_HARDWARE', sw_reboot_cause)

    def get_change_event(self, timeout=0):
        # SFP event
        if not self.sfp_module_initialized:
            self.__initialize_sfp()

        status, sfp_event = SfpEvent(self._sfp_list).get_sfp_event(timeout)

        return status, sfp_event

    def get_sfp(self, index):
        """
        Retrieves sfp represented by (1-based) index <index>
        Args:
            index: An integer, the index (1-based) of the sfp to retrieve.
            The index should be the sequence of a physical port in a chassis,
            starting from 1.
            For example, 1 for Ethernet0, 2 for Ethernet4 and so on.
        Returns:
            An object dervied from SfpBase representing the specified sfp
        """
        sfp = None
        if not self.sfp_module_initialized:
            self.__initialize_sfp()

        try:
            # The index will start from 1
            sfp = self._sfp_list[index-1]
        except IndexError:
            sys.stderr.write("SFP index {} out of range (1-{})\n".format(index, len(self._sfp_list)))
        return sfp

    def get_serial(self):
        return self._eeprom.get_serial()
        
    def get_revision(self):
        return self._eeprom.get_hw_revision()