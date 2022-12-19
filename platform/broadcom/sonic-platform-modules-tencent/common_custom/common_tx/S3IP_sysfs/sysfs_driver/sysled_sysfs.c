/*
 * sysled_sysfs.c
 *
 * This module create sysled kobjects and attributes in /sys/s3ip/sysled
 *
 * History
 *  [Version]                [Date]                    [Description]
 *   *  v1.0                2021-08-31                  S3IP sysfs
 */

#include <linux/slab.h>

#include "switch.h"
#include "sysled_sysfs.h"

static int g_sysled_loglevel = 0;

#define SYSLED_INFO(fmt, args...) do {                                        \
    if (g_sysled_loglevel & INFO) { \
        printk(KERN_INFO "[SYSLED_SYSFS][func:%s line:%d]\n"fmt, __func__, __LINE__, ## args); \
    } \
} while (0)

#define SYSLED_ERR(fmt, args...) do {                                        \
    if (g_sysled_loglevel & ERR) { \
        printk(KERN_ERR "[SYSLED_SYSFS][func:%s line:%d]\n"fmt, __func__, __LINE__, ## args); \
    } \
} while (0)

#define SYSLED_DBG(fmt, args...) do {                                        \
    if (g_sysled_loglevel & DBG) { \
        printk(KERN_DEBUG "[SYSLED_SYSFS][func:%s line:%d]\n"fmt, __func__, __LINE__, ## args); \
    } \
} while (0)

static struct switch_obj *g_sysled_obj = NULL;
static struct s3ip_sysfs_sysled_drivers_s *g_sysled_drv = NULL;

static ssize_t sys_led_status_show(struct switch_obj *obj, struct switch_attribute *attr, char *buf)
{
    int ret;

    check_p(g_sysled_drv);
    check_p(g_sysled_drv->get_sys_led_status);

    ret = g_sysled_drv->get_sys_led_status(buf, PAGE_SIZE);
    if (ret < 0) {
        SYSLED_ERR("get sys led status failed, ret: %d:\n", ret);
        return (ssize_t)snprintf(buf, PAGE_SIZE, "%s\n", SYSFS_DEV_ERROR);
    }
    SYSLED_DBG("get sys led status success:\n");
    return ret;
}

static ssize_t sys_led_status_store(struct switch_obj *obj, struct switch_attribute *attr,
                   const char *buf, size_t count)
{
    int ret, value;

    check_p(g_sysled_drv);
    check_p(g_sysled_drv->set_sys_led_status);

    sscanf(buf, "%d", &value);
    if (value < 0) {
        SYSLED_ERR("invaild led status value: %d, can't set sys led status\n", value);
        return -EINVAL;
    }
    ret = g_sysled_drv->set_sys_led_status(value);
    if (ret < 0) {
        SYSLED_ERR("set sys led status %d faield, ret: %d\n", value, ret);
        return -EIO;
    }
    SYSLED_DBG("set sys led status %d success\n", value);
    return count;
}

static ssize_t bmc_led_status_show(struct switch_obj *obj, struct switch_attribute *attr, char *buf)
{
    int ret;

    check_p(g_sysled_drv);
    check_p(g_sysled_drv->get_bmc_led_status);

    ret = g_sysled_drv->get_bmc_led_status(buf, PAGE_SIZE);
    if (ret < 0) {
        SYSLED_ERR("get bmc led status failed, ret: %d:\n", ret);
        return (ssize_t)snprintf(buf, PAGE_SIZE, "%s\n", SYSFS_DEV_ERROR);
    }
    SYSLED_DBG("get bmc led status success:\n");
    return ret;
}

static ssize_t bmc_led_status_store(struct switch_obj *obj, struct switch_attribute *attr,
                   const char *buf, size_t count)
{
    int ret, value;

    check_p(g_sysled_drv);
    check_p(g_sysled_drv->set_bmc_led_status);

    sscanf(buf, "%d", &value);
    if (value < 0) {
        SYSLED_ERR("invaild led status value: %d, can't set bmc led status\n", value);
        return -EINVAL;
    }
    ret = g_sysled_drv->set_bmc_led_status(value);
    if (ret < 0) {
        SYSLED_ERR("set bmc led status %d faield, ret: %d\n", value, ret);
        return -EIO;
    }
    SYSLED_DBG("set bmc led status %d success\n", value);
    return count;
}

