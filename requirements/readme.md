List of dependencies [![Requirements Status](https://requires.io/github/SickRage/SickRage/requirements.svg?branch=develop)](https://requires.io/github/SickRage/SickRage/requirements/?branch=develop)
======================

 Status  |  Package  |  Version / Commit  | Notes
:------: | :-------: | :----------------: | -----
:exclamation: | adba | ??? | **Modified**<br>not on PYPI - [GH:lad1337/adba](https://github.com/lad1337/adba)
:ok: | babelfish | 0.5.5 | Resolved by [#3877](https://github.com/SickRage/SickRage/pull/3877)
:ok: | backports_abc | 0.5
:ok: | backports.ssl-match-hostname | 3.5.0.1
:ok: | beautifulsoup4 | 4.5.3
:ok: | bencode | 1.0 | Resolved by [#3858](https://github.com/SickRage/SickRage/pull/3858) + [#3871](https://github.com/SickRage/SickRage/pull/3871)<br>A newer version (fork) is available: [GH:fuzeman/bencode.py](https://github.com/fuzeman/bencode.py)
:ok: | cachecontrol | 0.11.5
:warning: | certgen.py | [d52975c](https://github.com/pyca/pyopenssl/blob/d52975cef3a36e18552aeb23de7c06aa73d76454/examples/certgen.py) | Source: [GH:pyca/pyopenssl](https://github.com/pyca/pyopenssl/blob/master/examples/certgen.py)
:ok: | certifi | 2017.4.17
:ok: | cfscrape | 1.7.1 | Note: Can't upgrade to latest version<br>because Node.js is now required.
:ok: | chardet | 3.0.4 | Resolved by [#3870](https://github.com/SickRage/SickRage/pull/3870)
:ok: | configobj | 4.6.0
:ok: | decorator | 4.0.10
:warning: | dogpile.cache | [229615b](https://bitbucket.org/zzzeek/dogpile.cache/src/229615be466d00c9c135a90d8965679ab3e4edaa/dogpile/) | Bitbucket
:ok: | dogpile.core | 0.4.1
:ok: | enum34 | 1.0.4
:warning: | enzyme | [9572bea](https://github.com/Diaoul/enzyme/tree/9572bea606a6145dad153cd712653d6cf10ef18e)
:ok: | fake-useragent | 0.1.2 | Note: There's a `ua.json` file that's used by `sickbeard.common`,<br>should be moved to a better location.
:warning: | feedparser | [f1dd1bb](https://github.com/kurtmckee/feedparser/tree/f1dd1bb923ebfe6482fc2521c1f150b4032289ec) | Vanilla'd by [#3877](https://github.com/SickRage/SickRage/pull/3877)
:warning: | futures | [43bfc41](https://github.com/agronholm/pythonfutures/tree/43bfc41626208d78f4db1839e2808772defdfdca)
:warning: | guessit | [a4fb286](https://github.com/guessit-io/guessit/tree/a4fb2865d4b697397aa976388bbd0edf558a24fb)
:warning: | hachoir_core | [708fdf6](https://bitbucket.org/haypo/hachoir/src/708fdf64a982ba2e638aa59d94f143112066b8ce/hachoir-core/hachoir_core/) | Bitbucket
:warning: | hachoir_metadata | [708fdf6](https://bitbucket.org/haypo/hachoir/src/708fdf64a982ba2e638aa59d94f143112066b8ce/hachoir-metadata/hachoir_metadata/) | Bitbucket
:warning: | hachoir_parser | [708fdf6](https://bitbucket.org/haypo/hachoir/src/708fdf64a982ba2e638aa59d94f143112066b8ce/hachoir-parser/hachoir_parser/) | Bitbucket
:ok: | html5lib | 1.0b10
:ok: | httplib2 | 0.9.2 | + tests folder from [cf631a7](https://github.com/httplib2/httplib2/tree/cf631a73e2f3f43897b65206127ced82382d35f5)
:ok: | idna | 2.5 | Added in [#3870](https://github.com/SickRage/SickRage/pull/3870)
:warning: | IMDbPY | 5.1.1 | Resolved by [#3877](https://github.com/SickRage/SickRage/pull/3877)<br>**Still can't install this from requirements.txt**,<br>because we need to be able to use `--no-deps`, but it's unsupported in the context of requirement files.<br>A workaround seems to be to use `pip install --no-deps -r requirements.txt`, which is fine as long as we list ALL dependencies (which is planned).<br>Also, I don't think `install_requires` in `setup.py` supports anything more than simple package version constraints, maybe VCS sources (git/mercurial/etc..) - untested.
:warning: | js2py | [05e77f0](https://github.com/PiotrDabkowski/Js2Py/tree/05e77f0d4ffe91ef418a93860e666962cfd193b8)
:warning: | jsonrpclib | [e3a3cde](https://github.com/joshmarshall/jsonrpclib/tree/e3a3cdedc9577b25b91274815b38ba7f3bc43c68)
:warning: | libgrowl | - | **Custom by Sick-Beard's midgetspy**<br>Some of the code is from [GH:kfdm/gntp](https://github.com/kfdm/gntp)
:warning: | libtrakt | - | **Custom**<br>Just a small note -<br>if needed, [GH:fuzeman/trakt.py](https://github.com/fuzeman/trakt.py) is a great implementation of Trakt.tv's API.
:ok: | lockfile | 0.11.0
:ok: | Mako | 1.0.6
:ok: | markdown2 | 2.3.4 | Resolved by [#3877](https://github.com/SickRage/SickRage/pull/3877)
:ok: | MarkupSafe | 1.0
:ok: | ndg-httpsclient | 0.3.3
:ok: | oauthlib | 2.0.2 | Added in [#3870](https://github.com/SickRage/SickRage/pull/3870)
:warning: | pgi | [38f8349](https://github.com/pygobject/pgi/tree/38f834902247a5851cb4c72ba018f160ae26d612)
:exclamation: | pkg_resources.py | - | Copied from setuptools and looks to be modified.<br>Maybe we don't really need this?<br>Used to load the egg files for `pymediainfo` and `pytz`.
:ok: | profilehooks | 1.5
:ok: | putio.py | 6.1.0
:ok: | pyasn1 | 0.1.7 | + LICENSE
:ok: | PyGithub | 1.34 | Resolved by [#3877](https://github.com/SickRage/SickRage/pull/3877)
:ok: | PyJWT | 1.5.0 | Added in [#3877](https://github.com/SickRage/SickRage/pull/3877)
:ok: | pymediainfo | 2.0 | as an `.egg` file, loaded by `pkg_resources`
:ok: | pynma | 1.0
:ok: | PySocks | 1.6.7 | Added in [#3877](https://github.com/SickRage/SickRage/pull/3877)
:warning: | pysrt | [47aaa59](https://github.com/byroot/pysrt/tree/47aaa592c3bc185cd2bc1d58d1451bf98be3c1ef)
:ok: | python-dateutil | 2.6.0 | Resolved by [#3877](https://github.com/SickRage/SickRage/pull/3877)
:exclamation: | python-fanart | 1.4.0 | **Modified**<br>API url was updated. No newer version.
:ok: | python-twitter | 3.3 | Updated in [#3870](https://github.com/SickRage/SickRage/pull/3870)
:ok: | pytz | 2016.4 | as an `.egg` file, loaded by `pkg_resources`
:exclamation: | rarfile | [3e54b22](https://github.com/markokr/rarfile/tree/3e54b222c8703eea64cd07102df7bb9408b582b3) | *v3.0 Github release*<br>**Modified**<br>See [`059dd933#diff-c1f4e96`](https://github.com/SickRage/SickRage/commit/059dd933b9da3a0f83c6cbb4f47c198e5a957fc6#diff-c1f4e968aa545d42d2e462672169da4a)
:warning: | rebulk | [42d0a58](https://github.com/Toilal/rebulk/tree/42d0a58af9d793334616a6582f2a83b0fae0dd5f)
:ok: | requests | 2.18.1 | Updated in [#3870](https://github.com/SickRage/SickRage/pull/3870)
:ok: | requests-oauthlib | 0.8.0 | Added in [#3870](https://github.com/SickRage/SickRage/pull/3870)
:exclamation: | rtorrent-python | 0.2.9 | **Modified**<br>See [commits log for `lib/rtorrent`](https://github.com/SickRage/SickRage/commits/master/lib/rtorrent)
:exclamation: | send2trash | 1.3.0 | **Modified**<br>See [`9ad8114`](https://github.com/SickRage/SickRage/commit/9ad811432ab0ca3292410d29464ce2532361eb55)
:ok: | singledispatch | 3.4.0.3
:ok: | six | 1.10.0
:warning: | sqlalchemy | [ccc0c44](https://github.com/zzzeek/sqlalchemy/tree/ccc0c44c3a60fc4906e5e3b26cc6d2b7a69d33bf)
:ok: | stevedore | 1.10.0
:warning: | subliminal | [7eb7a53](https://github.com/Diaoul/subliminal/tree/7eb7a53fe6bcaf3e01a6b44c8366faf7c96f7f1b) | **Modified**<br>Subscenter provider disabled until fixed upstream, [#3825 `diff-ab7eb9b`](https://github.com/SickRage/SickRage/pull/3825/files#diff-ab7eb9ba0a2d4c74c16795ff40f2bd62)
:warning: | synchronous-deluge | - | **Custom: by Christian Dale**
:ok: | tmdbsimple | 0.3.0 | Note: Package naming is modified.
:ok: | tornado | 4.5.1 | Note: Contains a `routes.py` file,<br>which is not a part of the original package
:ok: | tus.py | 1.2.0
:exclamation: | tvdb_api | 1.9 | **Heavily Modified**<br>Deprecated API, will be disabled by October 1st, 2017
:warning: | twilio | [f91e1a9](https://github.com/twilio/twilio-python/tree/f91e1a9e6f4e0a60589b2b90cb66b89b879b9c3e)
:ok: | tzlocal | 1.4 | Resolved by [#3877](https://github.com/SickRage/SickRage/pull/3877)
:ok: | Unidecode | 0.04.20 | Updated in [#3877](https://github.com/SickRage/SickRage/pull/3877)
:ok: | urllib3 | 1.21.1 | Added in [#3870](https://github.com/SickRage/SickRage/pull/3870)
:ok: | validators | 0.10
:ok: | webencodings | 0.5.1
:ok: | win-inet-pton | 1.0.1 | Required for PySocks on Windows systems<br>Added in [#3877](https://github.com/SickRage/SickRage/pull/3877)
:ok: | xmltodict | 0.11.0 | Resolved by [#3877](https://github.com/SickRage/SickRage/pull/3877)

***

:heavy_minus_sign: Removed libs:
-------------

 Package  |  Reason  | Reference
:-------: | :------: | ---------
MultipartPostHandler.py | Unused | Removed in [#3716](https://github.com/SickRage/SickRage/pull/3716)
oauth2 | Outdated | Removed in [#3870](https://github.com/SickRage/SickRage/pull/3870)
simplejson | Unused | Removed in [#3877](https://github.com/SickRage/SickRage/pull/3877)
SocksiPy | Outdated | Replaced with PySocks in [#3877](https://github.com/SickRage/SickRage/pull/3877)
sqliteshelf.py | Unused | Removed in [#3716](https://github.com/SickRage/SickRage/pull/3716)
