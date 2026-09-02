"""Unit tests for get_git_revision / format_git_revision (Help & Info SHA)."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest import mock

from sickchill import init_helpers


def _clear_revision_cache() -> None:
    init_helpers._revision_cache = None


class TestGetGitRevision(unittest.TestCase):
    def setUp(self):
        _clear_revision_cache()
        self._env_backup = {key: os.environ.get(key) for key in ("SICKCHILL_SHA", "SICKCHILL_BRANCH", "GIT_SHA", "GIT_BRANCH")}
        for key in self._env_backup:
            os.environ.pop(key, None)

    def tearDown(self):
        _clear_revision_cache()
        for key, value in self._env_backup.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_from_git_checkout(self):
        sha = "e1f8475ded8dabcdef0123456789abcdef012345"
        with mock.patch.object(init_helpers, "git_folder") as gf:
            gf.exists.return_value = True
            gf.parent = Path("/repo")
            with mock.patch.object(init_helpers, "_git_output") as git_out:
                git_out.side_effect = [
                    ".git",  # rev-parse --git-dir
                    sha,  # rev-parse HEAD
                    "develop",  # rev-parse --abbrev-ref HEAD
                ]
                branch, got_sha = init_helpers.get_git_revision()
        self.assertEqual(branch, "develop")
        self.assertEqual(got_sha, sha)
        # Cached: second call does not hit git again
        with mock.patch.object(init_helpers, "_git_output") as git_out2:
            self.assertEqual(init_helpers.get_git_revision(), ("develop", sha))
            git_out2.assert_not_called()

    def test_skips_git_when_dot_git_missing(self):
        """No .git file/dir → do not spawn git (pip install / bare tree)."""
        with mock.patch.object(init_helpers, "git_folder") as gf:
            gf.exists.return_value = False
            with mock.patch.object(init_helpers, "_git_output") as git_out:
                with mock.patch.object(init_helpers, "_revision_file") as rev_file:
                    rev_file.is_file.return_value = False
                    self.assertEqual(init_helpers.get_git_revision(), ("", ""))
                    git_out.assert_not_called()

    def test_worktree_git_file_still_looked_up(self):
        """Worktrees use a .git *file*; exists() is enough (not is_dir())."""
        sha = "cccccccccccccccccccccccccccccccccccccccc"
        with mock.patch.object(init_helpers, "git_folder") as gf:
            gf.exists.return_value = True
            gf.is_dir.return_value = False  # file pointer
            gf.parent = Path("/repo")
            with mock.patch.object(init_helpers, "_git_output") as git_out:
                git_out.side_effect = [".git", sha, "HEAD"]
                branch, got_sha = init_helpers.get_git_revision()
        self.assertEqual(branch, "HEAD")
        self.assertEqual(got_sha, sha)
        gf.is_dir.assert_not_called()

    def test_from_revision_file_when_no_git(self):
        sha = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        with mock.patch.object(init_helpers, "_revision_from_git", return_value=None):
            with mock.patch.object(init_helpers, "_revision_file") as rev_file:
                rev_file.is_file.return_value = True
                with mock.patch.object(
                    init_helpers,
                    "_parse_revision_file",
                    return_value=("SHA-tag", sha),
                ):
                    branch, got_sha = init_helpers.get_git_revision()
        self.assertEqual(branch, "SHA-tag")
        self.assertEqual(got_sha, sha)

    def test_parse_revision_file_formats(self):
        with self.subTest("branch and sha"):
            path = mock.Mock(spec=Path)
            path.read_text.return_value = "develop deadbeefdeadbeefdeadbeefdeadbeefdeadbeef\n"
            self.assertEqual(
                init_helpers._parse_revision_file(path),
                ("develop", "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"),
            )
        with self.subTest("sha only"):
            path = mock.Mock(spec=Path)
            path.read_text.return_value = "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef\n"
            self.assertEqual(
                init_helpers._parse_revision_file(path),
                ("", "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"),
            )
        with self.subTest("unknown placeholder ignored"):
            path = mock.Mock(spec=Path)
            path.read_text.return_value = "develop unknown\n"
            self.assertEqual(init_helpers._parse_revision_file(path), ("", ""))
        with self.subTest("empty"):
            path = mock.Mock(spec=Path)
            path.read_text.return_value = "\n"
            self.assertEqual(init_helpers._parse_revision_file(path), ("", ""))
        with self.subTest("missing file"):
            path = mock.Mock(spec=Path)
            path.read_text.side_effect = OSError("nope")
            self.assertEqual(init_helpers._parse_revision_file(path), ("", ""))

    def test_from_env_when_git_and_file_absent(self):
        sha = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        os.environ["SICKCHILL_SHA"] = sha
        os.environ["SICKCHILL_BRANCH"] = "feature/x"
        with mock.patch.object(init_helpers, "_revision_from_git", return_value=None):
            with mock.patch.object(init_helpers, "_revision_file") as rev_file:
                rev_file.is_file.return_value = False
                branch, got_sha = init_helpers.get_git_revision()
        self.assertEqual(branch, "feature/x")
        self.assertEqual(got_sha, sha)

    def test_env_unknown_treated_as_empty(self):
        os.environ["GIT_SHA"] = "unknown"
        os.environ["GIT_BRANCH"] = "unknown"
        with mock.patch.object(init_helpers, "_revision_from_git", return_value=None):
            with mock.patch.object(init_helpers, "_revision_file") as rev_file:
                rev_file.is_file.return_value = False
                self.assertEqual(init_helpers.get_git_revision(), ("", ""))

    def test_all_missing_returns_empty(self):
        with mock.patch.object(init_helpers, "_revision_from_git", return_value=None):
            with mock.patch.object(init_helpers, "_revision_file") as rev_file:
                rev_file.is_file.return_value = False
                self.assertEqual(init_helpers.get_git_revision(), ("", ""))


class TestFormatGitRevision(unittest.TestCase):
    def setUp(self):
        _clear_revision_cache()

    def tearDown(self):
        _clear_revision_cache()

    def test_branch_and_short_sha(self):
        with mock.patch.object(
            init_helpers,
            "get_git_revision",
            return_value=("develop", "e1f8475ded8dabcdef0123456789abcdef012345"),
        ):
            self.assertEqual(init_helpers.format_git_revision(), "develop@e1f8475ded8d")

    def test_detached_head_omits_branch(self):
        with mock.patch.object(
            init_helpers,
            "get_git_revision",
            return_value=("HEAD", "e1f8475ded8dabcdef0123456789abcdef012345"),
        ):
            self.assertEqual(init_helpers.format_git_revision(), "e1f8475ded8d")

    def test_empty(self):
        with mock.patch.object(init_helpers, "get_git_revision", return_value=("", "")):
            self.assertEqual(init_helpers.format_git_revision(), "")


if __name__ == "__main__":
    unittest.main()
