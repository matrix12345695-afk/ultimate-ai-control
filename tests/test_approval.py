import sqlite3
import unittest
from approval import init_approvals, request_approval, decide, is_authorized

class ApprovalTest(unittest.TestCase):
    def setUp(self):
        self.conn=sqlite3.connect(":memory:")
        init_approvals(self.conn)
        self.payload={"commit":"abc123","target":"production"}
        self.id=request_approval(self.conn,1,"deploy","production",self.payload)

    def tearDown(self):
        self.conn.close()

    def test_requires_admin(self):
        with self.assertRaises(PermissionError):
            decide(self.conn,self.id,"bad","admin",True)

    def test_approval_exact_artifact(self):
        decide(self.conn,self.id,"admin","admin",True)
        self.assertTrue(is_authorized(self.conn,self.id,1,"deploy","production",self.payload))
        self.assertFalse(is_authorized(self.conn,self.id,1,"deploy","production",{"commit":"different"}))
        self.assertFalse(is_authorized(self.conn,self.id,1,"deploy","staging",self.payload))

    def test_denied(self):
        decide(self.conn,self.id,"admin","admin",False)
        self.assertFalse(is_authorized(self.conn,self.id,1,"deploy","production",self.payload))

    def test_cannot_reapprove(self):
        decide(self.conn,self.id,"admin","admin",True)
        with self.assertRaises(ValueError):
            decide(self.conn,self.id,"admin","admin",True)

if __name__=="__main__":
    unittest.main()
