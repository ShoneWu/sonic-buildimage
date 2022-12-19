#include <linux/init.h>
#include <linux/module.h>
#include <linux/i2c.h>
#include <linux/device.h>
#include <linux/kdev_t.h>
#include <linux/leds.h>
#include <linux/reboot.h>
#include <linux/delay.h>
#include <linux/spinlock.h>
#include <linux/kernel.h>
#include <linux/sched.h>
#include <asm/irq.h>
#include <asm/types.h>
#include <asm/io.h>
#include <linux/poll.h>
#include <linux/wait.h>
#include <linux/pci.h>
#include <linux/interrupt.h>
#include <asm/delay.h>
#include <linux/err.h>
#include <linux/io.h>
#include <linux/of_address.h>
#include <linux/of_irq.h>
#include <linux/of.h>
#include <linux/of_device.h>
#include <linux/gpio.h>

#define SEP(XXX) 1

#if SEP("defines")

#define CTC_GPIO_BASE         496
int xirq_gpio_0 = 0;
int xirq_gpio_1 = 0;
int xirq_gpio_6 = 0;
int xirq_gpio_7 = 0;
int xirq_gpio_15 = 0;
#define IS_INVALID_PTR(_PTR_) ((_PTR_ == NULL) || IS_ERR(_PTR_))
#define IS_VALID_PTR(_PTR_) (!IS_INVALID_PTR(_PTR_))
#define SFP_NUM                 4
#define PORT_NUM                (48+SFP_NUM)
#endif

#if SEP("ctc:pinctl")
u8 ctc_gpio_set(u8 gpio_pin, u8 val)
{
    gpio_set_value_cansleep(gpio_pin + CTC_GPIO_BASE, val);
    return 0;
}

u8 ctc_gpio_get(u8 gpio_pin)
{
    return gpio_get_value_cansleep(gpio_pin + CTC_GPIO_BASE);
}

u8 ctc_gpio_direction_config(u8 gpio_pin, u8 dir,u8 default_out)
{
    return dir ? gpio_direction_input(gpio_pin + CTC_GPIO_BASE)
               : gpio_direction_output(gpio_pin + CTC_GPIO_BASE,default_out);
}

static void ctc_pincrtl_init(void)
{
    /* configure mgmt-phy reset-pin output on product, mgmt-phy release must before this */
    ctc_gpio_direction_config(4, 0, 1);
    /* configure power-up pin output on product */
    ctc_gpio_direction_config(6, 0, 0);
    /* configure phy interrupt pin input */
    ctc_gpio_direction_config(0, 1, 0);
    ctc_gpio_direction_config(1, 1, 0);
    /* configure phy reset-pin output, for release phy */
    ctc_gpio_direction_config(5, 0, 1);

    return;
}

static void ctc_irq_init(void)
{
    struct device_node *xnp;
    for_each_node_by_type(xnp, "ctc-irq")
    {
        if (of_device_is_compatible(xnp, "centec,ctc-irq"))
        {
            xirq_gpio_0 = irq_of_parse_and_map(xnp, 0);
            printk(KERN_INFO "ctc-irq GPIO0 IRQ is %d\n", xirq_gpio_0);
            xirq_gpio_1 = irq_of_parse_and_map(xnp, 1);
            printk(KERN_INFO "ctc-irq GPIO1 IRQ is %d\n", xirq_gpio_1);
            xirq_gpio_15 = irq_of_parse_and_map(xnp, 2);
            printk(KERN_INFO "ctc-irq GPIO15 IRQ is %d\n", xirq_gpio_15);
        }
    }
    return;
}
#endif

#if SEP("i2c:smbus")
static int s5800_48t4s_smbus_read_reg(struct i2c_client *client, unsigned char reg, unsigned char* value)
{
    int ret = 0;

    if (IS_INVALID_PTR(client))
    {
        printk(KERN_CRIT "invalid i2c client");
        return -1;
    }
    
    ret = i2c_smbus_read_byte_data(client, reg);
    if (ret >= 0) {
        *value = (unsigned char)ret;
    }
    else
    {
        *value = 0;
        printk(KERN_CRIT "i2c_smbus op failed: ret=%d reg=%d\n",ret ,reg);
        return ret;
    }

    return 0;
}

