# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from .codegen import generate_dummy_callable


def CallbackAttribute(info):
    func = generate_dummy_callable(info, info.name)
    func._is_callback = True

    return func
