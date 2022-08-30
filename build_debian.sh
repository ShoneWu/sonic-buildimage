#!/bin/bash
## This script is to automate the preparation for a debian file system, which will be used for
## an ONIE installer image.
##
## USAGE:
##   USERNAME=username PASSWORD=password ./build_debian
## ENVIRONMENT:
##   USERNAME
##          The name of the default admin user
##   PASSWORD
##          The password, expected by chpasswd command

## Default user
[ -n "$USERNAME" ] || {
    echo "Error: no or empty USERNAME"
    exit 1
}

## Password for the default user
[ -n "$PASSWORD" ] || {
    echo "Error: no or empty PASSWORD"
    exit 1
}

## Include common functions
. functions.sh

## Enable debug output for script
set -x -e

CONFIGURED_ARCH=$([ -f .arch ] && cat .arch || echo amd64)

## docker engine version (with platform)
if [[ $CONFIGURED_ARCH == armhf || $CONFIGURED_ARCH == arm64 ]]; then
    # Version name differs between ARCH, copying same version as in sonic-slave docker
    DOCKER_VERSION=18.06.3~ce~3-0~debian
else
    DOCKER_VERSION=5:18.09.8~3-0~debian-stretch
fi
LINUX_KERNEL_VERSION=4.9.0-14-2

## Working directory to prepare the file system
FILESYSTEM_ROOT=./fsroot
PLATFORM_DIR=platform
## Hostname for the linux image
HOSTNAME=sonic
DEFAULT_USERINFO="Default admin user,,,"

## Read ONIE image related config file
. ./onie-image.conf
[ -n "$ONIE_IMAGE_PART_SIZE" ] || {
    echo "Error: Invalid ONIE_IMAGE_PART_SIZE in onie image config file"
    exit 1
}
[ -n "$ONIE_INSTALLER_PAYLOAD" ] || {
    echo "Error: Invalid ONIE_INSTALLER_PAYLOAD in onie image config file"
    exit 1
}
[ -n "$FILESYSTEM_SQUASHFS" ] || {
    echo "Error: Invalid FILESYSTEM_SQUASHFS in onie image config file"
    exit 1
}

## Prepare the file system directory
if [[ -d $FILESYSTEM_ROOT ]]; then
    sudo rm -rf $FILESYSTEM_ROOT || die "Failed to clean chroot directory"
fi
mkdir -p $FILESYSTEM_ROOT
mkdir -p $FILESYSTEM_ROOT/$PLATFORM_DIR
mkdir -p $FILESYSTEM_ROOT/$PLATFORM_DIR/x86_64-grub
touch $FILESYSTEM_ROOT/$PLATFORM_DIR/firsttime

## make / as a mountpoint in chroot env, needed by dockerd
pushd $FILESYSTEM_ROOT
sudo mount --bind . .
popd

## Build a basic Debian system by debootstrap
echo '[INFO] Debootstrap...'
if [[ $CONFIGURED_ARCH == armhf || $CONFIGURED_ARCH == arm64 ]]; then
    # qemu arm bin executable for cross-building
    sudo mkdir -p $FILESYSTEM_ROOT/usr/bin
    sudo cp /usr/bin/qemu*static $FILESYSTEM_ROOT/usr/bin || true
    sudo http_proxy=$http_proxy debootstrap --variant=minbase --arch $CONFIGURED_ARCH stretch $FILESYSTEM_ROOT http://deb.debian.org/debian
else
    sudo http_proxy=$http_proxy debootstrap --variant=minbase --arch $CONFIGURED_ARCH stretch $FILESYSTEM_ROOT http://debian-archive.trafficmanager.net/debian
fi

## Config hostname and hosts, otherwise 'sudo ...' will complain 'sudo: unable to resolve host ...'
sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo '$HOSTNAME' > /etc/hostname"
sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo '127.0.0.1       $HOSTNAME' >> /etc/hosts"
sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo '127.0.0.1       localhost' >> /etc/hosts"

