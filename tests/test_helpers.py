"""
Test oldbeard.helpers

Public Methods:
    indentXML
    remove_non_release_groups
    remove_file_failed
    makeDir
    searchIndexerForShowID
    list_media_files
    copyFile
    moveFile
    link
    hardlinkFile
    symlink
    moveAndSymlinkFile
    make_dirs
    rename_ep_file
    delete_empty_folders
    fileBitFilter
    chmodAsParent
    fixSetGroupID
    get_absolute_number_from_season_and_episode
    get_all_episodes_from_absolute_number
    sanitizeSceneName
    create_https_certificates
    backupVersionedFile
    get_lan_ip
    check_url
    anon_url
    encrypt
    decrypt
    full_sanitizeSceneName
    get_show
    is_hidden_folder
    set_up_anidb_connection
    makeZip
    extractZip
    backup_config_zip
    restore_config_zip
    touchFile
    getURL
    download_file
    get_size
    generateApiKey
    remove_article
    generateCookieSecret
    verify_freespace
    pretty_time_delta
    is_file_locked
    disk_usage
    sortable_name
    manage_torrents_url
    bdecode
Private Methods:
    _check_against_names
    _setUpSession
"""

import os
import ssl
import unittest
from pathlib import Path
from shutil import rmtree

from sickchill import settings
from sickchill.oldbeard import helpers

TEST_RESULT = "Show.Name.S01E01.HDTV.x264-SICKCHILL"
TEST_CASES = {
    "removewords": [
        TEST_RESULT,
        "Show.Name.S01E01.HDTV.x264-SICKCHILL[cttv]",
        "Show.Name.S01E01.HDTV.x264-SICKCHILL.RiPSaLoT",
        "Show.Name.S01E01.HDTV.x264-SICKCHILL[GloDLS]",
        "Show.Name.S01E01.HDTV.x264-SICKCHILL[EtHD]",
        "Show.Name.S01E01.HDTV.x264-SICKCHILL-20-40",
        "Show.Name.S01E01.HDTV.x264-SICKCHILL[NO-RAR] - [ www.torrentday.com ]",
        "Show.Name.S01E01.HDTV.x264-SICKCHILL[rarbg]",
        "Show.Name.S01E01.HDTV.x264-SICKCHILL[Seedbox]",
        "{ www.SceneTime.com } - Show.Name.S01E01.HDTV.x264-SICKCHILL",
        "].[www.tensiontorrent.com] - Show.Name.S01E01.HDTV.x264-SICKCHILL",
        "[ www.TorrentDay.com ] - Show.Name.S01E01.HDTV.x264-SICKCHILL",
        "Show.Name.S01E01.HDTV.x264-SICKCHILL[silv4]",
        "Show.Name.S01E01.HDTV.x264-SICKCHILL[AndroidTwoU]",
        "[www.newpct1.com]Show.Name.S01E01.HDTV.x264-SICKCHILL",
        "Show.Name.S01E01.HDTV.x264-SICKCHILL-NZBGEEK",
        ".www.Cpasbien.pwShow.Name.S01E01.HDTV.x264-SICKCHILL",
        "Show.Name.S01E01.HDTV.x264-SICKCHILL [1044]",
        "[ www.Cpasbien.pw ] Show.Name.S01E01.HDTV.x264-SICKCHILL",
        "Show.Name.S01E01.HDTV.x264-SICKCHILL.[BT]",
        "Show.Name.S01E01.HDTV.x264-SICKCHILL[vtv]",
        "Show.Name.S01E01.HDTV.x264-SICKCHILL.[www.usabit.com]",
        "[www.Cpasbien.com] Show.Name.S01E01.HDTV.x264-SICKCHILL",
        "Show.Name.S01E01.HDTV.x264-SICKCHILL[ettv]",
        "Show.Name.S01E01.HDTV.x264-SICKCHILL[rartv]",
        "Show.Name.S01E01.HDTV.x264-SICKCHILL-Siklopentan",
        "Show.Name.S01E01.HDTV.x264-SICKCHILL-RP",
        "Show.Name.S01E01.HDTV.x264-SICKCHILL[PublicHD]",
        "[www.Cpasbien.pe] Show.Name.S01E01.HDTV.x264-SICKCHILL",
        "Show.Name.S01E01.HDTV.x264-SICKCHILL[eztv]",
        "Show.Name.S01E01.HDTV.x264-SICKCHILL-[SpastikusTV]",
        "].[ www.tensiontorrent.com ] - Show.Name.S01E01.HDTV.x264-SICKCHILL",
        "[ www.Cpasbien.com ] Show.Name.S01E01.HDTV.x264-SICKCHILL",
        "Show.Name.S01E01.HDTV.x264-SICKCHILL- { www.SceneTime.com }",
        "Show.Name.S01E01.HDTV.x264-SICKCHILL- [ www.torrentday.com ]",
        "Show.Name.S01E01.HDTV.x264-SICKCHILL.Renc",
    ]
}


