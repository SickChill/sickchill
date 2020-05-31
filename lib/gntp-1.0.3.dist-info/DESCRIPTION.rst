GNTP
====

This is a Python library for working with the `Growl Notification
Transport Protocol <http://www.growlforwindows.com/gfw/help/gntp.aspx>`_

It should work as a dropin replacement for the older Python bindings

Installation
------------

You can install with pip

::

    $ pip install gntp

then test the module

::

    $ python -m gntp.notifier

Simple Usage
------------

::

    # GNTP uses the standard Python logging
    import logging
    logging.basicConfig(level=logging.INFO)

    import gntp.notifier

    # Simple "fire and forget" notification
    gntp.notifier.mini("Here's a quick message")

    # More complete example
    growl = gntp.notifier.GrowlNotifier(
        applicationName = "My Application Name",
        notifications = ["New Updates","New Messages"],
        defaultNotifications = ["New Messages"],
        # hostname = "computer.example.com", # Defaults to localhost
        # password = "abc123" # Defaults to a blank password
    )
    growl.register()

    # Send one message
    growl.notify(
        noteType = "New Messages",
        title = "You have a new message",
        description = "A longer message description",
        icon = "http://example.com/icon.png",
        sticky = False,
        priority = 1,
    )

    # Try to send a different type of message
    # This one may fail since it is not in our list
    # of defaultNotifications
    growl.notify(
        noteType = "New Updates",
        title = "There is a new update to download",
        description = "A longer message description",
        icon = "http://example.com/icon.png",
        sticky = False,
        priority = -1,
    )


URL based images do not work in the OSX version of
`growl <http://code.google.com/p/growl/issues/detail?id=423>`_ 1.4
You can send the image along with the notification to get around this.

::

    image = open('/path/to/image.png', 'rb').read()
    growl.notify(
        noteType = "New Messages",
        title = "You have a new message",
        description = "This time we embed the image",
        icon = image,
    )

.. note:: With Growl 2 and above user can choose to pass notification to system
   wide notifications center. In this case ``icon`` argument would be ignored
   by the notification center (there would always be Growl icon instead).

Bugs
----

`GitHub issue tracker <https://github.com/kfdm/gntp/issues>`_


Changelog
---------
`v1.0.3 <https://github.com/kfdm/gntp/compare/v1.0.2...v1.0.3>`_
    - Allow file:// scheme to be used for icons

`v1.0.2 <https://github.com/kfdm/gntp/compare/v1.0.1...v1.0.2>`_
    - Fix bug with incoming password hash
    - Added info about license in each source file

`v1.0.1 <https://github.com/kfdm/gntp/compare/v1.0...v1.0.1>`_
    - Fix bug with binary data (images) being encoded incorrectly

`v1.0 <https://github.com/kfdm/gntp/compare/v0.9...v1.0>`_
    - Python 3.3 Support

`v0.9 <https://github.com/kfdm/gntp/compare/v0.8...v0.9>`_
    - Remove duplicate code from gntp.config
    - Catch all errors and rethrow them as gntp.errors to make it easier for
      other programs to deal with errors from the gntp library.
    - Ensure that we open resource files as "rb" and update the documentation

`v0.8 <https://github.com/kfdm/gntp/compare/v0.7...v0.8>`_
    - Fix a bug where resource sections were missing a CRLF
    - Fix a bug where the cli client was using config values over options
    - Add support for coalescing

`v0.7 <https://github.com/kfdm/gntp/compare/0.6...v0.7>`_
    - Support for images
    - Better test coverage support

`0.6 <https://github.com/kfdm/gntp/compare/0.5...0.6>`_
    - ConfigParser aware GrowlNotifier that reads settings from ~/.gntp