## Config basic fstab
sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c 'echo "proc /proc proc defaults 0 0" >> /etc/fstab'
sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c 'echo "sysfs /sys sysfs defaults 0 0" >> /etc/fstab'

## Setup proxy
[ -n "$http_proxy" ] && sudo /bin/bash -c "echo 'Acquire::http::Proxy \"$http_proxy\";' > $FILESYSTEM_ROOT/etc/apt/apt.conf.d/01proxy"

## Note: mounting is necessary to makedev and install linux image
echo '[INFO] Mount all'
## Output all the mounted device for troubleshooting
mount
trap_push 'sudo umount $FILESYSTEM_ROOT/proc || true'
sudo LANG=C chroot $FILESYSTEM_ROOT mount proc /proc -t proc

## Pointing apt to public apt mirrors and getting latest packages, needed for latest security updates
sudo cp files/apt/sources.list.$CONFIGURED_ARCH $FILESYSTEM_ROOT/etc/apt/sources.list
sudo cp files/apt/apt.conf.d/{81norecommends,apt-{clean,gzip-indexes,no-languages},no-check-valid-until} $FILESYSTEM_ROOT/etc/apt/apt.conf.d/
sudo LANG=C chroot $FILESYSTEM_ROOT bash -c 'apt-mark auto `apt-mark showmanual`'

## Note: set lang to prevent locale warnings in your chroot
sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y update
sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y upgrade
echo '[INFO] Install packages for building image'
sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install makedev psmisc systemd-sysv

## Create device files
echo '[INFO] MAKEDEV'
if [[ $CONFIGURED_ARCH == armhf || $CONFIGURED_ARCH == arm64 ]]; then
    sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c 'cd /dev && MAKEDEV generic-arm'
else
    sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c 'cd /dev && MAKEDEV generic'
fi
## Install initramfs-tools and linux kernel
## Note: initramfs-tools recommends depending on busybox, and we really want busybox for
## 1. commands such as touch
## 2. mount supports squashfs
## However, 'dpkg -i' plus 'apt-get install -f' will ignore the recommended dependency. So
## we install busybox explicitly
sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install busybox
echo '[INFO] Install SONiC linux kernel image'
## Note: duplicate apt-get command to ensure every line return zero
sudo dpkg --root=$FILESYSTEM_ROOT -i $debs_path/initramfs-tools-core_*.deb || \
    sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install -f
sudo dpkg --root=$FILESYSTEM_ROOT -i $debs_path/initramfs-tools_*.deb || \
    sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install -f
sudo dpkg --root=$FILESYSTEM_ROOT -i $debs_path/linux-image-${LINUX_KERNEL_VERSION}-*_${CONFIGURED_ARCH}.deb || \
    sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install -f
sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install acl
if [[ $CONFIGURED_ARCH == amd64 ]]; then
    sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install dmidecode hdparm
fi

## Update initramfs for booting with squashfs+overlay
cat files/initramfs-tools/modules | sudo tee -a $FILESYSTEM_ROOT/etc/initramfs-tools/modules > /dev/null

## Hook into initramfs: change fs type from vfat to ext4 on arista switches
sudo mkdir -p $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-premount/
sudo cp files/initramfs-tools/arista-convertfs $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-premount/arista-convertfs
sudo chmod +x $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-premount/arista-convertfs
sudo cp files/initramfs-tools/arista-hook $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-premount/arista-hook
sudo chmod +x $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-premount/arista-hook
sudo cp files/initramfs-tools/mke2fs $FILESYSTEM_ROOT/etc/initramfs-tools/hooks/mke2fs
sudo chmod +x $FILESYSTEM_ROOT/etc/initramfs-tools/hooks/mke2fs
sudo cp files/initramfs-tools/setfacl $FILESYSTEM_ROOT/etc/initramfs-tools/hooks/setfacl
sudo chmod +x $FILESYSTEM_ROOT/etc/initramfs-tools/hooks/setfacl

# Hook into initramfs: rename the management interfaces on arista switches
sudo cp files/initramfs-tools/arista-net $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-premount/arista-net
sudo chmod +x $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-premount/arista-net

