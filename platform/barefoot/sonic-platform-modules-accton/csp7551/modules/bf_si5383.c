/****************************************************************************
 * Copyright 2022 Accton Corp.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 *	Description:
 *		This daemon is access SI5383 by smbus
 *
 *	First version: 2022/08/04
 *		   Author: Zhenling Yin
 ******************************************************************************/
#include <linux/module.h>
#include <linux/types.h>
#include <linux/errno.h>
#include <linux/string.h>
#include <linux/watchdog.h>
#include <linux/string.h>
#include <linux/kernel.h>
#include <linux/i2c.h>
#include <linux/mutex.h>
#include <linux/delay.h>

#include "bf_si5383.h"

#define WR_ADDR_MSB   0x20
#define WR_ADDR_LSB   0x21
#define WR_DATE0      0x22
#define WR_DATE1      0x23
#define WR_DATE2      0x24
#define WR_DATE3      0x25
#define WR_DATE4      0x26
#define WR_DATE5      0x27
#define WR_DATE6      0x28
#define WR_DATE7      0x29
#define WR_LENGTH_CMD 0x2A


#define RD_ADDR_MSB   0x30
#define RD_ADDR_LSB   0x31
#define RD_LENGTH_CMD 0x32
#define RD_DATE0      0x33
#define RD_DATE1      0x34
#define RD_DATE2      0x35
#define RD_DATE3      0x36
#define RD_DATE4      0x37
#define RD_DATE5      0x38
#define RD_DATE6      0x39
#define RD_DATE7      0x3A

#define DEV_READY     0xFE

#define SI5383_I2C_CHANNEL 34
#define SI5383_I2C_ADDRESS 0x6F

static int bf_si5383_ppb = 0;

/** si5383 device ready
  *
  *  @param reg
  *     register to access
  *  @param data
  *    data to read from reg
  *  @param data_len
  *    data length
  *  @return
  *    0 on success and any other value on error
  */
int bf_si5383_dev_rdy(bool *ready)
{
	struct fpga_access acc_i2c = {0};
	int ret = 0;

	acc_i2c.channel = SI5383_I2C_CHANNEL;
	acc_i2c.addr = SI5383_I2C_ADDRESS;
	acc_i2c.offset = DEV_READY;
	acc_i2c.length = 1;
	memset(acc_i2c.buff, 0, FPGA_BUFF_MAX);
	ret = i2c_device_read_by_fpga_smbus(acc_i2c);
	if(ret)
	{
		printk(KERN_ERR "read SI5383 DEV_READY failed!\r\n");
		return -1;
	}
	
	if(acc_i2c.buff[0] != 0x0F)
		*ready = false;
	else
		*ready = true;
	
	return 0;
}
EXPORT_SYMBOL_GPL(bf_si5383_dev_rdy);

/** si5383 i2c read
  *
  *  @param reg
  *     register to access
  *  @param data
  *    data to read from reg
  *  @param data_len
  *    data length
  *  @return
  *    0 on success and any other value on error
  */
