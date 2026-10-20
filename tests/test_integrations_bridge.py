import importlib.util, json, pathlib, threading, unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
ROOT=pathlib.Path(__file__).resolve().parents[1]
path=ROOT/"scripts/integrations_bridge.py"
module=None
if path.exists():
    spec=importlib.util.spec_from_file_location("bridge",path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class Handler(BaseHTTPRequestHandler):
    calls=[]
    def log_message(self,*args):pass
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        self.calls.append((self.path,dict(self.headers),body))
        self.send_response(200);self.send_header("Content-Type","application/json");self.end_headers();self.wfile.write(b'{"status":"accepted"}')
    def do_GET(self):
        self.calls.append((self.path,dict(self.headers),None))
        if self.path=="/redirect":
            self.send_response(302);self.send_header("Location","http://127.0.0.1:1/secret");self.end_headers()
        else:
            self.send_response(401);self.end_headers();self.wfile.write(b'fixture-secret must not appear in errors')
class IntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        cls.base="http://127.0.0.1:"+str(cls.server.server_port)
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close()
    def m(self):self.assertIsNotNone(module,"integration bridge not implemented");return module
    def test_missing_key_denies(self):
        m=self.m()
        with self.assertRaises(ValueError):m.CogneeClient(self.base,"")
    def test_remote_http_denied(self):
        m=self.m()
        with self.assertRaises(ValueError):m.CogneeClient("http://example.com","fixture")
    def test_url_credentials_denied(self):
        m=self.m()
        with self.assertRaises(ValueError):m.CogneeClient("https://user:password@example.com","fixture")
    def test_add_uses_observed_camel_case_schema(self):
        m=self.m();c=m.CogneeClient(self.base,"fixture-secret")
        self.assertEqual(c.add_text(["neutral fixture"],"sneak_r14"),{"status":"accepted"})
        path,headers,body=Handler.calls[-1];self.assertEqual(path,"/api/v1/add_text");self.assertEqual(body,{"textData":["neutral fixture"],"datasetName":"sneak_r14"});self.assertEqual(headers.get("X-Api-Key"),"fixture-secret")
    def test_recall_requires_dataset(self):
        m=self.m();c=m.CogneeClient(self.base,"fixture")
        with self.assertRaises(ValueError):c.recall("question","")
    def test_recall_is_scoped_context(self):
        m=self.m();c=m.CogneeClient(self.base,"fixture");c.recall("question","sneak_r14")
        self.assertEqual(Handler.calls[-1][2]["datasets"],["sneak_r14"]);self.assertTrue(Handler.calls[-1][2]["onlyContext"])
    def test_error_does_not_expose_body_or_key(self):
        m=self.m();c=m.CogneeClient(self.base,"fixture-secret")
        with self.assertRaises(m.ProviderError) as e:c.request("GET","/error")
        self.assertNotIn("fixture-secret",str(e.exception));self.assertEqual(e.exception.status,401)
    def test_redirect_rejected(self):
        m=self.m();c=m.CogneeClient(self.base,"fixture")
        with self.assertRaises(m.ProviderError) as e:c.request("GET","/redirect")
        self.assertEqual(e.exception.status,302)
if __name__=="__main__":unittest.main()
