"""Small adversarial boundary check, executed inside the sandbox, not on the host."""
FILES={'tests/test_boundary.py': '''import os, pathlib, resource, socket, threading, unittest
class BoundaryTests(unittest.TestCase):
    def test_no_network(self):
        with self.assertRaises(OSError): socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    def test_production_paths_are_absent(self):
        self.assertFalse(pathlib.Path('/home/maksim/inventory-bot').exists())
        self.assertFalse(pathlib.Path('/home/maksim/.config/ultimate-review').exists())
        self.assertNotIn('TELEGRAM_BOT_TOKEN',os.environ)
        self.assertNotIn('OPENAI_API_KEY',os.environ)
    def test_source_readonly(self):
        with self.assertRaises(OSError): pathlib.Path('/workspace/escape').write_text('no')
    def test_process_forks_denied(self):
        with self.assertRaises(OSError): os.fork()
    def test_threads_denied(self):
        with self.assertRaises(RuntimeError): threading.Thread(target=lambda: None).start()
    def test_limits_and_no_capabilities(self):
        self.assertEqual(len(os.sched_getaffinity(0)),1)
        self.assertLessEqual(resource.getrlimit(resource.RLIMIT_AS)[1],320*1024*1024)
        status=pathlib.Path('/proc/self/status').read_text()
        self.assertIn('CapEff:\\t0000000000000000',status)
        self.assertIn('NoNewPrivs:\\t1',status)
'''}
