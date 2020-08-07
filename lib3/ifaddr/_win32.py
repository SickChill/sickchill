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


import ctypes
from ctypes import wintypes

import ifaddr._shared as shared

NO_ERROR=0
ERROR_BUFFER_OVERFLOW = 111
MAX_ADAPTER_NAME_LENGTH = 256
MAX_ADAPTER_DESCRIPTION_LENGTH = 128
MAX_ADAPTER_ADDRESS_LENGTH = 8
AF_UNSPEC = 0



class SOCKET_ADDRESS(ctypes.Structure):
    _fields_ = [('lpSockaddr', ctypes.POINTER(shared.sockaddr)),
               ('iSockaddrLength', wintypes.INT)]

class IP_ADAPTER_UNICAST_ADDRESS(ctypes.Structure):
    pass
IP_ADAPTER_UNICAST_ADDRESS._fields_ = \
    [('Length', wintypes.ULONG),
     ('Flags', wintypes.DWORD),
     ('Next', ctypes.POINTER(IP_ADAPTER_UNICAST_ADDRESS)),
     ('Address', SOCKET_ADDRESS),
     ('PrefixOrigin', ctypes.c_uint),
     ('SuffixOrigin', ctypes.c_uint),
     ('DadState', ctypes.c_uint),
     ('ValidLifetime', wintypes.ULONG),
     ('PreferredLifetime', wintypes.ULONG),
     ('LeaseLifetime', wintypes.ULONG),
     ('OnLinkPrefixLength', ctypes.c_uint8),
     ]

class IP_ADAPTER_ADDRESSES(ctypes.Structure):
    pass
IP_ADAPTER_ADDRESSES._fields_ = [('Length', wintypes.ULONG),
                                 ('IfIndex', wintypes.DWORD),
                                 ('Next', ctypes.POINTER(IP_ADAPTER_ADDRESSES)),
                                 ('AdapterName', ctypes.c_char_p),
                                 ('FirstUnicastAddress', ctypes.POINTER(IP_ADAPTER_UNICAST_ADDRESS)),
                                 ('FirstAnycastAddress', ctypes.POINTER(None)),
                                 ('FirstMulticastAddress', ctypes.POINTER(None)),
                                 ('FirstDnsServerAddress', ctypes.POINTER(None)),
                                 ('DnsSuffix', ctypes.c_wchar_p),
                                 ('Description', ctypes.c_wchar_p),
                                 ('FriendlyName', ctypes.c_wchar_p)
                                 ]


iphlpapi = ctypes.windll.LoadLibrary("Iphlpapi")


def enumerate_interfaces_of_adapter(nice_name, address):

    # Iterate through linked list and fill list
    addresses = []
    while True:
        addresses.append(address)
        if not address.Next:
            break
        address = address.Next[0]

    for address in addresses:
        ip = shared.sockaddr_to_ip(address.Address.lpSockaddr)
        network_prefix = address.OnLinkPrefixLength
        yield shared.IP(ip, network_prefix, nice_name)


def get_adapters():

    # Call GetAdaptersAddresses() with error and buffer size handling

    addressbuffersize = wintypes.ULONG(15*1024)
    retval = ERROR_BUFFER_OVERFLOW
    while retval == ERROR_BUFFER_OVERFLOW:
        addressbuffer = ctypes.create_string_buffer(addressbuffersize.value)
        retval = iphlpapi.GetAdaptersAddresses(wintypes.ULONG(AF_UNSPEC),
                                      wintypes.ULONG(0),
                                      None,
                                      ctypes.byref(addressbuffer),
                                      ctypes.byref(addressbuffersize))
    if retval != NO_ERROR:
        raise ctypes.WinError()

    # Iterate through adapters fill array
    address_infos = []
    address_info = IP_ADAPTER_ADDRESSES.from_buffer(addressbuffer)
    while True:
        address_infos.append(address_info)
        if not address_info.Next:
            break
        address_info = address_info.Next[0]


    # Iterate through unicast addresses
    result = []
    for adapter_info in address_infos:

        name = adapter_info.AdapterName
        nice_name = adapter_info.Description
        index = adapter_info.IfIndex

        if adapter_info.FirstUnicastAddress:
            ips = enumerate_interfaces_of_adapter(adapter_info.FriendlyName, adapter_info.FirstUnicastAddress[0])
            ips = list(ips)
            result.append(shared.Adapter(name, nice_name, ips,
                                         index=index))

    return result
