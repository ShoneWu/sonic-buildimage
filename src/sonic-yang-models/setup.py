import shutil
import os
import glob
import jinja2
from setuptools import setup, find_packages
from setuptools.command.build_py import build_py

# read me
with open('README.rst') as readme_file:
    readme = readme_file.read()

class my_build_py(build_py):
    def run(self):
        if not self.dry_run:
            print("hehe")

        if not os.path.exists("./yang-models"):
            os.makedirs("./yang-models")

        if not os.path.exists("./cvlyang-models"):
            os.makedirs("./cvlyang-models")

        # copy non-template yang model to internal yang model directory
        for fname in glob.glob("./yang-models/*.yang"):
            bfname = os.path.basename(fname)
            shutil.copyfile("./yang-models/{}".format(bfname), "./cvlyang-models/{}".format(bfname))

        # templated yang models
        env = jinja2.Environment(loader=jinja2.FileSystemLoader('./yang-templates/'), trim_blocks=True)
        for fname in glob.glob("./yang-templates/*.yang.j2"):
            bfname = os.path.basename(fname)
            template = env.get_template(bfname)
            yang_model = template.render(yang_model_type="py")
            cvlyang_model = template.render(yang_model_type="cvl")
            with open("./yang-models/{}".format(bfname.strip(".j2")), 'w') as f:
                f.write(yang_model)
            with open("./cvlyang-models/{}".format(bfname.strip(".j2")), 'w') as f:
                f.write(cvlyang_model)

        build_py.run(self)

