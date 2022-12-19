/*
 * curr_sensor_device_driver.c
 *
 * This module realize /sys/s3ip/curr_sensor attributes read and write functions
 *
 * History
 *  [Version]                [Date]                    [Description]
 *   *  v1.0                2021-08-31                  S3IP sysfs
 */

#include <linux/slab.h>

#include "device_driver_common.h"
#include "curr_sensor_sysfs.h"
#include "dfd_sysfs_common.h"

#define CURR_SENSOR_INFO(fmt, args...) LOG_INFO("curr_sensor: ", fmt, ##args)
#define CURR_SENSOR_ERR(fmt, args...)  LOG_ERR("curr_sensor: ", fmt, ##args)
#define CURR_SENSOR_DBG(fmt, args...)  LOG_DBG("curr_sensor: ", fmt, ##args)

static int g_loglevel = 0;
static struct switch_drivers_s *g_drv = NULL;

/*************************************main board current***************************************/
static int rg_get_main_board_curr_number(void)
{
    int ret;

    check_p(g_drv);
    check_p(g_drv->get_main_board_curr_number);

    ret = g_drv->get_main_board_curr_number();
    return ret;
}

/*
 * rg_get_main_board_curr_alias - Used to identify the location of the current sensor,
 * @curr_index: start with 1
 * @buf: Data receiving buffer
 * @count: length of buf
 *
 * This function returns the length of the filled buffer,
 * if not support this attributes filled "NA" to buf,
 * otherwise it returns a negative value on failed.
 */
static ssize_t rg_get_main_board_curr_alias(unsigned int curr_index, char *buf, size_t count)
{
    ssize_t ret;

    check_p(g_drv);
    check_p(g_drv->get_main_board_curr_alias);

    ret = g_drv->get_main_board_curr_alias(curr_index, buf, count);
    return ret;
}

/*
 * rg_get_main_board_curr_type - Used to get the model of current sensor,
 * @curr_index: start with 1
 * @buf: Data receiving buffer
 * @count: length of buf
 *
 * This function returns the length of the filled buffer,
 * if not support this attributes filled "NA" to buf,
 * otherwise it returns a negative value on failed.
 */
static ssize_t rg_get_main_board_curr_type(unsigned int curr_index, char *buf, size_t count)
{
    ssize_t ret;

    check_p(g_drv);
    check_p(g_drv->get_main_board_curr_type);

    ret = g_drv->get_main_board_curr_type(curr_index, buf, count);
    return ret;
}

/*
 * rg_get_main_board_curr_max - Used to get the maximum threshold of current sensor
 * filled the value to buf, the value is integer with mA
 * @curr_index: start with 1
 * @buf: Data receiving buffer
 * @count: length of buf
 *
 * This function returns the length of the filled buffer,
 * if not support this attributes filled "NA" to buf,
 * otherwise it returns a negative value on failed.
 */
static ssize_t rg_get_main_board_curr_max(unsigned int curr_index, char *buf, size_t count)
{
    ssize_t ret;

    check_p(g_drv);
    check_p(g_drv->get_main_board_curr_max);

    ret = g_drv->get_main_board_curr_max(curr_index, buf, count);
    return ret;
}

/*
 * rg_get_main_board_curr_min - Used to get the minimum threshold of current sensor
 * filled the value to buf, the value is integer with mA
 * @curr_index: start with 1
 * @buf: Data receiving buffer
 * @count: length of buf
 *
 * This function returns the length of the filled buffer,
 * if not support this attributes filled "NA" to buf,
 * otherwise it returns a negative value on failed.
 */
static ssize_t rg_get_main_board_curr_min(unsigned int curr_index, char *buf, size_t count)
{
    ssize_t ret;

    check_p(g_drv);
    check_p(g_drv->get_main_board_curr_min);

    ret = g_drv->get_main_board_curr_min(curr_index, buf, count);
    return ret;
}

/*
 * rg_get_main_board_curr_value - Used to get the input value of current sensor
 * filled the value to buf, the value is integer with mA
 * @curr_index: start with 1
 * @buf: Data receiving buffer
 * @count: length of buf
 *
 * This function returns the length of the filled buffer,
 * otherwise it returns a negative value on failed.
 */
static ssize_t rg_get_main_board_curr_value(unsigned int curr_index, char *buf, size_t count)
{
    ssize_t ret;

    check_p(g_drv);
    check_p(g_drv->get_main_board_curr_value);

    ret = g_drv->get_main_board_curr_value(curr_index, buf, count);
    return ret;
}
/*********************************end of main board current************************************/

static struct s3ip_sysfs_curr_sensor_drivers_s drivers = {
    /*
     * set ODM current sensor drivers to /sys/s3ip/curr_sensor,
     * if not support the function, set corresponding hook to NULL.
     */
    .get_main_board_curr_number = rg_get_main_board_curr_number,
    .get_main_board_curr_alias = rg_get_main_board_curr_alias,
    .get_main_board_curr_type = rg_get_main_board_curr_type,
    .get_main_board_curr_max = rg_get_main_board_curr_max,
    .get_main_board_curr_min = rg_get_main_board_curr_min,
    .get_main_board_curr_value = rg_get_main_board_curr_value,
};

static int __init curr_sensor_dev_drv_init(void)
{
    int ret;

    CURR_SENSOR_INFO("curr_sensor_init...\n");
    g_drv = switch_driver_get();
    check_p(g_drv);

    ret = s3ip_sysfs_curr_sensor_drivers_register(&drivers);
    if (ret < 0) {
        CURR_SENSOR_ERR("curr sensor drivers register err, ret %d.\n", ret);
        return ret;
    }

    CURR_SENSOR_INFO("curr_sensor_init success.\n");
    return 0;
}

static void __exit curr_sensor_dev_drv_exit(void)
{
    s3ip_sysfs_curr_sensor_drivers_unregister();
    CURR_SENSOR_INFO("curr_sensor_exit success.\n");
    return;
}

module_init(curr_sensor_dev_drv_init);
module_exit(curr_sensor_dev_drv_exit);
module_param(g_loglevel, int, 0644);
MODULE_PARM_DESC(g_loglevel, "the log level(info=0x1, err=0x2, dbg=0x4, all=0xf).\n");
MODULE_LICENSE("GPL");
MODULE_AUTHOR("sonic S3IP sysfs");
MODULE_DESCRIPTION("current sensors device driver");
