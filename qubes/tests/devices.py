# pylint: disable=protected-access,pointless-statement

#
# The Qubes OS Project, https://www.qubes-os.org/
#
# Copyright (C) 2015-2016  Joanna Rutkowska <joanna@invisiblethingslab.com>
# Copyright (C) 2015-2016  Wojtek Porczyk <woju@invisiblethingslab.com>
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

import qubes.devices

import qubes.tests

class TestDevice(qubes.devices.DeviceInfo):
    # pylint: disable=too-few-public-methods
    pass


class TestVMCollection(dict):
    def __iter__(self):
        return iter(set(self.values()))


class TestApp(object):
    # pylint: disable=too-few-public-methods
    def __init__(self):
        self.domains = TestVMCollection()


class TestVM(qubes.tests.TestEmitter):
    def __init__(self, app, name, *args, **kwargs):
        super(TestVM, self).__init__(*args, **kwargs)
        self.app = app
        self.name = name
        self.device = TestDevice(self, 'testdev', 'Description')
        self.events_enabled = True
        self.devices = {
            'testclass': qubes.devices.DeviceCollection(self, 'testclass')
        }
        self.app.domains[name] = self
        self.app.domains[self] = self
        self.running = False

    def __str__(self):
        return self.name

    @qubes.events.handler('device-list-attached:testclass')
    def dev_testclass_list_attached(self, event, persistent = False):
        for vm in self.app.domains:
            if vm.device.frontend_domain == self:
                yield (vm.device, {})

    @qubes.events.handler('device-list:testclass')
    def dev_testclass_list(self, event):
        yield self.device

    def is_halted(self):
        return not self.running



class TC_00_DeviceCollection(qubes.tests.QubesTestCase):
    def setUp(self):
        super().setUp()
        self.app = TestApp()
        self.emitter = TestVM(self.app, 'vm')
        self.app.domains['vm'] = self.emitter
        self.device = self.emitter.device
        self.collection = self.emitter.devices['testclass']
        self.assignment = qubes.devices.DeviceAssignment(
            backend_domain=self.device.backend_domain,
            ident=self.device.ident,
            persistent=True
        )

    def test_000_init(self):
        self.assertFalse(self.collection._set)

    def test_001_attach(self):
        self.collection.attach(self.assignment)
        self.assertEventFired(self.emitter, 'device-pre-attach:testclass')
        self.assertEventFired(self.emitter, 'device-attach:testclass')
        self.assertEventNotFired(self.emitter, 'device-pre-detach:testclass')
        self.assertEventNotFired(self.emitter, 'device-detach:testclass')

    def test_002_detach(self):
        self.collection.attach(self.assignment)
        self.collection.detach(self.assignment)
        self.assertEventFired(self.emitter, 'device-pre-attach:testclass')
        self.assertEventFired(self.emitter, 'device-attach:testclass')
        self.assertEventFired(self.emitter, 'device-pre-detach:testclass')
        self.assertEventFired(self.emitter, 'device-detach:testclass')

    def test_010_empty_detach(self):
        with self.assertRaises(LookupError):
            self.collection.detach(self.assignment)

    def test_011_double_attach(self):
        self.collection.attach(self.assignment)

        with self.assertRaises(qubes.devices.DeviceAlreadyAttached):
            self.collection.attach(self.assignment)

    def test_012_double_detach(self):
        self.collection.attach(self.assignment)
        self.collection.detach(self.assignment)

        with self.assertRaises(qubes.devices.DeviceNotAttached):
            self.collection.detach(self.assignment)

    def test_013_list_attached_persistent(self):
        self.assertEqual(set([]), set(self.collection.persistent()))
        self.collection.attach(self.assignment)
        self.assertEventFired(self.emitter, 'device-list-attached:testclass')
        self.assertEqual({self.device}, set(self.collection.persistent()))
        self.assertEqual({self.device},
            set(self.collection.persistent()))
        self.assertEqual(set([]),
            set(self.collection.attached()))

    def test_014_list_attached_non_persistent(self):
        self.assignment.persistent = False
        self.emitter.running = True
        self.collection.attach(self.assignment)
        # device-attach event not implemented, so manipulate object manually
        self.device.frontend_domain = self.emitter
        self.assertEqual({self.device},
            set(self.collection.attached()))
        self.assertEqual(set([]),
            set(self.collection.persistent()))
        self.assertEqual({self.device},
            set(self.collection.attached()))
        self.assertEventFired(self.emitter, 'device-list-attached:testclass')

    def test_015_list_available(self):
        self.assertEqual({self.device}, set(self.collection))
        self.assertEventFired(self.emitter, 'device-list:testclass')


class TC_01_DeviceManager(qubes.tests.QubesTestCase):
    def setUp(self):
        super().setUp()
        self.app = TestApp()
        self.emitter = TestVM(self.app, 'vm')
        self.manager = qubes.devices.DeviceManager(self.emitter)

    def test_000_init(self):
        self.assertEqual(self.manager, {})

    def test_001_missing(self):
        device = TestDevice(self.emitter.app.domains['vm'], 'testdev')
        assignment = qubes.devices.DeviceAssignment(
            backend_domain=device.backend_domain,
            ident=device.ident,
            persistent=True)
        self.manager['testclass'].attach(assignment)
        self.assertEventFired(self.emitter, 'device-attach:testclass')

