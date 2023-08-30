#
# Copyright (c) 2020-2021 NVIDIA CORPORATION & AFFILIATES.
# Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import ctypes
import functools
import subprocess
import json
import sys
import time
import os
from sonic_py_common import device_info
from sonic_py_common.logger import Logger

HWSKU_JSON = 'hwsku.json'

PORT_INDEX_KEY = "index"
PORT_TYPE_KEY = "port_type"
RJ45_PORT_TYPE = "RJ45"

logger = Logger()


def read_from_file(file_path, target_type, default='', raise_exception=False, log_func=logger.log_error):
    """
    Read content from file and convert to target type
    :param file_path: File path
    :param target_type: target type
    :param default: Default return value if any exception occur
    :param raise_exception: Raise exception to caller if True else just return default value
    :param log_func: function to log the error
    :return: String content of the file
    """
    try:
        with open(file_path, 'r') as f:
            value = f.read()
            if value is None:
                # None return value is not allowed in any case, so we log error here for further debug.
                logger.log_error('Failed to read from {}, value is None, errno is {}'.format(file_path, ctypes.get_errno()))
                # Raise ValueError for the except statement to handle this as a normal exception
                raise ValueError('File content of {} is None'.format(file_path))
            else:
                value = target_type(value.strip())
    except (ValueError, IOError) as e:
        if log_func:
            log_func('Failed to read from file {} - {}'.format(file_path, repr(e)))
        if not raise_exception:
            value = default
        else:
            raise e

    return value


def read_str_from_file(file_path, default='', raise_exception=False, log_func=logger.log_error):
    """
    Read string content from file
    :param file_path: File path
    :param default: Default return value if any exception occur
    :param raise_exception: Raise exception to caller if True else just return default value
    :param log_func: function to log the error
    :return: String content of the file
    """
    return read_from_file(file_path=file_path, target_type=str, default=default, raise_exception=raise_exception, log_func=log_func)


def read_int_from_file(file_path, default=0, raise_exception=False, log_func=logger.log_error):
    """
    Read content from file and cast it to integer
    :param file_path: File path
    :param default: Default return value if any exception occur
    :param raise_exception: Raise exception to caller if True else just return default value
    :param log_func: function to log the error
    :return: Integer value of the file content
    """
    return read_from_file(file_path=file_path, target_type=int, default=default, raise_exception=raise_exception, log_func=log_func)


def read_float_from_file(file_path, default=0.0, raise_exception=False, log_func=logger.log_error):
    """
    Read content from file and cast it to integer
    :param file_path: File path
    :param default: Default return value if any exception occur
    :param raise_exception: Raise exception to caller if True else just return default value
    :param log_func: function to log the error
    :return: Integer value of the file content
    """
    return read_from_file(file_path=file_path, target_type=float, default=default, raise_exception=raise_exception, log_func=log_func)


def _key_value_converter(content):
    ret = {}
    for line in content.splitlines():
        k,v = line.split(':')
        ret[k.strip()] = v.strip()
    return ret


def read_key_value_file(file_path, default={}, raise_exception=False, log_func=logger.log_error):
    """Read file content and parse the content to a dict. The file content should like:
       key1:value1
       key2:value2

    Args:
        file_path (str): file path
        default (dict, optional): default return value. Defaults to {}.
        raise_exception (bool, optional): If exception should be raised or hiden. Defaults to False.
        log_func (optional): logger function.. Defaults to logger.log_error.
    """
    return read_from_file(file_path=file_path, target_type=_key_value_converter, default=default, raise_exception=raise_exception, log_func=log_func)


def write_file(file_path, content, raise_exception=False, log_func=logger.log_error):
    """
    Write the given value to a file
    :param file_path: File path
    :param content: Value to write to the file
    :param raise_exception: Raise exception to caller if True
    :return: True if write success else False
    """
    try:
        with open(file_path, 'w') as f:
            f.write(str(content))
    except (ValueError, IOError) as e:
        if log_func:
            log_func('Failed to write {} to file {} - {}'.format(content, file_path, repr(e)))
        if not raise_exception:
            return False
        else:
            raise e
    return True


