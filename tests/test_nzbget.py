import datetime
import unittest
from base64 import standard_b64encode
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from sickchill.oldbeard import nzbget

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