# Hook into initramfs: resize root partition after migration from another NOS to SONiC on Dell switches
sudo cp files/initramfs-tools/resize-rootfs $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-premount/resize-rootfs
sudo chmod +x $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-premount/resize-rootfs

# Hook into initramfs: run fsck to repair a non-clean filesystem prior to be mounted
sudo cp files/initramfs-tools/fsck-rootfs $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-premount/fsck-rootfs
sudo chmod +x $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-premount/fsck-rootfs

## Hook into initramfs: after partition mount and loop file mount
## 1. Prepare layered file system
## 2. Bind-mount docker working directory (docker overlay storage cannot work over overlay rootfs)
sudo cp files/initramfs-tools/union-mount $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-bottom/union-mount
sudo chmod +x $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-bottom/union-mount
sudo cp files/initramfs-tools/varlog $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-bottom/varlog
sudo chmod +x $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-bottom/varlog
# Management interface (eth0) dhcp can be optionally turned off (during a migration from another NOS to SONiC)
#sudo cp files/initramfs-tools/mgmt-intf-dhcp $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-bottom/mgmt-intf-dhcp
#sudo chmod +x $FILESYSTEM_ROOT/etc/initramfs-tools/scripts/init-bottom/mgmt-intf-dhcp
sudo cp files/initramfs-tools/union-fsck $FILESYSTEM_ROOT/etc/initramfs-tools/hooks/union-fsck
sudo chmod +x $FILESYSTEM_ROOT/etc/initramfs-tools/hooks/union-fsck
pushd $FILESYSTEM_ROOT/usr/share/initramfs-tools/scripts/init-bottom && sudo patch -p1 < $OLDPWD/files/initramfs-tools/udev.patch; popd

if [[ $CONFIGURED_ARCH == amd64 ]]; then
    ## Install latest intel ixgbe driver
    sudo cp $files_path/ixgbe.ko $FILESYSTEM_ROOT/lib/modules/${LINUX_KERNEL_VERSION}-amd64/kernel/drivers/net/ethernet/intel/ixgbe/ixgbe.ko
fi

## Install docker
echo '[INFO] Install docker'
## Install apparmor utils since they're missing and apparmor is enabled in the kernel
## Otherwise Docker will fail to start
sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install apparmor
sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install apt-transport-https \
                                                       ca-certificates \
                                                       curl \
                                                       gnupg2 \
                                                       software-properties-common
sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT curl -o /tmp/docker.gpg -fsSL https://download.docker.com/linux/debian/gpg
sudo LANG=C chroot $FILESYSTEM_ROOT apt-key add /tmp/docker.gpg
sudo LANG=C chroot $FILESYSTEM_ROOT rm /tmp/docker.gpg
sudo LANG=C chroot $FILESYSTEM_ROOT add-apt-repository \
                                    "deb [arch=$CONFIGURED_ARCH] https://download.docker.com/linux/debian stretch stable"
sudo LANG=C chroot $FILESYSTEM_ROOT apt-get update
sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install docker-ce=${DOCKER_VERSION} docker-ce-cli=${DOCKER_VERSION}
sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y remove software-properties-common gnupg2

if [ "$INCLUDE_KUBERNETES" == "y" ]
then
    ## Install Kubernetes
    echo '[INFO] Install kubernetes'
    sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT curl -fsSL \
        https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
        sudo LANG=C chroot $FILESYSTEM_ROOT apt-key add -
    ## Check out the sources list update matches current Debian version
    sudo cp files/image_config/kubernetes/kubernetes.list $FILESYSTEM_ROOT/etc/apt/sources.list.d/
    sudo LANG=C chroot $FILESYSTEM_ROOT apt-get update
    sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install kubernetes-cni=${KUBERNETES_CNI_VERSION}-00
    sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install kubelet=${KUBERNETES_VERSION}-00
    sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install kubectl=${KUBERNETES_VERSION}-00
    sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install kubeadm=${KUBERNETES_VERSION}-00
    # kubeadm package auto install kubelet & kubectl
else
    echo '[INFO] Skipping Install kubernetes'
fi