static ssize_t sys_fan_led_status_show(struct switch_obj *obj, struct switch_attribute *attr, char *buf)
{
    int ret;

    check_p(g_sysled_drv);
    check_p(g_sysled_drv->get_sys_fan_led_status);

    ret = g_sysled_drv->get_sys_fan_led_status(buf, PAGE_SIZE);
    if (ret < 0) {
        SYSLED_ERR("get sys fan led status failed, ret: %d:\n", ret);
        return (ssize_t)snprintf(buf, PAGE_SIZE, "%s\n", SYSFS_DEV_ERROR);
    }
    SYSLED_DBG("get sys fan led status success:\n");
    return ret;
}

static ssize_t sys_fan_led_status_store(struct switch_obj *obj, struct switch_attribute *attr,
                   const char *buf, size_t count)
{
    int ret, value;

    check_p(g_sysled_drv);
    check_p(g_sysled_drv->set_sys_fan_led_status);

    sscanf(buf, "%d", &value);
    if (value < 0) {
        SYSLED_ERR("invaild led status value: %d, can't set sys fan led status\n", value);
        return -EINVAL;
    }
    ret = g_sysled_drv->set_sys_fan_led_status(value);
    if (ret < 0) {
        SYSLED_ERR("set sys fan led status %d faield, ret: %d\n", value, ret);
        return -EIO;
    }
    SYSLED_DBG("set sys fan led status %d success\n", value);
    return count;
}

static ssize_t sys_psu_led_status_show(struct switch_obj *obj, struct switch_attribute *attr, char *buf)
{
    int ret;

    check_p(g_sysled_drv);
    check_p(g_sysled_drv->get_sys_psu_led_status);

    ret = g_sysled_drv->get_sys_psu_led_status(buf, PAGE_SIZE);
    if (ret < 0) {
        SYSLED_ERR("get sys psu led status failed, ret: %d:\n", ret);
        return (ssize_t)snprintf(buf, PAGE_SIZE, "%s\n", SYSFS_DEV_ERROR);
    }
    SYSLED_DBG("get sys psu led status success:\n");
    return ret;
}

static ssize_t sys_psu_led_status_store(struct switch_obj *obj, struct switch_attribute *attr,
                   const char *buf, size_t count)
{
    int ret, value;

    check_p(g_sysled_drv);
    check_p(g_sysled_drv->set_sys_psu_led_status);

    sscanf(buf, "%d", &value);
    if (value < 0) {
        SYSLED_ERR("invaild led status value: %d, can't set sys psu led status\n", value);
        return -EINVAL;
    }
    ret = g_sysled_drv->set_sys_psu_led_status(value);
    if (ret < 0) {
        SYSLED_ERR("set sys psu led status %d faield, ret: %d\n", value, ret);
        return -EIO;
    }
    SYSLED_DBG("set sys psu led status %d success\n", value);
    return count;
}

static ssize_t id_led_status_show(struct switch_obj *obj, struct switch_attribute *attr, char *buf)
{
    int ret;

    check_p(g_sysled_drv);
    check_p(g_sysled_drv->get_id_led_status);

    ret = g_sysled_drv->get_id_led_status(buf, PAGE_SIZE);
    if (ret < 0) {
        SYSLED_ERR("get id led status failed, ret: %d:\n", ret);
        return (ssize_t)snprintf(buf, PAGE_SIZE, "%s\n", SYSFS_DEV_ERROR);
    }
    SYSLED_DBG("get id led status success:\n");
    return ret;
}