class HelpersTests(unittest.TestCase):
    """
    Test using test generator
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize test
        """
        super().__init__(*args, **kwargs)


def generator(test_strings):
    """
    Generate tests from test strings

    :param test_strings: to generate tests from
    :return: test
    """

    def _test(self):
        """
        Generate tests
        :param self:
        :return: test to run
        """
        for test_string in test_strings:
            assert helpers.remove_non_release_groups(test_string) == TEST_RESULT

    return _test


class HelpersZipTests(unittest.TestCase):
    """
    Test zip methods
    """

    def test_make_zip(self):
        """
        Test makeZip
        """
        here = os.path.dirname(__file__)
        files = [os.path.join(here, f) for f in os.listdir(here) if f[-3:] == ".py"]
        zip_path = os.path.join(here, "_test.zip")

        assert helpers.makeZip(files, zip_path)
        assert not helpers.makeZip(files, "/:/_test.zip")

        if os.path.isfile(zip_path):
            os.remove(zip_path)

    def test_extract_zip(self):
        """
        Test extractZip
        """
        here = os.path.dirname(__file__)
        files = [os.path.join(here, f) for f in os.listdir(here) if f[-3:] == ".py"]
        zip_path = os.path.join(here, "_test.zip")

        helpers.makeZip(files, zip_path)
        extract_path = os.path.join(here, "_extract_test")
        assert helpers.extractZip(zip_path, extract_path)
        assert not helpers.extractZip(zip_path, "/:/_extract")
        # Test skip directories:
        files += [os.path.join(here, "Logs")]
        helpers.makeZip(files, zip_path)
        assert helpers.extractZip(zip_path, extract_path)

        if os.path.isfile(zip_path):
            os.remove(zip_path)
        if os.path.isdir(extract_path):
            rmtree(extract_path)

    def test_backup_config_zip(self):
        """
        Test backup_config_zip
        """
        here = os.path.dirname(__file__)
        files = [os.path.join(here, f) for f in os.listdir(here) if f[-3:] in [".db", ".py"]]
        zip_path = os.path.join(here, "_backup_test.zip")

        assert helpers.backup_config_zip(files, zip_path, here)
        assert not helpers.backup_config_zip(files, "/:/_backup_test.zip")

        if os.path.isfile(zip_path):
            os.remove(zip_path)

    def test_restore_config_zip(self):
        """
        Test restore_config_zip
        """
        here = os.path.dirname(__file__)
        files = [os.path.join(here, f) for f in os.listdir(here) if f[-3:] in [".db", ".py"]]
        zip_path = os.path.join(here, "_backup_test.zip")

        helpers.backup_config_zip(files, zip_path, here)
        restore_container = os.path.join(here, "_restore_tests")
        os.path.exists(restore_container) or os.mkdir(restore_container)
        restore_path = os.path.join(restore_container, "test")
        assert not helpers.restore_config_zip(files[1], restore_path)  # test invalid zip
        assert helpers.restore_config_zip(zip_path, restore_path)
        assert helpers.restore_config_zip(zip_path, restore_path)  # test extractDir exists

        if os.path.isfile(zip_path):
            os.remove(zip_path)
        if os.path.isdir(restore_container):
            rmtree(restore_container)