## Add docker config drop-in to specify dockerd command line
sudo mkdir -p $FILESYSTEM_ROOT/etc/systemd/system/docker.service.d/
## Note: $_ means last argument of last command
sudo cp files/docker/docker.service.conf $_
## Fix systemd race between docker and containerd
sudo sed -i '/After=/s/$/ containerd.service/' $FILESYSTEM_ROOT/lib/systemd/system/docker.service

## Create default user
## Note: user should be in the group with the same name, and also in sudo/docker/redis groups
sudo LANG=C chroot $FILESYSTEM_ROOT useradd -G sudo,docker $USERNAME -c "$DEFAULT_USERINFO" -m -s /bin/bash
## Create password for the default user
echo "$USERNAME:$PASSWORD" | sudo LANG=C chroot $FILESYSTEM_ROOT chpasswd

## Create redis group
sudo LANG=C chroot $FILESYSTEM_ROOT groupadd -f redis
sudo LANG=C chroot $FILESYSTEM_ROOT usermod -aG redis $USERNAME

if [[ $CONFIGURED_ARCH == amd64 ]]; then
    ## Pre-install hardware drivers
    sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y install      \
        firmware-linux-nonfree
fi

## Pre-install the fundamental packages
## Note: gdisk is needed for sgdisk in install.sh
## Note: parted is needed for partprobe in install.sh
## Note: ca-certificates is needed for easy_install
## Note: don't install python-apt by pip, older than Debian repo one
sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install      \
    file                    \
    ifmetric                \
    iproute2                \
    bridge-utils            \
    isc-dhcp-client         \
    sudo                    \
    vim                     \
    tcpdump                 \
    dbus                    \
    ntp                     \
    ntpstat                 \
    openssh-server          \
    python                  \
    python-setuptools       \
    python-apt              \
    traceroute              \
    iputils-ping            \
    net-tools               \
    bsdmainutils            \
    ca-certificates         \
    i2c-tools               \
    efibootmgr              \
    usbutils                \
    pciutils                \
    iptables-persistent     \
    ebtables                \
    logrotate               \
    curl                    \
    kexec-tools             \
    less                    \
    unzip                   \
    gdisk                   \
    sysfsutils              \
    squashfs-tools          \
    grub2-common            \
    rsyslog                 \
    ethtool                 \
    screen                  \
    hping3                  \
    tcptraceroute           \
    mtr-tiny                \
    locales                 \
    cgroup-tools            \
    ipmitool                \
    ndisc6                  \
    makedumpfile            \
    conntrack               \
    python-pip              \
    jq                      \
    haveged


if [[ $CONFIGURED_ARCH == amd64 ]]; then
## Pre-install the fundamental packages for amd64 (x86)
sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install      \
    libftdi1                \
    flashrom                \
    mcelog
fi

## Set /etc/shadow permissions to -rw-------.
sudo LANG=c chroot $FILESYSTEM_ROOT chmod 600 /etc/shadow

## Set /etc/passwd, /etc/group permissions to -rw-r--r--.
sudo LANG=c chroot $FILESYSTEM_ROOT chmod 644 /etc/passwd
sudo LANG=c chroot $FILESYSTEM_ROOT chmod 644 /etc/group

# Needed to install kdump-tools
sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "mkdir -p /etc/initramfs-tools/conf.d"
sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo 'MODULES=most' >> /etc/initramfs-tools/conf.d/driver-policy"

#Adds a locale to a debian system in non-interactive mode
sudo sed -i '/^#.* en_US.* /s/^#//' $FILESYSTEM_ROOT/etc/locale.gen && \
    sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT locale-gen "en_US.UTF-8"
sudo LANG=en_US.UTF-8 DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT update-locale "LANG=en_US.UTF-8"
sudo LANG=C chroot $FILESYSTEM_ROOT bash -c "find /usr/share/i18n/locales/ ! -name 'en_US' -type f -exec rm -f {} +"

# Install certain fundamental packages from stretch-backports in order to get
# more up-to-date (but potentially less stable) versions
sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y -t stretch-backports install \
    picocom

