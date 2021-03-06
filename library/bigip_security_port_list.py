#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2017, F5 Networks Inc.
# GNU General Public License v3.0 (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: bigip_security_port_list
short_description: Manage port lists on BIG-IP AFM
description:
  - Manages the AFM port lists on a BIG-IP. This module can be used to add
    and remove port list entries.
version_added: "2.5"
options:
  name:
    description:
      - Specifies the name of the port list.
    required: True
  partition:
    description:
      - Device partition to manage resources on.
    default: Common
    version_added: 2.5
  description:
    description:
      - Description of the port list
  ports:
    description:
      - Simple list of port values to add to the list
  port_ranges:
    description:
      - A list of port ranges where the range starts with a port number, is followed
        by a dash (-) and then a second number.
      - If the first number is greater than the second number, the numbers will be
        reversed so-as to be properly formatted. ie, 90-78 would become 78-90.
  port_lists:
    description:
      - Simple list of existing port lists to add to this list. Port lists can be
        specified in either their fully qualified name (/Common/foo) or their short
        name (foo). If a short name is used, the C(partition) argument will automatically
        be prepended to the short name.
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as pip
    install f5-sdk.
requirements:
  - f5-sdk >= 3.0.4
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = r'''
- name: Create a simple port list
  bigip_security_port_list:
    name: foo
    ports:
      - 80
      - 443
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost

- name: Override the above list of ports with a new list
  bigip_security_port_list:
    name: foo
    ports:
      - 3389
      - 8080
      - 25
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost

- name: Create port list with series of ranges
  bigip_security_port_list:
    name: foo
    port_ranges:
      - 25-30
      - 80-500
      - 50-78
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost

- name: Use multiple types of port arguments
  bigip_security_port_list:
    name: foo
    port_ranges:
      - 25-30
      - 80-500
      - 50-78
    ports:
      - 8080
      - 443
    password: secret
    server: lb.mydomain.com
    state: present
    user: admin
  delegate_to: localhost

- name: Remove port list
  bigip_security_port_list:
    name: foo
    password: secret
    server: lb.mydomain.com
    state: absent
    user: admin
  delegate_to: localhost
'''

RETURN = r'''
ports:
  description: The new list of ports applied to the port list
  returned: changed
  type: list
  sample: [80, 443]
port_ranges:
  description: The new list of port ranges applied to the port list
  returned: changed
  type: list
  sample: [80-100, 200-8080]
ports:
  description: The new list of ports applied to the port list
  returned: changed
  type: list
  sample: [80, 443]
port_lists:
  description: The new list of port list names applied to the port list
  returned: changed
  type: list
  sample: [/Common/list1, /Common/list2]
'''

from ansible.module_utils.f5_utils import AnsibleF5Client
from ansible.module_utils.f5_utils import AnsibleF5Parameters
from ansible.module_utils.f5_utils import HAS_F5SDK
from ansible.module_utils.f5_utils import F5ModuleError
from ansible.module_utils.six import iteritems
from collections import defaultdict

try:
    from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
except ImportError:
    HAS_F5SDK = False


class Parameters(AnsibleF5Parameters):
    api_map = {
        'portLists': 'port_lists'
    }

    api_attributes = [
        'portLists', 'ports'
    ]

    returnables = [
        'ports', 'port_ranges', 'port_lists', 'description'
    ]

    updatables = [
        'description', 'ports', 'port_ranges', 'port_lists'
    ]

    def __init__(self, params=None):
        self._values = defaultdict(lambda: None)
        self._values['__warnings'] = []
        if params:
            self.update(params=params)

    def update(self, params=None):
        if params:
            for k, v in iteritems(params):
                if self.api_map is not None and k in self.api_map:
                    map_key = self.api_map[k]
                else:
                    map_key = k

                # Handle weird API parameters like `dns.proxy.__iter__` by
                # using a map provided by the module developer
                class_attr = getattr(type(self), map_key, None)
                if isinstance(class_attr, property):
                    # There is a mapped value for the api_map key
                    if class_attr.fset is None:
                        # If the mapped value does not have
                        # an associated setter
                        self._values[map_key] = v
                    else:
                        # The mapped value has a setter
                        setattr(self, map_key, v)
                else:
                    # If the mapped value is not a @property
                    self._values[map_key] = v

    def _fqdn_name(self, value):
        if value is not None and not value.startswith('/'):
            return '/{0}/{1}'.format(self.partition, value)
        return value

    def api_params(self):
        result = {}
        for api_attribute in self.api_attributes:
            if self.api_map is not None and api_attribute in self.api_map:
                result[api_attribute] = getattr(self, self.api_map[api_attribute])
            else:
                result[api_attribute] = getattr(self, api_attribute)
        result = self._filter_params(result)
        return result


