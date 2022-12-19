/*
 * fan_device_driver.c
 *
 * This module realize /sys/s3ip/fan attributes read and write functions
 *
 * History
 *  [Version]                [Date]                    [Description]
 *   *  v1.0                2021-08-31                  S3IP sysfs
 */

#include <linux/slab.h>

#include "device_driver_common.h"
#include "fan_sysfs.h"
#include "dfd_sysfs_common.h"

#define FAN_INFO(fmt, args...) LOG_INFO("fan: ", fmt, ##args)
#define FAN_ERR(fmt, args...)  LOG_ERR("fan: ", fmt, ##args)
#define FAN_DBG(fmt, args...)  LOG_DBG("fan: ", fmt, ##args)

static int g_loglevel = 0;
static struct switch_drivers_s *g_drv = NULL;

/********************************************fan**********************************************/
static int rg_get_fan_number(void)
{
    int ret;

    check_p(g_drv);
    check_p(g_drv->get_fan_number);

    ret = g_drv->get_fan_number();
    return ret;
}

static int rg_get_fan_motor_number(unsigned int fan_index)
{
    int ret;

    check_p(g_drv);
    check_p(g_drv->get_fan_motor_number);

    ret = g_drv->get_fan_motor_number(fan_index);
    return ret;
}

/*
 * rg_get_fan_model_name - Used to get fan model name,
 * @fan_index: start with 1
 * @buf: Data receiving buffer
 * @count: length of buf
 *
 * This function returns the length of the filled buffer,
 * if not support this attributes filled "NA" to buf,
 * otherwise it returns a negative value on failed.
 */
static ssize_t rg_get_fan_model_name(unsigned int fan_index, char *buf, size_t count)
{
    ssize_t ret;

    check_p(g_drv);
    check_p(g_drv->get_fan_model_name);

    ret = g_drv->get_fan_model_name(fan_index, buf, count);
    return ret;
}

/*
 * rg_get_fan_serial_number - Used to get fan serial number,
 * @fan_index: start with 1
 * @buf: Data receiving buffer
 * @count: length of buf
 *
 * This function returns the length of the filled buffer,
 * if not support this attributes filled "NA" to buf,
 * otherwise it returns a negative value on failed.
 */
static ssize_t rg_get_fan_serial_number(unsigned int fan_index, char *buf, size_t count)
{
    ssize_t ret;

    check_p(g_drv);
    check_p(g_drv->get_fan_serial_number);

    ret = g_drv->get_fan_serial_number(fan_index, buf, count);
    return ret;
}

/*
 * rg_get_fan_part_number - Used to get fan part number,
 * @fan_index: start with 1
 * @buf: Data receiving buffer
 * @count: length of buf
 *
 * This function returns the length of the filled buffer,
 * if not support this attributes filled "NA" to buf,
 * otherwise it returns a negative value on failed.
 */
static ssize_t rg_get_fan_part_number(unsigned int fan_index, char *buf, size_t count)
{
    ssize_t ret;

    check_p(g_drv);
    check_p(g_drv->get_fan_part_number);

    ret = g_drv->get_fan_part_number(fan_index, buf, count);
    return ret;
}

/*
 * rg_get_fan_hardware_version - Used to get fan hardware version,
 * @fan_index: start with 1
 * @buf: Data receiving buffer
 * @count: length of buf
 *
 * This function returns the length of the filled buffer,
 * if not support this attributes filled "NA" to buf,
 * otherwise it returns a negative value on failed.
 */
static ssize_t rg_get_fan_hardware_version(unsigned int fan_index, char *buf, size_t count)
{
    ssize_t ret;

    check_p(g_drv);
    check_p(g_drv->get_fan_hardware_version);

    ret = g_drv->get_fan_hardware_version(fan_index, buf, count);
    return ret;
}

/*
 * rg_get_fan_status - Used to get fan status,
 * filled the value to buf, fan status define as below:
 * 0: ABSENT
 * 1: OK
 * 2: NOT OK
 *
 * @fan_index: start with 1
 * @buf: Data receiving buffer
 * @count: length of buf
 *
 * This function returns the length of the filled buffer,
 * if not support this attributes filled "NA" to buf,
 * otherwise it returns a negative value on failed.
 */
static ssize_t rg_get_fan_status(unsigned int fan_index, char *buf, size_t count)
{
    ssize_t ret;

    check_p(g_drv);
    check_p(g_drv->get_fan_status);

    ret = g_drv->get_fan_status(fan_index, buf, count);
    return ret;
}

