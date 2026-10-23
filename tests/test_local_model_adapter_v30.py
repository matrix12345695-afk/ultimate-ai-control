import io
import json
import unittest

from local_model_adapter_v30 import local_endpoint, request_local_plan, environment_ready

ENDPOINT="http://127.0.0.1:11434/v1/chat/completions"
GOOD={"summary":"Plan only","affected_files":["tests/example.py"],"implementation_steps":["Review code"],"tests":["Run unit tests"],"risks":["Regressions"]}

class Response(io.BytesIO):
    headers = {}
    def __enter__(self): return self
    def __exit__(self,*args):self.close()

class LocalModelTests(unittest.TestCase):
    def test_disabled_never_calls_network(self):
        def never(*args,**kwargs): raise AssertionError("network attempted")
        with self.assertRaises(PermissionError):
            request_local_plan("control","Review","test",ENDPOINT,opener=never)
    def test_blocks_external_and_ambiguous_endpoints(self):
        for endpoint in ("https://127.0.0.1:11434/v1/chat/completions",
                         "http://localhost:11434/v1/chat/completions",
                         "http://127.0.0.2:11434/v1/chat/completions",
                         "http://8.8.8.8:11434/v1/chat/completions",
                         "http://127.0.0.1:11434/admin",
                         "http://user:pass@127.0.0.1:11434/v1/chat/completions",
                         "http://127.0.0.1:80/v1/chat/completions"):
            with self.subTest(endpoint=endpoint):
                with self.assertRaises(ValueError):local_endpoint(endpoint)
    def test_mocked_local_success_without_paid_api(self):
        calls=[]
        def opener(request,timeout):
            calls.append((request.full_url,request.get_method(),timeout))
            return Response(json.dumps({"choices":[{"message":{"content":json.dumps(GOOD)}}]}).encode())
        proposal=request_local_plan("control","Review path validator","free-local",ENDPOINT,True,opener)
        self.assertEqual(proposal["summary"],"Plan only")
        self.assertEqual(calls,[(ENDPOINT,"POST",25)])
    def test_fail_closed_output_validation(self):
        for content in ("not json",json.dumps(dict(GOOD,summary="token=abc123"))):
            def opener(req,timeout):
                return Response(json.dumps({"choices":[{"message":{"content":content}}]}).encode())
            with self.assertRaises((ValueError,json.JSONDecodeError)):
                request_local_plan("control","Plan","local",ENDPOINT,True,opener)
    def test_readiness_without_model_service(self):
        self.assertFalse(environment_ready({})["ready"])
        self.assertFalse(environment_ready({"LOCAL_AI_ENABLED":"true","LOCAL_AI_ENDPOINT":"https://external.example/v1/chat/completions"})["ready"])
        self.assertTrue(environment_ready({"LOCAL_AI_ENABLED":"true","LOCAL_AI_ENDPOINT":ENDPOINT,"LOCAL_AI_MODEL":"test"})["ready"])
if __name__=="__main__": unittest.main()