static int s5800_48t4s_smbus_write_reg(struct i2c_client *client, unsigned char reg, unsigned char value)
{
    int ret = 0;
    
    if (IS_INVALID_PTR(client))
    {
        printk(KERN_CRIT "invalid i2c client");
        return -1;
    }
    
    ret = i2c_smbus_write_byte_data(client, reg, value);
    if (ret != 0)
    {
        printk(KERN_CRIT "i2c_smbus op failed: ret=%d reg=%d\n",ret ,reg);
        return ret;
    }

    return 0;
}
#endif

#if SEP("i2c:master")
static struct i2c_adapter *i2c_adp_master          = NULL; /* i2c-1-cpu */

static int s5800_48t4s_init_i2c_master(void)
{
    /* find i2c-core master */
    i2c_adp_master = i2c_get_adapter(0);
    if(IS_INVALID_PTR(i2c_adp_master))
    {
        i2c_adp_master = NULL;
        printk(KERN_CRIT "s5800_48t4s_init_i2c_master can't find i2c-core bus\n");
        return -1;
    }
    
    return 0;
}

static int s5800_48t4s_exit_i2c_master(void)
{
    /* uninstall i2c-core master */
    if(IS_VALID_PTR(i2c_adp_master)) {
        i2c_put_adapter(i2c_adp_master);
        i2c_adp_master = NULL;
    }
    
    return 0;
}
#endif

//TODO!!!
#if SEP("i2c:gpio")
static struct i2c_adapter *i2c_adp_gpio0           = NULL; /* gpio0 */
static struct i2c_board_info i2c_dev_gpio0 = {
    I2C_BOARD_INFO("i2c-gpio0", 0x22),
};
static struct i2c_client  *i2c_client_gpio0      = NULL;

static int s5800_48t4s_init_i2c_gpio(void)
{
    int ret = 0;

    if (IS_INVALID_PTR(i2c_adp_master))
    {
         printk(KERN_CRIT "s5800_48t4s_init_i2c_gpio can't find i2c-core bus\n");
         return -1;
    }

    i2c_adp_gpio0 = i2c_get_adapter(0);
    if(IS_INVALID_PTR(i2c_adp_gpio0))
    {
        i2c_adp_gpio0 = NULL;
        printk(KERN_CRIT "get s5800_48t4s gpio0 i2c-adp failed\n");
        return -1;
    }

    i2c_client_gpio0 = i2c_new_client_device(i2c_adp_gpio0, &i2c_dev_gpio0);
    if(IS_INVALID_PTR(i2c_client_gpio0))
    {
        i2c_client_gpio0 = NULL;
        printk(KERN_CRIT "create s5800_48t4s board i2c client gpio0 failed\n");
        return -1;
    }

    /* gpio0 */
    /* tx enable and release mac led and close indicate led */
    ret  = s5800_48t4s_smbus_write_reg(i2c_client_gpio0, 0x02, 0xf0);
    /* bank 0 : output bank 1 : input */
    ret += s5800_48t4s_smbus_write_reg(i2c_client_gpio0, 0x06, 0x00);
    ret += s5800_48t4s_smbus_write_reg(i2c_client_gpio0, 0x07, 0xff);

    if (ret)
    {
        printk(KERN_CRIT "init s5800_48t4s board i2c gpio config failed\n");
        return -1;
    }

    return 0;
}

static int s5800_48t4s_exit_i2c_gpio(void)
{
    if(IS_VALID_PTR(i2c_client_gpio0)) {
        i2c_unregister_device(i2c_client_gpio0);
        i2c_client_gpio0 = NULL;
    }

    if(IS_VALID_PTR(i2c_adp_gpio0)) 
    {
        i2c_put_adapter(i2c_adp_gpio0);
        i2c_adp_gpio0 = NULL;
    }

    return 0;
}
#endif


#if SEP("drivers:psu")
static struct class* psu_class = NULL;
static struct device* psu_dev_psu1 = NULL;
static struct device* psu_dev_psu2 = NULL;

