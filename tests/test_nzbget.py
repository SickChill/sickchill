import datetime
import gzip
import unittest
from base64 import standard_b64encode
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from sickchill.oldbeard import nzbget, sab

NZB = b'<?xml version="1.0" encoding="UTF-8"?><nzb></nzb>'


def _result(body=NZB, nzbdata=False):
    episode = SimpleNamespace(airdate=datetime.date(2020, 1, 1), show=SimpleNamespace(indexerid=7), season=1, episode=1)
    provider = MagicMock()
    provider.name = "Indexer"
    provider.login.return_value = True
    provider.get_url.return_value = body
    show = SimpleNamespace(is_anime=False, quality=0)
    result = SimpleNamespace(
        name="Show.S01E01",
        url="http://indexer/dead" if body != NZB else "http://indexer/show.nzb",
        provider=provider,
        episodes=[episode],
        show=show,
        quality=4,
        priority=0,
        is_nzb=not nzbdata,
        is_nzbdata=nzbdata,
        extraInfo=[body] if nzbdata else [],
    )
    return result


def _proxy(version, append_result):
    proxy = MagicMock()
    proxy.writelog.return_value = True
    proxy.version.return_value = version
    proxy.append.return_value = append_result
    return proxy


class NzbGetSendTests(unittest.TestCase):
    def _send(self, result, version, append_result):
        proxy = _proxy(version, append_result)
        with (
            patch("sickchill.oldbeard.nzbget.settings.NZBGET_HOST", "localhost:6789"),
            patch("sickchill.oldbeard.nzbget.get_proxy", return_value=proxy),
            patch("sickchill.oldbeard.nzbget.settings.NZBGET_CATEGORY", "tv"),
            patch("sickchill.oldbeard.nzbget.settings.NZBGET_CATEGORY_BACKLOG", "tv"),
            patch("sickchill.oldbeard.nzbget.settings.NZBGET_PRIORITY", 0),
            patch("sickchill.oldbeard.nzbget.History") as history,
        ):
            sent = nzbget.send_nzb(result)
        return sent, proxy, history

    def test_dead_link_is_not_queued(self):
        sent, proxy, history = self._send(_result(b"<html>404</html>"), "26.3", 5)

        self.assertFalse(sent)
        proxy.append.assert_not_called()
        proxy.appendurl.assert_not_called()
        history.return_value.log_dead_url.assert_called_once_with("http://indexer/dead", "Show.S01E01", "Indexer")

    def test_empty_download_is_recorded_as_dead(self):
        sent, proxy, history = self._send(_result(b""), "21.1", 5)

        self.assertFalse(sent)
        proxy.append.assert_not_called()
        history.return_value.log_dead_url.assert_called_once_with("http://indexer/dead", "Show.S01E01", "Indexer")

    def test_http_404_is_recorded_and_server_error_is_not(self):
        gone = _result()
        gone.url = "http://indexer/missing"
        gone.provider.get_url.return_value = SimpleNamespace(status_code=404, content=b"<html>missing</html>")
        sent, proxy, history = self._send(gone, "26.3", 5)

        self.assertFalse(sent)
        proxy.append.assert_not_called()
        history.return_value.log_dead_url.assert_called_once_with("http://indexer/missing", "Show.S01E01", "Indexer")

        busy = _result()
        busy.url = "http://indexer/later"
        busy.provider.get_url.return_value = SimpleNamespace(status_code=503, content=b"busy")
        sent, proxy, history = self._send(busy, "26.3", 5)

        self.assertFalse(sent)
        proxy.append.assert_not_called()
        history.return_value.log_dead_url.assert_not_called()

    def test_truncated_gzip_is_rejected_and_valid_gzip_is_sent(self):
        sent, proxy, _history = self._send(_result(gzip.compress(NZB)[:8]), "26.3", 5)

        self.assertFalse(sent)
        proxy.append.assert_not_called()

        sent, proxy, history = self._send(_result(gzip.compress(NZB)), "26.3", 8)

        self.assertTrue(sent)
        self.assertEqual(proxy.append.call_args.args[1], standard_b64encode(NZB).decode("ascii"))
        history.return_value.log_dead_url.assert_not_called()

    def test_newznab_account_error_stays_retryable_and_missing_item_is_dead(self):
        account = _result(b'<?xml version="1.0" encoding="UTF-8"?><error code="100" description="Incorrect user credentials"/>')
        account.url = "http://indexer/account"
        account.provider.check_auth_from_data.return_value = False
        sent, proxy, history = self._send(account, "26.3", 5)

        self.assertFalse(sent)
        proxy.append.assert_not_called()
        account.provider.check_auth_from_data.assert_called_once()
        history.return_value.log_dead_url.assert_not_called()

        missing = _result(b'<?xml version="1.0" encoding="UTF-8"?><error code="300" description="No such item"/>')
        missing.url = "http://indexer/missing-item"
        missing.provider.check_auth_from_data.return_value = False
        sent, proxy, history = self._send(missing, "26.3", 5)

        self.assertFalse(sent)
        proxy.append.assert_not_called()
        history.return_value.log_dead_url.assert_called_once_with("http://indexer/missing-item", "Show.S01E01", "Indexer")
        missing.provider.check_auth_from_data.assert_not_called()

        coded = _result(b'<?xml version="1.0" encoding="UTF-8"?><error code="101"/>')
        coded.url = "http://indexer/limited"
        coded.provider.check_auth_from_data.return_value = False
        sent, _proxy_obj, history = self._send(coded, "26.3", 5)

        self.assertFalse(sent)
        coded.provider.check_auth_from_data.assert_called_once()
        history.return_value.log_dead_url.assert_not_called()

        described = _result(b'<?xml version="1.0" encoding="UTF-8"?><error description="Request limit reached"/>')
        described.url = "http://indexer/described"
        described.provider.check_auth_from_data.return_value = False
        sent, proxy, history = self._send(described, "26.3", 5)

        self.assertFalse(sent)
        proxy.append.assert_not_called()
        described.provider.check_auth_from_data.assert_called_once()
        history.return_value.log_dead_url.assert_not_called()

        broken = _result(b'<?xml version="1.0" encoding="UTF-8"?><error code="100" description="Incorrect user credentials"/>')
        broken.url = "http://indexer/boom"
        broken.provider.check_auth_from_data.side_effect = RuntimeError("checker failed")
        sent, proxy, history = self._send(broken, "26.3", 5)

        self.assertFalse(sent)
        proxy.append.assert_not_called()
        history.return_value.log_dead_url.assert_not_called()

    def test_login_failure_is_not_recorded_as_dead(self):
        result = _result()
        result.provider.login.return_value = False
        sent, proxy, history = self._send(result, "26.3", 5)

        self.assertFalse(sent)
        proxy.append.assert_not_called()
        history.return_value.log_dead_url.assert_not_called()

    def test_version_13_and_newer_receive_base64_text(self):
        sent, proxy, history = self._send(_result(), "26.3", 8)

        self.assertTrue(sent)
        content = proxy.append.call_args.args[1]
        self.assertIsInstance(content, str)
        self.assertEqual(content, standard_b64encode(NZB).decode("ascii"))
        self.assertNotIn("http://indexer", content)
        proxy.appendurl.assert_not_called()
        history.return_value.log_dead_url.assert_not_called()

    def test_version_12_receives_base64_text(self):
        sent, proxy, _history = self._send(_result(), "12.0", True)

        self.assertTrue(sent)
        self.assertEqual(proxy.append.call_args.args[4], standard_b64encode(NZB).decode("ascii"))
        proxy.appendurl.assert_not_called()

    def test_version_0_receives_base64_text(self):
        sent, proxy, _history = self._send(_result(), "0.8.0", True)

        self.assertTrue(sent)
        self.assertEqual(proxy.append.call_args.args[3], standard_b64encode(NZB).decode("ascii"))

    def test_version_11_receives_base64_text(self):
        sent, proxy, _history = self._send(_result(), "11.0", True)

        self.assertTrue(sent)
        self.assertEqual(proxy.append.call_args.args[4], standard_b64encode(NZB).decode("ascii"))
        proxy.appendurl.assert_not_called()

    def test_nzbdata_string_is_base64_text(self):
        sent, proxy, history = self._send(_result(NZB.decode("ascii"), nzbdata=True), "26.3", 4)

        self.assertTrue(sent)
        self.assertEqual(proxy.append.call_args.args[1], standard_b64encode(NZB).decode("ascii"))
        proxy.append.call_args.args[1].encode("ascii")
        history.return_value.log_dead_url.assert_not_called()

    def test_rejected_append_returns_false(self):
        sent, _proxy_obj, history = self._send(_result(), "26.3", 0)

        self.assertFalse(sent)
        history.return_value.log_dead_url.assert_not_called()