if [[ $CONFIGURED_ARCH == amd64 ]]; then
    sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y download \
        grub-pc-bin

    sudo mv $FILESYSTEM_ROOT/grub-pc-bin*.deb $FILESYSTEM_ROOT/$PLATFORM_DIR/x86_64-grub
fi

## Disable kexec supported reboot which was installed by default
sudo sed -i 's/LOAD_KEXEC=true/LOAD_KEXEC=false/' $FILESYSTEM_ROOT/etc/default/kexec

## Remove sshd host keys, and will regenerate on first sshd start
sudo rm -f $FILESYSTEM_ROOT/etc/ssh/ssh_host_*_key*
sudo cp files/sshd/host-ssh-keygen.sh $FILESYSTEM_ROOT/usr/local/bin/
sudo cp -f files/sshd/sshd.service $FILESYSTEM_ROOT/lib/systemd/system/ssh.service
# Config sshd
# 1. Set 'UseDNS' to 'no'
# 2. Configure sshd to close all SSH connetions after 15 minutes of inactivity
sudo augtool -r $FILESYSTEM_ROOT <<'EOF'
touch /files/etc/ssh/sshd_config/EmptyLineHack
rename /files/etc/ssh/sshd_config/EmptyLineHack ""
set /files/etc/ssh/sshd_config/UseDNS no
ins #comment before /files/etc/ssh/sshd_config/UseDNS
set /files/etc/ssh/sshd_config/#comment[following-sibling::*[1][self::UseDNS]] "Disable hostname lookups"

rm /files/etc/ssh/sshd_config/ClientAliveInterval
rm /files/etc/ssh/sshd_config/ClientAliveCountMax
touch /files/etc/ssh/sshd_config/EmptyLineHack
rename /files/etc/ssh/sshd_config/EmptyLineHack ""
set /files/etc/ssh/sshd_config/ClientAliveInterval 900
set /files/etc/ssh/sshd_config/ClientAliveCountMax 0
ins #comment before /files/etc/ssh/sshd_config/ClientAliveInterval
set /files/etc/ssh/sshd_config/#comment[following-sibling::*[1][self::ClientAliveInterval]] "Close inactive client sessions after 15 minutes"
save
quit
EOF
# Configure sshd to listen for v4 connections; disable listening for v6 connections
sudo sed -i 's/^ListenAddress ::/#ListenAddress ::/' $FILESYSTEM_ROOT/etc/ssh/sshd_config
sudo sed -i 's/^#ListenAddress 0.0.0.0/ListenAddress 0.0.0.0/' $FILESYSTEM_ROOT/etc/ssh/sshd_config

sudo mkdir -p $FILESYSTEM_ROOT/var/core

# Config sysctl
sudo augtool --autosave "
set /files/etc/sysctl.conf/kernel.core_pattern '|/usr/bin/coredump-compress %e %t %p %P'
set /files/etc/sysctl.conf/kernel.softlockup_panic 1
set /files/etc/sysctl.conf/kernel.panic 10
set /files/etc/sysctl.conf/kernel.panic_on_unrecovered_nmi 1
set /files/etc/sysctl.conf/vm.panic_on_oom 2
set /files/etc/sysctl.conf/fs.suid_dumpable 2
" -r $FILESYSTEM_ROOT

