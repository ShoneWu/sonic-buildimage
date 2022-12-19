/*
 * Copyright(C) 2001-2012 Ruijie Network. All rights reserved.
 */
/*
 * rg_plat_sff.c
 * Original Author: sonic_rd@ruijie.com.cn 2020-02-17
 *
 * This module create sff kobjects and attributes in /sys/rg_plat/xcvr
 *
 * History
 *  [Version]        [Author]                   [Date]            [Description]
 *   *  v1.0    sonic_rd@ruijie.com.cn         2020-02-17          Initial version
 */

#include <linux/slab.h>

#include "./include/rg_plat_switch.h"
#include "./include/rg_sysfs_common.h"

#define SFF_INFO(fmt, args...) LOG_INFO("sff: ", fmt, ##args)
#define SFF_ERR(fmt, args...)  LOG_ERR("sff: ", fmt, ##args)
#define SFF_DBG(fmt, args...)  LOG_DBG("sff: ", fmt, ##args)

struct sff_obj_t{
    struct switch_obj *sff_obj;
    struct bin_attribute bin;
    int sff_creat_bin_flag;
};

struct sff_t{
    unsigned int sff_number;
    struct sff_obj_t *sff;
};

static int g_loglevel = 0;
static struct sff_t g_sff;
static struct switch_obj *g_sff_obj = NULL;
static struct switch_drivers_t *g_drv = NULL;

static ssize_t sff_cpld_info_show(struct switch_obj *obj, struct switch_attribute *attr, char *buf)
{
    unsigned int sff_index;
    int ret;
    struct switch_device_attribute *sff_cpld_attr;

    check_p(g_drv);
    check_p(g_drv->get_sff_cpld_info);

    sff_index = obj->index;
    sff_cpld_attr = to_switch_device_attr(attr);
    check_p(sff_cpld_attr);
    SFF_DBG("sff_cpld_info_show, sff index:0x%x, sff cpld attr type:0x%x\n", sff_index, sff_cpld_attr->type);
    ret = g_drv->get_sff_cpld_info(sff_index, sff_cpld_attr->type, buf, PAGE_SIZE);
    if(ret < 0) {
        SFF_ERR("sff_cpld_info_show error. sff index:0x%x, sff cpld attr type:0x%x, ret:%d\n",
            sff_index, sff_cpld_attr->type,ret );
        return (ssize_t)snprintf(buf, PAGE_SIZE, "%s\n", RG_SYSFS_DEV_ERROR);
    }
    SFF_DBG("sff_cpld_info_show ok. sff index:0x%x, sff cpld attr type:0x%x, ret:%d\n", sff_index, sff_cpld_attr->type, ret);
    return ret;
}

static ssize_t sff_polling_read(struct file *filp, struct kobject *kobj, struct bin_attribute *attr,
                   char *buf, loff_t offset, size_t count)
{
    struct switch_obj *sff_obj;
    ssize_t rd_len;
    unsigned int sff_index;

    check_p(g_drv);
    check_p(g_drv->get_sff_polling_data);

    sff_obj = to_switch_obj(kobj);
    sff_index = sff_obj->index;

    memset(buf, 0, count);

    rd_len = g_drv->get_sff_polling_data(sff_index, buf, offset, count);
    if (rd_len < 0) {
        SFF_ERR("sff_polling_read error. sff index:%u, offset:0x%llx, read len:%lu, ret:%ld.\n",
            sff_index, offset,count, rd_len);
        return -EIO;
    }

    SFF_DBG("sff_polling_read, sff index:%u, offset:0x%llx, read len:%lu, really read len:%ld.\n",
        sff_index, offset, count, rd_len);

    return rd_len;
}

#if 0
static ssize_t sff_cpld_info_store(struct switch_obj *obj, struct switch_attribute *attr,
                                    const char* buf, size_t count)
{
    unsigned int sff_index;
    int ret, value;
    struct switch_device_attribute *sff_cpld_attr;

    check_p(g_drv);
    check_p(g_drv->set_sff_cpld_info);

    sscanf(buf, "%d", &value);
    if (value < 0 || value > 1) {
        SFF_DBG(" invalid value:%d, can't set.\n", value);
        return -EINVAL;
    }

    sff_index = obj->index;
    sff_cpld_attr = to_switch_device_attr(attr);
    check_p(sff_cpld_attr);
    SFF_DBG("sff_cpld_info_show, sff index:%d, sff cpld attr type:0x%x, set value:%d.\n", sff_index, sff_cpld_attr->type, value);

    ret = g_drv->set_sff_cpld_info(sff_index, sff_cpld_attr->type, value);
    if(ret < 0) {
        SFF_DBG("can not set cpld register = %d. sff index:%d, sff cpld attr type:0x%x,\n", value, sff_index, sff_cpld_attr->type);
        return -EIO;
    }

    return count;
}
#endif

