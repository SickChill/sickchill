(Very short) Tutorial
=====================

First create a Github instance::

    from github import Github

    # using username and password
    g = Github("user", "password")

    # or using an access token
    g = Github("access_token")

Then play with your Github objects::

    for repo in g.get_user().get_repos():
        print(repo.name)
        repo.edit(has_wiki=False)

Reference documentation
=======================

See http://pygithub.readthedocs.io/en/latest/

