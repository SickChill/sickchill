"""
Create a test database for testing.

Methods:
    create_test_log_folder
    create_test_cache_folder
    setup_test_db
    teardown_test_db
    setup_test_episode_file
    teardown_test_episode_file
    setup_test_show_dir
    teardown_test_show_dir

Classes:
    SickChillTestDBCase
    TestDBConnection
    TestCacheDBConnection
"""

import os.path
import shutil
import unittest

import pytest
from configobj import ConfigObj

import sickchill.logger
import sickchill.oldbeard.config
import sickchill.oldbeard.tvcache
import sickchill.start
from sickchill import settings
from sickchill.oldbeard import db, providers
from sickchill.oldbeard.databases import cache, failed, main
from sickchill.show.indexers import ShowIndexer
from sickchill.tv import TVEpisode, TVShow

# =================
#  test globals
# =================
TEST_DIR = os.path.abspath(os.path.dirname(__file__))
TEST_DB_NAME = "sickchill.db"
TEST_CACHE_DB_NAME = "cache.db"
TEST_FAILED_DB_NAME = "failed.db"

SHOW_NAME = "show name"
SEASON = 4
EPISODE = 2
FILENAME = "show name - s0" + str(SEASON) + "e0" + str(EPISODE) + ".mkv"
FILE_DIR = os.path.join(TEST_DIR, SHOW_NAME)
FILE_PATH = os.path.join(FILE_DIR, FILENAME)
SHOW_DIR = os.path.join(TEST_DIR, SHOW_NAME + " final")
PROCESSING_DIR = os.path.join(TEST_DIR, "Downloads")
NUM_SEASONS = 5
EPISODES_PER_SEASON = 20

# =================
#  prepare env functions
# =================


def create_test_log_folder():
    """
    Create a log folder for test logs.
    """
    if not os.path.isdir(settings.LOG_DIR):
        os.mkdir(settings.LOG_DIR)


def create_test_cache_folder():
    """
    Create a cache folder for caching tests.
    """
    if not os.path.isdir(settings.CACHE_DIR):
        os.mkdir(settings.CACHE_DIR)


# call env functions at appropriate time during SickChill var setup

# =================
#  SickChill globals
# =================


settings.showList = []
settings.QUALITY_DEFAULT = 4  # hdtv
settings.SEASON_FOLDERS_DEFAULT = 0

settings.NAMING_PATTERN = ""
settings.NAMING_ABD_PATTERN = ""
settings.NAMING_SPORTS_PATTERN = ""
settings.NAMING_MULTI_EP = 1

settings.TV_DOWNLOAD_DIR = PROCESSING_DIR

# settings.PROVIDER_ORDER = ["sick_beard_index"]
settings.providerList = providers.makeProviderList()

settings.DATA_DIR = TEST_DIR
settings.CONFIG_FILE = os.path.join(settings.DATA_DIR, "config.ini")
settings.CFG = ConfigObj(settings.CONFIG_FILE, encoding="UTF-8", indent_type="  ")
settings.GUI_NAME = "slick"

settings.BRANCH = sickchill.oldbeard.config.check_setting_str(settings.CFG, "General", "branch")
settings.CUR_COMMIT_HASH = sickchill.oldbeard.config.check_setting_str(settings.CFG, "General", "cur_commit_hash")
settings.GIT_USERNAME = sickchill.oldbeard.config.check_setting_str(settings.CFG, "General", "git_username")
settings.GIT_TOKEN = sickchill.oldbeard.config.check_setting_str(settings.CFG, "General", "git_token_password", censor_log=True)

settings.LOG_DIR = os.path.join(TEST_DIR, "Logs")
sickchill.logger.log_file = os.path.join(settings.LOG_DIR, "test_sickchill.log")
create_test_log_folder()

settings.CACHE_DIR = os.path.join(TEST_DIR, "cache")
create_test_cache_folder()

sickchill.logger.init_logging(False, True)

sickchill.indexer = ShowIndexer()


# =================
#  dummy functions
# =================
def _dummy_save_config():
    """
    Override the SickChill save_config which gets called during a db upgrade.

    :return: True
    """
    return True


# this overrides the SickChill save_config which gets called during a db upgrade
# this might be considered a hack
sickchill.start.save_config = _dummy_save_config


def _fake_specify_ep(self, season, episode):
    """
    Override contact to TVDB indexer.

    :param self: ...not used
    :param season: Season to search for  ...not used
    :param episode: Episode to search for  ...not used
    """
    _ = self, season, episode  # throw away unused variables


# the real one tries to contact TVDB just stop it from getting more info on the ep
TVEpisode.specifyEpisode = _fake_specify_ep


# =================
#  test classes
# =================
class SickChillTestDBCase(unittest.TestCase):
    """
    Superclass for testing the database.

    Methods:
        setUp
        tearDown
    """

    def setUp(self):
        settings.showList = []
        setup_test_db()
        setup_test_episode_file()
        setup_test_show_dir()

    def tearDown(self):
        settings.showList = []
        teardown_test_db()
        teardown_test_episode_file()
        teardown_test_show_dir()