/*
 * rg_get_fan_led_status - Used to get fan led status
 * filled the value to buf, led status value define as below:
 * 0: dark
 * 1: green
 * 2: yellow
 * 3: red
 * 4: blue
 * 5: green light flashing
 * 6: yellow light flashing
 * 7: red light flashing
 * 8: blue light flashing
 *
 * @fan_index: start with 1
 * @buf: Data receiving buffer
 * @count: length of buf
 *
 * This function returns the length of the filled buffer,
 * if not support this attributes filled "NA" to buf,
 * otherwise it returns a negative value on failed.
 */
static ssize_t rg_get_fan_led_status(unsigned int fan_index, char *buf, size_t count)
{
    ssize_t ret;

    check_p(g_drv);
    check_p(g_drv->get_fan_led_status);

    ret = g_drv->get_fan_led_status(fan_index, buf, count);
    return ret;
}

/*
 * rg_set_fan_led_status - Used to set fan led status
 * @fan_index: start with 1
 * @status: led status, led status value define as below:
 * 0: dark
 * 1: green
 * 2: yellow
 * 3: red
 * 4: blue
 * 5: green light flashing
 * 6: yellow light flashing
 * 7: red light flashing
 * 8: blue light flashing
 *
 * This function returns 0 on success,
 * otherwise it returns a negative value on failed.
 */
static int rg_set_fan_led_status(unsigned int fan_index, int status)
{
    int ret;

    check_p(g_drv);
    check_p(g_drv->set_fan_led_status);

    ret = g_drv->set_fan_led_status(fan_index, status);
    return ret;
}

/*
 * rg_get_fan_direction - Used to get fan air flow direction,
 * filled the value to buf, air flow direction define as below:
 * 0: F2B
 * 1: B2F
 *
 * @fan_index: start with 1
 * @buf: Data receiving buffer
 * @count: length of buf
 *
 * This function returns the length of the filled buffer,
 * if not support this attributes filled "NA" to buf,
 * otherwise it returns a negative value on failed.
 */
static ssize_t rg_get_fan_direction(unsigned int fan_index, char *buf, size_t count)
{
    ssize_t ret;

    check_p(g_drv);
    check_p(g_drv->get_fan_direction);

    ret = g_drv->get_fan_direction(fan_index, buf, count);
    return ret;
}

/*
 * rg_get_fan_motor_speed - Used to get fan motor speed
 * filled the value to buf
 * @fan_index: start with 1
 * @motor_index: start with 1
 * @buf: Data receiving buffer
 * @count: length of buf
 *
 * This function returns the length of the filled buffer,
 * if not support this attributes filled "NA" to buf,
 * otherwise it returns a negative value on failed.
 */
static ssize_t rg_get_fan_motor_speed(unsigned int fan_index, unsigned int motor_index,
                   char *buf, size_t count)
{
    ssize_t ret;

    check_p(g_drv);
    check_p(g_drv->get_fan_motor_speed);

    ret = g_drv->get_fan_motor_speed(fan_index, motor_index, buf, count);
    return ret;
}

/*
 * rg_get_fan_motor_speed_tolerance - Used to get fan motor speed tolerance
 * filled the value to buf
 * @fan_index: start with 1
 * @motor_index: start with 1
 * @buf: Data receiving buffer
 * @count: length of buf
 *
 * This function returns the length of the filled buffer,
 * if not support this attributes filled "NA" to buf,
 * otherwise it returns a negative value on failed.
 */
static ssize_t rg_get_fan_motor_speed_tolerance(unsigned int fan_index, unsigned int motor_index,
                   char *buf, size_t count)
{
    ssize_t ret;

    check_p(g_drv);
    check_p(g_drv->get_fan_motor_speed_tolerance);

    ret = g_drv->get_fan_motor_speed_tolerance(fan_index, motor_index, buf, count);
    return ret;
}

/*
 * rg_get_fan_motor_speed_target - Used to get fan motor speed target
 * filled the value to buf
 * @fan_index: start with 1
 * @motor_index: start with 1
 * @buf: Data receiving buffer
 * @count: length of buf
 *
 * This function returns the length of the filled buffer,
 * if not support this attributes filled "NA" to buf,
 * otherwise it returns a negative value on failed.
 */
static ssize_t rg_get_fan_motor_speed_target(unsigned int fan_index, unsigned int motor_index,
                   char *buf, size_t count)
{
    ssize_t ret;

    check_p(g_drv);
    check_p(g_drv->get_fan_motor_speed_target);

    ret = g_drv->get_fan_motor_speed_target(fan_index, motor_index, buf, count);
    return ret;
}

/*
 * rg_get_fan_motor_speed_max - Used to get the maximum threshold of fan motor
 * filled the value to buf
 * @fan_index: start with 1
 * @motor_index: start with 1
 * @buf: Data receiving buffer
 * @count: length of buf
 *
 * This function returns the length of the filled buffer,
 * if not support this attributes filled "NA" to buf,
 * otherwise it returns a negative value on failed.
 */