static ssize_t s5800_48t4s_psu_read_presence(struct device *dev, struct device_attribute *attr, char *buf)
{
    int ret = 0;
    unsigned char present_no = 0;
    unsigned char present = 0;
    unsigned char value = 0;
    struct i2c_client *i2c_psu_client = NULL;

    if (psu_dev_psu1 == dev)
    {
        i2c_psu_client = i2c_client_gpio0;
        present_no = 9;
    }
    else if (psu_dev_psu2 == dev)
    {
        i2c_psu_client = i2c_client_gpio0;
        present_no = 13;
    }
    else
    {
        return sprintf(buf, "Error: unknown psu device\n");
    }

    if (IS_INVALID_PTR(i2c_psu_client))
    {
        return sprintf(buf, "Error: psu i2c-adapter invalid\n");
    }

    ret = s5800_48t4s_smbus_read_reg(i2c_psu_client, present_no/8, &present);
    if (ret != 0)
    {
        return sprintf(buf, "Error: read psu data:%s failed\n", attr->attr.name);
    }

    value = ((present & (1<<(present_no%8))) ? 1 : 0 );
    
    return sprintf(buf, "%d\n", value);
}

static ssize_t s5800_48t4s_psu_read_status(struct device *dev, struct device_attribute *attr, char *buf)
{
    int ret = 0;
    unsigned char workstate_no = 0;
    unsigned char workstate = 0;
    unsigned char value = 0;
    struct i2c_client *i2c_psu_client = NULL;

    if (psu_dev_psu1 == dev)
    {
        i2c_psu_client = i2c_client_gpio0;
        workstate_no = 11;
    }
    else if (psu_dev_psu2 == dev)
    {
        i2c_psu_client = i2c_client_gpio0;
        workstate_no = 15;
    }
    else
    {
        return sprintf(buf, "Error: unknown psu device\n");
    }

    if (IS_INVALID_PTR(i2c_psu_client))
    {
        return sprintf(buf, "Error: psu i2c-adapter invalid\n");
    }

    ret = s5800_48t4s_smbus_read_reg(i2c_psu_client, workstate_no/8, &workstate);
    if (ret != 0)
    {
        return sprintf(buf, "Error: read psu data:%s failed\n", attr->attr.name);
    }

    value = ((workstate & (1<<(workstate_no%8))) ? 0 : 1 );
    
    return sprintf(buf, "%d\n", value);
}

static DEVICE_ATTR(psu_presence, S_IRUGO, s5800_48t4s_psu_read_presence, NULL);
static DEVICE_ATTR(psu_status, S_IRUGO, s5800_48t4s_psu_read_status, NULL);

static int s5800_48t4s_init_psu(void)
{
    int ret = 0;
    
    psu_class = class_create(THIS_MODULE, "psu");
    if (IS_INVALID_PTR(psu_class))
    {
        psu_class = NULL;
        printk(KERN_CRIT "create s5800_48t4s class psu failed\n");
        return -1;
    }

    psu_dev_psu1 = device_create(psu_class, NULL, MKDEV(222,0), NULL, "psu1");
    if (IS_INVALID_PTR(psu_dev_psu1))
    {
        psu_dev_psu1 = NULL;
        printk(KERN_CRIT "create s5800_48t4s psu1 device failed\n");
        return -1;
    }

    psu_dev_psu2 = device_create(psu_class, NULL, MKDEV(222,1), NULL, "psu2");
    if (IS_INVALID_PTR(psu_dev_psu2))
    {
        psu_dev_psu2 = NULL;
        printk(KERN_CRIT "create s5800_48t4s psu2 device failed\n");
        return -1;
    }

    ret = device_create_file(psu_dev_psu1, &dev_attr_psu_presence);
    if (ret != 0)
    {
        printk(KERN_CRIT "create s5800_48t4s psu1 device attr:presence failed\n");
        return -1;
    }

    ret = device_create_file(psu_dev_psu1, &dev_attr_psu_status);
    if (ret != 0)
    {
        printk(KERN_CRIT "create s5800_48t4s psu1 device attr:status failed\n");
        return -1;
    }

    ret = device_create_file(psu_dev_psu2, &dev_attr_psu_presence);
    if (ret != 0)
    {
        printk(KERN_CRIT "create s5800_48t4s psu2 device attr:presence failed\n");
        return -1;
    }

    ret = device_create_file(psu_dev_psu2, &dev_attr_psu_status);
    if (ret != 0)
    {
        printk(KERN_CRIT "create s5800_48t4s psu2 device attr:status failed\n");
        return -1;
    }
    
    return 0;
}

