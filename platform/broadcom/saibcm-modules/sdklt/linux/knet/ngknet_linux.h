/*! \file ngknet_linux.h
 *
 * Data structure and macro definitions for Linux kernel APIs abstraction.
 *
 */
/*
 * $Copyright: Copyright 2018-2021 Broadcom. All rights reserved.
 * The term 'Broadcom' refers to Broadcom Inc. and/or its subsidiaries.
 * 
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License 
 * version 2 as published by the Free Software Foundation.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * A copy of the GNU General Public License version 2 (GPLv2) can
 * be found in the LICENSES folder.$
 */

#ifndef NGKNET_LINUX_H
#define NGKNET_LINUX_H

#include <linux/version.h>
#include <linux/skbuff.h>
#include <linux/kthread.h>
#include <linux/netdevice.h>

/*!
 * Kernel abstraction
 */

#define MODULE_PARAM(n, t, p)   module_param(n, t, p)

#if LINUX_VERSION_CODE < KERNEL_VERSION(3,10,0)
#define kal_vlan_hwaccel_put_tag(skb, proto, tci) \
    __vlan_hwaccel_put_tag(skb, tci)
#define NETIF_F_HW_VLAN_CTAG_RX NETIF_F_HW_VLAN_RX
#define NETIF_F_HW_VLAN_CTAG_TX NETIF_F_HW_VLAN_TX
#else
#define kal_vlan_hwaccel_put_tag(skb, proto, tci) \
    __vlan_hwaccel_put_tag(skb, htons(proto), tci)
#endif /* KERNEL_VERSION(3,10,0) */

#if LINUX_VERSION_CODE < KERNEL_VERSION(3,6,0)
static inline int
kal_support_paged_skb(void)
{
    return false;
}
#else
static inline int
kal_support_paged_skb(void)
{
    return true;
}
#endif /* KERNEL_VERSION(3,6,0) */

#if LINUX_VERSION_CODE < KERNEL_VERSION(3,6,0)
static inline struct page *
kal_dev_alloc_page(void)
{
    return NULL;
}
#elif LINUX_VERSION_CODE < KERNEL_VERSION(3,19,0)
static inline struct page *
kal_dev_alloc_page(void)
{
    return alloc_pages(GFP_ATOMIC | __GFP_ZERO | __GFP_COLD |
                       __GFP_COMP | __GFP_MEMALLOC, 0);
}
#else
static inline struct page *
kal_dev_alloc_page(void)
{
    return dev_alloc_page();
}
#endif /* KERNEL_VERSION(3,6,0) */

#if LINUX_VERSION_CODE < KERNEL_VERSION(3,6,0)
static inline struct sk_buff *
kal_build_skb(void *data, unsigned int frag_size)
{
    return NULL;
}
#else
static inline struct sk_buff *
kal_build_skb(void *data, unsigned int frag_size)
{
    return build_skb(data, frag_size);
}
#endif /* KERNEL_VERSION(3,6,0) */

#if LINUX_VERSION_CODE < KERNEL_VERSION(4,7,0)
static inline void
kal_netif_trans_update(struct net_device *dev)
{
    dev->trans_start = jiffies;
}
#else
static inline void
kal_netif_trans_update(struct net_device *dev)
{
    netif_trans_update(dev);
}
#endif /* KERNEL_VERSION(4,7,0) */

#if LINUX_VERSION_CODE < KERNEL_VERSION(3,17,0)
static inline void
kal_time_val_get(struct timeval *tv)
{
    do_gettimeofday(tv);
}
#else
static inline void
kal_time_val_get(struct timeval *tv)
{
    struct timespec64 ts;
    ktime_get_real_ts64(&ts);
    tv->tv_sec = ts.tv_sec;
    tv->tv_usec = ts.tv_nsec / 1000;
}
#endif /* KERNEL_VERSION(3,17,0) */

static inline unsigned long
kal_copy_from_user(void *to, const void __user *from,
                   unsigned int dl, unsigned int sl)
{
    unsigned int len = dl;

    if (unlikely(len != sl)) {
        printk(KERN_WARNING "Unmatched linux_ngknet.ko, please use the latest.\n");
        len = min(dl, sl);
    }

    return copy_from_user(to, from, len);
}

static inline unsigned long
kal_copy_to_user(void __user *to, const void *from,
                 unsigned int dl, unsigned int sl)
{
    unsigned int len = dl;

    if (unlikely(len != sl)) {
        printk(KERN_WARNING "Unmatched linux_ngknet.ko, please use the latest.\n");
        len = min(dl, sl);
    }

    return copy_to_user(to, from, len);
}

/*!
 * System abstraction
 */

static inline void *
sal_alloc(unsigned int sz, char *s)
{
    return kmalloc(sz, GFP_KERNEL);
}

static inline void
sal_free(void *addr)
{
    kfree(addr);
}

static inline void *
sal_memset(void *dest, int c, size_t cnt)
{
    return memset(dest, c, cnt);
}

static inline void *
sal_memcpy(void *dest, const void *src, size_t cnt)
{
    return memcpy(dest, src, cnt);
}

static inline char *
sal_strncpy(char *dest, const char *src, size_t cnt)
{
    return strncpy(dest, src, cnt);
}

/*!
 * Time
 */

extern unsigned long
sal_time_usecs(void);

extern void
sal_usleep(unsigned long usec);

/*!
 * Synchronization
 */

typedef struct sal_sem_s {
    char semaphore_opaque_type;
} *sal_sem_t;

typedef struct sal_spinlock_s {
    char spinlock_opaque_type;
} *sal_spinlock_t;

#define SAL_SEM_FOREVER         -1
#define SAL_SEM_BINARY          1
#define SAL_SEM_COUNTING        0

extern sal_sem_t
sal_sem_create(char *desc, int binary, int count);

extern void
sal_sem_destroy(sal_sem_t sem);

extern int
sal_sem_take(sal_sem_t sem, int usec);

extern int
sal_sem_give(sal_sem_t sem);

extern sal_spinlock_t
sal_spinlock_create(char *desc);

extern void
sal_spinlock_destroy(sal_spinlock_t lock);

extern int
sal_spinlock_lock(sal_spinlock_t lock);

extern int
sal_spinlock_unlock(sal_spinlock_t lock);

#endif /* NGKNET_LINUX_H */

