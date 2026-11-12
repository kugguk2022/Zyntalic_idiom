"""HTTP boundary checks using a real child server on an ephemeral local port."""
import json
import os
import socket
import subprocess
import tempfile
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request,urlopen

class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        with socket.socket() as s:s.bind(('127.0.0.1',0));cls.port=s.getsockname()[1]
        cls.proc=subprocess.Popen(['python','app.py'],env=dict(os.environ,PORT=str(cls.port),INQUIRY_DATA=cls.temp.name,INQUIRY_ADMIN_TOKEN='test-only-secret'),stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        for _ in range(50):
            try:
                cls.request('/health');return
            except OSError:time.sleep(.05)
        raise RuntimeError('Server startup failed')
    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate();cls.proc.communicate(timeout=5);cls.temp.cleanup()
    @classmethod
    def request(cls,path,body=None,token=None):
        headers={'Content-Type':'application/json'}
        if token:headers['Authorization']='Bearer '+token
        req=Request('http://127.0.0.1:'+str(cls.port)+path,data=json.dumps(body).encode() if body is not None else None,headers=headers)
        try:
            with urlopen(req,timeout=3) as r:return r.status,r.read(),r.headers
        except HTTPError as e:return e.code,e.read(),e.headers
    def test_public_state_is_empty_and_static_policy(self):
        status,b,h=self.request('/api/state');self.assertEqual(status,200);self.assertEqual(json.loads(b)['events'],[])
        status,b,h=self.request('/');self.assertEqual(status,200);self.assertIn('script-src',h['Content-Security-Policy']);self.assertIn(b'Team room',b)
    def test_intake_requires_authentication(self):
        self.assertEqual(self.request('/api/relay',{})[0],401)
        self.assertEqual(self.request('/api/freeze',{},'wrong')[0],401)
        self.assertEqual(self.request('/api/relay',{},'test-only-secret')[0],400)
    def test_demo_is_isolated_and_public(self):
        status,b,_=self.request('/api/benchmark');demo=json.loads(b)
        self.assertEqual(status,200);self.assertEqual(len(demo['cases']),7);self.assertTrue(all(c['passed'] for c in demo['cases']))
        self.assertEqual(json.loads(self.request('/api/state')[1])['events'],[])
    def test_traversal_and_data_not_served(self):
        for path in ['/../app.py','/data/inquiry.sqlite3','/app.py']:
            self.assertEqual(self.request(path)[0],404)

if __name__=='__main__':unittest.main()