int bf_si5383_i2c_rd(si5383_register_op_t cfg)
{
	struct fpga_access acc_i2c = {0};
	int index = 0;
	int retry = 0;
	int ret = 0;
	
	if(cfg.length > SI5383_RW_DATE_MAX)
	{
		printk(KERN_ERR "SI5383 read data length invalid!\r\n");
		return -1;
	}

	acc_i2c.channel = SI5383_I2C_CHANNEL;
	acc_i2c.addr = SI5383_I2C_ADDRESS;
	acc_i2c.offset = RD_ADDR_MSB;
	acc_i2c.length = 1;
	acc_i2c.buff[0] = (cfg.address >> 8) & 0xff;
	ret = i2c_device_write_by_fpga_smbus(acc_i2c);
	if(ret)
	{
		printk(KERN_ERR "write SI5383 RD_ADDR_MSB failed!\r\n");
		return -1;
	}
	
	acc_i2c.channel = SI5383_I2C_CHANNEL;
	acc_i2c.addr = SI5383_I2C_ADDRESS;
	acc_i2c.offset = RD_ADDR_LSB;
	acc_i2c.length = 1;
	acc_i2c.buff[0] = cfg.address & 0xff;
	ret = i2c_device_write_by_fpga_smbus(acc_i2c);
	if(ret)
	{
		printk(KERN_ERR "write SI5383 RD_ADDR_LSB failed!\r\n");
		return -1;
	}
	
	acc_i2c.channel = SI5383_I2C_CHANNEL;
	acc_i2c.addr = SI5383_I2C_ADDRESS;
	acc_i2c.offset = RD_LENGTH_CMD;
	acc_i2c.length = 1;
	acc_i2c.buff[0] = (cfg.length - 1) << 4 | 0x01;
	ret = i2c_device_write_by_fpga_smbus(acc_i2c);
	if(ret)
	{
		printk(KERN_ERR "write SI5383 RD_LENGTH_CMD failed!\r\n");
		return -1;
	}
	
	retry = 10;
	while(retry)
	{
		memset(acc_i2c.buff, 0, FPGA_BUFF_MAX);
		ret = i2c_device_read_by_fpga_smbus(acc_i2c);
		if((ret == 0) && ((acc_i2c.buff[0] & 0x01) == 0x00))
			break;
		retry--;
		msleep(5);
	}
	
	if((retry == 0) && ((acc_i2c.buff[0] & 0x01) != 0x00))
	{
		printk(KERN_ERR "SI5383 RD_CMD status read failed or error!\r\n");
		return -1;
	}
	
	acc_i2c.channel = SI5383_I2C_CHANNEL;
	acc_i2c.addr = SI5383_I2C_ADDRESS;
	//acc_i2c.offset = RD_DATE0;
	acc_i2c.length = 1;
	memset(acc_i2c.buff, 0, FPGA_BUFF_MAX);
	for(index = 0; index < cfg.length; index++)
	{
		acc_i2c.offset = RD_DATE0 + index;
		ret = i2c_device_read_by_fpga_smbus(acc_i2c);
		if(ret)
		{
			printk(KERN_ERR "SI5383 RD_DATE register read %d failed!\r\n", (RD_DATE0+index));
			return -1;
		}
		cfg.value[index] = acc_i2c.buff[0];
	}
	
    return 0;
}
EXPORT_SYMBOL_GPL(bf_si5383_i2c_rd);

/** si5383 i2c write
 *
 *  @param chip_id
 *    chip_id
 *  @param reg
 *     register to access
 *  @param data
 *    data to write to reg
 *  @return
 *    0 on success and any other value on error
 */