class HelpersDirectoryTests(unittest.TestCase):
    """
    Test directory methods
    """

    @unittest.skip("Not yet implemented")
    def test_make_dirs(self):
        """
        Test make_dirs
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_delete_empty_folders(self):
        """
        Test delete_empty_folders
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_make_dir(self):
        """
        Test makeDir
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_is_hidden_folder(self):
        """
        Test is_hidden_folder
        """
        pass


class HelpersFileTests(unittest.TestCase):
    """
    Test file helpers
    """

    @unittest.skip("Not yet implemented")
    def test_is_file_locked(self):
        """
        Test is_file_locked
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_remove_file_failed(self):
        """
        Test remove_file_failed
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_list_media_files(self):
        """
        Test list_media_files
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_copy_file(self):
        """
        Test copyFile
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_move_file(self):
        """
        Test moveFile
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_rename_ep_file(self):
        """
        Test rename_ep_file
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_file_bit_filter(self):
        """
        Test fileBitFilter
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_chmod_as_parent(self):
        """
        Test chmodAsParent
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_backup_versioned_file(self):
        """
        Test backupVersionedFile
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_verify_free_space(self):
        """
        Test verify_freespace
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_get_disk_space_usage(self):
        """
        Test disk_usage
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_download_file(self):
        """
        Test download_file
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_get_size(self):
        """
        Test get_size
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_touch_file(self):
        """
        Test touchFile
        """
        pass


