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
babelfish=0.5.5
beautifulsoup4==4.5.3
bencode==1.0
# certgen.py==d52975c # source: https://github.com/pyca/pyopenssl/blob/d52975cef3a36e18552aeb23de7c06aa73d76454/examples/certgen.py
git+https://github.com/kurtmckee/feedparser.git@f1dd1bb923ebfe6482fc2521c1f150b4032289ec#egg=feedparser
html5lib==0.999999999
  - six [required: Any, installed: 1.10.0]
  - webencodings [required: Any, installed: 0.5.1]
IMDbPY==5.1.1
Mako==1.0.6
  - MarkupSafe [required: >=0.9.2, installed: 1.0]
markdown2==2.3.4
PyGithub==1.34
  - pyjwt [required: Any, installed: 1.5.0]
PySocks==1.6.7
  - win-inet-pton==1.0.1
python-dateutil==2.6.0
  - six [required: >=1.5, installed: 1.10.0]
python-twitter==3.3
  - future [required: Any, installed: 0.16.0] # <-- Not really needed, so not installed
  - requests [required: Any, installed: 2.18.1]
  - requests-oauthlib [required: Any, installed: 0.8.0]
requests==2.18.1
  - certifi [required: >=2017.4.17, installed: 2017.4.17]
  - chardet [required: >=3.0.2,<3.1.0, installed: 3.0.4]
  - idna [required: >=2.5,<2.6, installed: 2.5]
  - urllib3 [required: <1.22,>=1.21.1, installed: 1.21.1]
requests-oauthlib==0.8.0
  - oauthlib [required: >=0.6.2, installed: 2.0.2]
  - requests [required: >=2.0.0, installed: 2.18.1]
tornado==4.5.1
  - backports-abc [required: >=0.4, installed: 0.5]
  - backports.ssl-match-hostname [required: Any, installed: 3.5.0.1]
  - certifi [required: Any, installed: 2017.4.17]
  - singledispatch [required: Any, installed: 3.4.0.3]
    - six [required: Any, installed: 1.10.0]
tzlocal==1.4
  - pytz [required: Any, installed: 2016.4]
Unidecode==0.04.20
validators==0.10
  - decorator [required: >=3.4.0, installed: 4.0.10]
  - six [required: >=1.4.0, installed: 1.10.0]
xmltodict==0.11.0
```

```
 pip install --target=lib -U --global-option="--no-user-cfg" --no-binary --no-compile requests_oauthlib
 pip install --target=lib -U --global-option="--no-user-cfg" --no-binary --no-compile requests
```
