Libraries directory
======================

Vendored python packages and custom libraries go in this folder.

Keep this list updated with installed versions and their dependencies,<br/>
and ordered by the top-level library name.

Adding a new package
---------
The best practice is to install the package within a Python **virtual environment** (using `virtualenv`),<br/>
then use `pipdeptree -p PACKAGE` to get a list of the package (+dependencies) versions.<br/>
Add the output to the list below to the appropriate location (based on the top-level package name)

***

Packages List
=========
```
Mako==1.0.6
  - MarkupSafe [required: >=0.9.2, installed: 1.0]
tornado==4.5.1
  - backports-abc [required: >=0.4, installed: 0.5]
  - backports.ssl-match-hostname [required: Any, installed: 3.5.0.1]
  - certifi [required: Any, installed: 2017.4.17]
  - singledispatch [required: Any, installed: 3.4.0.3]
    - six [required: Any, installed: 1.10.0]
```
