#############################################################################
# Edgecore
#
# Module contains an implementation of SONiC Platform Base API and
# provides the fan status which are available in the platform
#
#############################################################################


try:
    from sonic_platform_base.fan_base import FanBase
    from .helper import APIHelper
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

PSU_FAN_MAX_RPM = 25500
FAN_FRONT_MAX_RPM = 21400
FAN_REAR_MAX_RPM = 22100

CPLD_I2C_PATH = "/sys/bus/i2c/devices/17-0066/fan"
PSU_HWMON_I2C_PATH = ["/sys/bus/i2c/devices/10-0059/", "/sys/bus/i2c/devices/9-0058/"]
PSU_CPLD_I2C_PATH = ["/sys/bus/i2c/devices/10-0051/", "/sys/bus/i2c/devices/9-0050/"]

FAN_NAME_LIST = ["FAN-1F", "FAN-2F", "FAN-3F", "FAN-4F", "FAN-5F", "FAN-6F",
                 "FAN-1R", "FAN-2R", "FAN-3R", "FAN-4R", "FAN-5R", "FAN-6R"]

class Fan(FanBase):
    """Platform-specific Fan class"""

    def __init__(self, fan_tray_index, fan_index=0, is_psu_fan=False, psu_index=0):
        self._api_helper=APIHelper()
        self.fan_index = fan_index
        self.fan_tray_index = fan_tray_index
        self.is_psu_fan = is_psu_fan
        if self.is_psu_fan:
            self.psu_index = psu_index
            self.psu_hwmon_path = PSU_HWMON_I2C_PATH[self.psu_index]

        FanBase.__init__(self)


    def get_direction(self):
        """
        Retrieves the direction of fan
        Returns:
            A string, either FAN_DIRECTION_INTAKE or FAN_DIRECTION_EXHAUST
            depending on fan direction
        """


        if not self.is_psu_fan:
            dir_str = "{}{}{}".format(CPLD_I2C_PATH, self.fan_tray_index+1, '_direction')
            val = self._api_helper.read_txt_file(dir_str)
            if val is not None:
                if val == '0': #F2B
                    direction = self.FAN_DIRECTION_EXHAUST
                else:
                    direction = self.FAN_DIRECTION_INTAKE
            else:
                direction = self.FAN_DIRECTION_EXHAUST

        else: #For PSU
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
        if self.get_presence():
            if self.is_psu_fan:
                psu_fan_path = "{}{}".format(self.psu_hwmon_path, 'psu_fan1_speed_rpm')
                fan_speed_rpm = self._api_helper.read_txt_file(psu_fan_path)
                if (fan_speed_rpm is not None) and (fan_speed_rpm.isdigit()):
                    speed = int(fan_speed_rpm) * 100 / PSU_FAN_MAX_RPM
                    if speed > 100:
                        speed = 100
                else:
                    return 0
            else:
                input_path = "{}{}{}{}".format(CPLD_I2C_PATH, "1" if (self.fan_index == 1) else "", self.fan_tray_index+1, '_input')
                speed_input = self._api_helper.read_txt_file(input_path)


                speed_max = FAN_REAR_MAX_RPM if (self.fan_index == 1) else FAN_FRONT_MAX_RPM

                if speed_input is None or speed_max is None:
                    return 0

                speed = int(speed_input) * 100 / int(speed_max)
                if speed > 100:
                    speed = 100

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
        speed = 0
        if self.is_psu_fan:
            raise NotImplementedError
        else:
            speed_path = "{}{}".format(CPLD_I2C_PATH, '_duty_cycle_percentage')
            speed = self._api_helper.read_txt_file(speed_path)
            if speed is None:
                return 0

        return int(speed)

    def get_speed_tolerance(self):
        """
        Retrieves the speed tolerance of the fan
        Returns:
            An integer, the percentage of variance from target speed which is
                 considered tolerable
        """
        raise NotImplementedError

    def set_speed(self, speed):
        """
        Sets the fan speed
        Args:
            speed: An integer, the percentage of full fan speed to set fan to,
                   in the range 0 (off) to 100 (full speed)
        Returns:
            A boolean, True if speed is set successfully, False if not

        """

        if not self.is_psu_fan:
            speed_path = "{}{}".format(CPLD_I2C_PATH, '_duty_cycle_percentage')
            return self._api_helper.write_txt_file(speed_path, int(speed))

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
        raise NotImplementedError

    def get_presence(self):
        """
        Retrieves the presence of the FAN
        Returns:
            bool: True if FAN is present, False if not
        """
        if not self.is_psu_fan:
            present_path = "{}{}{}".format(CPLD_I2C_PATH, self.fan_tray_index+1, '_present')
            val=self._api_helper.read_txt_file(present_path)
        else:
            present_path = "{}{}".format(PSU_CPLD_I2C_PATH[self.psu_index], 'psu_present')
            val=self._api_helper.read_txt_file(present_path)

        if val is not None:
            return int(val, 10)==1
        else:
            return False

    def get_name(self):
        """
        Retrieves the name of the device
            Returns:
            string: The name of the device
        """
        fan_name = FAN_NAME_LIST[self.fan_tray_index + self.fan_index*6] \
            if not self.is_psu_fan \
            else "PSU-{} FAN-{}".format(self.psu_index+1, self.fan_index+1)

        return fan_name

    def get_status(self):
        """
        Retrieves the operational status of the device
        Returns:
            A boolean value, True if device is operating properly, False if not
        """
        if not self.is_psu_fan:
            dir_str = "{}{}{}".format(CPLD_I2C_PATH, self.fan_tray_index+1, '_fault')
            val = self._api_helper.read_txt_file(dir_str)
            if val is not None:
                if val == '0':
                    status = True
                else:
                    status = False
            else:
                status = False
            return status
        else:
            return self.get_speed() > 0

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
        return "N/A"

    def is_replaceable(self):
        """
        Indicate whether this device is replaceable.
        Returns:
            bool: True if it is replaceable.
        """
        return True if not self.is_psu_fan else False

    def get_position_in_parent(self):
        """
        Retrieves 1-based relative physical position in parent device.
        If the agent cannot determine the parent-relative position
        for some reason, or if the associated value of
        entPhysicalContainedIn is'0', then the value '-1' is returned
        Returns:
            integer: The 1-based relative physical position in parent device
            or -1 if cannot determine the position
        """
        return (self.fan_tray_index+1) \
            if not self.is_psu_fan else (self.psu_index+1)

    def get_status_led(self):
        """
        Gets the state of the fan status LED
        Returns:
            A string, one of the predefined STATUS_LED_COLOR_* strings above
        """
        return {
            True: self.STATUS_LED_COLOR_GREEN,
            False: self.STATUS_LED_COLOR_RED
        }.get(self.get_status(), self.STATUS_LED_COLOR_OFF)
