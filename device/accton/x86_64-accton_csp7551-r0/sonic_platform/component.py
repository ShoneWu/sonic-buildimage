#############################################################################
# Edgecore
#
# Component contains an implementation of SONiC Platform Base API and
# provides the components firmware management function
#
#############################################################################

import shlex
import subprocess
import sys
import os
try:
    import pexpect
except:
    print('no pexpect module')
import re

try:
    from sonic_platform_base.component_base import ComponentBase
    from .helper import APIHelper
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

CPLD_ADDR_MAPPING = {
    "SYS_CPLD": "LPC base addr:0xfc800000",
    "FAN_CPLD": "bmc-curl-path-fan-cpld",
    "PORT_CPLD1": "33-0062",
    "PORT_CPLD2": "34-0064",
}
SYSFS_PATH = "/sys/bus/i2c/devices/"
BIOS_VERSION_PATH = "/sys/class/dmi/id/bios_version"
COMPONENT_LIST= [
   ("SYS_CPLD", "SYS CPLD"),
   ("FAN_CPLD", "FAN CPLD"),
   ("PORT_CPLD1", "PORT CPLD 1"),
   ("PORT_CPLD2", "PORT CPLD 2"),
   ("FPGA", "FPGA"),
   ("BIOS", "Basic Input/Output System"),
   ("BMC", "Baseboard Management Controller"),
   ("REFRESH", "Refresh action.\nThis component is used to trigger component firmware refresh and will cause the system to restart.\nUsers can use below command to trigger refresh action.\n'config platform firmware install chassis component REFRESH fw /etc/accton/fw/csp7551/chassis/refresh'")
]
BMC_USB0_IPv6 = "fe80::ff:fe00:1%usb0"
UPDATE_BIOS_CMD = "flashrom -p internal -l /tmp/layout -i BIOS -w {} --noverify-all"
class Component(ComponentBase):
    """Platform-specific Component class"""

    DEVICE_TYPE = "component"

    def __init__(self, component_index=0):
        self._api_helper=APIHelper()
        ComponentBase.__init__(self)
        self.index = component_index
        self.name = self.get_name()

    def _syscmd_call(self,cmd):
        subprocess.call(cmd, stderr=subprocess.STDOUT, shell=True)

    def _syscmd_output(self,cmd):
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        data, err = proc.communicate()
        status = proc.returncode
        data = data.decode(errors="ignore")
        err = err.decode(errors="ignore")
        return status, data, err

    def _scp_transfile(self,fw_path, bmc_file):
        if not os.path.isfile(fw_path):
            print( "File not exist")
            return False
        self._syscmd_call("ifconfig usb0 up")
        ping_cmd = 'ping6 %s -c 2' %BMC_USB0_IPv6
        st, log, err = self._syscmd_output(ping_cmd)
        if st != 0:
            print ("Cpu ping %s fail, please check the usb0 between cpu and bmc" %BMC_USB0_IPv6)
            return False
        scp_command = 'sudo scp -o StrictHostKeyChecking=no -o ' \
                      'UserKnownHostsFile=/dev/null -r %s root@[fe80::ff:fe00:1%%usb0]:%s' \
                      % (os.path.abspath(fw_path), bmc_file)
        for n in range(0, 3):
            child = pexpect.spawn(scp_command, timeout=120)
            expect_list = [pexpect.EOF, pexpect.TIMEOUT, "'s password:"]
            i = child.expect(expect_list, timeout=120)
            bmc_pwd = "0penBmc"
            if i == 2 and bmc_pwd != None:
                child.sendline(bmc_pwd)
                data = child.read()
                child.close()
                return os.path.isfile(fw_path)
            elif i == 0:
                return True
            else:
                print ("Failed to scp %s to BMC, index %d, retry %d" % (fw_path, i, n))
                continue
        print( "Failed to scp %s to BMC, index %d" % (fw_path, i))
        return False

    def __execute_cmd(self, command):
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # Poll process for new output until finished
        while True:
            nextline = process.stdout.readline()
            if nextline.decode("utf-8") == '' and process.poll() is not None:
                break
            sys.stdout.write(nextline.decode("utf-8"))
            sys.stdout.flush()

        sys.stdout.write(nextline.decode("utf-8"))
        sys.stdout.flush()

        output = process.communicate()[0]
        exitCode = process.returncode
        if (exitCode == 0):
            return exitCode
        else:
            print("\"{}\" return {}!".format(command, exitCode))
            return exitCode

    def __update_refresh_file(self,type):
        refresh_path="/etc/accton/fw/csp7551/chassis/refresh"
        if not os.path.isfile(refresh_path):
            with open(refresh_path,'w') as f:
                f.write(str(type))
        else:
            with open(refresh_path,'r') as f:
                val = f.read(1)
            if val == "\n" or val == "" :
                val = type
            else:
                val = int(val)
                val = val | type
            with open(refresh_path,'w') as f:
                f.write(str(val))

    def __get_cpld_version(self):
        # Retrieves the CPLD firmware version
        cpld_version = dict()
        for cpld_name in CPLD_ADDR_MAPPING:
            if cpld_name == "SYS_CPLD":
                try:
                    result = subprocess.run(['busybox', 'devmem', '0xfc800001', '8'], stdout=subprocess.PIPE)
                    cpld_major_version_raw = result.stdout.decode('ascii').rstrip()
                    result = subprocess.run(['busybox', 'devmem', '0xfc800002', '8'], stdout=subprocess.PIPE)
                    cpld_minor_version_raw = result.stdout.decode('ascii').rstrip()
                    cpld_version[cpld_name] = "{}.{}".format(int(cpld_major_version_raw,16),int(cpld_minor_version_raw,16))
                except Exception as e:
                    print('Get exception when read SYS CPLD version.')
                    cpld_version[cpld_name] = 'None'
            elif cpld_name == "FAN_CPLD":
                try:
                    cmd = "ipmitool raw 0x36 0x12"
                    version = subprocess.check_output(cmd, shell=True).decode('ascii').splitlines()
                    major_ver ="0x" + version[0].split()[0]
                    minor_ver = "0x" + version[0].split()[1]
                    cpld_version[cpld_name] = "{}.{}".format(int(major_ver,16),int(minor_ver,16))
                except Exception as e:
                    print('Get exception when read FAN CPLD version.')
                    cpld_version[cpld_name] = 'None'
            else:
                try:
                    cpld_major_version_path = "{}{}{}".format(SYSFS_PATH, CPLD_ADDR_MAPPING[cpld_name], '/major_version')
                    cpld_major_version_raw = self._api_helper.read_txt_file(cpld_major_version_path)
                    cpld_minor_version_path = "{}{}{}".format(SYSFS_PATH, CPLD_ADDR_MAPPING[cpld_name], '/minor_version')
                    cpld_minor_version_raw = self._api_helper.read_txt_file(cpld_minor_version_path)
                    cpld_version[cpld_name] = "{}.{}".format(int(cpld_major_version_raw,16),int(cpld_minor_version_raw,16))
                except Exception as e:
                    print('Get exception when read PORT CPLD version.')
                    cpld_version[cpld_name] = 'None'

        return cpld_version

    def __get_fpga_version(self):
        try:
            bar0 = subprocess.check_output("lspci -s $(lspci | grep Xilinx | cut -d \" \" -f 1) -v | grep \"Memory at\" | cut -d \" \" -f 3 | cut -c1-6", shell=True).decode('ascii').rstrip()
            bar0_addr = "0x{}{}".format(bar0, '01')
            result = subprocess.run(['busybox', 'devmem', bar0_addr, '8'], stdout=subprocess.PIPE)
            fpga_major_version_raw = result.stdout.decode('ascii').rstrip()
            bar0_addr = "0x{}{}".format(bar0, '00')
            result = subprocess.run(['busybox', 'devmem', bar0_addr, '8'], stdout=subprocess.PIPE)
            fpga_minor_version_raw = result.stdout.decode('ascii').rstrip()
            fpga_version = "{}.{}".format(int(fpga_major_version_raw,16),int(fpga_minor_version_raw,16))
            return fpga_version
        except Exception as e:
            print('Get exception when read FPGA version.')
            return None

    def __get_bios_version(self):
        # Retrieves the BIOS firmware version
        try:
            with open(BIOS_VERSION_PATH, 'r') as fd:
                bios_version = fd.read()
                return bios_version.strip()
        except Exception as e:
            return None

    def __get_bmc_version(self):
        try:
            get_fpga_cpld_bmc_ver_cmd = "ipmitool mc info"
            mc_info = subprocess.check_output(get_fpga_cpld_bmc_ver_cmd, shell=True).decode('ascii').splitlines()
            bmc_mojor_version = "ERROR"
            bmc_minor_version = "ERROR"
            for line in mc_info:
                if "Firmware Revision" in line:
                    bmc_mojor_version = line.split(":")[1].strip()
                if "Aux Firmware Rev Info" in line:
                    bmc_minor_version = mc_info[mc_info.index(line)+1].strip()
            bmc_version = "{}.{:02d}".format(bmc_mojor_version,int(bmc_minor_version,16))
            return bmc_version
        except Exception as e:
            print('Get exception when read BMC version.')
            return None

    def __get_onie_version(self):
        try:
            sys_eeprom_onie_str = subprocess.check_output("decode-syseeprom | grep ONIE", shell=True).decode('ascii').rstrip().split()[-1]
            fpga_version = "{}".format(sys_eeprom_onie_str)
            return fpga_version
        except Exception as e:
            print('Get exception when read ONIE version.')
            return None

    def __cpld_upd(self, image_path):
        retcode = 0xff
        if self.name == "PORT_CPLD1" or self.name == "PORT_CPLD2":
            cpld_upd_cmd = "cpld_jtag.sh port {}".format(image_path)
            retcode = self.__execute_cmd(cpld_upd_cmd)
        elif self.name == "SYS_CPLD":
            cpld_upd_cmd = "cpld_jtag.sh control {}".format(image_path)
            retcode = self.__execute_cmd(cpld_upd_cmd)
        elif self.name == "FAN_CPLD":
            cpld_upd_cmd = "cpld_jtag.sh control {}".format(image_path)
            retcode = self.__execute_cmd(cpld_upd_cmd)

        if retcode == 0:
            if self.name == "PORT_CPLD1" or self.name == "PORT_CPLD2":
                self.__update_refresh_file(0)
            elif self.name == "SYS_CPLD":
                self.__update_refresh_file(2)
            elif self.name == "FAN_CPLD":
                self.__update_refresh_file(1)
            return True
        else:
            return False

    def __fpga_upd(self, image_path):
        retcode = 0xff
        if self.name == "FPGA":
            print("Erasing the SPI flash, this takes about a minute...")
            fpga_upd_cmd = "fpga_upd -E"
            retcode = self.__execute_cmd(fpga_upd_cmd)
            print("Programing the SPI flash...")
            fpga_upd_cmd = "fpga_upd -W -F {}".format(image_path)
            retcode = self.__execute_cmd(fpga_upd_cmd)
        '''
        #TBD, implement after dual images feature is done.
        elif self.name == "FPGA_PRIMARY":
            cpld_upd_cmd = "cpld_jtag.sh port {}".format(image_path)
            retcode = self.__execute_cmd(cpld_upd_cmd)
        elif self.name == "FPGA_GOLDEN":
            cpld_upd_cmd = "cpld_jtag.sh port {}".format(image_path)
            retcode = self.__execute_cmd(cpld_upd_cmd)
        '''
        if retcode == 0:
            self.__update_refresh_file(0)
            return True
        else:
            return False

    def __bmc_upd(self, image_path):
        print("This action only transfer image to bmc.")
        print("Use refresh to apply the bmc image, it may takes few minutes...")
        retcode = self._scp_transfile(image_path,"/run/initramfs/image-bmc")
        if retcode == True:
            self.__update_refresh_file(4)
            return True
        else:
            return False

    def __bios_upd(self, image_path):
        self._syscmd_call("echo '01000000:01FFFFFF BIOS' > /tmp/layout")
        cmd = UPDATE_BIOS_CMD.format(image_path)
        st, log , err= self._syscmd_output(cmd)
        if st != 0 or log is None:
            print('error on upd cmd of bios : status {}, err is {}'.format(st, err))
            return False
        #self._syscmd_call("rm -rf /tmp/layout")
        for line in log.splitlines():
            if "VERIFIED" in line:
                print("Update Scuess")
                self.__update_refresh_file(0)
                return True
            elif "identical" in line:
                print("Content identical , not need update, return True")
                return True
        print("Update Fail")
        return False

    def __refresh(self, image_path):
        if not os.path.isfile(image_path):
            print("No refresh file exits")
            return False
        with open(image_path,'r') as f:
            refresh_type = f.read(1)
        if refresh_type == "\n" or refresh_type == "" :
            print("no content in refresh file, no need to refresh")
            return False
        with open(image_path, 'w') as f:
            f.write("")
        cmd = "sync;sync;sync"
        self._syscmd_call(cmd)
        #mat = re.match(r'.*refresh_(\d)',image_path,re.M|re.I)
        #if mat == None:
        #    print("{} is not valid".format(image_path))
        #    return False
        #refresh_type = mat.group(1)
        cmd = "ipmitool raw 0x36 0x13 {}".format("0x" + refresh_type)
        st, log, err = self._syscmd_output(cmd)
        if st != 0 or log is None:
            print('error on refresh cmd : status {}, err is {}'.format(st, err))
            return False
        return True

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

        if "CPLD" in self.name:
            cpld_version = self.__get_cpld_version()
            fw_version = cpld_version.get(self.name)
        elif self.name == "FPGA":
            fw_version = self.__get_fpga_version()
        elif self.name == "BIOS":
            fw_version = self.__get_bios_version()
        elif self.name == "BMC":
            fw_version = self.__get_bmc_version()
        elif self.name == "ONIE":
            fw_version = self.__get_onie_version()
        elif self.name == "REFRESH":
            fw_version = "1.0"

        return fw_version

    def install_firmware(self, image_path):
        """
        Install firmware to module
        Args:
            image_path: A string, path to firmware image
        Returns:
            A boolean, True if install successfully, False if not
        """
        ret = False
        if "CPLD" in self.name:
            ret = self.__cpld_upd(image_path)
        elif "FPGA" == self.name:
            ret = self.__fpga_upd(image_path)
        elif "BMC" == self.name:
            ret = self.__bmc_upd(image_path)
        elif "BIOS" == self.name:
            ret = self.__bios_upd(image_path)
        elif "REFRESH" == self.name:
            ret = self.__refresh(image_path)
        return ret

    def update_firmware(self, image_path):
        """
        Install firmware to module
        Args:
            image_path: A string, path to firmware image
        Returns:
            A boolean, True if install successfully, False if not
        """
        ret = False
        if "CPLD" in self.name:
            ret = self.__cpld_upd(image_path)
        elif "FPGA" == self.name:
            ret = self.__fpga_upd(image_path)
        elif "BMC" == self.name:
            ret = self.__bmc_upd(image_path)
        elif "BIOS" == self.name:
            ret = self.__bios_upd(image_path)
        elif "REFRESH" == self.name:
            ret = self.__refresh(image_path)

        return ret