static int s5800_48t4s_exit_psu(void)
{
    if (IS_VALID_PTR(psu_dev_psu1))
    {
        device_remove_file(psu_dev_psu1, &dev_attr_psu_presence);
        device_remove_file(psu_dev_psu1, &dev_attr_psu_status);
        device_destroy(psu_class, MKDEV(222,0));
    }

    if (IS_VALID_PTR(psu_dev_psu2))
    {
        device_remove_file(psu_dev_psu2, &dev_attr_psu_presence);
        device_remove_file(psu_dev_psu2, &dev_attr_psu_status);
        device_destroy(psu_class, MKDEV(222,1));
    }

    if (IS_VALID_PTR(psu_class))
    {
        class_destroy(psu_class);
        psu_class = NULL;
    }

    return 0;
}
#endif

#if SEP("drivers:leds")
extern void s5800_48t4s_led_set(struct led_classdev *led_cdev, enum led_brightness set_value);
extern enum led_brightness s5800_48t4s_led_get(struct led_classdev *led_cdev);
extern void s5800_48t4s_led_port_set(struct led_classdev *led_cdev, enum led_brightness set_value);
extern enum led_brightness s5800_48t4s_led_port_get(struct led_classdev *led_cdev);

static struct led_classdev led_dev_system = {
    .name = "system",
    .brightness_set = s5800_48t4s_led_set,
    .brightness_get = s5800_48t4s_led_get,
};
static struct led_classdev led_dev_idn = {
    .name = "idn",
    .brightness_set = s5800_48t4s_led_set,
    .brightness_get = s5800_48t4s_led_get,
};
static struct led_classdev led_dev_fan1 = {
    .name = "fan1",
    .brightness_set = s5800_48t4s_led_set,
    .brightness_get = s5800_48t4s_led_get,
};
static struct led_classdev led_dev_fan2 = {
    .name = "fan2",
    .brightness_set = s5800_48t4s_led_set,
    .brightness_get = s5800_48t4s_led_get,
};
static struct led_classdev led_dev_fan3 = {
    .name = "fan3",
    .brightness_set = s5800_48t4s_led_set,
    .brightness_get = s5800_48t4s_led_get,
};
static struct led_classdev led_dev_fan4 = {
    .name = "fan4",
    .brightness_set = s5800_48t4s_led_set,
    .brightness_get = s5800_48t4s_led_get,
};
static struct led_classdev led_dev_psu1 = {
    .name = "psu1",
    .brightness_set = s5800_48t4s_led_set,
    .brightness_get = s5800_48t4s_led_get,
};
static struct led_classdev led_dev_psu2 = {
    .name = "psu2",
    .brightness_set = s5800_48t4s_led_set,
    .brightness_get = s5800_48t4s_led_get,
};
static struct led_classdev led_dev_port[PORT_NUM] = {
{   .name = "port1",     .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port2",     .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port3",     .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port4",     .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port5",     .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port6",     .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port7",     .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port8",     .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port9",     .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port10",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port11",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port12",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port13",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port14",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port15",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port16",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port17",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port18",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port19",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port20",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port21",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port22",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port23",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port24",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port25",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port26",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port27",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port28",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port29",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port30",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port31",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port32",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port33",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port34",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port35",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port36",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port37",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port38",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port39",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port40",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port41",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port42",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port43",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port44",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port45",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port46",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port47",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port48",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port49",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port50",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port51",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
{   .name = "port52",    .brightness_set = s5800_48t4s_led_port_set,    .brightness_get = s5800_48t4s_led_port_get,},
};
static unsigned char port_led_mode[PORT_NUM] = {0};

void s5800_48t4s_led_set(struct led_classdev *led_cdev, enum led_brightness set_value)
{
    int ret = 0;
    unsigned char reg = 0;
    unsigned char mask = 0;
    unsigned char shift = 0;
    unsigned char led_value = 0;
    struct i2c_client *i2c_led_client = i2c_client_gpio0;

    if (0 == strcmp(led_dev_system.name, led_cdev->name))
    {
        reg = 0x2;
        mask = 0x60;
        shift = 5;
    }
    else if (0 == strcmp(led_dev_idn.name, led_cdev->name))
    {
        reg = 0x2;
        mask = 0x10;
        shift = 4;
    }
    else if (0 == strcmp(led_dev_fan1.name, led_cdev->name))
    {
        goto not_support;
    }
    else if (0 == strcmp(led_dev_fan2.name, led_cdev->name))
    {
        goto not_support;
    }
    else if (0 == strcmp(led_dev_fan3.name, led_cdev->name))
    {
        goto not_support;
    }
    else if (0 == strcmp(led_dev_fan4.name, led_cdev->name))
    {
        goto not_support;
    }
    else if (0 == strcmp(led_dev_psu1.name, led_cdev->name))
    {
        goto not_support;
    }
    else if (0 == strcmp(led_dev_psu2.name, led_cdev->name))
    {
        goto not_support;
    }
    else
    {
        goto not_support;
    }

    ret = s5800_48t4s_smbus_read_reg(i2c_led_client, reg, &led_value);
    if (ret != 0)
    {
        printk(KERN_CRIT "Error: read %s led attr failed\n", led_cdev->name);
        return;
    }

    led_value = ((led_value & (~mask)) | ((set_value << shift) & (mask)));
    
    ret = s5800_48t4s_smbus_write_reg(i2c_led_client, reg, led_value);
    if (ret != 0)
    {
        printk(KERN_CRIT "Error: write %s led attr failed\n", led_cdev->name);
        return;
    }

    return;
    
not_support:

    printk(KERN_INFO "Error: led not support device:%s\n", led_cdev->name);
    return;
}

enum led_brightness s5800_48t4s_led_get(struct led_classdev *led_cdev)
{
    int ret = 0;
    unsigned char reg = 0;
    unsigned char mask = 0;
    unsigned char shift = 0;
    unsigned char led_value = 0;
    struct i2c_client *i2c_led_client = i2c_client_gpio0;

