import gzip
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('backup', ROOT/'scripts'/'rollback_backup.py')
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='.test-', dir=ROOT)
        self.root = Path(self.temp.name)
        self.snapshot = self.root/'input.json'
        self.store = self.root/'store'

    def tearDown(self):
        self.temp.cleanup()

    def snapshot_for(self, number):
        self.snapshot.write_text(json.dumps({'format':backup.FORMAT,'payload':{'run':number}}),encoding='utf-8')

    def test_rotation_keeps_exactly_one_backup(self):
        for number in [1,2]:
            self.snapshot_for(number)
            backup.rotate(self.snapshot,self.store)
            backup.verify(self.store)
            self.assertEqual(len(list(self.store.glob('*.gz'))),1)
            self.assertEqual(json.loads(gzip.decompress((self.store/backup.NAME).read_bytes()))['payload']['run'],number)
            self.assertFalse(list(self.store.glob('*.tmp')))

    def test_invalid_snapshot_preserves_previous_backup(self):
        self.snapshot_for(1)
        backup.rotate(self.snapshot,self.store)
        original = (self.store/backup.NAME).read_bytes()
        self.snapshot.write_text('{}',encoding='utf-8')
        with self.assertRaises(ValueError):
            backup.rotate(self.snapshot,self.store)
        self.assertEqual(original,(self.store/backup.NAME).read_bytes())

    def test_corrupt_existing_file_is_not_overwritten(self):
        self.snapshot_for(1)
        self.store.mkdir()
        (self.store/backup.NAME).write_bytes(b'not a backup')
        with self.assertRaises(OSError):
            backup.rotate(self.snapshot,self.store)
        self.assertEqual((self.store/backup.NAME).read_bytes(),b'not a backup')

    def test_failed_replace_keeps_previous_backup_and_removes_temporary(self):
        self.snapshot_for(1)
        backup.rotate(self.snapshot,self.store)
        original = (self.store/backup.NAME).read_bytes()
        self.snapshot_for(2)
        with mock.patch.object(backup.os,'replace',side_effect=OSError('simulated failure')):
            with self.assertRaises(OSError):
                backup.rotate(self.snapshot,self.store)
        self.assertEqual(original,(self.store/backup.NAME).read_bytes())
        self.assertFalse(list(self.store.glob('*.tmp')))

    def test_verify_detects_modified_metadata(self):
        self.snapshot_for(1)
        backup.rotate(self.snapshot,self.store)
        meta = json.loads((self.store/backup.META).read_text(encoding='utf-8'))
        meta['sha256_uncompressed']='incorrect'
        (self.store/backup.META).write_text(json.dumps(meta),encoding='utf-8')
        with self.assertRaises(ValueError):
            backup.verify(self.store)

    def test_verify_reports_extra_archive_without_deleting_it(self):
        self.snapshot_for(1)
        backup.rotate(self.snapshot,self.store)
        other = self.store/'old.gz'
        other.write_bytes(b'keep me')
        with self.assertRaises(ValueError):
            backup.verify(self.store)
        self.assertEqual(other.read_bytes(),b'keep me')


if __name__=='__main__':
    unittest.main()
