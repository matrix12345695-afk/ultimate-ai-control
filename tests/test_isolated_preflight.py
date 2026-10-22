import tempfile
import unittest
from pathlib import Path
from deploy.isolated_preflight import check

class DeploymentIsolationTest(unittest.TestCase):
    def test_isolated_empty_directory(self):
        with tempfile.TemporaryDirectory() as root:
            target=Path(root)/"ultimate"
            target.mkdir()
            data=check(target,Path(root)/"inventory")
            self.assertEqual(data["status"],"PREFLIGHT_ONLY")
            self.assertFalse(data["deploy_performed"])

    def test_inventory_path_blocked(self):
        with tempfile.TemporaryDirectory() as root:
            inventory=Path(root)/"inventory"
            inventory.mkdir()
            for target in (inventory,inventory/"inside",Path(root)):
                with self.assertRaises(ValueError):
                    check(target,inventory)

    def test_nonempty_target_blocked(self):
        with tempfile.TemporaryDirectory() as root:
            target=Path(root)/"ultimate"
            target.mkdir()
            (target/"data.db").write_text("important")
            with self.assertRaises(ValueError):
                check(target,Path(root)/"inventory")
if __name__=="__main__":
    unittest.main()