setup(
    author="lnos-coders",
    author_email='lnos-coders@linkedin.com',
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Package contains YANG models for sonic.",
    license="GNU General Public License v3",
    long_description=readme + '\n\n',
    install_requires = [
    ],
    tests_require = [
        'pytest',
        'ijson==2.6.1'
    ],
    setup_requires = [
        'pytest-runner',
        'wheel'
    ],
    include_package_data=True,
    keywords='sonic-yang-models',
    name='sonic-yang-models',
    py_modules=[],
    packages=find_packages(),
    version='1.0',
    cmdclass={'build_py': my_build_py},
    data_files=[
        ('yang-models', ['./yang-models/sonic-acl.yang',
                         './yang-models/sonic-auto_techsupport.yang',
                         './yang-models/sonic-bgp-common.yang',
                         './yang-models/sonic-bgp-device-global.yang',
                         './yang-models/sonic-bgp-global.yang',
                         './yang-models/sonic-bgp-monitor.yang',
                         './yang-models/sonic-bgp-internal-neighbor.yang',
                         './yang-models/sonic-bgp-neighbor.yang',
                         './yang-models/sonic-bgp-peergroup.yang',
                         './yang-models/sonic-bgp-peerrange.yang',
                         './yang-models/sonic-bgp-allowed-prefix.yang',
                         './yang-models/sonic-bgp-voq-chassis-neighbor.yang',
                         './yang-models/sonic-breakout_cfg.yang',
                         './yang-models/sonic-buffer-pg.yang',
                         './yang-models/sonic-buffer-pool.yang',
                         './yang-models/sonic-buffer-port-ingress-profile-list.yang',
                         './yang-models/sonic-buffer-port-egress-profile-list.yang',
                         './yang-models/sonic-buffer-profile.yang',
                         './yang-models/sonic-buffer-queue.yang',
                         './yang-models/sonic-cable-length.yang',
                         './yang-models/sonic-chassis-module.yang',                         
                         './yang-models/sonic-copp.yang',
                         './yang-models/sonic-crm.yang',
                         './yang-models/sonic-default-lossless-buffer-parameter.yang',
                         './yang-models/sonic-device_metadata.yang',
                         './yang-models/sonic-device_neighbor.yang',
                         './yang-models/sonic-device_neighbor_metadata.yang',
                         './yang-models/sonic-dhcpv6-relay.yang',
                         './yang-models/sonic-extension.yang',
                         './yang-models/sonic-flex_counter.yang',
                         './yang-models/sonic-feature.yang',
                         './yang-models/sonic-system-defaults.yang',
                         './yang-models/sonic-interface.yang',
                         './yang-models/sonic-kdump.yang',
                         './yang-models/sonic-loopback-interface.yang',
                         './yang-models/sonic-lossless-traffic-pattern.yang',
                         './yang-models/sonic-mgmt_interface.yang',
                         './yang-models/sonic-mgmt_port.yang',
                         './yang-models/sonic-mgmt_vrf.yang',
                         './yang-models/sonic-mirror-session.yang',
                         './yang-models/sonic-mux-cable.yang',
                         './yang-models/sonic-mux-linkmgr.yang',
                         './yang-models/sonic-ntp.yang',
                         './yang-models/sonic-nat.yang',
                         './yang-models/sonic-nvgre-tunnel.yang',
                         './yang-models/sonic-passwh.yang',
                         './yang-models/sonic-pbh.yang',
                         './yang-models/sonic-port.yang',
                         './yang-models/sonic-policer.yang',
                         './yang-models/sonic-portchannel.yang',
                         './yang-models/sonic-pfcwd.yang',
                         './yang-models/sonic-route-common.yang',
                         './yang-models/sonic-route-map.yang',
                         './yang-models/sonic-routing-policy-sets.yang',
                         './yang-models/sonic-sflow.yang',
                         './yang-models/sonic-snmp.yang',
                         './yang-models/sonic-syslog.yang',
                         './yang-models/sonic-system-aaa.yang',
                         './yang-models/sonic-system-tacacs.yang',
                         './yang-models/sonic-system-radius.yang',
                         './yang-models/sonic-telemetry.yang',
                         './yang-models/sonic-types.yang',
                         './yang-models/sonic-versions.yang',
                         './yang-models/sonic-vlan.yang',
                         './yang-models/sonic-voq-inband-interface.yang',
                         './yang-models/sonic-vrf.yang',
                         './yang-models/sonic-mclag.yang',
                         './yang-models/sonic-vlan-sub-interface.yang',
                         './yang-models/sonic-warm-restart.yang',
                         './yang-models/sonic-lldp.yang',
                         './yang-models/sonic-scheduler.yang',
                         './yang-models/sonic-wred-profile.yang',
                         './yang-models/sonic-queue.yang',
                         './yang-models/sonic-dscp-fc-map.yang',
                         './yang-models/sonic-exp-fc-map.yang',
                         './yang-models/sonic-dscp-tc-map.yang',
                         './yang-models/sonic-dot1p-tc-map.yang',
                         './yang-models/sonic-storm-control.yang',
                         './yang-models/sonic-tc-priority-group-map.yang',
                         './yang-models/sonic-tc-queue-map.yang',
                         './yang-models/sonic-peer-switch.yang',
                         './yang-models/sonic-pfc-priority-queue-map.yang',
                         './yang-models/sonic-pfc-priority-priority-group-map.yang',
                         './yang-models/sonic-port-qos-map.yang',
                         './yang-models/sonic-macsec.yang']),
        ('cvlyang-models', ['./cvlyang-models/sonic-acl.yang',
                         './cvlyang-models/sonic-bgp-common.yang',
                         './cvlyang-models/sonic-bgp-global.yang',
                         './cvlyang-models/sonic-bgp-monitor.yang',
                         './cvlyang-models/sonic-bgp-neighbor.yang',
                         './cvlyang-models/sonic-bgp-peergroup.yang',
                         './cvlyang-models/sonic-bgp-peerrange.yang',
                         './cvlyang-models/sonic-bgp-allowed-prefix.yang',
                         './cvlyang-models/sonic-breakout_cfg.yang',
                         './cvlyang-models/sonic-copp.yang',
                         './cvlyang-models/sonic-crm.yang',
                         './cvlyang-models/sonic-device_metadata.yang',
                         './cvlyang-models/sonic-device_neighbor.yang',
                         './cvlyang-models/sonic-device_neighbor_metadata.yang',
                         './cvlyang-models/sonic-extension.yang',
                         './cvlyang-models/sonic-flex_counter.yang',
                         './cvlyang-models/sonic-feature.yang',
                         './cvlyang-models/sonic-system-defaults.yang',
                         './cvlyang-models/sonic-interface.yang',
                         './cvlyang-models/sonic-kdump.yang',
                         './cvlyang-models/sonic-loopback-interface.yang',
                         './cvlyang-models/sonic-mgmt_interface.yang',
                         './cvlyang-models/sonic-mgmt_port.yang',
                         './cvlyang-models/sonic-mgmt_vrf.yang',
                         './cvlyang-models/sonic-ntp.yang',
                         './cvlyang-models/sonic-nat.yang',
                         './cvlyang-models/sonic-nvgre-tunnel.yang',
                         './cvlyang-models/sonic-pbh.yang',
                         './cvlyang-models/sonic-policer.yang',
                         './cvlyang-models/sonic-port.yang',
                         './cvlyang-models/sonic-portchannel.yang',
                         './cvlyang-models/sonic-pfcwd.yang',
                         './cvlyang-models/sonic-route-common.yang',
                         './cvlyang-models/sonic-route-map.yang',
                         './cvlyang-models/sonic-routing-policy-sets.yang',
                         './cvlyang-models/sonic-sflow.yang',
                         './cvlyang-models/sonic-snmp.yang',
                         './cvlyang-models/sonic-system-aaa.yang',
                         './cvlyang-models/sonic-system-tacacs.yang',
                         './cvlyang-models/sonic-telemetry.yang',
                         './cvlyang-models/sonic-types.yang',
                         './cvlyang-models/sonic-versions.yang',
                         './cvlyang-models/sonic-vlan.yang',
                         './cvlyang-models/sonic-vrf.yang',
                         './cvlyang-models/sonic-warm-restart.yang',
                         './cvlyang-models/sonic-lldp.yang',
                         './cvlyang-models/sonic-scheduler.yang',
                         './cvlyang-models/sonic-wred-profile.yang',
                         './cvlyang-models/sonic-queue.yang',
                         './cvlyang-models/sonic-dscp-tc-map.yang',
                         './cvlyang-models/sonic-dot1p-tc-map.yang',
                         './cvlyang-models/sonic-tc-priority-group-map.yang',
                         './cvlyang-models/sonic-tc-queue-map.yang',
                         './cvlyang-models/sonic-pfc-priority-queue-map.yang',
                         './cvlyang-models/sonic-pfc-priority-priority-group-map.yang',
                         './cvlyang-models/sonic-port-qos-map.yang',
                         './cvlyang-models/sonic-macsec.yang']),
    ],
    zip_safe=False,
)