static ssize_t sff_number_show(struct switch_obj *obj, struct switch_attribute *attr, char *buf)
{
    return (ssize_t)snprintf(buf, PAGE_SIZE, "%d\n", g_sff.sff_number);
}

/************************************sff attrs*******************************************/
static struct switch_attribute sff_number_att = __ATTR(num_sffs, S_IRUGO, sff_number_show, NULL);
static SWITCH_DEVICE_ATTR(present, S_IRUGO, sff_cpld_info_show, NULL, RG_SFF_MODULE_PRESENT);

/*******************************xcvr dir and attrs*******************************************/
static struct attribute *xcvr_dir_attrs[] = {
    &sff_number_att.attr,
    NULL,
};

static struct attribute_group sff_xcvr_attr_group = {
    .attrs = xcvr_dir_attrs,
};

/*******************************sff dir and attrs*******************************************/
static struct attribute *sff_attrs[] = {
    &switch_dev_attr_present.switch_attr.attr,
    NULL,
};

static struct attribute_group sff_attr_group = {
    .attrs = sff_attrs,
};

static int sff_sub_single_create_attrs(unsigned int index)
{
    struct sff_obj_t * curr_sff;

    curr_sff = &g_sff.sff[index-1];
    if (sysfs_create_group(&curr_sff->sff_obj->kobj, &sff_attr_group) != 0) {
        rg_plat_kobject_delete(&curr_sff->sff_obj);
        return -EBADRQC;
    }

    return 0;
}

static int sff_sub_single_create_kobj(struct kobject *parent, unsigned int index)
{
    struct sff_obj_t * curr_sff;
    char sff_dir_name[DIR_NAME_MAX_LEN];
    int ret;

    check_p(g_drv->get_sff_dir_name);
    ret = g_drv->get_sff_dir_name(index, sff_dir_name, sizeof(sff_dir_name));
    if (ret < 0) {
        SFF_ERR("sff index:%d, get sff dir name error. please check sff config.\n", index);
        return -ENOSYS;
    }

    curr_sff = &g_sff.sff[index-1];

    curr_sff->sff_obj = rg_plat_kobject_create(sff_dir_name, parent);
    if (!curr_sff->sff_obj) {
        SFF_ERR("sff index:%d, create %s object error! \n", index, sff_dir_name);
        return -EBADRQC;
    }

    SFF_DBG("create sff kobj ok. sff index:%d, dir name:%s\n",index, sff_dir_name);
    curr_sff->sff_obj->index = index;

    return 0;
}

static void sff_sub_single_remove_kobj_and_attrs(unsigned int index)
{
    struct sff_obj_t * curr_sff;

    curr_sff = &g_sff.sff[index-1];
    /* remove sff dir and attr */
    if (curr_sff->sff_obj) {
        SFF_DBG("delete sff%d attrs.\n", curr_sff->sff_obj->index);
        curr_sff->sff_obj->index = 0;
        if (curr_sff->sff_creat_bin_flag) {
            sysfs_remove_bin_file(&curr_sff->sff_obj->kobj, &curr_sff->bin);
        }
        sysfs_remove_group(&curr_sff->sff_obj->kobj, &sff_attr_group);
        rg_plat_kobject_delete(&curr_sff->sff_obj);
    }

    return;
}

static int sff_sub_single_create_eeprom_attrs(unsigned int index)
{
    int ret, eeprom_size;
    struct sff_obj_t * curr_sff;

    check_p(g_drv->get_sff_polling_size);

    eeprom_size = g_drv->get_sff_polling_size();
    if (eeprom_size < 0) {
        SFF_INFO("sff index:%u, don't support sff polling, ret:%d.\n", index, eeprom_size);
        return 0;
    }

    curr_sff = &g_sff.sff[index-1];

    sysfs_bin_attr_init(&curr_sff->bin);
    curr_sff->bin.attr.name = "eeprom";
    curr_sff->bin.attr.mode = 0444;
    curr_sff->bin.read = sff_polling_read;
    curr_sff->bin.size = eeprom_size;

    ret = sysfs_create_bin_file(&curr_sff->sff_obj->kobj, &curr_sff->bin);
    if (ret) {
        SFF_ERR("sff index:%d, create eeprom bin error, ret:%d. \n", index, ret);
        sysfs_remove_group(&curr_sff->sff_obj->kobj, &sff_attr_group);
        rg_plat_kobject_delete(&curr_sff->sff_obj);
        return -EBADRQC;
    }

    SFF_DBG("sff index:%u, create bin file success, eeprom size:%d.\n", index, eeprom_size);
    curr_sff->sff_creat_bin_flag = 1;

    return 0;
}

