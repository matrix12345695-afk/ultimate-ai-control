import unittest
from monitoring import transitions
class Tests(unittest.TestCase):
 def test_new_failure(self):
  self.assertEqual(len(transitions({}, {'site':(False,'timeout')})),1)
 def test_no_repeat(self):
  state={'site':(False,'timeout')}
  self.assertEqual(transitions(state,state),[])
 def test_recovery(self):
  self.assertIn('RECOVERED',transitions({'site':(False,'timeout')},{'site':(True,'ok')})[0])
