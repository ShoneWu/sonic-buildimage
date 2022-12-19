#include <linux/module.h>
#include <linux/io.h>
#include <linux/device.h>
#include <linux/delay.h>
#include <linux/platform_device.h>

#include <rg_lpc_drv.h>

static int g_rg_lpc_drv_device_debug = 0;
static int g_rg_lpc_drv_device_error = 0;

module_param(g_rg_lpc_drv_device_debug, int, S_IRUGO | S_IWUSR);
module_param(g_rg_lpc_drv_device_error, int, S_IRUGO | S_IWUSR);

#define RG_LPC_DRV_DEVICE_DEBUG_VERBOSE(fmt, args...) do {                                        \
    if (g_rg_lpc_drv_device_debug) { \
        printk(KERN_INFO "[RG_LPC_DRV_DEVICE][VER][func:%s line:%d]\r\n"fmt, __func__, __LINE__, ## args); \
    } \
} while (0)

#define RG_LPC_DRV_DEVICE_DEBUG_ERROR(fmt, args...) do {                                        \
    if (g_rg_lpc_drv_device_error) { \
        printk(KERN_ERR "[RG_LPC_DRV_DEVICE][ERR][func:%s line:%d]\r\n"fmt, __func__, __LINE__, ## args); \
    } \
} while (0)

static lpc_drv_device_t lpc_drv_device_data_0 = {
    .lpc_io_name = "rg_lpc",
    .pci_domain = 0x0000,
    .pci_bus = 0x00,
    .pci_slot = 0x1f,
    .pci_fn = 0,
    .lpc_io_base = 0x700,
    .lpc_io_size = 0x100,
    .lpc_gen_dec = 0x84,
};

static lpc_drv_device_t lpc_drv_device_data_1 = {
    .lpc_io_name = "rg_lpc",
    .pci_domain = 0x0000,
    .pci_bus = 0x00,
    .pci_slot = 0x1f,
    .pci_fn = 0,
    .lpc_io_base = 0x900,
    .lpc_io_size = 0x100,
    .lpc_gen_dec = 0x88,
};

static void rg_lpc_drv_device_release(struct device *dev)
{
    return;
}

static struct platform_device lpc_drv_device[] = {
    {
        .name   = "rg-lpc",
        .id = 1,
        .dev    = {
            .platform_data  = &lpc_drv_device_data_0,
            .release = rg_lpc_drv_device_release,
        },
    },
    {
        .name   = "rg-lpc",
        .id = 2,
        .dev    = {
            .platform_data  = &lpc_drv_device_data_1,
            .release = rg_lpc_drv_device_release,
        },
    },
};

static int __init rg_lpc_drv_device_init(void)
{
    int i;
    int ret = 0;
    lpc_drv_device_t *lpc_drv_device_data;

    RG_LPC_DRV_DEVICE_DEBUG_VERBOSE("enter!\n");
    for (i = 0; i < ARRAY_SIZE(lpc_drv_device); i++) {
        lpc_drv_device_data = lpc_drv_device[i].dev.platform_data;
        ret = platform_device_register(&lpc_drv_device[i]);
        if (ret < 0) {
            lpc_drv_device_data->device_flag = -1; /* device register failed, set flag -1 */
            printk(KERN_ERR "rg-lpc.%d register failed!\n", i + 1);
        } else {
            lpc_drv_device_data->device_flag = 0; /* device register suucess, set flag 0 */
        }
    }
    return 0;
}

static void __exit rg_lpc_drv_device_exit(void)
{
    int i;
    lpc_drv_device_t *lpc_drv_device_data;

    RG_LPC_DRV_DEVICE_DEBUG_VERBOSE("enter!\n");
    for (i = ARRAY_SIZE(lpc_drv_device) - 1; i >= 0; i--) {
        lpc_drv_device_data = lpc_drv_device[i].dev.platform_data;
        if (lpc_drv_device_data->device_flag == 0) { /* device register success, need unregister */
            platform_device_unregister(&lpc_drv_device[i]);
        }
    }
}

module_init(rg_lpc_drv_device_init);
module_exit(rg_lpc_drv_device_exit);
MODULE_DESCRIPTION("RG LPC DRV Devices");
MODULE_LICENSE("GPL");
MODULE_AUTHOR("sonic_rd@ruijie.com.cn");
