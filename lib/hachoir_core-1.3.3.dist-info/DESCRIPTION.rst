Hachoir project
===============

Hachoir is a Python library used to represent of a binary file as a tree of
Python objects. Each object has a type, a value, an address, etc. The goal is
to be able to know the meaning of each bit in a file.

Why using slow Python code instead of fast hardcoded C code? Hachoir has many
interesting features:

 * Autofix: Hachoir is able to open invalid / truncated files
 * Lazy: Open a file is very fast since no information is read from file,
   data are read and/or computed when the user ask for it
 * Types: Hachoir has many predefined field types (integer, bit, string, etc.)
   and supports string with charset (ISO-8859-1, UTF-8, UTF-16, ...)
 * Addresses and sizes are stored in bit, so flags are stored as classic fields
 * Endian: You have to set endian once, and then number are converted in the
   right endian
 * Editor: Using Hachoir representation of data, you can edit, insert, remove
   data and then save in a new file.

Website: http://bitbucket.org/haypo/hachoir/wiki/hachoir-core

Installation
============

For the installation, use setup.py or see: http://bitbucket.org/haypo/hachoir/wiki/Install

hachoir-core 1.3.3 (2010-02-26)
===============================

 * Add writelines() method to UnicodeStdout

hachoir-core 1.3.2 (2010-01-28)
===============================

 * MANIFEST.in includes also the documentation

hachoir-core 1.3.1 (2010-01-21)
===============================

 * Create MANIFEST.in to include ChangeLog and other files for setup.py

hachoir-core 1.3 (2010-01-20)
=============================

 * Add more charsets to GenericString: CP874, WINDOWS-1250, WINDOWS-1251,
   WINDOWS-1254, WINDOWS-1255, WINDOWS-1256,WINDOWS-1257, WINDOWS-1258,
   ISO-8859-16
 * Fix initLocale(): return charset even if config.unicode_stdout is False
 * initLocale() leave sys.stdout and sys.stderr unchanged if the readline
   module is loaded: Hachoir can now be used correctly with ipython
 * HachoirError: replace "message" attribute by "text" to fix Python 2.6
   compatibility (message attribute is deprecated)
 * StaticFieldSet: fix Python 2.6 warning, object.__new__() takes one only
   argument (the class).
 * Fix GenericFieldSet.readMoreFields() result: don't count the number of
   added fields in a loop, use the number of fields before/after the operation
   using len()
 * GenericFieldSet.__iter__() supports iterable result for _fixFeedError() and
   _stopFeeding()
 * New seekable field set implementation in
   hachoir_core.field.new_seekable_field_set

hachoir-core 1.2.1 (2008-10)
============================

 * Create configuration option "unicode_stdout" which avoid replacing
   stdout and stderr by objects supporting unicode string
 * Create TimedeltaWin64 file type
 * Support WINDOWS-1252 and WINDOWS-1253 charsets for GenericString
 * guessBytesCharset() now supports ISO-8859-7 (greek)
 * durationWin64() is now deprecated, use TimedeltaWin64 instead

hachoir-core 1.2 (2008-09)
==========================

 * Create Field.getFieldType(): describe a field type and gives some useful
   informations (eg. the charset for a string)
 * Create TimestampUnix64
 * GenericString: only guess the charset once; if the charset attribute
   if not set, guess it when it's asked by the user.

hachoir-core 1.1 (2008-04-01)
=============================

Main change: string values are always encoded as Unicode. Details:

 * Create guessBytesCharset() and guessStreamCharset()
 * GenericString.createValue() is now always Unicode: if charset is not
   specified, try to guess it. Otherwise, use default charset (ISO-8859-1)
 * RawBits: add createRawDisplay() to avoid slow down on huge fields
 * Fix SeekableFieldSet.current_size (use offset and not current_max_size)
 * GenericString: fix UTF-16-LE string with missing nul byte
 * Add __nonzero__() method to GenericTimestamp
 * All stream errors now inherit from StreamError (instead of HachoirError),
   and create  and OutputStreamError
 * humanDatetime(): strip microseconds by default (add optional argument to
   keep them)

hachoir-core 1.0 (2007-07-10)
=============================

Version 1.0.1 changelog:
 * Rename parser.tags to parser.PARSER_TAGS to be compatible
   with future hachoir-parser 1.0

Visible changes:
 * New field type: TimestampUUID60
 * SeekableFieldSet: fix __getitem__() method and implement __iter__()
   and __len__() methods, so it can now be used in hachoir-wx
 * String value is always Unicode, even on conversion error: use
 * OutputStream: add readBytes() method
 * Create Language class using ISO-639-2
 * Add hachoir_core.profiler module to run a profiler on a function
 * Add hachoir_core.timeout module to call a function with a timeout

Minor changes:
 * Fix many spelling mistakes
 * Dict: use iteritems() instead of items() for faster operations on
   huge dictionaries



