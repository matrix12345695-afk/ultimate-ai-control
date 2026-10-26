import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
spec=importlib.util.spec_from_file_location('nova_backup_guard',Path(__file__).resolve().parents[1]/'ci/nova-recovery/backup_guard.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)

class BackupGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.path=self.root/'archive';self.raw=b'PGDMP'+b'x'*2000;self.manifest=guard.publish_archive(self.path,self.raw)
    def tearDown(self): self.temp.cleanup()
    def test_private_integrity_and_exclusive_archive(self):
        self.assertEqual(self.path.stat().st_mode&0o777,0o600);self.assertEqual(guard.verified_bytes(self.path,self.manifest),self.raw)
        with self.assertRaises(FileExistsError): guard.publish_archive(self.path,b'y'*2000)
        self.assertEqual(self.path.read_bytes(),self.raw)
    def test_wrong_live_source_or_arbitrary_target_never_calls_executor(self):
        run=Mock()
        for target in ('nova_recovery_source','novaweb_crm_dev','inventory','postgres','nova_recovery_target;DROP DATABASE postgres'):
            with self.assertRaises(ValueError): guard.restore(run,self.path,self.manifest,target)
        run.assert_not_called()
    def test_nonempty_or_identity_mismatch_prevents_restore(self):
        for response in (b'nova_recovery_target|1',b'other|0',b'nova_recovery_target|0|unexpected'):
            run=Mock(return_value=response)
            with self.assertRaises(ValueError): guard.restore(run,self.path,self.manifest,'nova_recovery_target')
            self.assertEqual(run.call_count,1);self.assertEqual(run.call_args.args[0],'psql')
    def test_corrupt_truncated_missing_symlink_unsafe_mode_prevent_any_connection(self):
        run=Mock();self.path.write_bytes(self.raw[:-1]+b'y')
        with self.assertRaises(ValueError): guard.restore(run,self.path,self.manifest,'nova_recovery_target')
        self.path.write_bytes(b'PGDMP')
        with self.assertRaises(ValueError): guard.restore(run,self.path,self.manifest,'nova_recovery_target')
        self.path.unlink()
        with self.assertRaises(FileNotFoundError): guard.restore(run,self.path,self.manifest,'nova_recovery_target')
        target=self.root/'target';target.write_bytes(self.raw);target.chmod(0o600);self.path.symlink_to(target)
        with self.assertRaises(ValueError): guard.restore(run,self.path,self.manifest,'nova_recovery_target')
        self.path.unlink();self.path.write_bytes(self.raw);self.path.chmod(0o644)
        with self.assertRaises(ValueError): guard.restore(run,self.path,self.manifest,'nova_recovery_target')
        run.assert_not_called()
    def test_manifest_scope_version_size_and_extra_fields_rejected_before_connection(self):
        run=Mock()
        for change in ({'scope':'cluster'},{'postgres_major':16},{'format':'plain-sql'},{'bytes':True},{'sha256':'f'*64},{'extra':'unapproved'}):
            with self.assertRaises(ValueError): guard.restore(run,self.path,dict(self.manifest,**change),'nova_recovery_target')
        run.assert_not_called()
    def test_empty_target_uses_atomic_restore_without_clean_or_drop(self):
        run=Mock(side_effect=[b'nova_recovery_target|0',b''])
        guard.restore(run,self.path,self.manifest,'nova_recovery_target')
        args=run.call_args_list[1].args;self.assertIn('--single-transaction',args);self.assertIn('--exit-on-error',args);self.assertNotIn('--clean',args);self.assertEqual(run.call_args_list[1].kwargs['input'],self.raw)
    def test_empty_or_oversize_never_creates_file(self):
        p=self.root/'bad'
        for raw in (b'',b'x'*1000,b'x'*(32*1024**2+1)):
            with self.assertRaises(ValueError): guard.publish_archive(p,raw)
            self.assertFalse(p.exists())
    def test_symlink_destination_never_overwrites_target(self):
        link=self.root/'link';link.symlink_to(self.path)
        with self.assertRaises(FileExistsError): guard.publish_archive(link,self.raw)
        self.assertEqual(self.path.read_bytes(),self.raw)
