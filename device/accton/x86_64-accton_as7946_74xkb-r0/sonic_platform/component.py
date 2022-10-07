#############################################################################
# Edgecore
#
# Component contains an implementation of SONiC Platform Base API and
# provides the components firmware management function
#
#############################################################################

import shlex
import subprocess

try:
    from sonic_platform_base.component_base import ComponentBase
    from .helper import APIHelper
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

CPLD_VERSION_PATH = {
    "CPLD1": "/sys/devices/platform/as7946_74xkb_sys/cpu_cpld_ver",
    "CPLD2": "/sys/devices/platform/as7946_74xkb_sys/system_cpld1_ver",
    "CPLD3": "/sys/devices/platform/as7946_74xkb_sys/fan_cpld_ver",
}
BIOS_VERSION_PATH = "/sys/class/dmi/id/bios_version"

COMPONENT_LIST= [
   ("CPLD1", "CPU CPLD"),
   ("CPLD2", "SYSTEM CPLD"),
   ("CPLD3", "FAN CPLD"),
   ("BIOS", "Basic Input/Output System")

]

class Component(ComponentBase):
    """Platform-specific Component class"""

    DEVICE_TYPE = "component"

    def __init__(self, component_index=0):
        self._api_helper=APIHelper()
        ComponentBase.__init__(self)
        self.index = component_index
        self.name = self.get_name()

    def __run_command(self, command):
        # Run bash command and print output to stdout
        try:
            process = subprocess.Popen(
                shlex.split(command), stdout=subprocess.PIPE)
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
            rc = process.poll()
            if rc != 0:
                return False
        except Exception:
            return False
        return True

    def __get_bios_version(self):
        # Retrieves the BIOS firmware version
        try:
            with open(BIOS_VERSION_PATH, 'r') as fd:
                bios_version = fd.read()
                return bios_version.strip()
        except Exception as e:
            return None

    def __get_cpld_version(self):
        # Retrieves the CPLD firmware version
        cpld_version = dict()
        for cpld_name in CPLD_VERSION_PATH:
            try:
                if self.name == cpld_name:
                    with open(CPLD_VERSION_PATH[cpld_name], 'r') as fd:
                        cpld_version = fd.read()
                        return cpld_version.strip()
            except Exception as e:
                return None

        return None

    def get_name(self):
        """
        Retrieves the name of the component
         Returns:
            A string containing the name of the component
        """
        return COMPONENT_LIST[self.index][0]

    def get_description(self):
        """
        Retrieves the description of the component
            Returns:
            A string containing the description of the component
        """
        return COMPONENT_LIST[self.index][1]

    def get_firmware_version(self):
        """
        Retrieves the firmware version of module
        Returns:
            string: The firmware versions of the module
        """
        fw_version = None
        if self.name == "BIOS":
            fw_version = self.__get_bios_version()
        elif "CPLD" in self.name:
            fw_version = self.__get_cpld_version()

        return fw_version

    def install_firmware(self, image_path):
        """
        Install firmware to module
        Args:
            image_path: A string, path to firmware image
        Returns:
            A boolean, True if install successfully, False if not
        """
        raise NotImplementedError