class HelpersFileLinksTests(unittest.TestCase):
    """
    Test sym and hard links
    """

    @unittest.skip("Not yet implemented")
    def test_link(self):
        """
        Test link
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_hardlink_file(self):
        """
        Test hardlinkFile
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_symlink(self):
        """
        Test symlink
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_move_and_symlink_file(self):
        """
        Test moveAndSymlinkFile
        """
        pass


class HelpersEncryptionTests(unittest.TestCase):
    """
    Test encryption and decryption
    """

    def test_create_https_certificates(self):
        """
        Test that create_https_certificates successfully generates certificate and private key
        """
        try:
            import OpenSSL
        except ModuleNotFoundError as error:
            self.skipTest("pyOpenSSL is not installed or error importing it")
            return False
        except ImportError as error:
            self.skipTest(f"OpenSSL module not available: {error}")
            return False

        base_path = Path(__file__).parent.absolute()
        cert_path = base_path / "base.crt"
        pkey_path = base_path / "base.key"

        def removeTestFiles():
            for test_file in [cert_path, pkey_path]:
                try:
                    test_file.unlink()
                except (FileNotFoundError, ValueError):
                    pass

        removeTestFiles()  # always remove existing

        assert helpers.create_https_certificates(cert_path, pkey_path)

        assert cert_path.is_file()
        assert cert_path.stat().st_size > 0, "Generated cert is empty"

        assert pkey_path.is_file()
        assert pkey_path.stat().st_size > 0, "Generated pkey is empty"

        try:
            ctx = helpers.make_context(False)
            assert ctx
        except Exception as error:
            removeTestFiles()
            self.fail(f"Error creating ssl context: {error}")

        try:
            ctx.load_cert_chain(str(cert_path), str(pkey_path))
            ctx.cert_store_stats()
        except ssl.SSLError as error:
            removeTestFiles()
            self.fail(f"Unable to load certificate chain: {error}")

    @unittest.skip("Not yet implemented")
    def test_encrypt(self):
        """
        Test encrypt
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_decrypt(self):
        """
        Test decrypt
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_generate_cookie_secret(self):
        """
        Test generateCookieSecret
        """
        pass


class HelpersShowTests(unittest.TestCase):
    """
    Test show methods
    """

    @unittest.skip("Not yet implemented")
    def test_search_indexer_for_show_id(self):
        """
        Test searchIndexerForShowID
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_check_against_names(self):
        """
        Test _check_against_names
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_get_show(self):
        """
        Test get_show
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_get_abs_no_from_s_and_e(self):
        """
        Test get_absolute_number_from_season_and_episode
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_get_all_eps_from_abs_no(self):
        """
        Test get_all_episodes_from_absolute_number
        """
        pass


class HelpersConnectionTests(unittest.TestCase):
    """
    Test connections
    """

    @unittest.skip("Not yet implemented")
    def test_get_lan_ip(self):
        """
        Test get_lan_ip
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_check_url(self):
        """
        Test check_url
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_anon_url(self):
        """
        Test anon_url
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_set_up_anidb_connection(self):
        """
        Test set_up_anidb_connection
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_set_up_session(self):
        """
        Test _setUpSession
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_get_url(self):
        """
        Test getURL
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_generate_api_key(self):
        """
        Test generateApiKey
        """
        pass


class HelpersMiscTests(unittest.TestCase):
    """
    Test misc helper methods
    """

    @unittest.skip("Not yet implemented")
    def test_indent_xml(self):
        """
        Test indentXML
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_remove_non_release_groups(self):
        """
        Test remove_non_release_groups
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_fix_set_group_id(self):
        """
        Test fixSetGroupID
        """
        pass

    def test_sanitize_scene_name(self):
        """
        Test sanitizeSceneName
        """
        cases = [
            {"name": "", "anime": False, "expected": ""},
            {"name": "Name, with: bad (chars)!", "anime": False, "expected": "Name.with.bad.chars"},
            {"name": "Rock & Roll", "anime": False, "expected": "Rock.and.Roll"},
            {"name": "This is a-test", "anime": False, "expected": "This.is.a.test"},
            {"name": "Trailing dot.", "anime": False, "expected": "Trailing.dot"},
            {"name": "Kuroko's Basketball", "anime": True, "expected": "Kuroko's.Basketball"},
            {"name": "Name with — unusual & characters…", "anime": False, "expected": "Name.with.—.unusual.and.characters"},
            {"name": "Too....many....dots...", "anime": False, "expected": "Too.many.dots"},
            {"name": "'Single' and “Double” quotes", "anime": False, "expected": "Single.and.“Double”.quotes"},
        ]

        for case in cases:
            with self.subTest(case=case):
                self.assertEqual(helpers.sanitizeSceneName(case["name"], anime=case["anime"]), case["expected"])

    def test_full_sanitize_scene_name(self):
        cases = [
            {"name": "Name, with: bad (chars)!", "expected": "name with bad chars"},
            {"name": "a basic name", "expected": "a basic name"},
        ]
        for case in cases:
            with self.subTest(case=case):
                self.assertEqual(helpers.full_sanitizeSceneName(case["name"]), case["expected"])

    @unittest.skip("Not yet implemented")
    def test_remove_article(self):
        """
        Test remove_article
        """
        pass

    @unittest.skip("Not yet implemented")
    def test_pretty_time_delta(self):
        """
        Test pretty_time_delta
        """
        pass

    def test_sortable_name(self):
        """
        Test that sortable_name returns the correct show name
        """
        cases = [
            # raw_name, SORT_ARTICLE, expected
            ("The Big Bang Theory", False, "big bang theory"),
            ("A Big World", False, "big world"),
            ("An Unexpected Journey", False, "unexpected journey"),
            ("The Big Bang Theory", True, "the big bang theory"),
            ("A Big World", True, "a big world"),
            ("An Unexpected Journey", True, "an unexpected journey"),
        ]
        for raw_name, option, expected in cases:
            settings.SORT_ARTICLE = option
            assert helpers.sortable_name(raw_name) == expected

    @unittest.skip("Not yet implemented")
    def test_manage_torrents_url(self):
        """
        Test manage_torrents_url
        """
        pass


if __name__ == "__main__":
    print("==================")
    print("STARTING - Helpers TESTS")
    print("==================")
    print("######################################################################")
    for name, test_data in TEST_CASES.items():
        test_name = "test_{0}".format(name)
        test = generator(test_data)
        setattr(HelpersTests, test_name, test)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(HelpersTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(HelpersConnectionTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(HelpersDirectoryTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(HelpersEncryptionTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(HelpersFileLinksTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(HelpersFileTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(HelpersMiscTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(HelpersShowTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(HelpersZipTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
