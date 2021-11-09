#!/usr/bin/env python

########################################################################
# Accton CSP-7551
#
# Module contains an implementation of SONiC Platform Base API and
# provides the Fan-Drawers' information available in the platform.
#
########################################################################

try:
    from sonic_platform_base.fan_drawer_base import FanDrawerBase
    from sonic_platform.fan import Fan
except ImportError as e:
    raise ImportError(str(e) + "- required module not found")

FANS_PER_FANTRAY = 2
FANS_PER_PSU=1
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
