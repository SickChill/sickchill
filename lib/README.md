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
beautifulsoup4==4.5.3
bencode==1.0
# certgen.py==d52975c # source: https://github.com/pyca/pyopenssl/blob/d52975cef3a36e18552aeb23de7c06aa73d76454/examples/certgen.py
html5lib==0.999999999
  - six [required: Any, installed: 1.10.0]
  - webencodings [required: Any, installed: 0.5.1]
Mako==1.0.6
  - MarkupSafe [required: >=0.9.2, installed: 1.0]
requests==2.18.1
  - certifi [required: >=2017.4.17, installed: 2017.4.17]
  - chardet [required: >=3.0.2,<3.1.0, installed: 3.0.4]
  - idna [required: >=2.5,<2.6, installed: 2.5]
  - urllib3 [required: <1.22,>=1.21.1, installed: 1.21.1]
tornado==4.5.1
  - backports-abc [required: >=0.4, installed: 0.5]
  - backports.ssl-match-hostname [required: Any, installed: 3.5.0.1]
  - certifi [required: Any, installed: 2017.4.17]
  - singledispatch [required: Any, installed: 3.4.0.3]
    - six [required: Any, installed: 1.10.0]
```
