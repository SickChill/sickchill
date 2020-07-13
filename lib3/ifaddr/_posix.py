# Copyright (c) 2014 Stefan C. Mueller

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.


import sys
import os
import ctypes.util
import ipaddress
import collections
import socket

import ifaddr._shared as shared
#from ifaddr._shared import sockaddr, Interface, sockaddr_to_ip, ipv6_prefixlength

class ifaddrs(ctypes.Structure):
    pass
ifaddrs._fields_ = [('ifa_next', ctypes.POINTER(ifaddrs)),
                    ('ifa_name', ctypes.c_char_p),
                    ('ifa_flags', ctypes.c_uint),
                    ('ifa_addr', ctypes.POINTER(shared.sockaddr)),
                    ('ifa_netmask', ctypes.POINTER(shared.sockaddr))]

libc = ctypes.CDLL(ctypes.util.find_library("socket" if os.uname()[0] == "SunOS" else "c"), use_errno=True)

def get_adapters():

    addr0 = addr = ctypes.POINTER(ifaddrs)()
    retval = libc.getifaddrs(ctypes.byref(addr))
    if retval != 0:
        eno = ctypes.get_errno()
        raise OSError(eno, os.strerror(eno))

    ips = collections.OrderedDict()

    def add_ip(adapter_name, ip):
        if not adapter_name in ips:
            try:
                index = socket.if_nametoindex(adapter_name)
            except (OSError, AttributeError):
                index = None
            ips[adapter_name] = shared.Adapter(adapter_name, adapter_name, [],
                                               index=index)
        ips[adapter_name].ips.append(ip)


    while addr:
        name = addr[0].ifa_name
        if sys.version_info[0] > 2:
            name = name.decode(encoding='UTF-8')
        ip = shared.sockaddr_to_ip(addr[0].ifa_addr)
        if ip:
            if addr[0].ifa_netmask and not addr[0].ifa_netmask[0].sa_familiy:
                addr[0].ifa_netmask[0].sa_familiy = addr[0].ifa_addr[0].sa_familiy
            netmask = shared.sockaddr_to_ip(addr[0].ifa_netmask)
            if isinstance(netmask, tuple):
                netmask = netmask[0]
                if sys.version_info[0] > 2:
                    netmaskStr = str(netmask)
                else:
                    netmaskStr = unicode(netmask)
                prefixlen = shared.ipv6_prefixlength(ipaddress.IPv6Address(netmaskStr))
            else:
                if sys.version_info[0] > 2:
                    netmaskStr = str('0.0.0.0/' + netmask)
                else:
                    netmaskStr = unicode('0.0.0.0/' + netmask)
                prefixlen = ipaddress.IPv4Network(netmaskStr).prefixlen
            ip = shared.IP(ip, prefixlen, name)
            add_ip(name, ip)
        addr = addr[0].ifa_next

    libc.freeifaddrs(addr0)

    return ips.values()
