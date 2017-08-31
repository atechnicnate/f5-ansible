#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2016 F5 Networks Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {
    'status': ['preview'],
    'supported_by': 'community',
    'metadata_version': '1.0'
}

DOCUMENTATION = '''
---
module: bigip_raw
short_description: Run raw commands on F5 devices.
description:
  - Sends an arbitrary command to a BIG-IP node and returns the results
    read from the device. This module includes an argument that will cause
    the module to wait for a specific condition before returning or timing
    out if the condition is not met. This module is different from the
    C(bigip_command) module, insofar as it does B(not) automatically run
    commands in C(tmsh).
version_added: "2.5"
options:
  commands:
    description:
      - The commands to send to the remote BIG-IP device over the
        configured provider. The resulting output from the command
        is returned. If the I(wait_for) argument is provided, the
        module is not returned until the condition is satisfied or
        the number of retries as expired.
      - The I(commands) argument also accepts an alternative form
        that allows for complex values that specify the command
        to run and the output format to return. This can be done
        on a command by command basis. The complex argument supports
        the keywords C(command) and C(output) where C(command) is the
        command to run and C(output) is 'text' or 'one-line'.
    required: True
  wait_for:
    description:
      - Specifies what to evaluate from the output of the command
        and what conditionals to apply.  This argument will cause
        the task to wait for a particular conditional to be true
        before moving forward. If the conditional is not true
        by the configured retries, the task fails. See examples.
    aliases: ['waitfor']
  match:
    description:
      - The I(match) argument is used in conjunction with the
        I(wait_for) argument to specify the match policy. Valid
        values are C(all) or C(any). If the value is set to C(all)
        then all conditionals in the I(wait_for) must be satisfied. If
        the value is set to C(any) then only one of the values must be
        satisfied.
    default: all
  retries:
    description:
      - Specifies the number of retries a command should by tried
        before it is considered failed. The command is run on the
        target device every retry and evaluated against the I(wait_for)
        conditionals.
    default: 10
  interval:
    description:
      - Configures the interval in seconds to wait between retries
        of the command. If the command does not pass the specified
        conditional, the interval indicates how to long to wait before
        trying the command again.
    default: 1
notes:
  - Requires the f5-sdk Python package on the host. This is as easy as pip
    install f5-sdk.
requirements:
  - f5-sdk >= 2.2.3
extends_documentation_fragment: f5
author:
  - Tim Rupp (@caphrim007)
'''

EXAMPLES = '''
- name: Run show version on remote devices
  bigip_raw:
    commands: show sys version
    server: "lb.mydomain.com"
    password: "secret"
    user: "admin"
    validate_certs: "no"
  delegate_to: localhost

- name: Run show version and check to see if output contains BIG-IP
  bigip_raw:
    commands: show sys version
    wait_for: result[0] contains BIG-IP
    server: "lb.mydomain.com"
    password: "secret"
    user: "admin"
    validate_certs: "no"
  delegate_to: localhost

- name: Run multiple commands on remote nodes
  bigip_raw:
    commands:
      - show sys version
      - list ltm virtual
    server: "lb.mydomain.com"
    password: "secret"
    user: "admin"
    validate_certs: "no"
  delegate_to: localhost

- name: Run multiple commands and evaluate the output
  bigip_raw:
    commands:
      - show sys version
      - list ltm virtual
    wait_for:
      - result[0] contains BIG-IP
      - result[1] contains my-vs
    server: "lb.mydomain.com"
    password: "secret"
    user: "admin"
    validate_certs: "no"
  delegate_to: localhost
'''

RETURN = '''
stdout:
    description: The set of responses from the commands
    returned: always
    type: list
    sample: ['...', '...']

stdout_lines:
    description: The value of stdout split into a list
    returned: always
    type: list
    sample: [['...', '...'], ['...'], ['...']]

failed_conditions:
    description: The list of conditionals that have failed
    returned: failed
    type: list
    sample: ['...', '...']
'''

import time