    if (0 == strcmp(led_dev_system.name, led_cdev->name))
    {
        reg = 0x2;
        mask = 0x60;
        shift = 5;
    }
    else if (0 == strcmp(led_dev_idn.name, led_cdev->name))
    {
        reg = 0x2;
        mask = 0x10;
        shift = 4;
    }
    else if (0 == strcmp(led_dev_fan1.name, led_cdev->name))
    {
        goto not_support;
    }
    else if (0 == strcmp(led_dev_fan2.name, led_cdev->name))
    {
        goto not_support;
    }
    else if (0 == strcmp(led_dev_fan3.name, led_cdev->name))
    {
        goto not_support;
    }
    else if (0 == strcmp(led_dev_fan4.name, led_cdev->name))
    {
        goto not_support;
    }
    else if (0 == strcmp(led_dev_psu1.name, led_cdev->name))
    {
        goto not_support;
    }
    else if (0 == strcmp(led_dev_psu2.name, led_cdev->name))
    {
        goto not_support;
    }
    else
    {
        goto not_support;
    }

    ret = s5800_48t4s_smbus_read_reg(i2c_led_client, reg, &led_value);
    if (ret != 0)
    {
        printk(KERN_CRIT "Error: read %s led attr failed\n", led_cdev->name);
        return 0;
    }

    led_value = ((led_value & mask) >> shift);

    return led_value;
    
not_support:

    printk(KERN_INFO "Error: not support device:%s\n", led_cdev->name);
    return 0;
}

void s5800_48t4s_led_port_set(struct led_classdev *led_cdev, enum led_brightness set_value)
{
    int portNum = 0;
    
    sscanf(led_cdev->name, "port%d", &portNum);
    
    port_led_mode[portNum-1] = set_value;

    return;
}

enum led_brightness s5800_48t4s_led_port_get(struct led_classdev *led_cdev)
{
    int portNum = 0;
    
    sscanf(led_cdev->name, "port%d", &portNum);    
    
