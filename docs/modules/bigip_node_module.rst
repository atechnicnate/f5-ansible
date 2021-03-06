.. _bigip_node:


bigip_node - Manages F5 BIG-IP LTM nodes
++++++++++++++++++++++++++++++++++++++++

.. versionadded:: 1.4


.. contents::
   :local:
   :depth: 2


Synopsis
--------

* Manages F5 BIG-IP LTM nodes.


Requirements (on host that executes module)
-------------------------------------------

  * f5-sdk >= 3.0.2


Options
-------

.. raw:: html

    <table border=1 cellpadding=4>
    <tr>
    <th class="head">parameter</th>
    <th class="head">required</th>
    <th class="head">default</th>
    <th class="head">choices</th>
    <th class="head">comments</th>
    </tr>
                <tr><td>address<br/><div style="font-size: small;"> (added in 2.2)</div></td>
    <td>no</td>
    <td></td>
        <td></td>
        <td><div>IP address of the node. This can be either IPv4 or IPv6. When creating a new node, one of either <code>address</code> or <code>fqdn</code> must be provided. This parameter cannot be updated after it is set.</div></br>
    <div style="font-size: small;">aliases: ip, host<div>        </td></tr>
                <tr><td>description<br/><div style="font-size: small;"></div></td>
    <td>no</td>
    <td></td>
        <td></td>
        <td><div>Specifies descriptive text that identifies the node.</div>        </td></tr>
                <tr><td>fqdn<br/><div style="font-size: small;"> (added in 2.5)</div></td>
    <td>no</td>
    <td></td>
        <td></td>
        <td><div>FQDN name of the node. This can be any name that is a valid RFC 1123 DNS name. Therefore, the only characters that can be used are "A" to "Z", "a" to "z", "0" to "9", the hyphen ("-") and the period (".").</div><div>FQDN names must include at lease one period; delineating the host from the domain. ex. <code>host.domain</code>.</div><div>FQDN names must end with a letter or a number.</div><div>When creating a new node, one of either <code>address</code> or <code>fqdn</code> must be provided. This parameter cannot be updated after it is set.</div></br>
    <div style="font-size: small;">aliases: hostname<div>        </td></tr>
                <tr><td>monitor_type<br/><div style="font-size: small;"> (added in 1.3)</div></td>
    <td>no</td>
    <td></td>
        <td><ul><li>and_list</li><li>m_of_n</li><li>single</li></ul></td>
        <td><div>Monitor rule type when <code>monitors</code> is specified. When creating a new pool, if this value is not specified, the default of 'and_list' will be used.</div><div>Both <code>single</code> and <code>and_list</code> are functionally identical since BIG-IP considers all monitors as "a list". BIG=IP either has a list of many, or it has a list of one. Where they differ is in the extra guards that <code>single</code> provides; namely that it only allows a single monitor.</div>        </td></tr>
                <tr><td>monitors<br/><div style="font-size: small;"> (added in 2.2)</div></td>
    <td>no</td>
    <td></td>
        <td></td>
        <td><div>Specifies the health monitors that the system currently uses to monitor this node.</div>        </td></tr>
                <tr><td>name<br/><div style="font-size: small;"></div></td>
    <td>yes</td>
    <td></td>
        <td></td>
        <td><div>Specifies the name of the node.</div>        </td></tr>
                <tr><td>partition<br/><div style="font-size: small;"> (added in 2.5)</div></td>
    <td>no</td>
    <td>Common</td>
        <td></td>
        <td><div>Device partition to manage resources on.</div>        </td></tr>
                <tr><td>quorum<br/><div style="font-size: small;"> (added in 2.2)</div></td>
    <td>no</td>
    <td></td>
        <td></td>
        <td><div>Monitor quorum value when <code>monitor_type</code> is <code>m_of_n</code>.</div>        </td></tr>
                <tr><td>state<br/><div style="font-size: small;"></div></td>
    <td>no</td>
    <td>present</td>
        <td><ul><li>present</li><li>absent</li><li>enabled</li><li>disabled</li><li>offline</li></ul></td>
        <td><div>Specifies the current state of the node. <code>enabled</code> (All traffic allowed), specifies that system sends traffic to this node regardless of the node's state. <code>disabled</code> (Only persistent or active connections allowed), Specifies that the node can handle only persistent or active connections. <code>offline</code> (Only active connections allowed), Specifies that the node can handle only active connections. In all cases except <code>absent</code>, the node will be created if it does not yet exist.</div><div>Be particularly careful about changing the status of a node whose FQDN cannot be resolved. These situations disable your ability to change their <code>state</code> to <code>disabled</code> or <code>offline</code>. They will remain in an *Unavailable - Enabled* state.</div>        </td></tr>
        </table>
    </br>