static int sff_sub_single_create_kobj_and_attrs(struct kobject *parent, unsigned int index)
{
    int ret;

    ret = sff_sub_single_create_kobj(parent, index);
    if (ret < 0) {
        SFF_ERR("sff index:%d, create sff dir error.\n", index);
        return ret;
    }

    ret = sff_sub_single_create_attrs(index);
    if (ret < 0) {
        SFF_ERR("sff index:%d, create sff attr error.\n", index);
        return ret;
    }

    ret = sff_sub_single_create_eeprom_attrs(index);

    return ret;
}

static int sff_sub_create_kobj_and_attrs(struct kobject *parent, int sff_num)
{
    unsigned int sff_index, i;

    g_sff.sff = kzalloc(sizeof(struct sff_obj_t) * sff_num, GFP_KERNEL);
    if (!g_sff.sff) {
        SFF_ERR("kzalloc g_sff.sff error, sff number = %d.\n", sff_num);
        return -ENOMEM;
    }

    for (sff_index = 1; sff_index <= sff_num; sff_index++) {
        if (sff_sub_single_create_kobj_and_attrs(parent, sff_index) != 0 ) {
            goto error;
        }
    }
    return 0;
error:
    for (i = 1; i < sff_index; i++) {
        sff_sub_single_remove_kobj_and_attrs(i);
    }
    if (g_sff.sff) {
        kfree(g_sff.sff);
        g_sff.sff = NULL;
    }
    return -EBADRQC;
}

static int sff_sub_create(void)
{
    int ret, sff_num;

    check_p(g_drv->get_dev_number);
    sff_num = g_drv->get_dev_number(RG_MAIN_DEV_SFF, RG_MINOR_DEV_NONE);
    g_sff.sff_number = sff_num;
    if (sff_num <= 0) {
        SFF_ERR("ERROR. port number:%d\n", sff_num);
        return -EINVAL;
    }

    ret = sff_sub_create_kobj_and_attrs(&g_sff_obj->kobj, sff_num);

    return ret;
}

static void sff_sub_remove(void)
{
    unsigned int sff_index;

    if (g_sff.sff) {
       for (sff_index = 1; sff_index <= g_sff.sff_number; sff_index++) {
           sff_sub_single_remove_kobj_and_attrs(sff_index);
       }
       kfree(g_sff.sff);
    }
    memset(&g_sff, 0, sizeof(struct sff_t));
    return ;
}

static int sff_xcvr_create(void)
{
    g_sff_obj = rg_plat_kobject_create(RG_SFF_SYSFS_NAME, NULL);
    if (!g_sff_obj) {
        return -ENOMEM;
    }

    g_sff_obj->index = 0;
    if (sysfs_create_group(&g_sff_obj->kobj, &sff_xcvr_attr_group) != 0) {
        rg_plat_kobject_delete(&g_sff_obj);
        SFF_ERR("create sff dir attrs error!\n");
        return -EBADRQC;
    }
    return 0;
}

static void sff_xcvr_remove(void)
{
    if (g_sff_obj) {
        sysfs_remove_group(&g_sff_obj->kobj, &sff_xcvr_attr_group);
        rg_plat_kobject_delete(&g_sff_obj);
    }

    return ;
}

static int rg_sff_init(void)
{
    int ret;

    SFF_INFO("rg_sff_init...\n");
    g_drv = dfd_plat_driver_get();
    check_p(g_drv);

    ret = sff_xcvr_create();
    if (ret < 0) {
        goto sff_root_error;
    }

    ret = sff_sub_create();
    if (ret < 0) {
        goto sff_sub_error;
    }
    SFF_INFO("rg_sff_init ok.\n");
    return 0;

sff_sub_error:
    sff_xcvr_remove();
sff_root_error:
    return ret;
}

static void rg_sff_exit(void)
{
    sff_sub_remove();
    sff_xcvr_remove();
    SFF_INFO("rg_sff_exit ok.\n");
    return ;
}

module_init(rg_sff_init);
module_exit(rg_sff_exit);
module_param(g_loglevel, int, 0644);
MODULE_PARM_DESC(g_loglevel, "the log level(info=0x1, err=0x2, dbg=0x4).\n");
MODULE_LICENSE("GPL");
MODULE_AUTHOR("sonic_rd <sonic_rd@ruijie.com.cn>");
MODULE_DESCRIPTION("RUIJIE sff sysfs driver");