    return port_led_mode[portNum-1];
}

static int s5800_48t4s_init_led(void)
{
    int ret = 0;
    int i = 0;

    ret = led_classdev_register(NULL, &led_dev_system);
    if (ret != 0)
    {
        printk(KERN_CRIT "create s5800_48t4s led_dev_system device failed\n");
        return -1;
    }

    ret = led_classdev_register(NULL, &led_dev_idn);
    if (ret != 0)
    {
        printk(KERN_CRIT "create s5800_48t4s led_dev_idn device failed\n");
        return -1;
    }

    ret = led_classdev_register(NULL, &led_dev_fan1);
    if (ret != 0)
    {
        printk(KERN_CRIT "create s5800_48t4s led_dev_fan1 device failed\n");
        return -1;
    }

    ret = led_classdev_register(NULL, &led_dev_fan2);
    if (ret != 0)
    {
        printk(KERN_CRIT "create s5800_48t4s led_dev_fan2 device failed\n");
        return -1;
    }

    ret = led_classdev_register(NULL, &led_dev_fan3);
    if (ret != 0)
    {
        printk(KERN_CRIT "create s5800_48t4s led_dev_fan3 device failed\n");
        return -1;
    }

    ret = led_classdev_register(NULL, &led_dev_fan4);
    if (ret != 0)
    {
        printk(KERN_CRIT "create s5800_48t4s led_dev_fan4 device failed\n");
        return -1;
    }

    ret = led_classdev_register(NULL, &led_dev_psu1);
    if (ret != 0)
    {
        printk(KERN_CRIT "create s5800_48t4s led_dev_psu1 device failed\n");
        return -1;
    }

    ret = led_classdev_register(NULL, &led_dev_psu2);
    if (ret != 0)
    {
        printk(KERN_CRIT "create s5800_48t4s led_dev_psu2 device failed\n");
        return -1;
    }

    for (i=0; i<PORT_NUM; i++)
    {
        ret = led_classdev_register(NULL, &(led_dev_port[i]));
        if (ret != 0)
        {
            printk(KERN_CRIT "create s5800_48t4s led_dev_port%d device failed\n", i);
            continue;
        }
    }
    
    return ret;
}

static int s5800_48t4s_exit_led(void)
{
    int i = 0;

    led_classdev_unregister(&led_dev_system);
    led_classdev_unregister(&led_dev_idn);
    led_classdev_unregister(&led_dev_fan1);
    led_classdev_unregister(&led_dev_fan2);
    led_classdev_unregister(&led_dev_fan3);
    led_classdev_unregister(&led_dev_fan4);
    led_classdev_unregister(&led_dev_psu1);
    led_classdev_unregister(&led_dev_psu2);

    for (i=0; i<PORT_NUM; i++)
    {
        led_classdev_unregister(&(led_dev_port[i]));
    }

    return 0;
}
#endif

#if SEP("drivers:sfp")
#define MAX_SFP_EEPROM_DATA_LEN 256
struct sfp_info_t {
    char data[MAX_SFP_EEPROM_DATA_LEN+1];
    unsigned short data_len;
    int presence;
    spinlock_t lock;
};
static struct class* sfp_class = NULL;
static struct device* sfp_dev[SFP_NUM+1] = {NULL};
static struct sfp_info_t sfp_info[SFP_NUM+1];

static ssize_t s5800_48t4s_sfp_read_presence(struct device *dev, struct device_attribute *attr, char *buf)
{
    int portNum = 0;
    const char *name = dev_name(dev);
    unsigned long flags = 0;
    int presence = 0;

    sscanf(name, "sfp%d", &portNum);

    if ((portNum < 1) || (portNum > SFP_NUM))
    {
        printk(KERN_CRIT "sfp read presence, invalid port number!\n");
        buf[0] = '\0';
        return 0;
    }

    spin_lock_irqsave(&(sfp_info[portNum].lock), flags);
    presence = sfp_info[portNum].presence;
    spin_unlock_irqrestore(&(sfp_info[portNum].lock), flags);
    return sprintf(buf, "%d\n", presence);
}

static ssize_t s5800_48t4s_sfp_write_presence(struct device *dev, struct device_attribute *attr, const char *buf, size_t size)
{
    int portNum = 0;
    const char *name = dev_name(dev);
    unsigned long flags = 0;
    int presence = simple_strtol(buf, NULL, 10);

    sscanf(name, "sfp%d", &portNum);

    if ((portNum < 1) || (portNum > SFP_NUM))
    {
        printk(KERN_CRIT "sfp read presence, invalid port number!\n");
        return size;
    }

    spin_lock_irqsave(&(sfp_info[portNum].lock), flags);
    sfp_info[portNum].presence = presence;
    spin_unlock_irqrestore(&(sfp_info[portNum].lock), flags);
    
    return size;
}

static ssize_t s5800_48t4s_sfp_read_enable(struct device *dev, struct device_attribute *attr, char *buf)
{
    int ret = 0;
    unsigned char value = 0;
    unsigned char reg_no = 0;
    unsigned char input_bank = 0;
    int portNum = 0;
    const char *name = dev_name(dev);
    struct i2c_client *i2c_sfp_client = NULL;

    sscanf(name, "sfp%d", &portNum);

    if ((portNum < 1) || (portNum > SFP_NUM))
    {
        printk(KERN_CRIT "sfp read enable, invalid port number!\n");
        value = 0;
    }

    reg_no = portNum - 1;
    i2c_sfp_client = i2c_client_gpio0;

    input_bank = (reg_no/8) + 0x2;
    ret = s5800_48t4s_smbus_read_reg(i2c_sfp_client, input_bank, &value);
    if (ret != 0)
    {
        return sprintf(buf, "Error: read sfp enable: %s failed\n", attr->attr.name);
    }

    value = ((value & (1<<(reg_no%8))) ? 0 : 1 );
    
    return sprintf(buf, "%d\n", value);
}

static ssize_t s5800_48t4s_sfp_write_enable(struct device *dev, struct device_attribute *attr, const char *buf, size_t size)
{
    int ret = 0;
    unsigned char value = 0;
    unsigned char set_value = simple_strtol(buf, NULL, 10);
    unsigned char reg_no = 0;
    unsigned char input_bank = 0;
    unsigned char output_bank = 0;
    int portNum = 0;
    const char *name = dev_name(dev);
    struct i2c_client *i2c_sfp_client = NULL;

    sscanf(name, "sfp%d", &portNum);

    if ((portNum < 1) || (portNum > SFP_NUM))
    {
        printk(KERN_CRIT "sfp read enable, invalid port number!\n");
        return size;
    }

    reg_no = portNum - 1;
    i2c_sfp_client = i2c_client_gpio0;

    set_value = ((set_value > 0) ? 0 : 1);

    input_bank = (reg_no/8) + 0x2;
    ret = s5800_48t4s_smbus_read_reg(i2c_sfp_client, input_bank, &value);
    if (ret != 0)
    {
        printk(KERN_CRIT "Error: read %s enable failed\n", name);
        return size;
    }

    if (set_value)
    {
        value = (value | (1<<(reg_no % 8)));
    }
    else
    {
        value = (value & (~(1<<(reg_no % 8))));
    }
    
    output_bank = (reg_no/8) + 0x2;
    ret = s5800_48t4s_smbus_write_reg(i2c_sfp_client, output_bank, value);
    if (ret != 0)
    {
        printk(KERN_CRIT "Error: write %s enable failed\n", name);
        return size;
    }
    
    return size;
}

static ssize_t s5800_48t4s_sfp_read_eeprom(struct device *dev, struct device_attribute *attr, char *buf)
{
    int portNum = 0;
    const char *name = dev_name(dev);
    unsigned long flags = 0;
    size_t size = 0;

    sscanf(name, "sfp%d", &portNum);

    if ((portNum < 1) || (portNum > SFP_NUM))
    {
        printk(KERN_CRIT "sfp read eeprom, invalid port number!\n");
        buf[0] = '\0';
        return 0;
    }

    spin_lock_irqsave(&(sfp_info[portNum].lock), flags);
    memcpy(buf, sfp_info[portNum].data, sfp_info[portNum].data_len);
    size = sfp_info[portNum].data_len;
    spin_unlock_irqrestore(&(sfp_info[portNum].lock), flags);

    return size;
}

static ssize_t s5800_48t4s_sfp_write_eeprom(struct device *dev, struct device_attribute *attr, const char *buf, size_t size)
{
    int portNum = 0;
    const char *name = dev_name(dev);
    unsigned long flags = 0;

    sscanf(name, "sfp%d", &portNum);

    if ((portNum < 1) || (portNum > SFP_NUM))
    {
        printk(KERN_CRIT "sfp write eeprom, invalid port number!\n");
        return size;
    }

    spin_lock_irqsave(&(sfp_info[portNum].lock), flags);
    memcpy(sfp_info[portNum].data, buf, size);
    sfp_info[portNum].data_len = size;
    spin_unlock_irqrestore(&(sfp_info[portNum].lock), flags);
    
    return size;
}

static DEVICE_ATTR(sfp_presence, S_IRUGO|S_IWUSR, s5800_48t4s_sfp_read_presence, s5800_48t4s_sfp_write_presence);
static DEVICE_ATTR(sfp_enable, S_IRUGO|S_IWUSR, s5800_48t4s_sfp_read_enable, s5800_48t4s_sfp_write_enable);
static DEVICE_ATTR(sfp_eeprom, S_IRUGO|S_IWUSR, s5800_48t4s_sfp_read_eeprom, s5800_48t4s_sfp_write_eeprom);
static int s5800_48t4s_init_sfp(void)
{
    int ret = 0;
    int i = 0;
    
    sfp_class = class_create(THIS_MODULE, "sfp");
    if (IS_INVALID_PTR(sfp_class))
    {
        sfp_class = NULL;
        printk(KERN_CRIT "create s5800_48t4s class sfp failed\n");
        return -1;
    }

    for (i=1; i<=SFP_NUM; i++)
    {
        memset(&(sfp_info[i].data), 0, MAX_SFP_EEPROM_DATA_LEN+1);
        sfp_info[i].data_len = 0;
        spin_lock_init(&(sfp_info[i].lock));

        sfp_dev[i] = device_create(sfp_class, NULL, MKDEV(223,i), NULL, "sfp%d", i);
        if (IS_INVALID_PTR(sfp_dev[i]))
        {
            sfp_dev[i] = NULL;
            printk(KERN_CRIT "create s5800_48t4s sfp[%d] device failed\n", i);
            continue;
        }

        ret = device_create_file(sfp_dev[i], &dev_attr_sfp_presence);
        if (ret != 0)
        {
            printk(KERN_CRIT "create s5800_48t4s sfp[%d] device attr:presence failed\n", i);
            continue;
        }

        ret = device_create_file(sfp_dev[i], &dev_attr_sfp_enable);
        if (ret != 0)
        {
            printk(KERN_CRIT "create s5800_48t4s sfp[%d] device attr:enable failed\n", i);
            continue;
        }

        ret = device_create_file(sfp_dev[i], &dev_attr_sfp_eeprom);
        if (ret != 0)
        {
            printk(KERN_CRIT "create s5800_48t4s sfp[%d] device attr:eeprom failed\n", i);
            continue;
        }
    }
    
    return ret;
}

static int s5800_48t4s_exit_sfp(void)
{
    int i = 0;

    for (i=1; i<=SFP_NUM; i++)
    {
        if (IS_VALID_PTR(sfp_dev[i]))
        {
            device_remove_file(sfp_dev[i], &dev_attr_sfp_presence);
            device_remove_file(sfp_dev[i], &dev_attr_sfp_enable);
            device_remove_file(sfp_dev[i], &dev_attr_sfp_eeprom);
            device_destroy(sfp_class, MKDEV(223,i));
            sfp_dev[i] = NULL;
        }
    }

    if (IS_VALID_PTR(sfp_class))
    {
        class_destroy(sfp_class);
        sfp_class = NULL;
    }

    return 0;
}
#endif

static int s5800_48t4s_init(void)
{
    int ret = 0;
    int failed = 0;
    
    printk(KERN_ALERT "install s5800_48t4s board dirver...\n");

    ctc_irq_init();
    ctc_pincrtl_init();
    
    ret = s5800_48t4s_init_i2c_master();
    if (ret != 0)
    {
        failed = 1;
    }

    ret = s5800_48t4s_init_i2c_gpio();
    if (ret != 0)
    {
        failed = 1;
    }

    ret = s5800_48t4s_init_psu();
    if (ret != 0)
    {
        failed = 1;
    }

    ret = s5800_48t4s_init_led();
    if (ret != 0)
    {
        failed = 1;
    }

    ret = s5800_48t4s_init_sfp();
    if (ret != 0)
    {
        failed = 1;
    }

    if (failed)
        printk(KERN_INFO "install s5800_48t4s board driver failed\n");
    else
        printk(KERN_ALERT "install s5800_48t4s board dirver...ok\n");
    
    return 0;
}

static void s5800_48t4s_exit(void)
{
    printk(KERN_INFO "uninstall s5800_48t4s board dirver...\n");
    
    s5800_48t4s_exit_sfp();
    s5800_48t4s_exit_led();
    s5800_48t4s_exit_psu();
    s5800_48t4s_exit_i2c_gpio();
    s5800_48t4s_exit_i2c_master();
}

MODULE_LICENSE("Dual BSD/GPL");
MODULE_AUTHOR("sec <sec@feisu.com>");
MODULE_DESCRIPTION("s5800-48t4s board driver");
module_init(s5800_48t4s_init);
module_exit(s5800_48t4s_exit);
