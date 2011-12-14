#!/usr/bin/env python
#
# Copyright (C) 2011 Linaro Limited
#
# Author: Zygmunt Krynicki <zygmunt.krynicki@linaro.org>
#
# This file is part of LAVA Serial
#
# LAVA Serial is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3
# as published by the Free Software Foundation
#
# LAVA Serial is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with LAVA Serial.  If not, see <http://www.gnu.org/licenses/>.


try:
    from setuptools import setup, find_packages
except ImportError:
    print "This package requires setuptools to be configured"
    print "It can be installed with debian/ubuntu package python-setuptools"
    raise


setup(
    name='lava-serial',
    version=":versiontools:lava.serial:",
    author="Zygmunt Krynicki",
    author_email="zygmunt.krynicki@linaro.org",
    namespace_packages=['lava'],
    packages=find_packages(),
    description="LAVA friendly serial line support",
    license="AGPL",
    entry_points="""
    [lava.commands]
    serial = lava.serial.commands:SerialCommand
    [lava.serial.commands]
    console = lava.serial.commands:ConsoleCommand
    """,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Topic :: Software Development :: Testing"],
    install_requires=[
        'versiontools >= 1.8.2',
        'lava-tool >= 0.3a1',
        'pyserial >= 2.6',
    ],
    setup_requires=[
        'versiontools >= 1.8.2'
    ],
    zip_safe=True,
    include_package_data=True
)
