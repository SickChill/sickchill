from __future__ import absolute_import
import sys

if sys.version_info[0] < 3:
    from Tkinter import *
    from Tkinter import (_cnfmerge, _default_root, _flatten,
                          _support_default_root, _test,
                         _tkinter, _setit)

    try: # >= 2.7.4
        from Tkinter import (_join) 
    except ImportError: 
        pass

    try: # >= 2.7.4
        from Tkinter import (_stringify)
    except ImportError: 
        pass

    try: # >= 2.7.9
        from Tkinter import (_splitdict)
    except ImportError:
        pass

else:
    raise ImportError('This package should not be accessible on Python 3. '
                      'Either you are trying to run from the python-future src folder '
                      'or your installation of python-future is corrupted.')
