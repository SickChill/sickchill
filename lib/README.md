SickRage vendor folder
======================

Vendored python packages and custom libraries go in here.<br/>
Keep this list updated with installed versions and their dependencies,
and ordered by the top-level library name.

When adding a new package, please install locally using `virtualenv` and then use `pipdeptree`
```
pipdeptree -p PACKAGE
```


Packages List
----------------
```
tornado==4.5.1
  - backports-abc [required: >=0.4, installed: 0.5]
  - backports.ssl-match-hostname [required: Any, installed: 3.5.0.1]
  - certifi [required: Any, installed: 2017.4.17]
  - singledispatch [required: Any, installed: 3.4.0.3]
    - six [required: Any, installed: 1.10.0]
```
