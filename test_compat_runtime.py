import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from compat.manager import RuntimeManager
from compat.utils import resolve_requirements
from compat.exceptions import RuntimeNotFoundError, WorkerError
from compat_test_helpers import get_new_pydantic_version, get_old_pydantic_version, fail_fast


class CompatRuntimeTests(unittest.TestCase):
    def setUp(self):
        self._tempdir = tempfile.TemporaryDirectory()
        self.tempdir = Path(self._tempdir.name)
        self.manager = RuntimeManager(cache_dir=self.tempdir)
        self._patcher = patch("compat.runtime._manager", self.manager)
        self._patcher.start()

    def tearDown(self):
        self._patcher.stop()
        self._tempdir.cleanup()

    def test_resolve_requirements_from_source_file(self):
        source_file = Path(__file__).resolve()
        requirements = resolve_requirements("runtimes/old_requirements.txt", str(source_file))
        expected = source_file.parent / "runtimes" / "old_requirements.txt"

        self.assertTrue(requirements.exists())
        self.assertEqual(requirements, expected.resolve())

    def test_runtime_installs_and_runs_isolated_versions(self):
        old_version = get_old_pydantic_version()
        new_version = get_new_pydantic_version()

        self.assertEqual(old_version, "1.10.15")
        self.assertEqual(new_version, "2.5.3")
        self.assertNotEqual(old_version, new_version)

    def test_runtime_propagates_worker_exceptions(self):
        with self.assertRaises(WorkerError) as cm:
            fail_fast(-1)

        self.assertIn("ValueError", str(cm.exception))
        self.assertIn("x must be non-negative, got -1", str(cm.exception))

    def test_runtime_cache_invalidate_and_list(self):
        req_path = self.tempdir / "requirements.txt"
        req_path.write_text("dummy-package==0.0.1", encoding="utf-8")

        runtime_dir = self.tempdir / self.manager._hash_requirements(req_path)
        runtime_dir.mkdir()
        (runtime_dir / ".compat_ready").write_text("ok", encoding="utf-8")
        (runtime_dir / "artifact.txt").write_text("data", encoding="utf-8")

        manager = RuntimeManager(cache_dir=self.tempdir)
        runtimes = manager.list_runtimes()

        self.assertEqual(len(runtimes), 1)
        self.assertTrue(runtimes[0]["ready"])
        self.assertEqual(runtimes[0]["name"], runtime_dir.name)

        manager.invalidate(req_path)
        self.assertFalse(runtime_dir.exists())

    def test_invalidate_missing_requirements_raises(self):
        manager = RuntimeManager(cache_dir=self.tempdir)
        missing_path = self.tempdir / "missing.txt"

        with self.assertRaises(RuntimeNotFoundError):
            manager.invalidate(missing_path)


if __name__ == "__main__":
    unittest.main()
