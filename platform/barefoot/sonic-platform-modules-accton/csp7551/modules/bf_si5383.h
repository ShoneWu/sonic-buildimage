
#define SI5383_RW_DATE_MAX  8
#define FPGA_BUFF_MAX       256

typedef struct {
    unsigned int address;                     /* 16-bit register address */
    unsigned char value[SI5383_RW_DATE_MAX];  /* 8-bit register data */
    unsigned char length;                     /* data length*/
} si5383_register_op_t;

struct fpga_access {
    unsigned char   addr;       /* 0x0 - 0x7F */
    unsigned char   offset;
    unsigned char   length;
    unsigned char   channel;
    /* intput output buff */
    unsigned char   buff[FPGA_BUFF_MAX];
};

/*******************************************************************************
* DESCRIPTION:
*   get si5383 device ready status
* INPUTS:
*   none
* OUTPUTS:
*	ready：true or false
* RETURNS:
*   OK,  success
*   <0,  fail
*******************************************************************************/
extern int bf_si5383_dev_rdy(bool *ready);


/*******************************************************************************
* DESCRIPTION:
*   read si5383 register value by smbus
* INPUTS:
*   cfg.address : register address
*   cfg.length  : read data length
* OUTPUTS:
*	cfg.value   ：register value
* RETURNS:
*   OK,  success
*   <0,  fail
*******************************************************************************/
extern int bf_si5383_i2c_rd(si5383_register_op_t cfg);


/*******************************************************************************
* DESCRIPTION:
*   write si5383 register value by smbus
* INPUTS:
*   cfg.address : register address
*   cfg.value   ：register value
*   cfg.length  : read data length
* OUTPUTS:
*	none
* RETURNS:
*   OK,  success
*   <0,  fail
*******************************************************************************/
extern int bf_si5383_i2c_wr(si5383_register_op_t cfg);


/*******************************************************************************
* DESCRIPTION:
*   set si5383 ppb
* INPUTS:
*   ppb : set ppb value
* OUTPUTS:
*	none
* RETURNS:
*   OK,  success
*   <0,  fail
*******************************************************************************/
extern int bf_si5383_ppb_set(int ppb);


/*******************************************************************************
* DESCRIPTION:
*   get si5383 ppb
* INPUTS:
*   none
* OUTPUTS:
*	ppb : get ppb value
* RETURNS:
*   OK,  success
*   <0,  fail
*******************************************************************************/
extern int bf_si5383_ppb_get(int *ppb);


/*******************************************************************************
* DESCRIPTION:
*   set fpga register value
* INPUTS:
*   reg_offset: fpga register
*   reg_value : specific value
* OUTPUTS:
*	none
* RETURNS:
*   OK,  success
*   <0,  fail
*******************************************************************************/
extern int fpga_reg_set(int reg_offset, int reg_value);


/*******************************************************************************
* DESCRIPTION:
*   get fpga register value
* INPUTS:
*   reg_offset: fpga register
* OUTPUTS:
*	reg_value : register value
* RETURNS:
*   OK,  success
*   <0,  fail
*******************************************************************************/
extern int fpga_reg_get(int reg_offset, int *reg_value);


/*******************************************************************************
* DESCRIPTION:
*   read i2c device register by fpga smbus
* INPUTS:
*   acc_i2c.addr   : i2c device address
*   acc_i2c.offset : i2c device register address
*   acc_i2c.length : read data length
*   acc_i2c.channel: smbus channel
* OUTPUTS:
*	acc_i2c.buff   : store register value
* RETURNS:
*   OK,  success
*   <0,  fail
*******************************************************************************/
extern int i2c_device_read_by_fpga_smbus(struct fpga_access acc_i2c);


/*******************************************************************************
* DESCRIPTION:
*   read i2c device register by fpga smbus
* INPUTS:
*   acc_i2c.addr   : i2c device address
*   acc_i2c.offset : i2c device register address
*   acc_i2c.length : read data length
*   acc_i2c.channel: smbus channel
*   acc_i2c.buff   : specific value
* OUTPUTS:
*	none
* RETURNS:
*   OK,  success
*   <0,  fail
*******************************************************************************/
extern int i2c_device_write_by_fpga_smbus(struct fpga_access acc_i2c);