Examples
--------

 ::

    
    - name: Add node
      bigip_node:
        server: lb.mydomain.com
        user: admin
        password: secret
        state: present
        partition: Common
        host: 10.20.30.40
        name: 10.20.30.40
      delegate_to: localhost

    - name: Add node with a single 'ping' monitor
      bigip_node:
        server: lb.mydomain.com
        user: admin
        password: secret
        state: present
        partition: Common
        host: 10.20.30.40
        name: mytestserver
        monitors:
          - /Common/icmp
      delegate_to: localhost

    - name: Modify node description
      bigip_node:
        server: lb.mydomain.com
        user: admin
        password: secret
        state: present
        partition: Common
        name: 10.20.30.40
        description: Our best server yet
      delegate_to: localhost

    - name: Delete node
      bigip_node:
        server: lb.mydomain.com
        user: admin
        password: secret
        state: absent
        partition: Common
        name: 10.20.30.40
      delegate_to: localhost

    - name: Force node offline
      bigip_node:
        server: lb.mydomain.com
        user: admin
        password: secret
        state: disabled
        partition: Common
        name: 10.20.30.40
      delegate_to: localhost

    - name: Add node by their FQDN
      bigip_node:
        server: lb.mydomain.com
        user: admin
        password: secret
        state: present
        partition: Common
        fqdn: foo.bar.com
        name: 10.20.30.40
      delegate_to: localhost


Return Values
-------------

Common return values are :doc:`documented here <http://docs.ansible.com/ansible/latest/common_return_values.html>`, the following are the fields unique to this module:

.. raw:: html

    <table border=1 cellpadding=4>
    <tr>
    <th class="head">name</th>
    <th class="head">description</th>
    <th class="head">returned</th>
    <th class="head">type</th>
    <th class="head">sample</th>
    </tr>

        <tr>
        <td> state </td>
        <td> ['Changed value for the internal state of the node.'] </td>
        <td align=center> changed and success </td>
        <td align=center> string </td>
        <td align=center> m_of_n </td>
    </tr>
            <tr>
        <td> session </td>
        <td> ['Changed value for the internal session of the node.'] </td>
        <td align=center> changed and success </td>
        <td align=center> string </td>
        <td align=center> user-disabled </td>
    </tr>
            <tr>
        <td> description </td>
        <td> ['Changed value for the description of the node.'] </td>
        <td align=center> changed and success </td>
        <td align=center> string </td>
        <td align=center> E-Commerce webserver in ORD </td>
    </tr>
            <tr>
        <td> quorum </td>
        <td> ['Changed value for the quorum of the node.'] </td>
        <td align=center> changed and success </td>
        <td align=center> int </td>
        <td align=center> 1 </td>
    </tr>
            <tr>
        <td> monitor_type </td>
        <td> ['Changed value for the monitor_type of the node.'] </td>
        <td align=center> changed and success </td>
        <td align=center> string </td>
        <td align=center> m_of_n </td>
    </tr>
            <tr>
        <td> monitors </td>
        <td> ['Changed list of monitors for the node.'] </td>
        <td align=center> changed and success </td>
        <td align=center> list </td>
        <td align=center> ['icmp', 'tcp_echo'] </td>
    </tr>
        
    </table>
    </br></br>

Notes
-----

.. note::
    - Requires the f5-sdk Python package on the host. This is as easy as pip install f5-sdk
    - Requires the netaddr Python package on the host. This is as easy as pip install netaddr
    - For more information on using Ansible to manage F5 Networks devices see https://www.ansible.com/ansible-f5.



Status
~~~~~~

This module is flagged as **preview** which means that it is not guaranteed to have a backwards compatible interface.


Support
~~~~~~~

This module is community maintained without core committer oversight.

For more information on what this means please read :doc:`/usage/support`


For help developing modules, should you be so inclined, please read :doc:`Getting Involved </development/getting-involved>`, :doc:`Writing a Module </development/writing-a-module>` and :doc:`Guidelines </development/guidelines>`.