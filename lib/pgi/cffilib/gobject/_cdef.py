# Copyright 2013 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

from .. import _fixup_cdef_enums


GOBJECT_CDEF = """
typedef enum {
  G_PARAM_READABLE            = 1 << 0,
  G_PARAM_WRITABLE            = 1 << 1,
  G_PARAM_CONSTRUCT           = 1 << 2,
  G_PARAM_CONSTRUCT_ONLY      = 1 << 3,
  G_PARAM_LAX_VALIDATION      = 1 << 4,
  G_PARAM_STATIC_NAME         = 1 << 5,
  G_PARAM_STATIC_NICK         = 1 << 6,
  G_PARAM_STATIC_BLURB        = 1 << 7,
  G_PARAM_DEPRECATED          = 1 << 31
} GParamFlags;

typedef enum
{
  G_SIGNAL_RUN_FIRST	= 1 << 0,
  G_SIGNAL_RUN_LAST	= 1 << 1,
  G_SIGNAL_RUN_CLEANUP	= 1 << 2,
  G_SIGNAL_NO_RECURSE	= 1 << 3,
  G_SIGNAL_DETAILED	= 1 << 4,
  G_SIGNAL_ACTION	= 1 << 5,
  G_SIGNAL_NO_HOOKS	= 1 << 6,
  G_SIGNAL_MUST_COLLECT = 1 << 7,
  G_SIGNAL_DEPRECATED   = 1 << 8
} GSignalFlags;

typedef struct _GValue GValue;

typedef gulong GType;

GType               g_type_from_name                    (const gchar *name);
void                g_type_init                         (void);
"""

GOBJECT_CDEF = _fixup_cdef_enums(GOBJECT_CDEF)