class ApiParameters(Parameters):
    @property
    def port_ranges(self):
        if self._values['ports'] is None:
            return None
        result = []
        for port_range in self._values['ports']:
            if '-' not in port_range['name']:
                continue
            start, stop = port_range['name'].split('-')
            start = int(start.strip())
            stop = int(stop.strip())
            if start > stop:
                stop, start = start, stop
            item = '{0}-{1}'.format(start, stop)
            result.append(item)
        return result

    @property
    def port_lists(self):
        if self._values['port_lists'] is None:
            return None
        result = []
        for x in self._values['port_lists']:
            item = '/{0}/{1}'.format(x['partition'], x['name'])
            result.append(item)
        return result

    @property
    def ports(self):
        if self._values['ports'] is None:
            return None
        result = [int(x['name']) for x in self._values['ports'] if '-' not in x['name']]
        return result


class ModuleParameters(Parameters):
    @property
    def ports(self):
        if self._values['ports'] is None:
            return None
        if any(x for x in self._values['ports'] if '-' in str(x)):
            raise F5ModuleError(
                "Ports must be whole numbers between 0 and 65,535"
            )
        if any(x for x in self._values['ports'] if 0 < x > 65535):
            raise F5ModuleError(
                "Ports must be whole numbers between 0 and 65,535"
            )
        result = [int(x) for x in self._values['ports']]
        return result

    @property
    def port_ranges(self):
        if self._values['port_ranges'] is None:
            return None
        result = []
        for port_range in self._values['port_ranges']:
            if '-' not in port_range:
                continue
            start, stop = port_range.split('-')
            start = int(start.strip())
            stop = int(stop.strip())
            if start > stop:
                stop, start = start, stop
            if 0 < start > 65535 or 0 < stop > 65535:
                raise F5ModuleError(
                    "Ports must be whole numbers between 0 and 65,535"
                )
            item = '{0}-{1}'.format(start, stop)
            result.append(item)
        return result


class Changes(Parameters):
    def to_return(self):
        result = {}
        try:
            for returnable in self.returnables:
                result[returnable] = getattr(self, returnable)
            result = self._filter_params(result)
        except Exception:
            pass
        return result


class ReportableChanges(Changes):
    pass


class UsableChanges(Changes):
    @property
    def ports(self):
        if self._values['ports'] is None and self._values['port_ranges'] is None:
            return None
        result = []
        if self._values['ports']:
            # The values of the 'key' index literally need to be string values.
            # If they are not, on BIG-IP 12.1.0 they will raise this REST exception.
            #
            # {
            #   "code": 400,
            #   "message": "one or more configuration identifiers must be provided",
            #   "errorStack": [],
            #   "apiError": 26214401
            # }
            result += [dict(name=str(x)) for x in self._values['ports']]
        if self._values['port_ranges']:
            result += [dict(name=str(x)) for x in self._values['port_ranges']]
        return result

    @property
    def port_lists(self):
        if self._values['port_lists'] is None:
            return None
        result = []
        for x in self._values['port_lists']:
            name, partition = x.split('/')
            result.append(dict(
                name=name,
                partition=partition
            ))
        return result


class Difference(object):
    def __init__(self, want, have=None):
        self.want = want
        self.have = have

    def compare(self, param):
        try:
            result = getattr(self, param)
            return result
        except AttributeError:
            return self.__default(param)

    def __default(self, param):
        attr1 = getattr(self.want, param)
        try:
            attr2 = getattr(self.have, param)
            if attr1 != attr2:
                return attr1
        except AttributeError:
            return attr1

    @property
    def ports(self):
        if self.want.ports is None:
            return None
        elif self.have.ports is None:
            return self.want.ports
        if sorted(self.want.ports) != sorted(self.have.ports):
            return self.want.ports

    @property
    def port_lists(self):
        if self.want.port_lists is None:
            return None
        elif self.have.port_lists is None:
            return self.want.port_lists
        if sorted(self.want.port_lists) != sorted(self.have.port_lists):
            return self.want.port_lists

    @property
    def port_ranges(self):
        if self.want.port_ranges is None:
            return None
        elif self.have.port_ranges is None:
            return self.want.port_ranges
        if sorted(self.want.port_ranges) != sorted(self.have.port_ranges):
            return self.want.port_ranges


