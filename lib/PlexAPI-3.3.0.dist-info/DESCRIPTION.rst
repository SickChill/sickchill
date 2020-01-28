Python-PlexAPI
==============
.. image:: https://readthedocs.org/projects/python-plexapi/badge/?version=latest
    :target: http://python-plexapi.readthedocs.io/en/latest/?badge=latest
.. image:: https://travis-ci.org/pkkid/python-plexapi.svg?branch=master
    :target: https://travis-ci.org/pkkid/python-plexapi
.. image:: https://coveralls.io/repos/github/pkkid/python-plexapi/badge.svg?branch=master
    :target: https://coveralls.io/github/pkkid/python-plexapi?branch=master


Overview
--------
Unofficial Python bindings for the Plex API. Our goal is to match all capabilities of the official
Plex Web Client. A few of the many features we currently support are:

* Navigate local or remote shared libraries.
* Perform library actions such as scan, analyze, empty trash.
* Remote control and play media on connected clients.
* Listen in on all Plex Server notifications.


Installation & Documentation
----------------------------

.. code-block:: python

    pip install plexapi

Documentation_ can be found at Read the Docs.

.. _Documentation: http://python-plexapi.readthedocs.io/en/latest/


Getting a PlexServer Instance
-----------------------------

There are two types of authentication. If you are running on a separate network
or using Plex Users you can log into MyPlex to get a PlexServer instance. An
example of this is below. NOTE: Servername below is the name of the server (not
the hostname and port).  If logged into Plex Web you can see the server name in
the top left above your available libraries.

.. code-block:: python

    from plexapi.myplex import MyPlexAccount
    account = MyPlexAccount('<USERNAME>', '<PASSWORD>')
    plex = account.resource('<SERVERNAME>').connect()  # returns a PlexServer instance

If you want to avoid logging into MyPlex and you already know your auth token
string, you can use the PlexServer object directly as above, but passing in
the baseurl and auth token directly.

.. code-block:: python

    from plexapi.server import PlexServer
    baseurl = 'http://plexserver:32400'
    token = '2ffLuB84dqLswk9skLos'
    plex = PlexServer(baseurl, token)


Usage Examples
--------------

.. code-block:: python

    # Example 1: List all unwatched movies.
    movies = plex.library.section('Movies')
    for video in movies.search(unwatched=True):
        print(video.title)


.. code-block:: python

    # Example 2: Mark all Game of Thrones episodes watched.
    plex.library.section('TV Shows').get('Game of Thrones').markWatched()


.. code-block:: python

    # Example 3: List all clients connected to the Server.
    for client in plex.clients():
        print(client.title)


.. code-block:: python

    # Example 4: Play the movie Cars on another client.
    # Note: Client must be on same network as server.
    cars = plex.library.section('Movies').get('Cars')
    client = plex.client("Michael's iPhone")
    client.playMedia(cars)


.. code-block:: python

    # Example 5: List all content with the word 'Game' in the title.
    for video in plex.search('Game'):
        print('%s (%s)' % (video.title, video.TYPE))


.. code-block:: python

    # Example 6: List all movies directed by the same person as Elephants Dream.
    movies = plex.library.section('Movies')
    die_hard = movies.get('Elephants Dream')
    director = die_hard.directors[0]
    for movie in movies.search(None, director=director):
        print(movie.title)


.. code-block:: python

    # Example 7: List files for the latest episode of The 100.
    last_episode = plex.library.section('TV Shows').get('The 100').episodes()[-1]
    for part in last_episode.iterParts():
        print(part.file)


.. code-block:: python

    # Example 8: Get audio/video/all playlists
    for playlist in plex.playlists():
        print(playlist.title)


.. code-block:: python

    # Example 9: Rate the 100 four stars.
    plex.library.section('TV Shows').get('The 100').rate(8.0)


Running tests over PlexAPI
--------------------------

In order to test the PlexAPI library you have to prepare a Plex Server instance with following libraries:

1. Movies section (agent `com.plexapp.agents.imdb`) containing both movies:
    * Sintel - https://durian.blender.org/
    * Elephants Dream - https://orange.blender.org/
    * Sita Sings the Blues - http://www.sitasingstheblues.com/
    * Big Buck Bunny - https://peach.blender.org/
2. TV Show section (agent `com.plexapp.agents.thetvdb`) containing the shows:
    * Game of Thrones (Season 1 and 2)
    * The 100 (Seasons 1 and 2)
    * (or symlink the above movies with proper names)
3. Music section (agent `com.plexapp.agents.lastfm`) containing the albums:
    * Infinite State - Unmastered Impulses - https://github.com/kennethreitz/unmastered-impulses
    * Broke For Free - Layers - http://freemusicarchive.org/music/broke_for_free/Layers/
4. A Photos section (any agent) containing the photoalbums (photoalbum is just a folder on your disk):
    * `Cats`
    * Within `Cats` album you need to place 3 photos (cute cat photos, of course)
    * Within `Cats` album you should place 3 more photoalbums (one of them should be named `Cats in bed`,
      names of others doesn't matter)
    * Within `Cats in bed` you need to place 7 photos
    * Within other 2 albums you should place 1 photo in each

Instead of manual creation of the library you could use a script `tools/plex-boostraptest.py` with appropriate
arguments and add this new server to a shared user which username is defined in environment veriable `SHARED_USERNAME`.
It uses `official docker image`_ to create a proper instance.

Also in order to run most of the tests you have to provide some environment variables:

* `PLEXAPI_AUTH_SERVER_BASEURL` containing an URL to your Plex instance, e.g. `http://127.0.0.1:32400` (without trailing
  slash)
* `PLEXAPI_AUTH_MYPLEX_USERNAME` and `PLEXAPI_AUTH_MYPLEX_PASSWORD` with your MyPlex username and password accordingly

After this step you can run tests with following command:

.. code-block:: bash

    py.test tests -rxXs --ignore=tests/test_sync.py

Some of the tests in main test-suite require a shared user in your account (e.g. `test_myplex_users`,
`test_myplex_updateFriend`, etc.), you need to provide a valid shared user's username to get them running you need to
provide the username of the shared user as an environment variable `SHARED_USERNAME`. You can enable a Guest account and
simply pass `Guest` as `SHARED_USERNAME` (or just create a user like `plexapitest` and play with it).

To be able to run tests over Mobile Sync api you have to some some more environment variables, to following values
exactly:

* PLEXAPI_HEADER_PROVIDES='controller,sync-target'
* PLEXAPI_HEADER_PLATFORM=iOS
* PLEXAPI_HEADER_PLATFORM_VERSION=11.4.1
* PLEXAPI_HEADER_DEVICE=iPhone

And finally run the sync-related tests:

.. code-block:: bash

    py.test tests/test_sync.py -rxXs

.. _official docker image: https://hub.docker.com/r/plexinc/pms-docker/

Common Questions
----------------

**Why are you using camelCase and not following PEP8 guidelines?**

This API reads XML documents provided by MyPlex and the Plex Server.
We decided to conform to their style so that the API variable names directly
match with the provided XML documents.


**Why don't you offer feature XYZ?**

This library is meant to be a wrapper around the XML pages the Plex
server provides. If we are not providing an API that is offerered in the
XML pages, please let us know! -- Adding additional features beyond that
should be done outside the scope of this library.


**What are some helpful links if trying to understand the raw Plex API?**

* https://github.com/plexinc/plex-media-player/wiki/Remote-control-API
* https://forums.plex.tv/discussion/104353/pms-web-api-documentation
* https://github.com/Arcanemagus/plex-api/wiki


