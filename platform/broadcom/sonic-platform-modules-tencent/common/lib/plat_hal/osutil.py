#!/usr/bin/env python3
#######################################################
#
# osutil.py
# Python implementation of the Class osutil
# Original author: rd@ruijie.com.cn
#
#######################################################

import os
import time
import glob
import re
from rjutil.smbus import SMBus
import time
import subprocess
from functools import wraps
import fcntl
import syslog


PLATFORM_HAL_DEBUG_FILE = "/etc/.platform_hal_debug_flag"


def platform_hal_debug(s):
    if os.path.exists(PLATFORM_HAL_DEBUG_FILE):
        syslog.openlog("PLATFORM_HAL", syslog.LOG_PID)
        syslog.syslog(syslog.LOG_DEBUG, s)


def retry(maxretry=6, delay=0.01):
    '''
        maxretry:  max retry times
        delay   :  interval after last retry
    '''
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            time_retry = maxretry
            time_delay = delay
            result_msg = ""
            while time_retry:
                try:
                    val, result_msg = f(*args, **kwargs)
                    if val is False:
                        time_retry -= 1
                        time.sleep(time_delay)
                        continue
                    else:
                        return val, result_msg
                except Exception as e:
                    time_retry -= 1
                    result_msg = str(e)
                    time.sleep(time_delay)
            return False, "max time retry last errmsg is {}".format(result_msg)
        return wrapper
    return decorator


pidfile = -1


