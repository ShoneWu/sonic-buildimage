#!/usr/bin/env python

########################################################################
# Accton CSP-7551
#
# Module contains an implementation of SONiC Platform Base API and
# provides the Fan-Drawers' information available in the platform.
#
########################################################################
import subprocess
import math
try:
    from sonic_platform_base.fan_drawer_base import FanDrawerBase
    from sonic_platform_base.fan_base import FanBase
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

FANS_PER_FANTRAY = 2
FANS_PER_PSU=1

PSU_FAN_MAX_RPM = 25500 #need update
FAN_MAX_FRONT_RPM = 16000
FAN_MAX_REAR_RPM = 14000
IPMI_FAN_INFO_CMD="ipmitool raw 0x36 0x11"
IPMI_PSU_PRESENT_GOOD_CMD="ipmitool raw 0x36 0x10"
IPMI_SENSOR_CMD="ipmitool raw 0x4 0x2d {0}"
IPMI_SENSOR_PARAM_CMD="ipmitool raw 0x4 0x21 0x00 0x00 {0} 0x00 24 6"
IPMI_FRU_CMD="ipmitool fru print {0}"

FAN_SENSOR_INDEX={
    0 : {
        0 : {"name" : "FAN1_FRONT", "index" : 9},
        1 : {"name" : "FAN1_REAR", "index" : 13}
    },
    1 : {
        0 : {"name" : "FAN2_FRONT", "index" : 10},
        1 : {"name" : "FAN2_REAR", "index" : 14}
    },
    2 : {
        0 : {"name" : "FAN3_FRONT", "index" : 11},
        1 : {"name" : "FAN3_REAR", "index" : 15}
    },
    3 : {
        0 : {"name" : "FAN4_FRONT", "index" : 12},
        1 : {"name" : "FAN4_REAR", "index" : 16}
    },
}

PSU_FAN_SENSOR_INDEX={
    0: 219,
    1: 220

}
FAN_FRU_INDEX={
    0:5,
    1:6,
    2:7,
    3:8
}

