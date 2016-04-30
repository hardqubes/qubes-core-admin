#!/usr/bin/python2
# -*- encoding: utf8 -*-
#
# The Qubes OS Project, http://www.qubes-os.org
#
# Copyright (C) 2010-2015  Joanna Rutkowska <joanna@invisiblethingslab.com>
# Copyright (C) 2015       Wojtek Porczyk <woju@invisiblethingslab.com>
# Copyright (C) 2016       Bahtiar `kalkin-` Gadimov <bahtiar@gadimov.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
import os

from qubes.storage import Pool, StoragePoolException, Volume


class LinuxModules(Volume):
    rw = False

    def __init__(self, target_dir, kernel_version, **kwargs):
        super(LinuxModules, self).__init__(**kwargs)
        self.kernels_dir = os.path.join(target_dir, kernel_version)
        self.path = os.path.join(self.kernels_dir, 'modules.img')
        self.vid = self.path
        self.vmlinuz = os.path.join(self.kernels_dir, 'vmlinuz')
        self.initramfs = os.path.join(self.kernels_dir, 'initramfs')


class LinuxKernel(Pool):
    driver = 'linux-kernel'

    def __init__(self, name=None, dir_path=None):
        assert dir_path, 'Missing dir_path'
        super(LinuxKernel, self).__init__(name=name)
        self.dir_path = dir_path

    def init_volume(self, vm, volume_config):
        assert 'volume_type' in volume_config, "Volume type missing " \
            + str(volume_config)
        volume_type = volume_config['volume_type']
        if volume_type != 'read-only':
            raise StoragePoolException("Unknown volume type " + volume_type)

        volume = LinuxModules(self.dir_path, vm.kernel, **volume_config)

        _check_path(volume.path)
        _check_path(volume.vmlinuz)
        _check_path(volume.initramfs)

        return volume

    def clone(self, source, target):
        return target

    def create(self, volume, source_volume):
        return volume

    def commit_template_changes(self, volume):
        return volume

    @property
    def config(self):
        return {
            'name': self.name,
            'dir_path': self.dir_path,
            'driver': LinuxKernel.driver,
        }

    def destroy(self):
        pass

    def remove(self, volume):
        pass

    def rename(self, volume, old_name, new_name):
        return volume

    def setup(self):
        pass

    def start(self, volume):
        path = volume.path
        if not os.path.exists(path):
            raise StoragePoolException('Missing kernel modules: %s' % path)

        return volume

    def stop(self, volume):
        pass


def _check_path(path):
    ''' Raise an :py:class:`qubes.storage.StoragePoolException` if ``path`` does
        not exist.
    '''
    if not os.path.exists(path):
        raise StoragePoolException('Missing file: %s' % path)