from setuptools import setup

DEVICE_NAME = 'accton'
HW_SKU = 'x86_64-accton_csp7551-r0'  

setup(
    name='sonic-platform',
    version='1.0',
    description='SONiC platform API implementation on Accton Platforms',
    license='Apache 2.0',
    author='SONiC Team',
    author_email='linuxnetdev@microsoft.com',
    url='https://github.com/Azure/sonic-buildimage',
    maintainer='Jostar Yang',
    maintainer_email='will_chen@accton.com',
    packages=[
        'sonic_platform',
    ],
    package_dir={
        'sonic_platform': 'sonic_platform'},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Plugins',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.7',
        'Topic :: Utilities',
    ],
    keywords='sonic SONiC platform PLATFORM',
)