def pre_initialize(init_func):
    def decorator(method):
        @functools.wraps(method)
        def _impl(self, *args, **kwargs):
            init_func(self)
            return method(self, *args, **kwargs)
        return _impl
    return decorator


def pre_initialize_one(init_func):
    def decorator(method):
        @functools.wraps(method)
        def _impl(self, index):
            init_func(self, index)
            return method(self, index)
        return _impl
    return decorator


def read_only_cache():
    """Decorator to cache return value for a method/function once.
       This decorator should be used for method/function when:
       1. Executing the method/function takes time. e.g. reading sysfs.
       2. The return value of this method/function never changes.
    """
    def decorator(method):
        method.return_value = None

        @functools.wraps(method)
        def _impl(*args, **kwargs):
            if not method.return_value:
                method.return_value = method(*args, **kwargs)
            return method.return_value
        return _impl
    return decorator


@read_only_cache()
def is_host():
    """
    Test whether current process is running on the host or an docker
    return True for host and False for docker
    """
    docker_env_file = '/.dockerenv'
    return os.path.exists(docker_env_file) is False


def default_return(return_value, log_func=logger.log_debug):
    def wrapper(method):
        @functools.wraps(method)
        def _impl(*args, **kwargs):
            try:
                return method(*args, **kwargs)
            except Exception as e:
                if log_func:
                    log_func('Faield to execute method {} - {}'.format(method.__name__, repr(e)))
                return return_value
        return _impl
    return wrapper


def run_command(command):
    """
    Utility function to run an shell command and return the output.
    :param command: Shell command string.
    :return: Output of the shell command.
    """
    try:
        process = subprocess.Popen(command, shell=True, universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return process.communicate()[0].strip()
    except Exception:
        return None


def load_json_file(filename, log_func=logger.log_error):
    # load 'platform.json' or 'hwsku.json' file
    data = None
    try:
        with open(filename) as fp:
            try:
                data = json.load(fp)
            except json.JSONDecodeError:
                if log_func:
                    log_func("failed to decode Json file.")
        return data
    except Exception as e:
        if log_func:
            log_func("error occurred while parsing json file: {}".format(sys.exc_info()[1]))
        return None


def extract_RJ45_ports_index():
    # Cross check 'platform.json' and 'hwsku.json' to extract the RJ45 port index if exists.
    hwsku_path = device_info.get_path_to_hwsku_dir()
    hwsku_file = os.path.join(hwsku_path, HWSKU_JSON)
    if not os.path.exists(hwsku_file):
        # Platforms having no hwsku.json do not have RJ45 port
        return None

    platform_file = device_info.get_path_to_port_config_file()
    platform_dict = load_json_file(platform_file)['interfaces']
    hwsku_dict = load_json_file(hwsku_file)['interfaces']
    port_name_to_index_map_dict = {}
    RJ45_port_index_list = []

    # Compose a interface name to index mapping from 'platform.json'
    for i, (key, value) in enumerate(platform_dict.items()):
        if PORT_INDEX_KEY in value:
            index_raw = value[PORT_INDEX_KEY]
            # The index could be "1" or "1, 1, 1, 1"
            index = index_raw.split(',')[0]
            port_name_to_index_map_dict[key] = index

    if not bool(port_name_to_index_map_dict):
        return None

    # Check if "port_type" specified as "RJ45", if yes, add the port index to the list.
    for i, (key, value) in enumerate(hwsku_dict.items()):
        if key in port_name_to_index_map_dict and PORT_TYPE_KEY in value and value[PORT_TYPE_KEY] == RJ45_PORT_TYPE:
            RJ45_port_index_list.append(int(port_name_to_index_map_dict[key])-1)

    return RJ45_port_index_list if bool(RJ45_port_index_list) else None


def wait_until(predict, timeout, interval=1, *args, **kwargs):
    """Wait until a condition become true

    Args:
        predict (object): a callable such as function, lambda
        timeout (int): wait time in seconds
        interval (int, optional): interval to check the predict. Defaults to 1.

    Returns:
        _type_: _description_
    """
    while timeout > 0:
        if predict(*args, **kwargs):
            return True
        time.sleep(interval)
        timeout -= interval
    return False
