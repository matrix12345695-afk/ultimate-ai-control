import sqlite3
import unittest
from datetime import datetime,timezone,timedelta
from mailbox_core_v37 import initialize,publish,claim_next
from mailbox_recovery_v40 import inspect_claims
class RecoveryTests(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(":memory:",isolation_level=None)
  initialize(self.db)
  publish(self.db,"a"*48,{"nonce":"a"*48},"render-producer")
  claim_next(self.db,"vps-consumer")
  self.now=datetime.now(timezone.utc)
  self.db.execute("UPDATE review_mailbox SET created_at=?",( (self.now-timedelta(hours=1)).isoformat(),))
 def tearDown(self):self.db.close()
 def test_claim_is_flagged_but_not_requeued(self):
  flagged=inspect_claims(self.db,300,self.now)
  self.assertEqual(len(flagged),1)
  self.assertEqual(flagged[0]["state"],"manual_reconciliation")
  self.assertIsNone(claim_next(self.db,"vps-consumer"))
  self.assertEqual(self.db.execute("SELECT status FROM review_mailbox").fetchone()[0],"claimed")
 def test_requires_valid_threshold(self):
  with self.assertRaises(ValueError):inspect_claims(self.db,0,self.now)
