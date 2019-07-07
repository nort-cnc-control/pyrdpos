#!/usr/bin/env python3
#-*- encoding: utf-8 -*-

from distutils.core import setup, Extension
import pkgconfig

install_requires = [
    'rdp',
    'serial_datagram',
]

setup(name = 'RDPoS', version = '1.0', py_modules=['rdpos'])