def file_rw_lock(file_path):
    global pidfile
    pidfile = open(file_path, "r")
    try:
        fcntl.flock(pidfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
        platform_hal_debug("file_rw_lock success")
        return True
    except Exception as e:
        pidfile.close()
        pidfile = -1
        return False


def file_rw_unlock():
    try:
        global pidfile

        if pidfile != -1:
            fcntl.flock(pidfile, fcntl.LOCK_UN)
            pidfile.close()
            pidfile = -1
            platform_hal_debug("file_rw_unlock success")
        else:
            platform_hal_debug("pidfile is invalid, do nothing")
        return True
    except Exception as e:
        platform_hal_debug("file_rw_unlock err, msg: %s" % (str(e)))
        return False


def take_file_rw_lock(file_path):
    loop = 1000
    ret = False
    for i in range(0, loop):
        ret = file_rw_lock(file_path)
        if ret is True:
            break
        time.sleep(0.001)
    return ret


class osutil(object):
    """
       osutil
    """

    @staticmethod
    @retry(maxretry=6)
    def rji2cget_python(bus, addr, reg):
        with SMBus(bus) as y:
            val, ind = y.read_byte_data(addr, reg, True)
        return val, ind

    @staticmethod
    @retry(maxretry=6)
    def rji2cset_python(bus, addr, reg, value):
        with SMBus(bus) as y:
            val, ind = y.write_byte_data(addr, reg, value, True)
        return val, ind

    @staticmethod
    @retry(maxretry=6)
    def rji2cgetword_python(bus, addr, reg):
        with SMBus(bus) as y:
            val, ind = y.read_word_data(addr, reg, True)
        return val, ind

    @staticmethod
    @retry(maxretry=6)
    def rji2csetword_python(bus, addr, reg, value):
        with SMBus(bus) as y:
            val, ind = y.write_word_data(addr, reg, value, True)
        return val, ind

    @staticmethod
    @retry(maxretry=6)
    def rji2csetwordpec_python(bus, addr, reg, value):
        with SMBus(bus) as y:
            val, ind = y.write_word_data_pec(addr, reg, value, True)
        return val, ind

    @staticmethod
    @retry(maxretry=6)
    def rji2cset_byte_pec_python(bus, addr, reg, value):
        with SMBus(bus) as y:
            val, ind = y.write_byte_data_pec(addr, reg, value, True)
        return val, ind

    @staticmethod
    def command(cmdstr):
        retcode, output = subprocess.getstatusoutput(cmdstr)
        return retcode, output

    @staticmethod
    def geti2cword_i2ctool(bus, addr, offset):
        command_line = "i2cget -f -y %d 0x%02x 0x%02x  wp" % (bus, addr, offset)
        retrytime = 6
        ret_t = ""
        for i in range(retrytime):
            ret, ret_t = osutil.command(command_line)
            if ret == 0:
                return True, int(ret_t, 16)
            time.sleep(0.1)
        return False, ret_t

    @staticmethod
    def seti2cword_i2ctool(bus, addr, offset, val):
        command_line = "i2cset -f -y %d 0x%02x 0x%0x 0x%04x wp" % (bus, addr, offset, val)
        retrytime = 6
        ret_t = ""
        for i in range(retrytime):
            ret, ret_t = osutil.command(command_line)
            if ret == 0:
                return True, ret_t
            time.sleep(0.1)
        return False, ret_t

    @staticmethod
    def rji2cget_i2ctool(bus, devno, address):
        command_line = "i2cget -f -y %d 0x%02x 0x%02x " % (bus, devno, address)
        retrytime = 6
        ret_t = ""
        for i in range(retrytime):
            ret, ret_t = osutil.command(command_line)
            if ret == 0:
                return True, int(ret_t, 16)
            time.sleep(0.1)
        return False, ret_t

    @staticmethod
    def rji2cset_i2ctool(bus, devno, address, byte):
        command_line = "i2cset -f -y %d 0x%02x 0x%02x 0x%02x" % (
            bus, devno, address, byte)
        retrytime = 6
        ret_t = ""
        for i in range(retrytime):
            ret, ret_t = osutil.command(command_line)
            if ret == 0:
                return True, ret_t
        return False, ret_t

    @staticmethod
    def geti2cword(bus, addr, offset):
        return osutil.rji2cgetword_python(bus, addr, offset)

    @staticmethod
    def seti2cword(bus, addr, offset, val):
        return osutil.rji2csetword_python(bus, addr, offset, val)

    @staticmethod
    def seti2cwordpec(bus, addr, offset, val):
        return osutil.rji2csetwordpec_python(bus, addr, offset, val)

    @staticmethod
    def seti2c_byte_pec(bus, addr, offset, val):
        return osutil.rji2cset_byte_pec_python(bus, addr, offset, val)

    @staticmethod
    def rji2cget(bus, devno, address):
        return osutil.rji2cget_python(bus, devno, address)

    @staticmethod
    def rji2cset(bus, devno, address, byte):
        return osutil.rji2cset_python(bus, devno, address, byte)

    @staticmethod
    def byteTostr(val):
        strtmp = ''
        for i in range(len(val)):
            strtmp += chr(val[i])
        return strtmp

    @staticmethod
    def io_rd(reg_addr, read_len=1):
        try:
            regaddr = 0
            if isinstance(reg_addr, int):
                regaddr = reg_addr
            else:
                regaddr = int(reg_addr, 16)
            devfile = "/dev/port"
            fd = os.open(devfile, os.O_RDWR | os.O_CREAT)
            os.lseek(fd, regaddr, os.SEEK_SET)
            str = os.read(fd, read_len)
            return True, "".join(["%02x" % item for item in str])
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)
        finally:
            os.close(fd)

    @staticmethod
    def readsysfs(location, flock_path=None):
        flock_path_tmp = None
        platform_hal_debug("readsysfs, location:%s, flock_path:%s" % (location, flock_path))
        try:
            if flock_path is not None:
                flock_paths = glob.glob(flock_path)
                if len(flock_paths) != 0:
                    flock_path_tmp = flock_paths[0]
                    platform_hal_debug("try to get file lock, path:%s" % flock_path_tmp)
                    ret = take_file_rw_lock(flock_path_tmp)
                    if ret is False:
                        platform_hal_debug("take file lock timeout, path:%s" % flock_path_tmp)
                        return False, ("take file rw lock timeout, path:%s" % flock_path_tmp)
                else:
                    platform_hal_debug("config error, can't find flock_path:%s" % flock_path)

            locations = glob.glob(location)
            with open(locations[0], 'rb') as fd1:
                retval = fd1.read()
            retval = osutil.byteTostr(retval)
            if flock_path_tmp is not None:
                file_rw_unlock()

            retval = retval.rstrip('\r\n')
            retval = retval.lstrip(" ")
        except Exception as e:
            if flock_path_tmp is not None:
                file_rw_unlock()
            platform_hal_debug("readsysfs error, msg:%s" % str(e))
            return False, (str(e) + " location[%s]" % location)
        return True, retval

    @staticmethod
    def writesysfs(location, value):
        try:
            if not os.path.isfile(location):
                print(location, 'not found !')
                return False, ("location[%s] not found !" % location)
            with open(location, 'w') as fd1:
                fd1.write(value)
        except Exception as e:
            return False, (str(e) + " location[%s]" % location)
        return True, ("set location[%s] %s success !" % (location, value))

    @staticmethod
    def getdevmem(addr, digit, mask):
        command_line = "devmem 0x%02x %d" % (addr, digit)
        retrytime = 6
        ret_t = ""
        for i in range(retrytime):
            ret, ret_t = osutil.command(command_line)
            if ret == 0:
                if mask is not None:
                    ret_t = str(int(ret_t, 16) & mask)
            return True, ret_t
        return False, ret_t

    @staticmethod
    def readdevfile_ascii(path, offset, len):
        msg = ""
        ret = ""
        joinstr = ''
        fd = -1

        if not os.path.exists(path):
            msg = path + " not found !"
            return False, msg

        try:
            fd = os.open(path, os.O_RDONLY)
            os.lseek(fd, offset, os.SEEK_SET)
            ret = os.read(fd, len)
            for item in ret:
                joinstr += '%02x ' % item  # like sysfs, display in hex
        except Exception as e:
            msg = str(e)
            return False, msg
        finally:
            if fd > 0:
                os.close(fd)
        return True, joinstr

    @staticmethod
    def readdevfile(path, offset, len):
        msg = ""
        ret = ""
        fd = -1

        if not os.path.exists(path):
            msg = path + " not found !"
            return False, msg

        try:
            fd = os.open(path, os.O_RDONLY)
            os.lseek(fd, offset, os.SEEK_SET)
            ret = os.read(fd, len)
        except Exception as e:
            msg = str(e)
            return False, msg
        finally:
            if fd > 0:
                os.close(fd)
        return True, ret

    @staticmethod
    def rj_os_system(cmd):
        status, output = subprocess.getstatusoutput(cmd)
        return status, output

    @staticmethod
    def getsdkreg(reg):
        try:
            cmd = "bcmcmd -t 1 'getr %s ' < /dev/null" % reg
            ret, result = osutil.rj_os_system(cmd)
            result_t = result.strip().replace("\r", "").replace("\n", "")
            if ret != 0 or "Error:" in result_t:
                return False, result
            patt = r"%s.(.*):(.*)>drivshell" % reg
            rt = re.findall(patt, result_t, re.S)
            test = re.findall("=(.*)", rt[0][0])[0]
        except Exception as e:
            return False, 'get sdk register error'
        return True, test

    @staticmethod
    def getmactemp():
        try:
            result = {}
            # waitForDocker()
            # need to exec twice
            osutil.rj_os_system("bcmcmd -t 1 \"show temp\" < /dev/null")
            ret, log = osutil.rj_os_system("bcmcmd -t 1 \"show temp\" < /dev/null")
            if ret:
                return False, result
            else:
                logs = log.splitlines()
                for line in logs:
                    if "average" in line:
                        b = re.findall(r'\d+.\d+', line)
                        result["average"] = b[0]
                    elif "maximum" in line:
                        b = re.findall(r'\d+.\d+', line)
                        result["maximum"] = b[0]
        except Exception as e:
            return False, str(e)
        return True, result
