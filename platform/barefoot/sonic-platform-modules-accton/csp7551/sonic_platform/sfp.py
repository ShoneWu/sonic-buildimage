#############################################################################
# Edgecore
#
# Sfp contains an implementation of SONiC Platform Base API and
# provides the sfp device status which are available in the platform
#
#############################################################################

import os
import time
import sys

from ctypes import create_string_buffer

try:
    from sonic_platform_base.sonic_xcvr.sfp_optoe_base import SfpOptoeBase    
    from sonic_platform_base.sonic_sfp.sff8436 import sff8436Dom
    from sonic_platform_base.sonic_sfp.sff8436 import sff8436InterfaceId
    from sonic_platform_base.sonic_sfp.sff8472 import sff8472Dom
    from sonic_platform_base.sonic_sfp.sff8472 import sff8472InterfaceId
    #from sonic_platform_base.sonic_sfp.sff8472 import sffbase
    from sonic_platform_base.sonic_sfp.qsfp_dd import qsfp_dd_InterfaceId
    from sonic_platform_base.sonic_sfp.qsfp_dd import qsfp_dd_Dom
    from sonic_platform_base.sonic_sfp.sfputilhelper import SfpUtilHelper
    from .helper import APIHelper
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

SFP_TYPE = "SFP"
QSFP_TYPE = "QSFP"
QSFP_DD_TYPE = "QSFP_DD"

QSFP_INFO_OFFSET = 128
QSFP_DOM_OFFSET = 0

SFP_INFO_OFFSET = 0
SFP_DOM_OFFSET = 256

XCVR_INTFACE_BULK_OFFSET = 0
XCVR_INTFACE_BULK_WIDTH_QSFP = 20
XCVR_INTFACE_BULK_WIDTH_SFP = 21
XCVR_HW_REV_WIDTH_QSFP = 2
XCVR_HW_REV_WIDTH_SFP = 4
XCVR_CABLE_LENGTH_WIDTH_QSFP = 5
XCVR_VENDOR_NAME_OFFSET = 20
XCVR_VENDOR_NAME_WIDTH = 16
XCVR_VENDOR_OUI_OFFSET = 37
XCVR_VENDOR_OUI_WIDTH = 3
XCVR_VENDOR_PN_OFFSET = 40
XCVR_VENDOR_PN_WIDTH = 16
XCVR_HW_REV_OFFSET = 56
XCVR_HW_REV_WIDTH_OSFP = 2
XCVR_HW_REV_WIDTH_SFP = 4
XCVR_VENDOR_SN_OFFSET = 68
XCVR_VENDOR_SN_WIDTH = 16
XCVR_VENDOR_DATE_OFFSET = 84
XCVR_VENDOR_DATE_WIDTH = 8
XCVR_DOM_CAPABILITY_OFFSET = 92
XCVR_DOM_CAPABILITY_WIDTH = 2
XCVR_TYPE_OFFSET = 0
XCVR_EXT_SPECIFICATION_COMPLIANCE_OFFSET = 64
XCVR_EXT_SPECIFICATION_COMPLIANCE_WIDTH = 1

# Offset for values in QSFP eeprom
QSFP_DOM_REV_OFFSET = 1
QSFP_DOM_REV_WIDTH = 1
QSFP_TEMPE_OFFSET = 22
QSFP_TEMPE_WIDTH = 2
QSFP_VOLT_OFFSET = 26
QSFP_VOLT_WIDTH = 2
QSFP_CHANNL_MON_OFFSET = 34
QSFP_CHANNL_MON_WIDTH = 16
QSFP_CHANNL_MON_WITH_TX_POWER_WIDTH = 24
QSFP_CONTROL_OFFSET = 86
QSFP_CONTROL_WIDTH = 8
QSFP_CHANNL_RX_LOS_STATUS_OFFSET = 3
QSFP_CHANNL_RX_LOS_STATUS_WIDTH = 1
QSFP_CHANNL_TX_FAULT_STATUS_OFFSET = 4
QSFP_CHANNL_TX_FAULT_STATUS_WIDTH = 1
QSFP_POWEROVERRIDE_OFFSET = 93
QSFP_POWEROVERRIDE_WIDTH = 1
QSFP_MODULE_UPPER_PAGE3_START = 384
QSFP_MODULE_THRESHOLD_OFFSET = 128
QSFP_MODULE_THRESHOLD_WIDTH = 24
QSFP_CHANNEL_THRESHOLD_OFFSET = 176
QSFP_CHANNEL_THRESHOLD_WIDTH = 16
QSFP_VERSION_COMPLIANCE_OFFSET = 1
QSFP_VERSION_COMPLIANCE_WIDTH = 2
QSFP_OPTION_VALUE_OFFSET = 192
QSFP_OPTION_VALUE_WIDTH = 4

qsfp_cable_length_tup = ('Length(km)', 'Length OM3(2m)',
                         'Length OM2(m)', 'Length OM1(m)',
                         'Length Cable Assembly(m)')

qsfp_compliance_code_tup = ('10/40G Ethernet Compliance Code', 'SONET Compliance codes',
                            'SAS/SATA compliance codes', 'Gigabit Ethernet Compliant codes',
                            'Fibre Channel link length/Transmitter Technology',
                            'Fibre Channel transmission media', 'Fibre Channel Speed')


# Offset for values in SFP eeprom
SFP_TEMPE_OFFSET = 96
SFP_TEMPE_WIDTH = 2
SFP_VOLT_OFFSET = 98
SFP_VOLT_WIDTH = 2
SFP_CHANNL_MON_OFFSET = 100
SFP_CHANNL_MON_WIDTH = 6
SFP_MODULE_THRESHOLD_OFFSET = 0
SFP_MODULE_THRESHOLD_WIDTH = 40
SFP_CHANNL_THRESHOLD_OFFSET = 112
SFP_CHANNL_THRESHOLD_WIDTH = 2
SFP_STATUS_CONTROL_OFFSET = 110
SFP_STATUS_CONTROL_WIDTH = 1
SFP_TX_DISABLE_HARD_BIT = 7
SFP_TX_DISABLE_SOFT_BIT = 6

sfp_cable_length_tup = ('LengthSMFkm-UnitsOfKm', 'LengthSMF(UnitsOf100m)',
                        'Length50um(UnitsOf10m)', 'Length62.5um(UnitsOfm)',
                        'LengthCable(UnitsOfm)', 'LengthOM3(UnitsOf10m)')

sfp_compliance_code_tup = ('10GEthernetComplianceCode', 'InfinibandComplianceCode',
                           'ESCONComplianceCodes', 'SONETComplianceCodes',
                           'EthernetComplianceCodes', 'FibreChannelLinkLength',
                           'FibreChannelTechnology', 'SFP+CableTechnology',
                           'FibreChannelTransmissionMedia', 'FibreChannelSpeed')

# definitions of the offset and width for values in XCVR_QSFP_DD info eeprom
XCVR_EXT_TYPE_OFFSET_QSFP_DD = 72
XCVR_EXT_TYPE_WIDTH_QSFP_DD = 2
XCVR_CONNECTOR_OFFSET_QSFP_DD = 75
XCVR_CONNECTOR_WIDTH_QSFP_DD = 1
XCVR_CABLE_LENGTH_OFFSET_QSFP_DD = 74
XCVR_CABLE_LENGTH_WIDTH_QSFP_DD = 1
XCVR_HW_REV_OFFSET_QSFP_DD = 36
XCVR_HW_REV_WIDTH_QSFP_DD = 2
XCVR_VENDOR_DATE_OFFSET_QSFP_DD = 54
XCVR_VENDOR_DATE_WIDTH_QSFP_DD = 8
XCVR_DOM_CAPABILITY_OFFSET_QSFP_DD = 2
XCVR_DOM_CAPABILITY_WIDTH_QSFP_DD = 1
XCVR_MEDIA_TYPE_OFFSET_QSFP_DD = 85
XCVR_MEDIA_TYPE_WIDTH_QSFP_DD = 1
XCVR_FIRST_APPLICATION_LIST_OFFSET_QSFP_DD = 86
XCVR_FIRST_APPLICATION_LIST_WIDTH_QSFP_DD = 32
XCVR_SECOND_APPLICATION_LIST_OFFSET_QSFP_DD = 351
XCVR_SECOND_APPLICATION_LIST_WIDTH_QSFP_DD = 28

# definitions of the offset for values in QSFP_DD info eeprom
QSFP_DD_TYPE_OFFSET = 0
QSFP_DD_VENDOR_NAME_OFFSET = 1
QSFP_DD_VENDOR_PN_OFFSET = 20
QSFP_DD_VENDOR_SN_OFFSET = 38
QSFP_DD_VENDOR_OUI_OFFSET = 17

#definitions of the offset and width for values in DOM info eeprom
QSFP_DD_TEMPE_OFFSET = 14
QSFP_DD_TEMPE_WIDTH = 2
QSFP_DD_VOLT_OFFSET = 16
QSFP_DD_VOLT_WIDTH = 2
QSFP_DD_TX_BIAS_OFFSET = 42
QSFP_DD_TX_BIAS_WIDTH = 16
QSFP_DD_RX_POWER_OFFSET = 58
QSFP_DD_RX_POWER_WIDTH = 16
QSFP_DD_TX_POWER_OFFSET = 26
QSFP_DD_TX_POWER_WIDTH = 16
QSFP_DD_CHANNL_MON_OFFSET = 26
QSFP_DD_CHANNL_MON_WIDTH = 48
QSFP_DD_CHANNL_DISABLE_STATUS_OFFSET = 86
QSFP_DD_CHANNL_DISABLE_STATUS_WIDTH = 1
QSFP_DD_CHANNL_RX_LOS_STATUS_OFFSET = 19
QSFP_DD_CHANNL_RX_LOS_STATUS_WIDTH = 1
QSFP_DD_CHANNL_TX_FAULT_STATUS_OFFSET = 7
QSFP_DD_CHANNL_TX_FAULT_STATUS_WIDTH = 1
QSFP_DD_MODULE_THRESHOLD_OFFSET = 0
QSFP_DD_MODULE_THRESHOLD_WIDTH = 72
QSFP_DD_CHANNL_STATUS_OFFSET = 26
QSFP_DD_CHANNL_STATUS_WIDTH = 1

XCVR_TYPE_WIDTH = 1
QSFP_DD_DOM_BULK_DATA_START = 14
QSFP_DD_DOM_BULK_DATA_SIZE = 4

SFP_TYPE_CODE_LIST = [
    '03' # SFP/SFP+/SFP28
]
QSFP_TYPE_CODE_LIST = [
    '0d', # QSFP+ or later
    '11' # QSFP28 or later
]
QSFP_DD_TYPE_CODE_LIST = [
    '18', # QSFP-DD Double Density 8X Pluggable Transceiver
    '1e'
]

QSFP_PORT_START = 1
QSFP_PORT_END = 32
QSFP_DD_PORT_START = 0
QSFP_DD_PORT_END = 0
SFP_PORT_START = 0
SFP_PORT_END = 0
FPGA_PORT_START=33
FPGA_PORT_END=56