from ansible.module_utils.f5_utils import AnsibleF5Client
from ansible.module_utils.f5_utils import AnsibleF5Parameters
from ansible.module_utils.f5_utils import HAS_F5SDK
from ansible.module_utils.f5_utils import F5ModuleError
from ansible.module_utils.f5_utils import iControlUnexpectedHTTPError
from ansible.module_utils.netcli import FailedConditionsError
from ansible.module_utils.six import string_types
from ansible.module_utils.netcli import Conditional
from ansible.module_utils.network_common import ComplexList
from ansible.module_utils.network_common import to_list
from collections import deque


class Parameters(AnsibleF5Parameters):
    returnables = ['stdout', 'stdout_lines', 'warnings']

    def to_return(self):
        result = {}
        for returnable in self.returnables:
            result[returnable] = getattr(self, returnable)
        result = self._filter_params(result)
        return result

    @property
    def commands(self):
        commands = deque(self._values['commands'])
        commands.appendleft(
            'tmsh modify cli preference pager disabled'
        )
        return list(commands)


class ModuleManager(object):
    def __init__(self, client):
        self.client = client
        self.want = Parameters(self.client.module.params)
        self.changes = Parameters()

    def _to_lines(self, stdout):
        lines = list()
        for item in stdout:
            if isinstance(item, string_types):
                item = str(item).split('\n')
            lines.append(item)
        return lines

    def exec_module(self):
        result = dict()

        try:
            self.execute()
        except iControlUnexpectedHTTPError as e:
            raise F5ModuleError(str(e))

        result.update(**self.changes.to_return())
        result.update(dict(changed=True))
        return result

    def execute(self):
        warnings = list()

        commands = self.parse_commands(warnings)

        wait_for = self.want.wait_for or list()
        retries = self.want.retries

        conditionals = [Conditional(c) for c in wait_for]

        if self.client.check_mode:
            return

        while retries > 0:
            responses = self.execute_on_device(commands)

            for item in list(conditionals):
                if item(responses):
                    if self.want.match == 'any':
                        return item
                    conditionals.remove(item)

            if not conditionals:
                break

            time.sleep(self.want.interval)
            retries -= 1
        else:
            failed_conditions = [item.raw for item in conditionals]
            errmsg = 'One or more conditional statements have not been satisfied'
            raise FailedConditionsError(errmsg, failed_conditions)

        self.changes = Parameters({
            'stdout': responses,
            'stdout_lines': self._to_lines(responses),
            'warnings': warnings
        })

    def parse_commands(self, warnings):
        results = []
        commands = list(deque(set(self.want.commands)))
        spec = dict(
            command=dict(key=True),
            output=dict(
                default='text',
                choices=['text', 'one-line']
            ),
        )

        transform = ComplexList(spec, self.client.module)
        commands = transform(commands)

        for index, item in enumerate(commands):
            if item['output'] == 'one-line' and 'one-line' not in item['command']:
                item['command'] += ' one-line'
            elif item['output'] == 'text' and 'one-line' in item['command']:
                item['command'] = item['command'].replace('one-line', '')
            results.append(item)
        return results

    def execute_on_device(self, commands):
        responses = []
        for item in to_list(commands):
            output = self.client.api.tm.util.bash.exec_cmd(
                'run',
                utilCmdArgs='-c "{0}"'.format(item['command'])
            )
            if hasattr(output, 'commandResult'):
                responses.append(str(output.commandResult))
        return responses


class ArgumentSpec(object):
    def __init__(self):
        self.supports_check_mode = True
        self.argument_spec = dict(
            commands=dict(
                type='list',
                required=True
            ),
            wait_for=dict(
                type='list',
                aliases=['waitfor']
            ),
            match=dict(
                default='all',
                choices=['any', 'all']
            ),
            retries=dict(
                default=10,
                type='int'
            ),
            interval=dict(
                default=1,
                type='int'
            )
        )
        self.f5_product_name = 'bigip'


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
        client.module.exit_json(**results)
    except (FailedConditionsError, AttributeError) as e:
        client.module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()
