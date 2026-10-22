import tempfile
import unittest
from pathlib import Path
from deploy.stage_isolated import stage

class IsolatedStagingTests(unittest.TestCase):
    def test_stage_copies_only_safe_source_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); src=root/"source"; src.mkdir()
            (src/"main.py").write_text("print('ok')")
            (src/".env").write_text("secret")
            (src/"data").mkdir(); (src/"data"/"control.db").write_text("private")
            out=stage(src,root/"ultimate",root/"inventory")
            self.assertEqual(out["staged_files"],1)
            self.assertTrue((root/"ultimate"/"main.py").exists())
            self.assertFalse((root/"ultimate"/".env").exists())
            self.assertFalse((root/"ultimate"/"data").exists())

    def test_refuse_inventory_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); src=root/"src"; src.mkdir()
            inv=root/"inventory"; inv.mkdir()
            with self.assertRaises(ValueError):
                stage(src,inv,inv)
            with self.assertRaises(ValueError):
                stage(src,inv/"ultimate",inv)

    def test_refuse_nonempty_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); src=root/"src"; src.mkdir()
            target=root/"ultimate"; target.mkdir()
            (target/"existing.txt").write_text("important")
            with self.assertRaises(ValueError):
                stage(src,target,root/"inventory")
            self.assertEqual((target/"existing.txt").read_text(),"important")
if __name__=="__main__":
    unittest.main()