class Sfp(SfpOptoeBase):
    """Platform-specific Sfp class"""

    # Port number
    PORT_START = 1
    PORT_END = 32


    # Path to sysfs
    PLATFORM_ROOT_PATH = "/usr/share/sonic/device"
    PMON_HWSKU_PATH = "/usr/share/sonic/hwsku"
    HOST_CHK_CMD = "docker > /dev/null 2>&1"
        
    PLATFORM = "x86_64-accton_csp7551-r0"
    HWSKU = "Accton-CSP7551"

    _port_to_i2c_mapping = {
            1 : 1,
            2 : 2,
            3 : 3,
            4 : 4,
            5 : 5,
            6 : 6,
            7 : 7,
            8 : 8,
            9 : 9,
            10 : 10,
            11 : 11,
            12 : 12,
            13 : 13,
            14 : 14,
            15 : 15,
            16 : 16,
            17 : 17,
            18 : 18,
            19 : 19,
            20 : 20,
            21 : 21,
            22 : 22,
            23 : 23,
            24 : 24,
            25 : 25,
            26 : 26,
            27 : 27,
            28 : 28,
            29 : 29,
            30 : 30,
            31 : 31,
            32 : 32
    }

    def __init__(self, sfp_index=0):
        self._api_helper=APIHelper()
        # Init index
        self.index = sfp_index
        self.port_num = self.index + 1
        self.sfp_type = QSFP_TYPE



        # Init eeprom path
        eeprom_path = '/sys/bus/i2c/devices/{0}-0050/sfp_eeprom'
        self.port_to_eeprom_mapping = {}
        for x in range(self.PORT_START, self.PORT_END + 1):
            self.port_to_eeprom_mapping[x] = eeprom_path.format(self._port_to_i2c_mapping[x])

        self.info_dict_keys = ['type', 'hardware_rev', 'serial', 'manufacturer', 'model', 'connector', 'encoding', 'ext_identifier',
                               'ext_rateselect_compliance', 'cable_type', 'cable_length', 'nominal_bit_rate', 'specification_compliance', 'vendor_date', 'vendor_oui']

        self.dom_dict_keys = ['rx_los', 'tx_fault', 'reset_status', 'power_lpmode', 'tx_disable', 'tx_disable_channel', 'temperature', 'voltage',
                              'rx1power', 'rx2power', 'rx3power', 'rx4power', 'tx1bias', 'tx2bias', 'tx3bias', 'tx4bias', 'tx1power', 'tx2power', 'tx3power', 'tx4power']

        self.threshold_dict_keys = ['temphighalarm', 'temphighwarning', 'templowalarm', 'templowwarning', 'vcchighalarm', 'vcchighwarning', 'vcclowalarm', 'vcclowwarning', 'rxpowerhighalarm', 'rxpowerhighwarning',
                                    'rxpowerlowalarm', 'rxpowerlowwarning', 'txpowerhighalarm', 'txpowerhighwarning', 'txpowerlowalarm', 'txpowerlowwarning', 'txbiashighalarm', 'txbiashighwarning', 'txbiaslowalarm', 'txbiaslowwarning']

        SfpOptoeBase.__init__(self)
        self._detect_sfp_type()

        self._dom_capability_detect()
    def exec_check_output_no_chk_retcode(self, cmd):
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, shell=True)
        outs = p.communicate()
        return outs[0]+outs[1]


    def _convert_string_to_num(self, value_str):
        if "-inf" in value_str:
            return 'N/A'
        elif "Unknown" in value_str:
            return 'N/A'
        elif 'dBm' in value_str:
            t_str = value_str.rstrip('dBm')
            return float(t_str)
        elif 'mA' in value_str:
            t_str = value_str.rstrip('mA')
            return float(t_str)
        elif 'C' in value_str:
            t_str = value_str.rstrip('C')
            return float(t_str)
        elif 'Volts' in value_str:
            t_str = value_str.rstrip('Volts')
            return float(t_str)
        else:
            return 'N/A'

    def __write_txt_file(self, file_path, value):
        try:
            with open(file_path, 'w', buffering=0) as fd:
                fd.write(str(value))
        except Exception:
            return False
        return True

    def __is_host(self):
        return os.system(self.HOST_CHK_CMD) == 0

    def __get_path_to_port_config_file(self):
        platform_path = "/".join([self.PLATFORM_ROOT_PATH, self.PLATFORM])
        hwsku_path = "/".join([platform_path, self.HWSKU]
                              ) if self.__is_host() else self.PMON_HWSKU_PATH
        return "/".join([hwsku_path, "port_config.ini"])

    def __read_eeprom_specific_bytes(self, offset, num_bytes):
        sysfsfile_eeprom = None
        eeprom_raw = []

        for i in range(0, num_bytes):
            eeprom_raw.append("0x00")

        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           return eeprom_raw
        sysfs_sfp_i2c_client_eeprom_path = self.port_to_eeprom_mapping[self.port_num]
        try:
            sysfsfile_eeprom = open(
                sysfs_sfp_i2c_client_eeprom_path, mode="rb", buffering=0)
            sysfsfile_eeprom.seek(offset)
            raw = sysfsfile_eeprom.read(num_bytes)
            if sys.version_info[0] >= 3:
                for n in range(0, num_bytes):
                    eeprom_raw[n] = hex(raw[n])[2:].zfill(2)
            else:
                for n in range(0, num_bytes):
                    eeprom_raw[n] = hex(ord(raw[n]))[2:].zfill(2)
        except Exception:
            #print(sysfs_sfp_i2c_client_eeprom_path+" open failed!" )
            pass
        finally:
            if sysfsfile_eeprom:
                sysfsfile_eeprom.close()

        return eeprom_raw
    def _detect_sfp_type(self):
            eeprom_raw = []
            eeprom_raw = self.__read_eeprom_specific_bytes(XCVR_TYPE_OFFSET, XCVR_TYPE_WIDTH)
            if eeprom_raw[0] == "00":
                eeprom_raw = self.__read_eeprom_specific_bytes(XCVR_TYPE_OFFSET+128, XCVR_TYPE_WIDTH)

            if eeprom_raw:
                if eeprom_raw[0] in SFP_TYPE_CODE_LIST:
                    self.sfp_type = SFP_TYPE
                elif eeprom_raw[0] in QSFP_TYPE_CODE_LIST:
                    self.sfp_type = QSFP_TYPE
                elif eeprom_raw[0] in QSFP_DD_TYPE_CODE_LIST:
                    self.sfp_type = QSFP_DD_TYPE
                else:
                    # we don't regonize this identifier value, treat the xSFP module as the default type
                    if self.port_num in range(SFP_PORT_START, SFP_PORT_START+1):
                        self.sfp_type = SFP_TYPE
                    elif self.port_num in range(QSFP_DD_PORT_START, QSFP_DD_PORT_END+1):
                        self.sfp_type = QSFP_DD_TYPE
                    else:
                        self.sfp_type = QSFP_TYPE



    def _dom_capability_detect(self):
        if not self.get_presence():
            self.dom_supported = False
            self.dom_temp_supported = False
            self.dom_volt_supported = False
            self.dom_rx_power_supported = False
            self.dom_tx_bias_power_supported = False
            self.dom_tx_power_supported = False
            self.calibration = 0
            return

        if  self.sfp_type == SFP_TYPE:
            sfpi_obj = sff8472InterfaceId()
            if sfpi_obj is None:
                return None
            sfp_dom_capability_raw = self.__read_eeprom_specific_bytes(XCVR_DOM_CAPABILITY_OFFSET, XCVR_DOM_CAPABILITY_WIDTH)
            if sfp_dom_capability_raw is not None:
                sfp_dom_capability = int(sfp_dom_capability_raw[0], 16)
                self.dom_supported = (sfp_dom_capability & 0x40 != 0)
                if self.dom_supported:
                    self.dom_temp_supported = True
                    self.dom_volt_supported = True
                    self.dom_rx_power_supported = True
                    self.dom_tx_power_supported = True
                    if sfp_dom_capability & 0x20 != 0:
                        self.calibration = 1
                    elif sfp_dom_capability & 0x10 != 0:
                        self.calibration = 2
                    else:
                        self.calibration = 0
                else:
                    self.dom_temp_supported = False
                    self.dom_volt_supported = False
                    self.dom_rx_power_supported = False
                    self.dom_tx_power_supported = False
                    self.calibration = 0
                self.dom_tx_disable_supported = (int(sfp_dom_capability_raw[1], 16) & 0x40 != 0)

        elif self.sfp_type == QSFP_TYPE:
            self.calibration = 1
            sfpi_obj = sff8436InterfaceId()
            if sfpi_obj is None:
                self.dom_supported = False
            offset = 128

            # QSFP capability byte parse, through this byte can know whether it support tx_power or not.
            # TODO: in the future when decided to migrate to support SFF-8636 instead of SFF-8436,
            # need to add more code for determining the capability and version compliance
            # in SFF-8636 dom capability definitions evolving with the versions.
            qsfp_dom_capability_raw = self.__read_eeprom_specific_bytes((offset + XCVR_DOM_CAPABILITY_OFFSET), XCVR_DOM_CAPABILITY_WIDTH)
            if qsfp_dom_capability_raw is not None:
                qsfp_version_compliance_raw = self.__read_eeprom_specific_bytes(QSFP_VERSION_COMPLIANCE_OFFSET, QSFP_VERSION_COMPLIANCE_WIDTH)
                qsfp_version_compliance = int(qsfp_version_compliance_raw[0], 16)
                dom_capability = sfpi_obj.parse_dom_capability(qsfp_dom_capability_raw, 0)
                if qsfp_version_compliance >= 0x08:
                    self.dom_temp_supported = dom_capability['data']['Temp_support']['value'] == 'On'
                    self.dom_volt_supported = dom_capability['data']['Voltage_support']['value'] == 'On'
                    self.dom_rx_power_supported = dom_capability['data']['Rx_power_support']['value'] == 'On'
                    self.dom_tx_power_supported = dom_capability['data']['Tx_power_support']['value'] == 'On'
                else:
                    self.dom_temp_supported = True
                    self.dom_volt_supported = True
                    self.dom_rx_power_supported = dom_capability['data']['Rx_power_support']['value'] == 'On'
                    self.dom_tx_power_supported = True
                self.dom_supported = True
                self.calibration = 1
                sfpd_obj = sff8436Dom()
                if sfpd_obj is None:
                    return None
                qsfp_option_value_raw = self.__read_eeprom_specific_bytes(QSFP_OPTION_VALUE_OFFSET, QSFP_OPTION_VALUE_WIDTH)
                if qsfp_option_value_raw is not None:
                    optional_capability = sfpd_obj.parse_option_params(qsfp_option_value_raw, 0)
                    self.dom_tx_disable_supported = optional_capability['data']['TxDisable']['value'] == 'On'
                dom_status_indicator = sfpd_obj.parse_dom_status_indicator(qsfp_version_compliance_raw, 1)
                self.qsfp_page3_available = dom_status_indicator['data']['FlatMem']['value'] == 'Off'
            else:
                self.dom_supported = False
                self.dom_temp_supported = False
                self.dom_volt_supported = False
                self.dom_rx_power_supported = False
                self.dom_tx_power_supported = False
                self.calibration = 0
                self.qsfp_page3_available = False

        elif self.sfp_type == QSFP_DD_TYPE:
            sfpi_obj = qsfp_dd_InterfaceId()
            if sfpi_obj is None:
                self.dom_supported = False

            offset = 0
            # two types of QSFP-DD cable types supported: Copper and Optical.
            qsfp_dom_capability_raw = self.__read_eeprom_specific_bytes((offset + XCVR_DOM_CAPABILITY_OFFSET_QSFP_DD), XCVR_DOM_CAPABILITY_WIDTH_QSFP_DD)
            if qsfp_dom_capability_raw is not None:
                self.dom_temp_supported = True
                self.dom_volt_supported = True
                dom_capability = sfpi_obj.parse_dom_capability(qsfp_dom_capability_raw, 0)
                if dom_capability['data']['Flat_MEM']['value'] == 'Off':
                    self.dom_supported = True
                    self.second_application_list = True
                    self.dom_rx_power_supported = True
                    self.dom_tx_power_supported = True
                    self.dom_tx_bias_power_supported = True
                    self.dom_thresholds_supported = True
                    self.dom_rx_tx_power_bias_supported = True
                else:
                    self.dom_supported = False
                    self.second_application_list = False
                    self.dom_rx_power_supported = False
                    self.dom_tx_power_supported = False
                    self.dom_tx_bias_power_supported = False
                    self.dom_thresholds_supported = False
                    self.dom_rx_tx_power_bias_supported = False
            else:
                self.dom_supported = False
                self.dom_temp_supported = False
                self.dom_volt_supported = False
                self.dom_rx_power_supported = False
                self.dom_tx_power_supported = False
                self.dom_tx_bias_power_supported = False
                self.dom_thresholds_supported = False
                self.dom_rx_tx_power_bias_supported = False


        else:
            self.dom_supported = False
            self.dom_temp_supported = False
            self.dom_volt_supported = False
            self.dom_rx_power_supported = False
            self.dom_tx_power_supported = False

    def get_transceiver_info(self):
        """
        Retrieves transceiver info of this SFP
        Returns:
            A dict which contains following keys/values :
        ========================================================================
        keys                       |Value Format   |Information
        ---------------------------|---------------|----------------------------
        type                       |1*255VCHAR     |type of SFP
        hardware_rev               |1*255VCHAR     |hardware version of SFP
        serial                     |1*255VCHAR     |serial number of the SFP
        manufacturer               |1*255VCHAR     |SFP vendor name
        model                      |1*255VCHAR     |SFP model name
        connector                  |1*255VCHAR     |connector information
        encoding                   |1*255VCHAR     |encoding information
        ext_identifier             |1*255VCHAR     |extend identifier
        ext_rateselect_compliance  |1*255VCHAR     |extended rateSelect compliance
        cable_length               |INT            |cable length in m
        nominal_bit_rate           |INT            |nominal bit rate by 100Mbs
        specification_compliance   |1*255VCHAR     |specification compliance
        vendor_date                |1*255VCHAR     |vendor date
        vendor_oui                 |1*255VCHAR     |vendor OUI
        ========================================================================
        """
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           transceiver_info_dict = dict.fromkeys(self.info_dict_keys, 'N/A')
           return transceiver_info_dict
        # check present status
        if self.port_num in range(QSFP_PORT_START, QSFP_PORT_END+1) or self.port_num in range(QSFP_DD_PORT_START, QSFP_DD_PORT_END+1):
            self._detect_sfp_type()
            self._dom_capability_detect()
            eeprom_raw = []
            eeprom_raw = self.__read_eeprom_specific_bytes(XCVR_TYPE_OFFSET, XCVR_TYPE_WIDTH)

            if eeprom_raw:
                if '1e' in eeprom_raw[0]:
                    self.sfp_type = QSFP_TYPE
            #self.sfp_type = QSFP_TYPE
            #print("get_transceiver_info port{}".format(self.sfp_type))
            if self.sfp_type == QSFP_DD_TYPE:
                offset = 128
                #time.sleep(2)
                sfpi_obj = qsfp_dd_InterfaceId()
                transceiver_info_dict = dict.fromkeys(self.info_dict_keys, 'N/A')
                if not self.get_presence() or sfpi_obj is None:
                    print("Error: sfp_object open failed")
                    return transceiver_info_dict
                #print("get_transceiver_info1 port{}".format(self.sfp_type))



                sfp_type_raw = self.__read_eeprom_specific_bytes((offset + QSFP_DD_TYPE_OFFSET), XCVR_TYPE_WIDTH)
                if sfp_type_raw is not None:
                    sfp_type_data = sfpi_obj.parse_sfp_type(sfp_type_raw, 0)
                else:
                    return None

                sfp_vendor_name_raw = self.__read_eeprom_specific_bytes((offset + QSFP_DD_VENDOR_NAME_OFFSET), XCVR_VENDOR_NAME_WIDTH)
                if sfp_vendor_name_raw is not None:
                    sfp_vendor_name_data = sfpi_obj.parse_vendor_name(sfp_vendor_name_raw, 0)
                else:
                    return None

                sfp_vendor_pn_raw = self.__read_eeprom_specific_bytes((offset + QSFP_DD_VENDOR_PN_OFFSET), XCVR_VENDOR_PN_WIDTH)
                if sfp_vendor_pn_raw is not None:
                    sfp_vendor_pn_data = sfpi_obj.parse_vendor_pn(sfp_vendor_pn_raw, 0)
                else:
                    return None

                sfp_vendor_rev_raw = self.__read_eeprom_specific_bytes((offset + XCVR_HW_REV_OFFSET_QSFP_DD), XCVR_HW_REV_WIDTH_QSFP_DD)
                if sfp_vendor_rev_raw is not None:
                    sfp_vendor_rev_data = sfpi_obj.parse_vendor_rev(sfp_vendor_rev_raw, 0)
                else:
                    return None

                sfp_vendor_sn_raw = self.__read_eeprom_specific_bytes((offset + QSFP_DD_VENDOR_SN_OFFSET), XCVR_VENDOR_SN_WIDTH)
                if sfp_vendor_sn_raw is not None:
                    sfp_vendor_sn_data = sfpi_obj.parse_vendor_sn(sfp_vendor_sn_raw, 0)
                else:
                    return None

                sfp_vendor_oui_raw = self.__read_eeprom_specific_bytes((offset + QSFP_DD_VENDOR_OUI_OFFSET), XCVR_VENDOR_OUI_WIDTH)
                if sfp_vendor_oui_raw is not None:
                    sfp_vendor_oui_data = sfpi_obj.parse_vendor_oui(sfp_vendor_oui_raw, 0)
                else:
                    return None

                sfp_vendor_date_raw = self.__read_eeprom_specific_bytes((offset + XCVR_VENDOR_DATE_OFFSET_QSFP_DD), XCVR_VENDOR_DATE_WIDTH_QSFP_DD)
                if sfp_vendor_date_raw is not None:
                    sfp_vendor_date_data = sfpi_obj.parse_vendor_date(sfp_vendor_date_raw, 0)
                else:
                    return None

                sfp_connector_raw = self.__read_eeprom_specific_bytes((offset + XCVR_CONNECTOR_OFFSET_QSFP_DD), XCVR_CONNECTOR_WIDTH_QSFP_DD)
                if sfp_connector_raw is not None:

                    #print("sfp_connector_raw "+sfp_connector_raw[0]+ " "+str(self.port_num))
                    if sfp_connector_raw[0] == '0x00':
                        sfp_connector_raw[0] = '00'
                    sfp_connector_data = sfpi_obj.parse_connector(sfp_connector_raw, 0)
                else:
                    return None

                sfp_ext_identifier_raw = self.__read_eeprom_specific_bytes((offset + XCVR_EXT_TYPE_OFFSET_QSFP_DD), XCVR_EXT_TYPE_WIDTH_QSFP_DD)
                if sfp_ext_identifier_raw is not None:
                    sfp_ext_identifier_data = sfpi_obj.parse_ext_iden(sfp_ext_identifier_raw, 0)
                else:
                    return None

                sfp_cable_len_raw = self.__read_eeprom_specific_bytes((offset + XCVR_CABLE_LENGTH_OFFSET_QSFP_DD), XCVR_CABLE_LENGTH_WIDTH_QSFP_DD)
                if sfp_cable_len_raw is not None:
                    sfp_cable_len_data = sfpi_obj.parse_cable_len(sfp_cable_len_raw, 0)
                else:
                    return None

                sfp_media_type_raw = self.__read_eeprom_specific_bytes(XCVR_MEDIA_TYPE_OFFSET_QSFP_DD, XCVR_MEDIA_TYPE_WIDTH_QSFP_DD)
                if sfp_media_type_raw is not None:
                    if sfp_media_type_raw[0] == '0x00':
                        sfp_media_type_raw[0] = '00'
                    sfp_media_type_dict = sfpi_obj.parse_media_type(sfp_media_type_raw, 0)
                    if sfp_media_type_dict is None:
                        return None

                    host_media_list = ""
                    sfp_application_type_first_list = self.__read_eeprom_specific_bytes((XCVR_FIRST_APPLICATION_LIST_OFFSET_QSFP_DD), XCVR_FIRST_APPLICATION_LIST_WIDTH_QSFP_DD)
                    if self.second_application_list:
                        possible_application_count = 15
                        sfp_application_type_second_list = self.__read_eeprom_specific_bytes((XCVR_SECOND_APPLICATION_LIST_OFFSET_QSFP_DD), XCVR_SECOND_APPLICATION_LIST_WIDTH_QSFP_DD)
                        if sfp_application_type_first_list is not None and sfp_application_type_second_list is not None:
                            sfp_application_type_list = sfp_application_type_first_list + sfp_application_type_second_list
                        else:
                            return None
                    else:
                        possible_application_count = 8
                        if sfp_application_type_first_list is not None:
                            sfp_application_type_list = sfp_application_type_first_list
                        else:
                            return None

                    for i in range(0, possible_application_count):
                        if sfp_application_type_list[i * 4] == 'ff':
                            break
                        host_electrical, media_interface = sfpi_obj.parse_application(sfp_media_type_dict, sfp_application_type_list[i * 4], sfp_application_type_list[i * 4 + 1])
                        host_media_list = host_media_list + host_electrical + ' - ' + media_interface + '\n\t\t\t\t   '
                else:
                    return None

                transceiver_info_dict['type'] = str(sfp_type_data['data']['type']['value'])
                transceiver_info_dict['manufacturer'] = str(sfp_vendor_name_data['data']['Vendor Name']['value'])
                transceiver_info_dict['model'] = str(sfp_vendor_pn_data['data']['Vendor PN']['value'])
                transceiver_info_dict['hardware_rev'] = str(sfp_vendor_rev_data['data']['Vendor Rev']['value'])
                transceiver_info_dict['serial'] = str(sfp_vendor_sn_data['data']['Vendor SN']['value'])
                transceiver_info_dict['vendor_oui'] = str(sfp_vendor_oui_data['data']['Vendor OUI']['value'])
                transceiver_info_dict['vendor_date'] = str(sfp_vendor_date_data['data']['VendorDataCode(YYYY-MM-DD Lot)']['value'])

                transceiver_info_dict['connector'] = str(sfp_connector_data['data']['Connector']['value'])
                transceiver_info_dict['encoding'] = "Not supported for CMIS cables"
                transceiver_info_dict['ext_identifier'] = str(sfp_ext_identifier_data['data']['Extended Identifier']['value'])
                transceiver_info_dict['ext_rateselect_compliance'] = "Not supported for CMIS cables"
                transceiver_info_dict['specification_compliance'] = "Not supported for CMIS cables"
                transceiver_info_dict['cable_type'] = "Length Cable Assembly(m)"
                transceiver_info_dict['cable_length'] = str(sfp_cable_len_data['data']['Length Cable Assembly(m)']['value'])
                transceiver_info_dict['nominal_bit_rate'] = "Not supported for CMIS cables"
                transceiver_info_dict['application_advertisement'] = host_media_list

                return transceiver_info_dict
            else:
                sfpi_obj = sff8436InterfaceId() #QSFP
                transceiver_info_dict = dict.fromkeys(self.info_dict_keys, 'N/A')
                if not self.get_presence() or not sfpi_obj:
                    return transceiver_info_dict

                offset = QSFP_INFO_OFFSET
                sfp_interface_bulk_raw = self.__read_eeprom_specific_bytes(
                    (offset + XCVR_INTFACE_BULK_OFFSET), XCVR_INTFACE_BULK_WIDTH_QSFP)

                sfp_interface_bulk_data = sfpi_obj.parse_sfp_info_bulk(
                    sfp_interface_bulk_raw, 0)

                sfp_vendor_name_raw = self.__read_eeprom_specific_bytes(
                    (offset + XCVR_VENDOR_NAME_OFFSET), XCVR_VENDOR_NAME_WIDTH)
                sfp_vendor_name_data = sfpi_obj.parse_vendor_name(
                    sfp_vendor_name_raw, 0)

                sfp_vendor_pn_raw = self.__read_eeprom_specific_bytes(
                    (offset + XCVR_VENDOR_PN_OFFSET), XCVR_VENDOR_PN_WIDTH)
                sfp_vendor_pn_data = sfpi_obj.parse_vendor_pn(
                    sfp_vendor_pn_raw, 0)


                sfp_vendor_rev_raw = self.__read_eeprom_specific_bytes(
                    (offset + XCVR_HW_REV_OFFSET), XCVR_HW_REV_WIDTH_QSFP)

                sfp_vendor_rev_data = sfpi_obj.parse_vendor_rev(
                    sfp_vendor_rev_raw, 0)

                sfp_vendor_sn_raw = self.__read_eeprom_specific_bytes(
                    (offset + XCVR_VENDOR_SN_OFFSET), XCVR_VENDOR_SN_WIDTH)
                sfp_vendor_sn_data = sfpi_obj.parse_vendor_sn(
                    sfp_vendor_sn_raw, 0)

                sfp_vendor_oui_raw = self.__read_eeprom_specific_bytes(
                    (offset + XCVR_VENDOR_OUI_OFFSET), XCVR_VENDOR_OUI_WIDTH)
                if sfp_vendor_oui_raw is not None:
                    sfp_vendor_oui_data = sfpi_obj.parse_vendor_oui(
                        sfp_vendor_oui_raw, 0)

                sfp_vendor_date_raw = self.__read_eeprom_specific_bytes(
                    (offset + XCVR_VENDOR_DATE_OFFSET), XCVR_VENDOR_DATE_WIDTH)
                sfp_vendor_date_data = sfpi_obj.parse_vendor_date(
                    sfp_vendor_date_raw, 0)


                compliance_code_dict = dict()

                if sfp_interface_bulk_data:
                    transceiver_info_dict['type'] = sfp_interface_bulk_data['data']['type']['value']
                    transceiver_info_dict['connector'] = sfp_interface_bulk_data['data']['Connector']['value']
                    transceiver_info_dict['encoding'] = sfp_interface_bulk_data['data']['EncodingCodes']['value']
                    transceiver_info_dict['ext_identifier'] = sfp_interface_bulk_data['data']['Extended Identifier']['value']
                    transceiver_info_dict['ext_rateselect_compliance'] = sfp_interface_bulk_data['data']['RateIdentifier']['value']
                    transceiver_info_dict['type_abbrv_name'] = sfp_interface_bulk_data['data']['type_abbrv_name']['value']

                transceiver_info_dict['manufacturer'] = sfp_vendor_name_data[
                    'data']['Vendor Name']['value'] if sfp_vendor_name_data else 'N/A'
                transceiver_info_dict['model'] = sfp_vendor_pn_data['data']['Vendor PN']['value'] if sfp_vendor_pn_data else 'N/A'
                transceiver_info_dict['hardware_rev'] = sfp_vendor_rev_data['data']['Vendor Rev']['value'] if sfp_vendor_rev_data else 'N/A'
                transceiver_info_dict['serial'] = sfp_vendor_sn_data['data']['Vendor SN']['value'] if sfp_vendor_sn_data else 'N/A'
                transceiver_info_dict['vendor_oui'] = sfp_vendor_oui_data['data']['Vendor OUI']['value'] if sfp_vendor_oui_data else 'N/A'
                transceiver_info_dict['vendor_date'] = sfp_vendor_date_data[
                    'data']['VendorDataCode(YYYY-MM-DD Lot)']['value'] if sfp_vendor_date_data else 'N/A'
                transceiver_info_dict['cable_type'] = "Unknown"
                transceiver_info_dict['cable_length'] = "Unknown"

                for key in qsfp_cable_length_tup:
                    if key in sfp_interface_bulk_data['data']:
                        transceiver_info_dict['cable_type'] = key
                        transceiver_info_dict['cable_length'] = str(
                            sfp_interface_bulk_data['data'][key]['value'])

                for key in qsfp_compliance_code_tup:
                    if key in sfp_interface_bulk_data['data']['Specification compliance']['value']:
                        compliance_code_dict[key] = sfp_interface_bulk_data['data']['Specification compliance']['value'][key]['value']

                sfp_ext_specification_compliance_raw = self.__read_eeprom_specific_bytes(offset + XCVR_EXT_SPECIFICATION_COMPLIANCE_OFFSET, XCVR_EXT_SPECIFICATION_COMPLIANCE_WIDTH)
                if sfp_ext_specification_compliance_raw is not None:
                    sfp_ext_specification_compliance_data = sfpi_obj.parse_ext_specification_compliance(sfp_ext_specification_compliance_raw[0 : 1], 0)
                    if sfp_ext_specification_compliance_data['data']['Extended Specification compliance']['value'] != "Unspecified":
                        compliance_code_dict['Extended Specification compliance'] = sfp_ext_specification_compliance_data['data']['Extended Specification compliance']['value']

                transceiver_info_dict['specification_compliance'] = str(
                    compliance_code_dict)
                transceiver_info_dict['nominal_bit_rate'] = str(
                    sfp_interface_bulk_data['data']['Nominal Bit Rate(100Mbs)']['value'])


                return transceiver_info_dict

        elif self.port_num == SFP_PORT_START :
            sfpi_obj = sff8472InterfaceId() #SFP
            transceiver_info_dict = dict.fromkeys(self.info_dict_keys, 'N/A')
            if not self.get_presence() or not sfpi_obj:
                return transceiver_info_dict

            offset = SFP_INFO_OFFSET
            sfp_interface_bulk_raw = self.__read_eeprom_specific_bytes(
                (offset + XCVR_INTFACE_BULK_OFFSET), XCVR_INTFACE_BULK_WIDTH_SFP)

            sfp_interface_bulk_data = sfpi_obj.parse_sfp_info_bulk(
                sfp_interface_bulk_raw, 0)

            sfp_vendor_name_raw = self.__read_eeprom_specific_bytes(
                (offset + XCVR_VENDOR_NAME_OFFSET), XCVR_VENDOR_NAME_WIDTH)
            sfp_vendor_name_data = sfpi_obj.parse_vendor_name(
                sfp_vendor_name_raw, 0)

            sfp_vendor_pn_raw = self.__read_eeprom_specific_bytes(
                (offset + XCVR_VENDOR_PN_OFFSET), XCVR_VENDOR_PN_WIDTH)
            sfp_vendor_pn_data = sfpi_obj.parse_vendor_pn(
                sfp_vendor_pn_raw, 0)


            sfp_vendor_rev_raw = self.__read_eeprom_specific_bytes(
                (offset + XCVR_HW_REV_OFFSET), XCVR_HW_REV_WIDTH_SFP)

            sfp_vendor_rev_data = sfpi_obj.parse_vendor_rev(
                sfp_vendor_rev_raw, 0)

            sfp_vendor_sn_raw = self.__read_eeprom_specific_bytes(
                (offset + XCVR_VENDOR_SN_OFFSET), XCVR_VENDOR_SN_WIDTH)
            sfp_vendor_sn_data = sfpi_obj.parse_vendor_sn(
                sfp_vendor_sn_raw, 0)

            sfp_vendor_oui_raw = self.__read_eeprom_specific_bytes(
                (offset + XCVR_VENDOR_OUI_OFFSET), XCVR_VENDOR_OUI_WIDTH)
            if sfp_vendor_oui_raw is not None:
                sfp_vendor_oui_data = sfpi_obj.parse_vendor_oui(
                    sfp_vendor_oui_raw, 0)

            sfp_vendor_date_raw = self.__read_eeprom_specific_bytes(
                (offset + XCVR_VENDOR_DATE_OFFSET), XCVR_VENDOR_DATE_WIDTH)
            sfp_vendor_date_data = sfpi_obj.parse_vendor_date(
                sfp_vendor_date_raw, 0)


            compliance_code_dict = dict()

            if sfp_interface_bulk_data:
                transceiver_info_dict['type'] = sfp_interface_bulk_data['data']['type']['value']
                transceiver_info_dict['connector'] = sfp_interface_bulk_data['data']['Connector']['value']
                transceiver_info_dict['encoding'] = sfp_interface_bulk_data['data']['EncodingCodes']['value']
                transceiver_info_dict['ext_identifier'] = sfp_interface_bulk_data['data']['Extended Identifier']['value']
                transceiver_info_dict['ext_rateselect_compliance'] = sfp_interface_bulk_data['data']['RateIdentifier']['value']
                transceiver_info_dict['type_abbrv_name'] = sfp_interface_bulk_data['data']['type_abbrv_name']['value']

            transceiver_info_dict['manufacturer'] = sfp_vendor_name_data[
                'data']['Vendor Name']['value'] if sfp_vendor_name_data else 'N/A'
            transceiver_info_dict['model'] = sfp_vendor_pn_data['data']['Vendor PN']['value'] if sfp_vendor_pn_data else 'N/A'
            transceiver_info_dict['hardware_rev'] = sfp_vendor_rev_data['data']['Vendor Rev']['value'] if sfp_vendor_rev_data else 'N/A'
            transceiver_info_dict['serial'] = sfp_vendor_sn_data['data']['Vendor SN']['value'] if sfp_vendor_sn_data else 'N/A'
            transceiver_info_dict['vendor_oui'] = sfp_vendor_oui_data['data']['Vendor OUI']['value'] if sfp_vendor_oui_data else 'N/A'
            transceiver_info_dict['vendor_date'] = sfp_vendor_date_data[
                'data']['VendorDataCode(YYYY-MM-DD Lot)']['value'] if sfp_vendor_date_data else 'N/A'
            transceiver_info_dict['cable_type'] = "Unknown"
            transceiver_info_dict['cable_length'] = "Unknown"

            for key in sfp_cable_length_tup:
                if key in sfp_interface_bulk_data['data']:
                    transceiver_info_dict['cable_type'] = key
                    transceiver_info_dict['cable_length'] = str(
                        sfp_interface_bulk_data['data'][key]['value'])

            for key in sfp_compliance_code_tup:
                if key in sfp_interface_bulk_data['data']['Specification compliance']['value']:
                    compliance_code_dict[key] = sfp_interface_bulk_data['data']['Specification compliance']['value'][key]['value']

            transceiver_info_dict['specification_compliance'] = str(
                compliance_code_dict)
            transceiver_info_dict['nominal_bit_rate'] = str(
                sfp_interface_bulk_data['data']['NominalSignallingRate(UnitsOf100Mbd)']['value'])


            return transceiver_info_dict


    def get_transceiver_bulk_status(self):
        """
        Retrieves transceiver bulk status of this SFP
        Returns:
            A dict which contains following keys/values :
        ========================================================================
        keys                       |Value Format   |Information
        ---------------------------|---------------|----------------------------
        rx_los                     |BOOLEAN        |RX loss-of-signal status, True if has RX los, False if not.
        tx_fault                   |BOOLEAN        |TX fault status, True if has TX fault, False if not.
        reset_status               |BOOLEAN        |reset status, True if SFP in reset, False if not.
        lp_mode                    |BOOLEAN        |low power mode status, True in lp mode, False if not.
        tx_disable                 |BOOLEAN        |TX disable status, True TX disabled, False if not.
        tx_disabled_channel        |HEX            |disabled TX channels in hex, bits 0 to 3 represent channel 0
                                   |               |to channel 3.
        temperature                |INT            |module temperature in Celsius
        voltage                    |INT            |supply voltage in mV
        tx<n>bias                  |INT            |TX Bias Current in mA, n is the channel number,
                                   |               |for example, tx2bias stands for tx bias of channel 2.
        rx<n>power                 |INT            |received optical power in mW, n is the channel number,
                                   |               |for example, rx2power stands for rx power of channel 2.
        tx<n>power                 |INT            |TX output power in mW, n is the channel number,
                                   |               |for example, tx2power stands for tx power of channel 2.
        ========================================================================
        """
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           transceiver_dom_info_dict = dict.fromkeys(self.dom_dict_keys, 'N/A')
           return transceiver_dom_info_dict
        # check present status
        if self.port_num in range(SFP_PORT_START, SFP_PORT_END+1):
            self._detect_sfp_type()
            self._dom_capability_detect()
            transceiver_dom_info_dict = dict.fromkeys(self.dom_dict_keys, 'N/A')
            if not self.dom_supported:
                return transceiver_dom_info_dict
            sfpd_obj = sff8472Dom()
            if not self.get_presence() or not sfpd_obj:
                return transceiver_dom_info_dict

            eeprom_ifraw = self.__read_eeprom_specific_bytes(0, SFP_DOM_OFFSET)
            sfpi_obj = sff8472InterfaceId(eeprom_ifraw)
            cal_type = sfpi_obj.get_calibration_type()
            sfpd_obj._calibration_type = cal_type

            offset = SFP_DOM_OFFSET

            dom_temperature_raw = self.__read_eeprom_specific_bytes(
                (offset + SFP_TEMPE_OFFSET), SFP_TEMPE_WIDTH)

            if dom_temperature_raw is not None:
                dom_temperature_data = sfpd_obj.parse_temperature(
                    dom_temperature_raw, 0)
                transceiver_dom_info_dict['temperature'] = dom_temperature_data['data']['Temperature']['value']

            dom_voltage_raw = self.__read_eeprom_specific_bytes(
                (offset + SFP_VOLT_OFFSET), SFP_VOLT_WIDTH)
            if dom_voltage_raw is not None:
                dom_voltage_data = sfpd_obj.parse_voltage(dom_voltage_raw, 0)
                transceiver_dom_info_dict['voltage'] = dom_voltage_data['data']['Vcc']['value']

            dom_channel_monitor_raw = self.__read_eeprom_specific_bytes(
                (offset + SFP_CHANNL_MON_OFFSET), SFP_CHANNL_MON_WIDTH)
            if dom_channel_monitor_raw is not None:
                dom_voltage_data = sfpd_obj.parse_channel_monitor_params(
                    dom_channel_monitor_raw, 0)
                transceiver_dom_info_dict['tx1power'] = dom_voltage_data['data']['TXPower']['value']
                transceiver_dom_info_dict['rx1power'] = dom_voltage_data['data']['RXPower']['value']
                transceiver_dom_info_dict['tx1bias'] = dom_voltage_data['data']['TXBias']['value']
        else:
            #QSFP case
            self._detect_sfp_type()
            self._dom_capability_detect()
            if self.sfp_type == QSFP_DD_TYPE:
                offset = 0
                sfpd_obj = qsfp_dd_Dom()
                transceiver_dom_info_dict = dict.fromkeys(self.dom_dict_keys, 'N/A')
                if not self.get_presence() or sfpd_obj is None:
                    return transceiver_dom_info_dict
                #print("get_transceiver_bulk_status port{}".format(self.port_num))


                dom_data_raw = self.__read_eeprom_specific_bytes((offset + QSFP_DD_DOM_BULK_DATA_START), QSFP_DD_DOM_BULK_DATA_SIZE)
                if dom_data_raw is None:
                    return transceiver_dom_info_dict

                if self.dom_temp_supported:
                    start = QSFP_DD_TEMPE_OFFSET - QSFP_DD_DOM_BULK_DATA_START
                    end = start + QSFP_DD_TEMPE_WIDTH
                    dom_temperature_data = sfpd_obj.parse_temperature(dom_data_raw[start : end], 0)
                    temp = self._convert_string_to_num(dom_temperature_data['data']['Temperature']['value'])
                    if temp is not None:
                        transceiver_dom_info_dict['temperature'] = temp

                if self.dom_volt_supported:
                    start = QSFP_DD_VOLT_OFFSET - QSFP_DD_DOM_BULK_DATA_START
                    end = start + QSFP_DD_VOLT_WIDTH
                    dom_voltage_data = sfpd_obj.parse_voltage(dom_data_raw[start : end], 0)
                    volt = self._convert_string_to_num(dom_voltage_data['data']['Vcc']['value'])
                    if volt is not None:
                        transceiver_dom_info_dict['voltage'] = volt

                if self.dom_rx_tx_power_bias_supported:
                    # page 11h
                    offset = 512
                    dom_data_raw = self.__read_eeprom_specific_bytes(offset + QSFP_DD_CHANNL_MON_OFFSET, QSFP_DD_CHANNL_MON_WIDTH)
                    if dom_data_raw is None:
                        return transceiver_dom_info_dict
                    dom_channel_monitor_data = sfpd_obj.parse_channel_monitor_params(dom_data_raw, 0)

                    if self.dom_tx_power_supported:
                        transceiver_dom_info_dict['tx1power'] = str(self._convert_string_to_num(dom_channel_monitor_data['data']['TX1Power']['value']))
                        transceiver_dom_info_dict['tx2power'] = str(self._convert_string_to_num(dom_channel_monitor_data['data']['TX2Power']['value']))
                        transceiver_dom_info_dict['tx3power'] = str(self._convert_string_to_num(dom_channel_monitor_data['data']['TX3Power']['value']))
                        transceiver_dom_info_dict['tx4power'] = str(self._convert_string_to_num(dom_channel_monitor_data['data']['TX4Power']['value']))
                        transceiver_dom_info_dict['tx5power'] = str(self._convert_string_to_num(dom_channel_monitor_data['data']['TX5Power']['value']))
                        transceiver_dom_info_dict['tx6power'] = str(self._convert_string_to_num(dom_channel_monitor_data['data']['TX6Power']['value']))
                        transceiver_dom_info_dict['tx7power'] = str(self._convert_string_to_num(dom_channel_monitor_data['data']['TX7Power']['value']))
                        transceiver_dom_info_dict['tx8power'] = str(self._convert_string_to_num(dom_channel_monitor_data['data']['TX8Power']['value']))

                    if self.dom_rx_power_supported:
                        transceiver_dom_info_dict['rx1power'] = str(self._convert_string_to_num(dom_channel_monitor_data['data']['RX1Power']['value']))
                        transceiver_dom_info_dict['rx2power'] = str(self._convert_string_to_num(dom_channel_monitor_data['data']['RX2Power']['value']))
                        transceiver_dom_info_dict['rx3power'] = str(self._convert_string_to_num(dom_channel_monitor_data['data']['RX3Power']['value']))
                        transceiver_dom_info_dict['rx4power'] = str(self._convert_string_to_num(dom_channel_monitor_data['data']['RX4Power']['value']))
                        transceiver_dom_info_dict['rx5power'] = str(self._convert_string_to_num(dom_channel_monitor_data['data']['RX5Power']['value']))
                        transceiver_dom_info_dict['rx6power'] = str(self._convert_string_to_num(dom_channel_monitor_data['data']['RX6Power']['value']))
                        transceiver_dom_info_dict['rx7power'] = str(self._convert_string_to_num(dom_channel_monitor_data['data']['RX7Power']['value']))
                        transceiver_dom_info_dict['rx8power'] = str(self._convert_string_to_num(dom_channel_monitor_data['data']['RX8Power']['value']))

                    if self.dom_tx_bias_power_supported:
                        transceiver_dom_info_dict['tx1bias'] = str(dom_channel_monitor_data['data']['TX1Bias']['value'])
                        transceiver_dom_info_dict['tx2bias'] = str(dom_channel_monitor_data['data']['TX2Bias']['value'])
                        transceiver_dom_info_dict['tx3bias'] = str(dom_channel_monitor_data['data']['TX3Bias']['value'])
                        transceiver_dom_info_dict['tx4bias'] = str(dom_channel_monitor_data['data']['TX4Bias']['value'])
                        transceiver_dom_info_dict['tx5bias'] = str(dom_channel_monitor_data['data']['TX5Bias']['value'])
                        transceiver_dom_info_dict['tx6bias'] = str(dom_channel_monitor_data['data']['TX6Bias']['value'])
                        transceiver_dom_info_dict['tx7bias'] = str(dom_channel_monitor_data['data']['TX7Bias']['value'])
                        transceiver_dom_info_dict['tx8bias'] = str(dom_channel_monitor_data['data']['TX8Bias']['value'])

                return transceiver_dom_info_dict
            else:
                sfpd_obj = sff8436Dom()
                sfpi_obj = sff8436InterfaceId()
                transceiver_dom_info_dict = dict.fromkeys(self.dom_dict_keys, 'N/A')

                if not self.get_presence() or not sfpi_obj or not sfpd_obj:
                    return transceiver_dom_info_dict


                offset = QSFP_DOM_OFFSET
                offset_xcvr = QSFP_INFO_OFFSET
                self._detect_sfp_type()
                self._dom_capability_detect()
                # QSFP capability byte parse, through this byte can know whether it support tx_power or not.
                # TODO: in the future when decided to migrate to support SFF-8636 instead of SFF-8436,
                # need to add more code for determining the capability and version compliance
                # in SFF-8636 dom capability definitions evolving with the versions.
                qsfp_dom_capability_raw = self.__read_eeprom_specific_bytes(
                    (offset_xcvr + XCVR_DOM_CAPABILITY_OFFSET), XCVR_DOM_CAPABILITY_WIDTH)
                if qsfp_dom_capability_raw is not None:
                    qspf_dom_capability_data = sfpi_obj.parse_dom_capability(
                        qsfp_dom_capability_raw, 0)
                else:
                    return None
                if self.dom_temp_supported:
                    dom_temperature_raw = self.__read_eeprom_specific_bytes(
                        (offset + QSFP_TEMPE_OFFSET), QSFP_TEMPE_WIDTH)
                    if dom_temperature_raw is not None:
                        dom_temperature_data = sfpd_obj.parse_temperature(
                            dom_temperature_raw, 0)
                        transceiver_dom_info_dict['temperature'] = dom_temperature_data['data']['Temperature']['value']

                if self.dom_volt_supported:
                    dom_voltage_raw = self.__read_eeprom_specific_bytes(
                        (offset + QSFP_VOLT_OFFSET), QSFP_VOLT_WIDTH)
                    if dom_voltage_raw is not None:
                        dom_voltage_data = sfpd_obj.parse_voltage(dom_voltage_raw, 0)
                        transceiver_dom_info_dict['voltage'] = dom_voltage_data['data']['Vcc']['value']

                qsfp_dom_rev_raw = self.__read_eeprom_specific_bytes(
                    (offset + QSFP_DOM_REV_OFFSET), QSFP_DOM_REV_WIDTH)
                if qsfp_dom_rev_raw is not None:
                    qsfp_dom_rev_data = sfpd_obj.parse_sfp_dom_rev(qsfp_dom_rev_raw, 0)
                    qsfp_dom_rev = qsfp_dom_rev_data['data']['dom_rev']['value']

                # The tx_power monitoring is only available on QSFP which compliant with SFF-8636
                # and claimed that it support tx_power with one indicator bit.
                dom_channel_monitor_data = {}
                dom_channel_monitor_raw = None
                qsfp_tx_power_support = qspf_dom_capability_data['data']['Tx_power_support']['value']
                if (qsfp_dom_rev[0:8] != 'SFF-8636' or (qsfp_dom_rev[0:8] == 'SFF-8636' and qsfp_tx_power_support != 'on')):
                    dom_channel_monitor_raw = self.__read_eeprom_specific_bytes(
                        (offset + QSFP_CHANNL_MON_OFFSET), QSFP_CHANNL_MON_WIDTH)
                    if dom_channel_monitor_raw is not None:
                        dom_channel_monitor_data = sfpd_obj.parse_channel_monitor_params(
                            dom_channel_monitor_raw, 0)

                else:
                    dom_channel_monitor_raw = self.__read_eeprom_specific_bytes(
                        (offset + QSFP_CHANNL_MON_OFFSET), QSFP_CHANNL_MON_WITH_TX_POWER_WIDTH)
                    if dom_channel_monitor_raw is not None:
                        dom_channel_monitor_data = sfpd_obj.parse_channel_monitor_params_with_tx_power(
                            dom_channel_monitor_raw, 0)
                        transceiver_dom_info_dict['tx1power'] = dom_channel_monitor_data['data']['TX1Power']['value']
                        transceiver_dom_info_dict['tx2power'] = dom_channel_monitor_data['data']['TX2Power']['value']
                        transceiver_dom_info_dict['tx3power'] = dom_channel_monitor_data['data']['TX3Power']['value']
                        transceiver_dom_info_dict['tx4power'] = dom_channel_monitor_data['data']['TX4Power']['value']

                if dom_channel_monitor_raw:
                    transceiver_dom_info_dict['rx1power'] = dom_channel_monitor_data['data']['RX1Power']['value']
                    transceiver_dom_info_dict['rx2power'] = dom_channel_monitor_data['data']['RX2Power']['value']
                    transceiver_dom_info_dict['rx3power'] = dom_channel_monitor_data['data']['RX3Power']['value']
                    transceiver_dom_info_dict['rx4power'] = dom_channel_monitor_data['data']['RX4Power']['value']
                    transceiver_dom_info_dict['tx1bias'] = dom_channel_monitor_data['data']['TX1Bias']['value']
                    transceiver_dom_info_dict['tx2bias'] = dom_channel_monitor_data['data']['TX2Bias']['value']
                    transceiver_dom_info_dict['tx3bias'] = dom_channel_monitor_data['data']['TX3Bias']['value']
                    transceiver_dom_info_dict['tx4bias'] = dom_channel_monitor_data['data']['TX4Bias']['value']

        #End of else

        for key in transceiver_dom_info_dict:
            transceiver_dom_info_dict[key] = self._convert_string_to_num(
                transceiver_dom_info_dict[key])

        transceiver_dom_info_dict['rx_los'] = self.get_rx_los()
        transceiver_dom_info_dict['tx_fault'] = self.get_tx_fault()
        transceiver_dom_info_dict['reset_status'] = self.get_reset_status()
        transceiver_dom_info_dict['lp_mode'] = self.get_lpmode()

        return transceiver_dom_info_dict

    def get_transceiver_threshold_info(self):
        """
        Retrieves transceiver threshold info of this SFP
        Returns:
            A dict which contains following keys/values :
        ========================================================================
        keys                       |Value Format   |Information
        ---------------------------|---------------|----------------------------
        temphighalarm              |FLOAT          |High Alarm Threshold value of temperature in Celsius.
        templowalarm               |FLOAT          |Low Alarm Threshold value of temperature in Celsius.
        temphighwarning            |FLOAT          |High Warning Threshold value of temperature in Celsius.
        templowwarning             |FLOAT          |Low Warning Threshold value of temperature in Celsius.
        vcchighalarm               |FLOAT          |High Alarm Threshold value of supply voltage in mV.
        vcclowalarm                |FLOAT          |Low Alarm Threshold value of supply voltage in mV.
        vcchighwarning             |FLOAT          |High Warning Threshold value of supply voltage in mV.
        vcclowwarning              |FLOAT          |Low Warning Threshold value of supply voltage in mV.
        rxpowerhighalarm           |FLOAT          |High Alarm Threshold value of received power in dBm.
        rxpowerlowalarm            |FLOAT          |Low Alarm Threshold value of received power in dBm.
        rxpowerhighwarning         |FLOAT          |High Warning Threshold value of received power in dBm.
        rxpowerlowwarning          |FLOAT          |Low Warning Threshold value of received power in dBm.
        txpowerhighalarm           |FLOAT          |High Alarm Threshold value of transmit power in dBm.
        txpowerlowalarm            |FLOAT          |Low Alarm Threshold value of transmit power in dBm.
        txpowerhighwarning         |FLOAT          |High Warning Threshold value of transmit power in dBm.
        txpowerlowwarning          |FLOAT          |Low Warning Threshold value of transmit power in dBm.
        txbiashighalarm            |FLOAT          |High Alarm Threshold value of tx Bias Current in mA.
        txbiaslowalarm             |FLOAT          |Low Alarm Threshold value of tx Bias Current in mA.
        txbiashighwarning          |FLOAT          |High Warning Threshold value of tx Bias Current in mA.
        txbiaslowwarning           |FLOAT          |Low Warning Threshold value of tx Bias Current in mA.
        ========================================================================
        """
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           transceiver_dom_threshold_info_dict = dict.fromkeys(self.threshold_dict_keys, 'N/A')
           return transceiver_dom_threshold_info_dict
        # check present status
        if self.port_num in range(SFP_PORT_START, SFP_PORT_END+1):
            self._detect_sfp_type()
            self._dom_capability_detect()
            transceiver_dom_threshold_info_dict = dict.fromkeys(
                self.threshold_dict_keys, 'N/A')
            if not self.dom_supported:
                return transceiver_dom_threshold_info_dict

            sfpd_obj = sff8472Dom()

            if not self.get_presence() and not sfpd_obj:
                return transceiver_dom_threshold_info_dict

            eeprom_ifraw = self.__read_eeprom_specific_bytes(0, SFP_DOM_OFFSET)
            sfpi_obj = sff8472InterfaceId(eeprom_ifraw)
            cal_type = sfpi_obj.get_calibration_type()
            sfpd_obj._calibration_type = cal_type

            offset = SFP_DOM_OFFSET

            dom_module_threshold_raw = self.__read_eeprom_specific_bytes(
                (offset + SFP_MODULE_THRESHOLD_OFFSET), SFP_MODULE_THRESHOLD_WIDTH)
            if dom_module_threshold_raw is not None:
                dom_module_threshold_data = sfpd_obj.parse_alarm_warning_threshold(
                    dom_module_threshold_raw, 0)

                transceiver_dom_threshold_info_dict['temphighalarm'] = dom_module_threshold_data['data']['TempHighAlarm']['value']
                transceiver_dom_threshold_info_dict['templowalarm'] = dom_module_threshold_data['data']['TempLowAlarm']['value']
                transceiver_dom_threshold_info_dict['temphighwarning'] = dom_module_threshold_data['data']['TempHighWarning']['value']
                transceiver_dom_threshold_info_dict['templowwarning'] = dom_module_threshold_data['data']['TempLowWarning']['value']
                transceiver_dom_threshold_info_dict['vcchighalarm'] = dom_module_threshold_data['data']['VoltageHighAlarm']['value']
                transceiver_dom_threshold_info_dict['vcclowalarm'] = dom_module_threshold_data['data']['VoltageLowAlarm']['value']
                transceiver_dom_threshold_info_dict['vcchighwarning'] = dom_module_threshold_data[
                    'data']['VoltageHighWarning']['value']
                transceiver_dom_threshold_info_dict['vcclowwarning'] = dom_module_threshold_data['data']['VoltageLowWarning']['value']
                transceiver_dom_threshold_info_dict['txbiashighalarm'] = dom_module_threshold_data['data']['BiasHighAlarm']['value']
                transceiver_dom_threshold_info_dict['txbiaslowalarm'] = dom_module_threshold_data['data']['BiasLowAlarm']['value']
                transceiver_dom_threshold_info_dict['txbiashighwarning'] = dom_module_threshold_data['data']['BiasHighWarning']['value']
                transceiver_dom_threshold_info_dict['txbiaslowwarning'] = dom_module_threshold_data['data']['BiasLowWarning']['value']
                transceiver_dom_threshold_info_dict['txpowerhighalarm'] = dom_module_threshold_data['data']['TXPowerHighAlarm']['value']
                transceiver_dom_threshold_info_dict['txpowerlowalarm'] = dom_module_threshold_data['data']['TXPowerLowAlarm']['value']
                transceiver_dom_threshold_info_dict['txpowerhighwarning'] = dom_module_threshold_data['data']['TXPowerHighWarning']['value']
                transceiver_dom_threshold_info_dict['txpowerlowwarning'] = dom_module_threshold_data['data']['TXPowerLowWarning']['value']
                transceiver_dom_threshold_info_dict['rxpowerhighalarm'] = dom_module_threshold_data['data']['RXPowerHighAlarm']['value']
                transceiver_dom_threshold_info_dict['rxpowerlowalarm'] = dom_module_threshold_data['data']['RXPowerLowAlarm']['value']
                transceiver_dom_threshold_info_dict['rxpowerhighwarning'] = dom_module_threshold_data['data']['RXPowerHighWarning']['value']
                transceiver_dom_threshold_info_dict['rxpowerlowwarning'] = dom_module_threshold_data['data']['RXPowerLowWarning']['value']

            for key in transceiver_dom_threshold_info_dict:
                transceiver_dom_threshold_info_dict[key] = self._convert_string_to_num(
                    transceiver_dom_threshold_info_dict[key])

            return transceiver_dom_threshold_info_dict

        else:
            self._detect_sfp_type()
            self._dom_capability_detect()

            if self.sfp_type == QSFP_DD_TYPE:
                transceiver_dom_threshold_dict = dict.fromkeys(self.threshold_dict_keys, 'N/A')
                if not self.dom_supported:
                    return transceiver_dom_threshold_dict

                if not self.dom_thresholds_supported:
                    return transceiver_dom_threshold_dict
                sfpd_obj = qsfp_dd_Dom()
                if not self.get_presence() or not sfpd_obj:
                    return transceiver_dom_threshold_dict
                #print("get_transceiver_threshold_info port{}".format(self.port_num))
                self._detect_sfp_type()
                self._dom_capability_detect()



                # page 02
                offset = 384
                dom_module_threshold_raw = self.__read_eeprom_specific_bytes((offset + QSFP_DD_MODULE_THRESHOLD_OFFSET), QSFP_DD_MODULE_THRESHOLD_WIDTH)

                if dom_module_threshold_raw is None:
                    return transceiver_dom_threshold_dict

                dom_module_threshold_data = sfpd_obj.parse_module_threshold_values(dom_module_threshold_raw, 0)

                # Threshold Data
                transceiver_dom_threshold_dict['temphighalarm'] = dom_module_threshold_data['data']['TempHighAlarm']['value']
                transceiver_dom_threshold_dict['temphighwarning'] = dom_module_threshold_data['data']['TempHighWarning']['value']
                transceiver_dom_threshold_dict['templowalarm'] = dom_module_threshold_data['data']['TempLowAlarm']['value']
                transceiver_dom_threshold_dict['templowwarning'] = dom_module_threshold_data['data']['TempLowWarning']['value']
                transceiver_dom_threshold_dict['vcchighalarm'] = dom_module_threshold_data['data']['VccHighAlarm']['value']
                transceiver_dom_threshold_dict['vcchighwarning'] = dom_module_threshold_data['data']['VccHighWarning']['value']
                transceiver_dom_threshold_dict['vcclowalarm'] = dom_module_threshold_data['data']['VccLowAlarm']['value']
                transceiver_dom_threshold_dict['vcclowwarning'] = dom_module_threshold_data['data']['VccLowWarning']['value']
                transceiver_dom_threshold_dict['rxpowerhighalarm'] = dom_module_threshold_data['data']['RxPowerHighAlarm']['value']
                transceiver_dom_threshold_dict['rxpowerhighwarning'] = dom_module_threshold_data['data']['RxPowerHighWarning']['value']
                transceiver_dom_threshold_dict['rxpowerlowalarm'] = dom_module_threshold_data['data']['RxPowerLowAlarm']['value']
                transceiver_dom_threshold_dict['rxpowerlowwarning'] = dom_module_threshold_data['data']['RxPowerLowWarning']['value']
                transceiver_dom_threshold_dict['txbiashighalarm'] = dom_module_threshold_data['data']['TxBiasHighAlarm']['value']
                transceiver_dom_threshold_dict['txbiashighwarning'] = dom_module_threshold_data['data']['TxBiasHighWarning']['value']
                transceiver_dom_threshold_dict['txbiaslowalarm'] = dom_module_threshold_data['data']['TxBiasLowAlarm']['value']
                transceiver_dom_threshold_dict['txbiaslowwarning'] = dom_module_threshold_data['data']['TxBiasLowWarning']['value']
                transceiver_dom_threshold_dict['txpowerhighalarm'] = dom_module_threshold_data['data']['TxPowerHighAlarm']['value']
                transceiver_dom_threshold_dict['txpowerhighwarning'] = dom_module_threshold_data['data']['TxPowerHighWarning']['value']
                transceiver_dom_threshold_dict['txpowerlowalarm'] = dom_module_threshold_data['data']['TxPowerLowAlarm']['value']
                transceiver_dom_threshold_dict['txpowerlowwarning'] = dom_module_threshold_data['data']['TxPowerLowWarning']['value']

                return transceiver_dom_threshold_dict
            else:

                sfpd_obj = sff8436Dom()
                transceiver_dom_threshold_dict = dict.fromkeys(self.threshold_dict_keys, 'N/A')

                if not self.get_presence() or not sfpd_obj:
                    return transceiver_dom_threshold_dict
                if not self.dom_supported or not self.qsfp_page3_available:
                    return transceiver_dom_threshold_dict

                offset = QSFP_MODULE_UPPER_PAGE3_START



                dom_thres_raw = self.__read_eeprom_specific_bytes(
                    offset+QSFP_MODULE_THRESHOLD_OFFSET, QSFP_MODULE_THRESHOLD_WIDTH)

                if dom_thres_raw:
                    module_threshold_values = sfpd_obj.parse_module_threshold_values(
                        dom_thres_raw, 0)
                    module_threshold_data = module_threshold_values.get('data')
                    if module_threshold_data:
                        transceiver_dom_threshold_dict['temphighalarm'] = module_threshold_data['TempHighAlarm']['value']
                        transceiver_dom_threshold_dict['templowalarm'] = module_threshold_data['TempLowAlarm']['value']
                        transceiver_dom_threshold_dict['temphighwarning'] = module_threshold_data['TempHighWarning']['value']
                        transceiver_dom_threshold_dict['templowwarning'] = module_threshold_data['TempLowWarning']['value']
                        transceiver_dom_threshold_dict['vcchighalarm'] = module_threshold_data['VccHighAlarm']['value']
                        transceiver_dom_threshold_dict['vcclowalarm'] = module_threshold_data['VccLowAlarm']['value']
                        transceiver_dom_threshold_dict['vcchighwarning'] = module_threshold_data['VccHighWarning']['value']
                        transceiver_dom_threshold_dict['vcclowwarning'] = module_threshold_data['VccLowWarning']['value']

                dom_thres_raw = self.__read_eeprom_specific_bytes(
                    offset+QSFP_CHANNEL_THRESHOLD_OFFSET, QSFP_CHANNEL_THRESHOLD_WIDTH) if self.get_presence() and sfpd_obj else None
                channel_threshold_values = sfpd_obj.parse_channel_threshold_values(
                    dom_thres_raw, 0)
                channel_threshold_data = channel_threshold_values.get('data')
                if channel_threshold_data:
                    transceiver_dom_threshold_dict['rxpowerhighalarm'] = channel_threshold_data['RxPowerHighAlarm']['value']
                    transceiver_dom_threshold_dict['rxpowerlowalarm'] = channel_threshold_data['RxPowerLowAlarm']['value']
                    transceiver_dom_threshold_dict['rxpowerhighwarning'] = channel_threshold_data['RxPowerHighWarning']['value']
                    transceiver_dom_threshold_dict['rxpowerlowwarning'] = channel_threshold_data['RxPowerLowWarning']['value']
                    transceiver_dom_threshold_dict['txpowerhighalarm'] = "0.0dBm"
                    transceiver_dom_threshold_dict['txpowerlowalarm'] = "0.0dBm"
                    transceiver_dom_threshold_dict['txpowerhighwarning'] = "0.0dBm"
                    transceiver_dom_threshold_dict['txpowerlowwarning'] = "0.0dBm"
                    transceiver_dom_threshold_dict['txbiashighalarm'] = channel_threshold_data['TxBiasHighAlarm']['value']
                    transceiver_dom_threshold_dict['txbiaslowalarm'] = channel_threshold_data['TxBiasLowAlarm']['value']
                    transceiver_dom_threshold_dict['txbiashighwarning'] = channel_threshold_data['TxBiasHighWarning']['value']
                    transceiver_dom_threshold_dict['txbiaslowwarning'] = channel_threshold_data['TxBiasLowWarning']['value']

                for key in transceiver_dom_threshold_dict:
                    transceiver_dom_threshold_dict[key] = self._convert_string_to_num(
                        transceiver_dom_threshold_dict[key])

                return transceiver_dom_threshold_dict

    def get_reset_status(self):
        """
        Retrieves the reset status of SFP
        Returns:
            A Boolean, True if reset enabled, False if disabled
        """
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           return False
        if self.port_num > 0 and self.port_num < 17:
            cpld_path="/sys/bus/i2c/devices/33-0062"
        elif self.port_num >16 and self.port_num < 33:
            cpld_path="/sys/bus/i2c/devices/34-0064"

        reset_path="{}{}{}".format(cpld_path , "module_reset_" , str(self.port_num))
        val = self._api_helper.read_txt_file(reset_path)
        
        if val is not None:
            return int(val, 10) == 1
        else:        
            return False

    def get_rx_los(self):
        """
        Retrieves the RX LOS (lost-of-signal) status of SFP
        Returns:
            A Boolean, True if SFP has RX LOS, False if not.
            Note : RX LOS status is latched until a call to get_rx_los or a reset.
        """
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           return False
        path = "/sys/bus/i2c/devices/{}-0050/sfp_rx_los"
        port_ps = path.format(self._port_to_i2c_mapping[self.port_num])
        try:
            reg_file = open(port_ps)
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        reg_value = reg_file.readline().rstrip()
        if reg_value == '1':
            return True

        return False


    def get_tx_fault(self):
        """
        Retrieves the TX fault status of SFP
        Returns:
            A Boolean, True if SFP has TX fault, False if not
            Note : TX fault status is lached until a call to get_tx_fault or a reset.
        """
        #tx_fault = False
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           return False
        path = "/sys/bus/i2c/devices/{}-0050/sfp_tx_fault"
        port_ps = path.format(self._port_to_i2c_mapping[self.port_num])
        try:
            reg_file = open(port_ps)
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        reg_value = reg_file.readline().rstrip()
        if reg_value == '1':
            return True

        return False

    def get_tx_disable(self):
        """
        Retrieves the tx_disable status of this SFP
        Returns:
            A Boolean, True if tx_disable is enabled, False if disabled
        """
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           return False
        path = "/sys/bus/i2c/devices/{}-0050/sfp_tx_disable"
        port_ps = path.format(self._port_to_i2c_mapping[self.port_num])
        try:
            reg_file = open(port_ps)
        except IOError as e:
            print("Error: unable to open file: %s" % str(e))
            return False

        reg_value = reg_file.readline().rstrip()
        if reg_value == '1':
            return True

        return False

    def get_tx_disable_channel(self):
        """
        Retrieves the TX disabled channels in this SFP
        Returns:
            A hex of 4 bits (bit 0 to bit 3 as channel 0 to channel 3) to represent
            TX channels which have been disabled in this SFP.
            As an example, a returned value of 0x5 indicates that channel 0
            and channel 2 have been disabled.
        """
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           return False
        tx_disabled = 0
        for channel in range(1,5):
            path = "/sys/bus/i2c/devices/{}-0050/sfp_tx_disable{}"
            port_ps = path.format(self._port_to_i2c_mapping[self.port_num],channel)
            try:
                reg_file = open(port_ps)
            except IOError as e:
                print("Error: unable to open file: %s" % str(e))
                return False

            reg_value = reg_file.readline().rstrip()
            if reg_value == '1':
                tx_disabled |= 1 << (channel-1)
        return tx_disabled

    def get_lpmode(self):
        """
        Retrieves the lpmode (low power mode) status of this SFP
        Returns:
            A Boolean, True if lpmode is enabled, False if disabled
        """
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           return False
        if self.sfp_type == SFP_TYPE:
            # SFP doesn't support this feature
            return False
        else:
            power_set=self.get_power_set()
            power_override = self.get_power_override()
            return power_set and power_override

    def get_power_set(self):
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           return False
        if self.sfp_type == SFP_TYPE:
            # SFP doesn't support this feature
            return False
        else:
            power_set = False

            sfpd_obj = sff8436Dom()
            if sfpd_obj is None:
                return False

            dom_control_raw = self.__read_eeprom_specific_bytes(
                QSFP_POWEROVERRIDE_OFFSET, QSFP_CONTROL_WIDTH) if self.get_presence() else None
            if dom_control_raw is not None:
                dom_control_data = sfpd_obj.parse_control_bytes(dom_control_raw, 0)
                power_set = (
                    'On' == dom_control_data['data']['PowerSet']['value'])

            return power_set

    def get_power_override(self):
        """
        Retrieves the power-override status of this SFP
        Returns:
            A Boolean, True if power-override is enabled, False if disabled
        """
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           return False
        if self.sfp_type == SFP_TYPE:
            return False # SFP doesn't support this feature
        else:
            power_override = False


            sfpd_obj = sff8436Dom()
            if sfpd_obj is None:
                return False

            dom_control_raw = self.__read_eeprom_specific_bytes(
                QSFP_POWEROVERRIDE_OFFSET, QSFP_CONTROL_WIDTH) if self.get_presence() else None
            if dom_control_raw is not None:
                dom_control_data = sfpd_obj.parse_control_bytes(dom_control_raw, 0)
                power_override = (
                    'On' == dom_control_data['data']['PowerOverride']['value'])

            return power_override

    def get_temperature(self):
        """
        Retrieves the temperature of this SFP
        Returns:
            An integer number of current temperature in Celsius
        """
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           return 0
        transceiver_dom_info_dict = self.get_transceiver_bulk_status()
        return transceiver_dom_info_dict.get("temperature", "N/A")

    def get_voltage(self):
        """
        Retrieves the supply voltage of this SFP
        Returns:
            An integer number of supply voltage in mV
        """
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           return 0
        transceiver_dom_info_dict = self.get_transceiver_bulk_status()
        return transceiver_dom_info_dict.get("voltage", "N/A")

    def get_tx_bias(self):
        """
        Retrieves the TX bias current of this SFP
        Returns:
            A list of four integer numbers, representing TX bias in mA
            for channel 0 to channel 4.
            Ex. ['110.09', '111.12', '108.21', '112.09']
        """
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           return [0,0,0,0]
        transceiver_dom_info_dict = self.get_transceiver_bulk_status()

        tx1_bs = transceiver_dom_info_dict.get("tx1bias", "N/A")
        if self.sfp_type == SFP_TYPE:
            return [tx1_bs, "N/A", "N/A", "N/A"] if transceiver_dom_info_dict else []

        tx2_bs = transceiver_dom_info_dict.get("tx2bias", "N/A")
        tx3_bs = transceiver_dom_info_dict.get("tx3bias", "N/A")
        tx4_bs = transceiver_dom_info_dict.get("tx4bias", "N/A")
        return [tx1_bs, tx2_bs, tx3_bs, tx4_bs] if transceiver_dom_info_dict else []
    def get_rx_power(self):
        """
        Retrieves the received optical power for this SFP
        Returns:
            A list of four integer numbers, representing received optical
            power in mW for channel 0 to channel 4.
            Ex. ['1.77', '1.71', '1.68', '1.70']
        """
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           return [0,0,0,0]

        transceiver_dom_info_dict = self.get_transceiver_bulk_status()
        rx1_pw = transceiver_dom_info_dict.get("rx1power", "N/A")
        if self.sfp_type == SFP_TYPE:
            return [rx1_pw, "N/A", "N/A", "N/A"] if transceiver_dom_info_dict else []
        rx2_pw = transceiver_dom_info_dict.get("rx2power", "N/A")
        rx3_pw = transceiver_dom_info_dict.get("rx3power", "N/A")
        rx4_pw = transceiver_dom_info_dict.get("rx4power", "N/A")
        return [rx1_pw, rx2_pw, rx3_pw, rx4_pw] if transceiver_dom_info_dict else []


    def get_tx_power(self):
        """
        Retrieves the TX power of this SFP
        Returns:
            A list of four integer numbers, representing TX power in mW
            for channel 0 to channel 4.
            Ex. ['1.86', '1.86', '1.86', '1.86']
        """
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           return [0,0,0,0]

        transceiver_dom_info_dict = self.get_transceiver_bulk_status()
        tx1_pw = transceiver_dom_info_dict.get("tx1power", "N/A")
        if self.sfp_type == SFP_TYPE:
            return [tx1_pw, "N/A", "N/A", "N/A"] if transceiver_dom_info_dict else []
        tx2_pw = transceiver_dom_info_dict.get("tx2power", "N/A")
        tx3_pw = transceiver_dom_info_dict.get("tx3power", "N/A")
        tx4_pw = transceiver_dom_info_dict.get("tx4power", "N/A")
        return [tx1_pw, tx2_pw, tx3_pw, tx4_pw]

    def reset(self):
        """
        Reset SFP and return all user module settings to their default srate.
        Returns:
            A boolean, True if successful, False if not
        """
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           return False
        if self.port_num > 0 and self.port_num < 17:
            cpld_path="/sys/bus/i2c/devices/33-0062"
        elif self.port_num >16 and self.port_num < 33:
            cpld_path="/sys/bus/i2c/devices/34-0064"

        reset_path = "{}{}{}".format(cpld_path , 'module_reset_' , self.port_num)
        ret=self._api_helper.write_txt_file(reset_path, 1)
        if ret is not True:
            return ret

        time.sleep(0.01)
        ret=self._api_helper.write_txt_file(reset_path, 0)
        
        time.sleep(0.2)

        return ret

    def tx_disable(self, tx_disable):
        """
        Disable SFP TX for all channels
        Args:
            tx_disable : A Boolean, True to enable tx_disable mode, False to disable
                         tx_disable mode.
        Returns:
            A boolean, True if tx_disable is set successfully, False if not
        """
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           return False
        path = "/sys/bus/i2c/devices/{}-0050/sfp_tx_disable"
        tx_path = path.format(self._port_to_i2c_mapping[self.port_num])
        if tx_disable:
            ret=self._api_helper.write_txt_file(tx_path, 1)
        else:
            ret=self._api_helper.write_txt_file(tx_path, 0)

        if ret is not None:
            time.sleep(0.01)
            return ret
        else:
            return False

       


    def tx_disable_channel(self, channel, disable):
        """
        Sets the tx_disable for specified SFP channels
        Args:
            channel : A hex of 4 bits (bit 0 to bit 3) which represent channel 0 to 3,
                      e.g. 0x5 for channel 0 and channel 2.
            disable : A boolean, True to disable TX channels specified in channel,
                      False to enable
        Returns:
            A boolean, True if successful, False if not
        """ 
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           return False
        if not self.get_presence():
            return False
        ret_value=True
        for ch in range(1,5):
            if channel & 1<<(ch-1):
                path = "/sys/bus/i2c/devices/{}-0050/sfp_tx_disable{}"
                tx_path = path.format(self._port_to_i2c_mapping[self.port_num],ch)
                if disable:
                    ret=self._api_helper.write_txt_file(tx_path, 1)
                else:
                    ret=self._api_helper.write_txt_file(tx_path, 0)
                if ret is False:
                    ret_value = False
        return ret_value


    def set_lpmode(self, lpmode):
        """
        Sets the lpmode (low power mode) of SFP
        Args:
            lpmode: A Boolean, True to enable lpmode, False to disable it
            Note  : lpmode can be overridden by set_power_override
        Returns:
            A boolean, True if lpmode is set successfully, False if not
        """
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           return False
        if self.sfp_type == SFP_TYPE:
            return False # SFP doesn't support this feature
        else:
            if lpmode is True:
                self.set_power_override(True, True)
            else:
                self.set_power_override(False, False)

            return True
       
    def set_power_override(self, power_override, power_set):
        """
        Sets SFP power level using power_override and power_set
        Args:
            power_override :
                    A Boolean, True to override set_lpmode and use power_set
                    to control SFP power, False to disable SFP power control
                    through power_override/power_set and use set_lpmode
                    to control SFP power.
            power_set :
                    Only valid when power_override is True.
                    A Boolean, True to set SFP to low power mode, False to set
                    SFP to high power mode.
        Returns:
            A boolean, True if power-override and power_set are set successfully,
            False if not
        """
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           return False
        if self.sfp_type == SFP_TYPE:
            return False # SFP doesn't support this feature
        else:
            if not self.get_presence():
                return False
            try:
                power_override_bit = (1 << 0) if power_override else 0
                power_set_bit      = (1 << 1) if power_set else (1 << 3)

                buffer = create_string_buffer(1)
                if sys.version_info[0] >= 3:
                    buffer[0] = (power_override_bit | power_set_bit)
                else:
                    buffer[0] = chr(power_override_bit | power_set_bit)
                # Write to eeprom
                with open(self.port_to_eeprom_mapping[self.port_num], "r+b") as fd:
                    fd.seek(QSFP_POWEROVERRIDE_OFFSET)
                    fd.write(buffer[0])
                    time.sleep(0.01)
            except Exception:
                print ('Error: unable to open file: ', str(e))
                return False
            return True

    def get_name(self):
        """
        Retrieves the name of the device
            Returns:
            string: The name of the device
        """
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           return "FPGA"
        sfputil_helper = SfpUtilHelper()
        sfputil_helper.read_porttab_mappings(
            self.__get_path_to_port_config_file())
        name = sfputil_helper.logical[self.index] or "Unknown"
        return name

    def get_presence(self):
        """
        Retrieves the presence of the device
        Returns:
            bool: True if device is present, False if not
        """
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           return False
        if self.port_num > 0 and self.port_num < 17:
            cpld_path="/sys/bus/i2c/devices/33-0062"
        elif self.port_num >16 and self.port_num < 33:
            cpld_path="/sys/bus/i2c/devices/34-0064"
        present_path = "{}{}{}".format(cpld_path , '/module_present_' , self.port_num)
        val=self._api_helper.read_txt_file(present_path)
        if val is not None:
            return int(val, 10)==1
        else:
            return False

    def get_model(self):
        """
        Retrieves the model number (or part number) of the device
        Returns:
            string: Model/part number of device
        """
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           return "FPGA"
        transceiver_dom_info_dict = self.get_transceiver_info()
        return transceiver_dom_info_dict.get("model", "N/A")

    def get_serial(self):
        """
        Retrieves the serial number of the device
        Returns:
            string: Serial number of device
        """
        if self.port_num >=FPGA_PORT_START and self.port_num <=FPGA_PORT_END:
           return "FPGA"
        transceiver_dom_info_dict = self.get_transceiver_info()
        return transceiver_dom_info_dict.get("serial", "N/A")

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        return self.get_presence() and self.get_transceiver_bulk_status()