modify, publish, use, compile, sell, or distribute this software,
either in source code form or as a compiled binary, for any purpose,
commercial or non-commercial, and by any means.

Description: win_inet_pton
        =============
        
        Native inet_pton and inet_ntop implementation for Python on Windows (with ctypes).
        
        Credit Where Credit Is Due
        --------------------------
        
        This package is based on code that was originally written by https://github.com/nnemkin here: https://gist.github.com/nnemkin/4966028
        
        Why?
        ----
        
        I needed this functionality in https://github.com/SerenitySoftwareLLC/cahoots to get full windows support. I figured, since there were other people looking for a solution to this on the net, I should publish it.
        
        Usage
        -----
        
         .. code-block:: bash
        
            python -m pip install win_inet_pton
        
        Just import it, and it will auto-add the methods to the socket library:
        
         .. code-block:: python
        
            import win_inet_pton
            import socket
        
            socket.inet_pton(...)
            socket.inet_ntop(...)
        
        License
        -------
        
        This software released into the public domain. Anyone is free to copy,
        modify, publish, use, compile, sell, or distribute this software,
        either in source code form or as a compiled binary, for any purpose,
        commercial or non-commercial, and by any means.
        
Platform: UNKNOWN
Classifier: Development Status :: 5 - Production/Stable
Classifier: Intended Audience :: Developers
Classifier: Operating System :: OS Independent
Classifier: Operating System :: Microsoft :: Windows
Classifier: License :: Public Domain
Classifier: Programming Language :: Python
Classifier: Programming Language :: Python :: 2
Classifier: Programming Language :: Python :: 2.7
Classifier: Programming Language :: Python :: 3
Classifier: Programming Language :: Python :: 3.3
Classifier: Topic :: Utilities