class Fan(FanBase):
    def _syscmd(self,cmd):
        proc = subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=True,stderr=subprocess.PIPE)
        data, _ = proc.communicate()
        status=proc.returncode
        data=data.decode(errors="ignore")
        return status , data


    def get_param(self):
        if(self.is_psu_fan):
            command=IPMI_SENSOR_PARAM_CMD.format(PSU_FAN_SENSOR_INDEX[self.psu_index])
        else:
            command=IPMI_SENSOR_PARAM_CMD.format(FAN_SENSOR_INDEX[self.fan_tray_index][self.fan_index]["index"])
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

    def get_psu_sensor_command(self):
        index=PSU_FAN_SENSOR_INDEX[self.psu_index]
        return  IPMI_SENSOR_CMD.format(index)

    def get_fansensor_command(self):
        index=FAN_SENSOR_INDEX[self.fan_tray_index][self.fan_index]["index"]
        return  IPMI_SENSOR_CMD.format(index)

    def get_fru_command(self):
        index=FAN_FRU_INDEX[self.fan_tray_index]
        return  IPMI_FRU_CMD.format(index)

    """Platform-specific Fan class"""

    def __init__(self, fan_tray_index, fan_index=0, is_psu_fan=False, psu_index=0):
        #self._api_helper=APIHelper()
        self.fan_index = fan_index
        self.fan_tray_index = fan_tray_index
        self.is_psu_fan = is_psu_fan

        if self.is_psu_fan:
            self.psu_index = psu_index
        FanBase.__init__(self)

    def get_direction(self):
        """
        Retrieves the direction of fan
        Returns:
            A string, either FAN_DIRECTION_INTAKE or FAN_DIRECTION_EXHAUST
            depending on fan direction
        """
        direction = self.FAN_DIRECTION_EXHAUST

        return direction

    def get_speed(self):
        """
        Retrieves the speed of fan as a percentage of full speed
        Returns:
            An integer, the percentage of full fan speed, in the range 0 (off)
                 to 100 (full speed)
        """
        speed = 0
        if self.is_psu_fan:
            cmd = self.get_psu_sensor_command()
            st1, log1 = self._syscmd(cmd)
            if st1 != 0:
                return 0
            status=log1.split()[1].strip()
            if(int(status,16) & 1<<5 ==0):
                val=log1.split()[0].strip()
                val2=self.convert_ipmi(val)
                speed = val2*100/PSU_FAN_MAX_RPM
                if speed > 100:
                    speed=100
            else:
                return 0
        elif self.get_presence():
            cmd = self.get_fansensor_command()
            st1, log1 = self._syscmd(cmd)
            if st1 != 0:
                return 0
            status=log1.split()[1].strip()
            if(self.fan_index ==1):
                fan_max_speed = FAN_MAX_REAR_RPM
            else:
                fan_max_speed = FAN_MAX_FRONT_RPM
            if(int(status,16) & 1<<5 ==0):
                val=log1.split()[0].strip()
                val2=self.convert_ipmi(val)
                speed = val2*100/fan_max_speed
                if speed > 100:
                    speed=100
            else:
                return 0

        return int(speed)

    def get_target_speed(self):
        """
        Retrieves the target (expected) speed of the fan
        Returns:
            An integer, the percentage of full fan speed, in the range 0 (off)
                 to 100 (full speed)

        Note:
            speed_pc = pwm_target/255*100

            0   : when PWM mode is use
            pwm : when pwm mode is not use
        """
        if self.is_psu_fan:
            cmd = self.get_psu_sensor_command()
            st1, log1 = self._syscmd(cmd)
            if st1 != 0:
                return 0
            status=log1.split()[1].strip()
            if(int(status,16) & 1<<5 ==0):
                val=log1.split()[0].strip()
                val2=self.convert_ipmi(val)
                speed = val2*100/PSU_FAN_MAX_RPM
                if speed > 100:
                    speed=100
            else:
                return 0
        elif self.get_presence():
            st1, log1 = self._syscmd(IPMI_FAN_INFO_CMD)
            if st1 != 0:
                return False
            index=self.fan_tray_index
            fan=log1.split()[index+4].strip()
            speed = (int(fan,16)*100/255)
        return int(speed)


    def get_speed_tolerance(self):
        """
        Retrieves the speed tolerance of the fan
        Returns:
            An integer, the percentage of variance from target speed which is
                 considered tolerable
        """
        speed_tolerance = 10
        return int(speed_tolerance)


    def set_speed(self, speed):
        """
        Sets the fan speed
        Args:
            speed: An integer, the percentage of full fan speed to set fan to,
                   in the range 0 (off) to 100 (full speed)
        Returns:
            A boolean, True if speed is set successfully, False if not

        """

        return False

    def set_status_led(self, color):
        """
        Sets the state of the fan module status LED
        Args:
            color: A string representing the color with which to set the
                   fan module status LED
        Returns:
            bool: True if status LED state is set successfully, False if not
        """
        return False #Not supported

    def get_status_led(self):
        """
        Gets the state of the fan status LED
        Returns:
            A string, one of the predefined STATUS_LED_COLOR_* strings above
        """
        status=self.get_presence()
        if status is None:
            return  self.STATUS_LED_COLOR_OFF

        return {
            1: self.STATUS_LED_COLOR_GREEN,
            0: self.STATUS_LED_COLOR_RED
        }.get(status, self.STATUS_LED_COLOR_OFF)

    def get_name(self):
        """
        Retrieves the name of the device
            Returns:
            string: The name of the device
        """
        fan_name = FAN_SENSOR_INDEX[self.fan_tray_index][self.fan_index]["name"] \
            if not self.is_psu_fan \
            else "PSU-{} FAN-{}".format(self.psu_index+1, self.fan_index+1)

        return fan_name

    def get_presence(self):
        """
        Retrieves the presence of the FAN
        Returns:
            bool: True if FAN is present, False if not
        """
        if self.is_psu_fan:
            st1, log1 = self._syscmd(IPMI_PSU_PRESENT_GOOD_CMD)
            if st1 != 0:
                return False
            index=self.psu_index
            ps=log1.split()[index].strip()
            if(int(ps,16) & 1 ==1):
                return True
            else:
                return False
        else:
            st1, log1 = self._syscmd(IPMI_FAN_INFO_CMD)
            if st1 != 0:
                return False
            index=self.fan_tray_index
            ps=log1.split()[index].strip()
            if(int(ps,16) & 1 ==1):
                return True
            else:
                return False

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        if self.is_psu_fan:
            st1, log1 = self._syscmd(IPMI_PSU_PRESENT_GOOD_CMD)
            if st1 != 0:
                return False
            index=self.psu_index + 2
            ps=log1.split()[index].strip()
            if(int(ps,16) & 1 ==1):
                return True
            else:
                return False
        else:
            st1, log1 = self._syscmd(IPMI_FAN_INFO_CMD)
            if st1 != 0:
                return False
            index=self.fan_tray_index
            ps=log1.split()[index+8].strip()
            if(int(ps,16) & 1 ==1):
                return True
            else:
                return False

    def get_model(self):
        """
        Retrieves the model number (or part number) of the device
        Returns:
            string: Model/part number of device
        """

        return "N/A"

    def get_serial(self):
        """
        Retrieves the serial number of the device
        Returns:
            string: Serial number of device
        """
        if self.is_psu_fan:
            return "N/A"
        else:
            cmd = self.get_fru_command()
            st1, log1 = self._syscmd(cmd + "|grep Serial")
            if st1 != 0:
                return "N/A"
            serial = log1.split(":")[1].strip()
            if serial is None:
                return "N/A"
            return serial




class FanDrawer(FanDrawerBase):
    """Accton Platform-specific Fan class"""

    def __init__(self, fantray_index):

        FanDrawerBase.__init__(self)

        self.fantrayindex = fantray_index
        if fantray_index <4:
            for i in range(0,FANS_PER_FANTRAY):
                self._fan_list.append(Fan(fantray_index, i))
        #2PSU each PSU has one fan
        if fantray_index >=4:
            for i in range(0,FANS_PER_PSU):
                self._fan_list.append(Fan(fantray_index, i, is_psu_fan=True, psu_index=fantray_index-4))

    def get_name(self):
        """
        Retrieves the fan drawer name
        Returns:
            string: The name of the device
        """
        name = "Psu {}".format(self.fantrayindex-3)\
            if self.fantrayindex >=4 \
            else "FanTray {}".format(self.fantrayindex+1)

        return name