sysctl_net_cmd_string=""
while read line; do
  [[ "$line" =~ ^#.*$ ]] && continue
  sysctl_net_conf_key=`echo $line | awk -F '=' '{print $1}'`
  sysctl_net_conf_value=`echo $line | awk -F '=' '{print $2}'`
  sysctl_net_cmd_string=$sysctl_net_cmd_string"set /files/etc/sysctl.conf/$sysctl_net_conf_key $sysctl_net_conf_value"$'\n'
done < files/image_config/sysctl/sysctl-net.conf

sudo augtool --autosave "$sysctl_net_cmd_string" -r $FILESYSTEM_ROOT

if [[ $CONFIGURED_ARCH == amd64 ]]; then
    # Configure mcelog to log machine checks to syslog
    sudo sed -i 's/^#syslog = yes/syslog = yes/' $FILESYSTEM_ROOT/etc/mcelog/mcelog.conf
fi

## docker-py is needed by Ansible docker module
sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip install --upgrade 'pip==20.3.3'
sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip install 'docker-py==1.6.0'
## Note: keep pip installed for maintainance purpose

## Get gcc and python dev pkgs
sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y install gcc libpython2.7-dev
sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip install 'netifaces==0.10.7'

# Install scapy
sudo https_proxy=$https_proxy LANG=C chroot $FILESYSTEM_ROOT pip install 'scapy==2.4.4'

## Create /var/run/redis folder for docker-database to mount
sudo mkdir -p $FILESYSTEM_ROOT/var/run/redis

## Config DHCP for eth0
sudo tee -a $FILESYSTEM_ROOT/etc/network/interfaces > /dev/null <<EOF

auto eth0
allow-hotplug eth0
iface eth0 inet dhcp
EOF

sudo cp files/dhcp/rfc3442-classless-routes $FILESYSTEM_ROOT/etc/dhcp/dhclient-exit-hooks.d
sudo cp files/dhcp/sethostname $FILESYSTEM_ROOT/etc/dhcp/dhclient-exit-hooks.d/
sudo cp files/dhcp/sethostname6 $FILESYSTEM_ROOT/etc/dhcp/dhclient-exit-hooks.d/
sudo cp files/dhcp/graphserviceurl $FILESYSTEM_ROOT/etc/dhcp/dhclient-exit-hooks.d/
sudo cp files/dhcp/snmpcommunity $FILESYSTEM_ROOT/etc/dhcp/dhclient-exit-hooks.d/
sudo cp files/dhcp/vrf $FILESYSTEM_ROOT/etc/dhcp/dhclient-exit-hooks.d/
if [ -f files/image_config/ntp/ntp ]; then
    sudo cp ./files/image_config/ntp/ntp $FILESYSTEM_ROOT/etc/init.d/
fi

## Version file
sudo mkdir -p $FILESYSTEM_ROOT/etc/sonic
sudo tee $FILESYSTEM_ROOT/etc/sonic/sonic_version.yml > /dev/null <<EOF
build_version: '$(sonic_get_version)'
debian_version: '$(cat $FILESYSTEM_ROOT/etc/debian_version)'
kernel_version: '$kversion'
asic_type: $sonic_asic_platform
commit_id: '$(git rev-parse --short HEAD)'
build_date: $(date -u)
build_number: ${BUILD_NUMBER:-0}
built_by: $USER@$BUILD_HOSTNAME
EOF

## Copy over clean-up script
sudo cp ./files/scripts/core_cleanup.py $FILESYSTEM_ROOT/usr/bin/core_cleanup.py

## Copy ASIC config checksum
python files/build_scripts/generate_asic_config_checksum.py
if [[ ! -f './asic_config_checksum' ]]; then
    echo 'asic_config_checksum not found'
    exit 1
fi
sudo cp ./asic_config_checksum $FILESYSTEM_ROOT/etc/sonic/asic_config_checksum

if [ -f sonic_debian_extension.sh ]; then
    ./sonic_debian_extension.sh $FILESYSTEM_ROOT $PLATFORM_DIR
fi

## Organization specific extensions such as Configuration & Scripts for features like AAA, ZTP...
if [ "${enable_organization_extensions}" = "y" ]; then
   if [ -f files/build_templates/organization_extensions.sh ]; then
      sudo chmod 755 files/build_templates/organization_extensions.sh
      ./files/build_templates/organization_extensions.sh -f $FILESYSTEM_ROOT -h $HOSTNAME
   fi
fi

## Setup ebtable rules (rule file in text format)
sudo cp files/image_config/ebtables/ebtables.filter.cfg ${FILESYSTEM_ROOT}/etc

## Debug Image specific changes
## Update motd for debug image
if [ "$DEBUG_IMG" == "y" ]
then
    sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo '**************' >> /etc/motd"
    sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo 'Running DEBUG image' >> /etc/motd"
    sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo '**************' >> /etc/motd"
    sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo '/src has the sources' >> /etc/motd"
    sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo '/src is mounted in each docker' >> /etc/motd"
    sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo '/debug is created for core files or temp files' >> /etc/motd"
    sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo 'Create a subdir under /debug to upload your files' >> /etc/motd"
    sudo LANG=C chroot $FILESYSTEM_ROOT /bin/bash -c "echo '/debug is mounted in each docker' >> /etc/motd"

    sudo mkdir -p $FILESYSTEM_ROOT/src
    sudo cp $DEBUG_SRC_ARCHIVE_FILE $FILESYSTEM_ROOT/src/
    sudo mkdir -p $FILESYSTEM_ROOT/debug

fi

## Remove gcc and python dev pkgs
sudo LANG=C DEBIAN_FRONTEND=noninteractive chroot $FILESYSTEM_ROOT apt-get -y remove gcc libpython2.7-dev

## Update initramfs
sudo chroot $FILESYSTEM_ROOT update-initramfs -u

## Clean up apt
sudo LANG=C chroot $FILESYSTEM_ROOT apt-get -y autoremove
sudo LANG=C chroot $FILESYSTEM_ROOT apt-get autoclean
sudo LANG=C chroot $FILESYSTEM_ROOT apt-get clean
sudo LANG=C chroot $FILESYSTEM_ROOT bash -c 'rm -rf /usr/share/doc/* /usr/share/locale/* /var/lib/apt/lists/* /tmp/*'

## Clean up proxy
[ -n "$http_proxy" ] && sudo rm -f $FILESYSTEM_ROOT/etc/apt/apt.conf.d/01proxy

## Umount all
echo '[INFO] Umount all'
## Display all process details access /proc
sudo LANG=C chroot $FILESYSTEM_ROOT fuser -vm /proc
## Kill the processes
sudo LANG=C chroot $FILESYSTEM_ROOT fuser -km /proc || true
## Wait fuser fully kill the processes
sleep 15
sudo umount $FILESYSTEM_ROOT/proc || true

if [[ $CONFIGURED_ARCH == armhf || $CONFIGURED_ARCH == arm64 ]]; then
    # Remove qemu arm bin executable used for cross-building
    sudo rm -f $FILESYSTEM_ROOT/usr/bin/qemu*static || true
    DOCKERFS_PATH=../dockerfs/
fi

## Prepare empty directory to trigger mount move in initramfs-tools/mount_loop_root, implemented by patching
sudo mkdir $FILESYSTEM_ROOT/host

## Compress most file system into squashfs file
sudo rm -f $ONIE_INSTALLER_PAYLOAD $FILESYSTEM_SQUASHFS
## Output the file system total size for diag purpose
## Note: -x to skip directories on different file systems, such as /proc
sudo du -hsx $FILESYSTEM_ROOT
sudo mkdir -p $FILESYSTEM_ROOT/var/lib/docker
sudo mksquashfs $FILESYSTEM_ROOT $FILESYSTEM_SQUASHFS -e boot -e var/lib/docker -e $PLATFORM_DIR


# Ensure admin gid is 1000
gid_user=$(sudo LANG=C chroot $FILESYSTEM_ROOT id -g $USERNAME) || gid_user="none"
if [ "${gid_user}" != "1000" ]; then
    die "expect gid 1000. current:${gid_user}"
fi

## Compress docker files
pushd $FILESYSTEM_ROOT && sudo tar czf $OLDPWD/$FILESYSTEM_DOCKERFS -C ${DOCKERFS_PATH}var/lib/docker .; popd

## Compress together with /boot, /var/lib/docker and $PLATFORM_DIR as an installer payload zip file
pushd $FILESYSTEM_ROOT && sudo zip $OLDPWD/$ONIE_INSTALLER_PAYLOAD -r boot/ $PLATFORM_DIR/; popd
sudo zip -g $ONIE_INSTALLER_PAYLOAD $FILESYSTEM_SQUASHFS $FILESYSTEM_DOCKERFS