class SabSendTests(unittest.TestCase):
    def _send(self, result, sab_response):
        with (
            patch("sickchill.oldbeard.sab.settings.SAB_HOST", "http://sab:8080/"),
            patch("sickchill.oldbeard.sab.settings.SAB_APIKEY", "key"),
            patch("sickchill.oldbeard.sab.settings.SAB_USERNAME", ""),
            patch("sickchill.oldbeard.sab.settings.SAB_PASSWORD", ""),
            patch("sickchill.oldbeard.sab.settings.SAB_CATEGORY", "tv"),
            patch("sickchill.oldbeard.sab.settings.SAB_CATEGORY_BACKLOG", "backlog"),
            patch("sickchill.oldbeard.sab.settings.SAB_CATEGORY_ANIME", "anime"),
            patch("sickchill.oldbeard.sab.settings.SAB_CATEGORY_ANIME_BACKLOG", "anime-backlog"),
            patch("sickchill.oldbeard.sab.settings.SAB_FORCED", False),
            patch("sickchill.oldbeard.sab.helpers.getURL", return_value=sab_response) as sab_call,
            patch("sickchill.oldbeard.nzbget.History") as history,
        ):
            sent = sab.send_nzb(result)
        return sent, sab_call, history

    def test_dead_link_is_not_sent(self):
        sent, sab_call, history = self._send(_result(b"<html>404</html>"), {"status": True, "nzo_ids": ["1"]})

        self.assertFalse(sent)
        sab_call.assert_not_called()
        history.return_value.log_dead_url.assert_called_once_with("http://indexer/dead", "Show.S01E01", "Indexer")

    def test_valid_nzb_is_uploaded(self):
        sent, sab_call, history = self._send(_result(), {"status": True, "nzo_ids": ["SABnzbd_nzo_1"]})

        self.assertTrue(sent)
        params = sab_call.call_args.kwargs["params"]
        filename, body = sab_call.call_args.kwargs["files"]["nzbfile"]
        self.assertEqual(params["mode"], "addfile")
        self.assertNotIn("name", params)
        self.assertEqual(filename, "Show.S01E01.nzb")
        self.assertEqual(body, NZB)
        history.return_value.log_dead_url.assert_not_called()

    def test_account_error_stays_retryable_and_missing_item_is_dead(self):
        account = _result(b'<?xml version="1.0" encoding="UTF-8"?><error code="100" description="Incorrect user credentials"/>')
        account.url = "http://indexer/account"
        account.provider.check_auth_from_data.return_value = False
        sent, sab_call, history = self._send(account, {"status": True})

        self.assertFalse(sent)
        sab_call.assert_not_called()
        history.return_value.log_dead_url.assert_not_called()

        missing = _result(b'<?xml version="1.0" encoding="UTF-8"?><error code="300" description="No such item"/>')
        missing.url = "http://indexer/missing-item"
        sent, sab_call, history = self._send(missing, {"status": True})

        self.assertFalse(sent)
        sab_call.assert_not_called()
        history.return_value.log_dead_url.assert_called_once_with("http://indexer/missing-item", "Show.S01E01", "Indexer")

    def test_sab_rejection_does_not_record_a_dead_link(self):
        sent, sab_call, history = self._send(_result(), {"status": False, "error": "Failed to add NZB"})

        self.assertFalse(sent)
        sab_call.assert_called_once()
        history.return_value.log_dead_url.assert_not_called()

    def test_nzbdata_is_uploaded(self):
        sent, sab_call, _history = self._send(_result(NZB.decode("ascii"), nzbdata=True), {"status": True, "nzo_ids": ["1"]})

        self.assertTrue(sent)
        _filename, body = sab_call.call_args.kwargs["files"]["nzbfile"]
        self.assertEqual(body, NZB)