class SickChillTestPostProcessorCase(unittest.TestCase):
    """
    Superclass for testing the database.

    Methods:
        setUp
        tearDown
    """

    def setUp(self):
        settings.showList = []
        setup_test_db()
        setup_test_episode_file()
        setup_test_show_dir()
        setup_test_processing_dir()

        self.show = TVShow(1, 1, "en")
        self.show.name = SHOW_NAME
        self.show.location = FILE_DIR
        self.show.imdb_info = {"indexer_id": self.show.indexerid, "imdb_id": "tt000000"}

        self.show.episodes = {}
        for season in range(1, NUM_SEASONS):
            self.show.episodes[season] = {}
            for episode in range(1, EPISODES_PER_SEASON):
                if season == SEASON and episode == EPISODE:
                    episode = TVEpisode(self.show, season, episode, ep_file=FILE_PATH)
                else:
                    episode = TVEpisode(self.show, season, episode)
                self.show.episodes[season][episode] = episode
                episode.saveToDB()

        self.show.saveToDB()
        settings.showList = [self.show]

    def tearDown(self):
        settings.showList = []
        self.show.deleteShow(True)
        teardown_test_db()
        teardown_test_episode_file()
        teardown_test_show_dir()
        teardown_test_processing_dir()


class TestDBConnection(db.DBConnection, object):
    """
    Test connecting to the database.
    """

    __test__ = False

    def __init__(self, filename=TEST_DB_NAME, suffix=None, row_type=None):
        if TEST_DIR not in filename:
            filename = os.path.join(TEST_DIR, filename)
        super().__init__(filename=filename, suffix=suffix, row_type=row_type)


class TestCacheDBConnection(TestDBConnection, object):
    """
    Test connecting to the cache database.
    """

    __test__ = False

    def __init__(self, filename=TEST_CACHE_DB_NAME, suffix=None, row_type="dict"):
        if TEST_DIR not in filename:
            filename = os.path.join(TEST_DIR, filename)
        super().__init__(filename=filename, suffix=suffix, row_type=row_type)


# this will override the normal db connection
sickchill.oldbeard.db.DBConnection = TestDBConnection
sickchill.oldbeard.tvcache.CacheDBConnection = TestCacheDBConnection


# =================
#  test functions
# =================
def setup_test_db():
    """
    Set up the test databases.
    """
    # Upgrade the db to the latest version.
    # upgrading the db
    db.upgrade_database(db.DBConnection(), main.InitialSchema)

    # fix up any db problems
    db.sanity_check_database(db.DBConnection(), main.MainSanityCheck)

    # and for cache.db too
    db.upgrade_database(db.DBConnection("cache.db"), cache.InitialSchema)

    # and for failed.db too
    db.upgrade_database(db.DBConnection("failed.db"), failed.InitialSchema)


def teardown_test_db():
    """
    Tear down the test database.
    """
    from sickchill.oldbeard.db import db_cons

    for connection in db_cons:
        db_cons[connection].commit()
    #     db_cons[connection].close()
    #
    # for current_db in [ TEST_DB_NAME, TEST_CACHE_DB_NAME, TEST_FAILED_DB_NAME ]:
    #    filename = os.path.join(TEST_DIR, current_db)
    #    if os.path.exists(filename):
    #        try:
    #            os.remove(filename)
    #        except Exception as e:
    #            print('ERROR: Failed to remove ' + filename)
    #            print(Exception(e))


def setup_test_episode_file():
    """
    Create a test episode directory with a test episode in it.
    """
    if not os.path.exists(FILE_DIR):
        os.makedirs(FILE_DIR)

    try:
        with open(FILE_PATH, "w") as ep_file:
            ep_file.write("foo bar")
            ep_file.flush()

    # Catching too general exception
    except Exception:
        print("Unable to set up test episode")
        raise


def setup_test_processing_dir():
    if not os.path.exists(PROCESSING_DIR):
        os.makedirs(PROCESSING_DIR)

    for season in range(1, NUM_SEASONS):
        for episode in range(11, EPISODES_PER_SEASON):
            path = os.path.join(
                PROCESSING_DIR, "{show_name}.S0{season}E{episode}.HDTV.x264.[SickChill].mkv".format(show_name=SHOW_NAME, season=season, episode=episode)
            )
            with open(path, "w") as ep_file:
                ep_file.write("foo bar")
                ep_file.flush()


def teardown_test_processing_dir():
    if os.path.exists(PROCESSING_DIR):
        shutil.rmtree(PROCESSING_DIR)


def teardown_test_episode_file():
    """
    Remove the test episode.
    """
    if os.path.exists(FILE_DIR):
        shutil.rmtree(FILE_DIR)


def setup_test_show_dir():
    """
    Create a test show directory.
    """
    if not os.path.exists(SHOW_DIR):
        os.makedirs(SHOW_DIR)


def teardown_test_show_dir():
    """
    Remove the test show.
    """
    if os.path.exists(SHOW_DIR):
        shutil.rmtree(SHOW_DIR)


@pytest.fixture(scope="module")
def vcr_cassette_dir(request):
    # Put all cassettes in vhs/{module}/{test}.yaml
    return os.path.join(os.path.dirname(request.module.__file__), "cassettes")


@pytest.fixture()
def vcr_cassette_name(request):
    """Name of the VCR cassette"""
    return request.cls.provider.get_id() + ".yaml"