static ssize_t rg_get_fan_motor_speed_max(unsigned int fan_index, unsigned int motor_index,
                   char *buf, size_t count)
{
    ssize_t ret;

    check_p(g_drv);
    check_p(g_drv->get_fan_motor_speed_max);

    ret = g_drv->get_fan_motor_speed_max(fan_index, motor_index, buf, count);
    return ret;
}

/*
 * rg_get_fan_motor_speed_min - Used to get the minimum threshold of fan motor
 * filled the value to buf
 * @fan_index: start with 1
 * @motor_index: start with 1
 * @buf: Data receiving buffer
 * @count: length of buf
 *
 * This function returns the length of the filled buffer,
 * if not support this attributes filled "NA" to buf,
 * otherwise it returns a negative value on failed.
 */
static ssize_t rg_get_fan_motor_speed_min(unsigned int fan_index, unsigned int motor_index,
                   char *buf, size_t count)
{
    ssize_t ret;

    check_p(g_drv);
    check_p(g_drv->get_fan_motor_speed_min);

    ret = g_drv->get_fan_motor_speed_min(fan_index, motor_index, buf, count);
    return ret;
}

/*
 * rg_get_fan_ratio - Used to get the ratio of fan
 * filled the value to buf
 * @fan_index: start with 1
 * @buf: Data receiving buffer
 * @count: length of buf
 *
 * This function returns the length of the filled buffer,
 * if not support this attributes filled "NA" to buf,
 * otherwise it returns a negative value on failed.
 */
static ssize_t rg_get_fan_ratio(unsigned int fan_index, char *buf, size_t count)
{
    ssize_t ret;

    check_p(g_drv);
    check_p(g_drv->get_fan_ratio);

    ret = g_drv->get_fan_ratio(fan_index, buf, count);
    return ret;
}

/*
 * rg_set_fan_ratio - Used to set the ratio of fan
 * @fan_index: start with 1
 * @ratio: motor speed ratio, from 0 to 100
 *
 * This function returns 0 on success,
 * otherwise it returns a negative value on failed.
 */
static int rg_set_fan_ratio(unsigned int fan_index, int ratio)
{
    int ret;

    check_p(g_drv);
    check_p(g_drv->set_fan_ratio);

    ret = g_drv->set_fan_ratio(fan_index, ratio);
    return ret;
}
/****************************************end of fan*******************************************/

static struct s3ip_sysfs_fan_drivers_s drivers = {
    /*
     * set ODM fan drivers to /sys/s3ip/fan,
     * if not support the function, set corresponding hook to NULL.
     */
    .get_fan_number = rg_get_fan_number,
    .get_fan_motor_number = rg_get_fan_motor_number,
    .get_fan_model_name = rg_get_fan_model_name,
    .get_fan_serial_number = rg_get_fan_serial_number,
    .get_fan_part_number = rg_get_fan_part_number,
    .get_fan_hardware_version = rg_get_fan_hardware_version,
    .get_fan_status = rg_get_fan_status,
    .get_fan_led_status = rg_get_fan_led_status,
    .set_fan_led_status = rg_set_fan_led_status,
    .get_fan_direction = rg_get_fan_direction,
    .get_fan_motor_speed = rg_get_fan_motor_speed,
    .get_fan_motor_speed_tolerance = rg_get_fan_motor_speed_tolerance,
    .get_fan_motor_speed_target = rg_get_fan_motor_speed_target,
    .get_fan_motor_speed_max = rg_get_fan_motor_speed_max,
    .get_fan_motor_speed_min = rg_get_fan_motor_speed_min,
    .get_fan_ratio = rg_get_fan_ratio,
    .set_fan_ratio = rg_set_fan_ratio
};

static int __init fan_dev_drv_init(void)
{
    int ret;

    FAN_INFO("fan_init...\n");
    g_drv = switch_driver_get();
    check_p(g_drv);

    ret = s3ip_sysfs_fan_drivers_register(&drivers);
    if (ret < 0) {
        FAN_ERR("fan drivers register err, ret %d.\n", ret);
        return ret;
    }

    FAN_INFO("fan_init success.\n");
    return 0;
}

static void __exit fan_dev_drv_exit(void)
{
    s3ip_sysfs_fan_drivers_unregister();
    FAN_INFO("fan_exit success.\n");
    return;
}

module_init(fan_dev_drv_init);
module_exit(fan_dev_drv_exit);
module_param(g_loglevel, int, 0644);
MODULE_PARM_DESC(g_loglevel, "the log level(info=0x1, err=0x2, dbg=0x4, all=0xf).\n");
MODULE_LICENSE("GPL");
MODULE_AUTHOR("sonic S3IP sysfs");
MODULE_DESCRIPTION("fan device driver");