static ssize_t id_led_status_store(struct switch_obj *obj, struct switch_attribute *attr,
                   const char *buf, size_t count)
{
    int ret, value;

    check_p(g_sysled_drv);
    check_p(g_sysled_drv->set_id_led_status);

    sscanf(buf, "%d", &value);
    if (value < 0) {
        SYSLED_ERR("invaild led status value: %d, can't set id led status\n", value);
        return -EINVAL;
    }
    ret = g_sysled_drv->set_id_led_status(value);
    if (ret < 0) {
        SYSLED_ERR("set id led status %d faield, ret: %d\n", value, ret);
        return -EIO;
    }
    SYSLED_DBG("set id led status %d success\n", value);
    return count;
}

/************************************syseeprom dir and attrs*******************************************/
static struct switch_attribute sys_led_attr = __ATTR(sys_led_status, S_IRUGO | S_IWUSR, sys_led_status_show, sys_led_status_store);
static struct switch_attribute bmc_led_attr = __ATTR(bmc_led_status, S_IRUGO | S_IWUSR, bmc_led_status_show, bmc_led_status_store);
static struct switch_attribute fan_led_attr = __ATTR(fan_led_status, S_IRUGO | S_IWUSR, sys_fan_led_status_show, sys_fan_led_status_store);
static struct switch_attribute psu_led_attr = __ATTR(psu_led_status, S_IRUGO | S_IWUSR, sys_psu_led_status_show, sys_psu_led_status_store);
static struct switch_attribute id_led_attr = __ATTR(id_led_status, S_IRUGO | S_IWUSR, id_led_status_show, id_led_status_store);

static struct attribute *sysled_dir_attrs[] = {
    &sys_led_attr.attr,
    &bmc_led_attr.attr,
    &fan_led_attr.attr,
    &psu_led_attr.attr,
    &id_led_attr.attr,
    NULL,
};

static struct attribute_group sysled_attr_group = {
    .attrs = sysled_dir_attrs,
};

/* create syseled directory and attributes*/
static int sysled_root_create(void)
{
    g_sysled_obj = switch_kobject_create("sysled", NULL);
    if (!g_sysled_obj) {
        SYSLED_ERR("switch_kobject_create sysled error!\n");
        return -ENOMEM;
    }

    if (sysfs_create_group(&g_sysled_obj->kobj, &sysled_attr_group) != 0) {
        switch_kobject_delete(&g_sysled_obj);
        SYSLED_ERR("create sysled dir attrs error!\n");
        return -EBADRQC;
    }

    return 0;
}

/* delete syseled directory and attributes*/
static void sysled_root_remove(void)
{
    if (g_sysled_obj) {
        sysfs_remove_group(&g_sysled_obj->kobj, &sysled_attr_group);
        switch_kobject_delete(&g_sysled_obj);
    }

    return;
}

int s3ip_sysfs_sysled_drivers_register(struct s3ip_sysfs_sysled_drivers_s *drv)
{
    int ret;

    SYSLED_INFO("s3ip_sysfs_sysled_drivers_register...\n");
    if (g_sysled_drv) {
        SYSLED_ERR("g_sysled_drv is not NULL, can't register\n");
        return -EPERM;
    }

    check_p(drv);
    g_sysled_drv = drv;

    ret = sysled_root_create();
    if (ret < 0) {
        SYSLED_ERR("sysled create error.\n");
        g_sysled_drv = NULL;
        return ret;
    }
    SYSLED_INFO("s3ip_sysfs_sysled_drivers_register success\n");
    return 0;
}

void s3ip_sysfs_sysled_drivers_unregister(void)
{
    if (g_sysled_drv) {
        sysled_root_remove();
        g_sysled_drv = NULL;
        SYSLED_DBG("s3ip_sysfs_sysled_drivers_unregister success.\n");
    }
    return;
}

EXPORT_SYMBOL(s3ip_sysfs_sysled_drivers_register);
EXPORT_SYMBOL(s3ip_sysfs_sysled_drivers_unregister);
module_param(g_sysled_loglevel, int, 0644);
MODULE_PARM_DESC(g_sysled_loglevel, "the log level(info=0x1, err=0x2, dbg=0x4).\n");