int bf_si5383_i2c_wr(si5383_register_op_t cfg)
{
	struct fpga_access acc_i2c = {0};
	int index = 0;
	int retry = 0;
	int ret = 0;
	
	if(cfg.length > SI5383_RW_DATE_MAX)
	{
		printk(KERN_ERR "SI5383 write data length invalid!\r\n");
		return -1;
	}
	
	acc_i2c.channel = SI5383_I2C_CHANNEL;
	acc_i2c.addr = SI5383_I2C_ADDRESS;
	acc_i2c.offset = WR_ADDR_MSB;
	acc_i2c.length = 1;
	acc_i2c.buff[0] = (cfg.address >> 8) & 0xff;
	ret = i2c_device_write_by_fpga_smbus(acc_i2c);
	if(ret)
	{
		printk(KERN_ERR "write SI5383 WR_ADDR_MSB failed!\r\n");
		return -1;
	}

	acc_i2c.channel = SI5383_I2C_CHANNEL;
	acc_i2c.addr = SI5383_I2C_ADDRESS;
	acc_i2c.offset = WR_ADDR_LSB;
	acc_i2c.length = 1;
	acc_i2c.buff[0] = cfg.address & 0xff;
	ret = i2c_device_write_by_fpga_smbus(acc_i2c);
	if(ret)
	{
		printk(KERN_ERR "write SI5383 WR_ADDR_LSB failed!\r\n");
		return -1;
	}
	
	acc_i2c.channel = SI5383_I2C_CHANNEL;
	acc_i2c.addr = SI5383_I2C_ADDRESS;
	//acc_i2c.offset = WR_DATE0;
	acc_i2c.length = 1;
	memset(acc_i2c.buff, 0, FPGA_BUFF_MAX);
	for(index = 0; index < cfg.length; index++)
	{
		acc_i2c.offset = WR_DATE0 + index;
		acc_i2c.buff[0] = cfg.value[index];
		ret = i2c_device_write_by_fpga_smbus(acc_i2c);
		if(ret)
		{
			printk(KERN_ERR "SI5383 WR_DATE register write %d failed!\r\n", (WR_DATE0+index));
			return -1;
		}
	}
	
	acc_i2c.channel = SI5383_I2C_CHANNEL;
	acc_i2c.addr = SI5383_I2C_ADDRESS;
	acc_i2c.offset = WR_LENGTH_CMD;
	acc_i2c.length = 1;
	acc_i2c.buff[0] = (cfg.length - 1) << 4 | 0x01;
	ret = i2c_device_write_by_fpga_smbus(acc_i2c);
	if(ret)
	{
		printk(KERN_ERR "write SI5383 WR_LENGTH_CMD failed!\r\n");
		return -1;
	}

	retry = 10;
	while(retry)
	{
		memset(acc_i2c.buff, 0, FPGA_BUFF_MAX);
		ret = i2c_device_read_by_fpga_smbus(acc_i2c);
		if((ret == 0) && ((acc_i2c.buff[0] & 0x01) == 0x00))
			break;
		retry--;
		msleep(5);
	}
	
	if((retry == 0) && ((acc_i2c.buff[0] & 0x01) != 0x00))
	{
		printk(KERN_ERR "SI5383 WR_CMD status read failed or error!\r\n");
		return -1;
	}
	
	return 0;
}
EXPORT_SYMBOL_GPL(bf_si5383_i2c_wr);

/** si5383 ppb set
 *
 *  @param chip_id
 *    chip_id
 *  @param ppb
 *    ppb to set
 *  @return
 *    0 on success and any other value on error
 */
int bf_si5383_ppb_set(int ppb)
{
	si5383_register_op_t ppb_cfg = {0};
	int diff = 0;
	int i;

	// 5383 max range +10ppm to -10ppm = +10000ppb to -10000ppb
	if((bf_si5383_ppb+ppb) < -10000 || (bf_si5383_ppb+ppb) > 10000)
	{
		printk(KERN_ERR "SI5383 ppb adjust out of range!\r\n");
		return -1;
	}
	
	ppb_cfg.address = 0x001D;
	ppb_cfg.length = 1;
	memset(ppb_cfg.value, 0, SI5383_RW_DATE_MAX);

	if(ppb > 0)
	{
		diff = ppb;
		ppb_cfg.value[0] = 1;
		for(i = 0; i < diff; i++)
		{
			if(bf_si5383_i2c_wr(ppb_cfg))
			{
				bf_si5383_ppb += i;
				printk(KERN_ERR "SI5383 ppb adjust fail!\r\n");
				return -1;
			}
		}
	}
	else
	{
		diff = -(ppb);
		ppb_cfg.value[0] = 2;
		for(i = 0; i < diff; i++)
		{
			if(bf_si5383_i2c_wr(ppb_cfg))
			{
				bf_si5383_ppb -= i;
				printk(KERN_ERR "SI5383 ppb adjust fail!\r\n");
				return -1;
			}
		}
	}
	
	bf_si5383_ppb += ppb;
	return 0;
}
EXPORT_SYMBOL_GPL(bf_si5383_ppb_set);

/** si5383 ppb get
 *
 *  @param chip_id
 *    chip_id
 *  @param ppb
 *    return ppb
 *  @return
 *    0 on success and any other value on error
 */
int bf_si5383_ppb_get(int *ppb)
{
	*ppb = bf_si5383_ppb;
	return 0;
}
EXPORT_SYMBOL_GPL(bf_si5383_ppb_get);

MODULE_LICENSE("GPL");