class ModuleManager(object):
    def __init__(self, client):
        self.client = client
        self.want = ModuleParameters(params=self.client.module.params)
        self.have = ApiParameters()
        self.changes = UsableChanges()

    def _set_changed_options(self):
        changed = {}
        for key in Parameters.returnables:
            if getattr(self.want, key) is not None:
                changed[key] = getattr(self.want, key)
        if changed:
            self.changes = UsableChanges(changed)

    def _update_changed_options(self):
        diff = Difference(self.want, self.have)
        updatables = Parameters.updatables
        changed = dict()
        for k in updatables:
            change = diff.compare(k)
            if change is None:
                continue
            else:
                if isinstance(change, dict):
                    changed.update(change)
                else:
                    changed[k] = change
        if changed:
            self.changes = UsableChanges(changed)
            return True
        return False

    def should_update(self):
        result = self._update_changed_options()
        if result:
            return True
        return False

    def exec_module(self):
        changed = False
        result = dict()
        state = self.want.state

        try:
            if state == "present":
                changed = self.present()
            elif state == "absent":
                changed = self.absent()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        reportable = ReportableChanges(self.changes.to_return())
        changes = reportable.to_return()
        result.update(**changes)
        result.update(dict(changed=changed))
        self._announce_deprecations(result)
        return result

    def _announce_deprecations(self, result):
        warnings = result.pop('__warnings', [])
        for warning in warnings:
            self.client.module.deprecate(
                msg=warning['msg'],
                version=warning['version']
            )

    def present(self):
        if self.exists():
            return self.update()
        else:
            return self.create()

    def exists(self):
        result = self.client.api.tm.security.firewall.port_lists.port_list.exists(
            name=self.want.name,
            partition=self.want.partition
        )
        return result

    def update(self):
        self.have = self.read_current_from_device()
        if not self.should_update():
            return False
        if self.client.check_mode:
            return True
        self.update_on_device()
        return True

    def remove(self):
        if self.client.check_mode:
            return True
        self.remove_from_device()
        if self.exists():
            raise F5ModuleError("Failed to delete the resource.")
        return True

    def create(self):
        self._set_changed_options()
        if self.client.check_mode:
            return True
        self.create_on_device()
        return True

    def create_on_device(self):
        params = self.changes.api_params()
        self.client.api.tm.security.firewall.port_lists.port_list.create(
            name=self.want.name,
            partition=self.want.partition,
            **params
        )

    def update_on_device(self):
        params = self.changes.api_params()
        resource = self.client.api.tm.security.firewall.port_lists.port_list.load(
            name=self.want.name,
            partition=self.want.partition
        )
        resource.modify(**params)

    def absent(self):
        if self.exists():
            return self.remove()
        return False

    def remove_from_device(self):
        resource = self.client.api.tm.security.firewall.port_lists.port_list.load(
            name=self.want.name,
            partition=self.want.partition
        )
        if resource:
            resource.delete()

    def read_current_from_device(self):
        resource = self.client.api.tm.security.firewall.port_lists.port_list.load(
            name=self.want.name,
            partition=self.want.partition
        )
        result = resource.attrs
        return ApiParameters(result)


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.argument_spec = dict(
            name=dict(required=True),
            description=dict(),
            ports=dict(type='list'),
            port_ranges=dict(type='list'),
            port_lists=dict(type='list')
        )
        self.f5_product_name = 'bigip'


def cleanup_tokens(client):
    try:
        resource = client.api.shared.authz.tokens_s.token.load(
            name=client.api.icrs.token
        )
        resource.delete()
    except Exception:
        pass


def main():
    if not HAS_F5SDK:
        raise F5ModuleError("The python f5-sdk module is required")

    spec = ArgumentSpec()

    client = AnsibleF5Client(
        argument_spec=spec.argument_spec,
        supports_check_mode=spec.supports_check_mode,
        f5_product_name=spec.f5_product_name
    )

    try:
        mm = ModuleManager(client)
        results = mm.exec_module()
        cleanup_tokens(client)
        client.module.exit_json(**results)
    except F5ModuleError as e:
        cleanup_tokens(client)
        client.module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
