"""Single-process HF Docker app: public read-only inquiry, authenticated relay intake."""
import hashlib
import hmac
import json
import os
import sqlite3
import threading
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from engine import canonical, digest, validate_manifest, validate_ballot, tally, benchmark

ROOT=Path(__file__).resolve().parent
DATA=Path(os.environ.get('INQUIRY_DATA', '/data' if Path('/data').is_dir() else ROOT/'data'))
DATA.mkdir(parents=True,exist_ok=True)
DB=DATA/'inquiry.sqlite3'
LOCK=threading.Lock()

def connect():
    con=sqlite3.connect(DB)
    con.execute('CREATE TABLE IF NOT EXISTS manifest (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL)')
    con.execute('CREATE TABLE IF NOT EXISTS contributions (seq INTEGER PRIMARY KEY, payload TEXT NOT NULL, previous TEXT NOT NULL, hash TEXT NOT NULL)')
    con.execute('CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, participant TEXT UNIQUE NOT NULL, payload TEXT NOT NULL, previous TEXT NOT NULL, hash TEXT NOT NULL)')
    return con


def state():
    with connect() as con:
        row=con.execute('SELECT payload FROM manifest WHERE id=1').fetchone()
        rows=con.execute('SELECT seq,payload,previous,hash FROM events ORDER BY seq').fetchall()
    manifest=json.loads(row[0]) if row else None
    if manifest:
        check_assets(manifest)
    events=[{'seq':seq,'ballot':json.loads(b),'previous':prev,'hash':h} for seq,b,prev,h in rows]
    previous='0'*64
    for e in events:
        if e['previous']!=previous or e['hash']!=digest({'previous':previous,'ballot':e['ballot']}):
            raise ValueError('Ledger integrity check failed')
        previous=e['hash']
    return {'phase':'voting' if manifest else 'contributions / rules open','manifest':manifest,
            'draft':json.loads((ROOT/'manifest.example.json').read_text()),'events':events,
            'result':tally(manifest,[e['ballot'] for e in events]) if manifest else None,
            'contributions':read_contributions(),'head':previous,'storage':'Persistent only when INQUIRY_DATA points to a durable volume; export before restarting otherwise',
            'identity':'Relay only. Operator authentication does not verify the responding model.'}


def check_assets(m):
    for c in m['candidates']:
        path=(ROOT/c['asset'].lstrip('/')).resolve()
        if not path.is_relative_to(ROOT/'static') or not path.is_file(): raise ValueError('Missing bundled candidate asset')
        if hashlib.sha256(path.read_bytes()).hexdigest()!=c['sha256']: raise ValueError('Candidate bytes changed')


def freeze(m):
    validate_manifest(m)
    check_assets(m)
    with LOCK, connect() as con:
        if con.execute('SELECT 1 FROM manifest').fetchone(): raise ValueError('Already frozen; create a separate inquiry for new rules/candidates')
        con.execute('INSERT INTO manifest VALUES (1,?)',(canonical(m).decode(),))
    return state()


def submit(b):
    with LOCK, connect() as con:
        row=con.execute('SELECT payload FROM manifest').fetchone()
        if not row: raise ValueError('Freeze an actual roster and candidates before voting')
        m=json.loads(row[0]); check_assets(m); seen={x[0] for x in con.execute('SELECT participant FROM events')}
        validate_ballot(m,b,seen)
        last=con.execute('SELECT hash FROM events ORDER BY seq DESC LIMIT 1').fetchone()
        prev=last[0] if last else '0'*64
        con.execute('INSERT INTO events(participant,payload,previous,hash) VALUES(?,?,?,?)',
                    (b['participant'],canonical(b).decode(),prev,digest({'previous':prev,'ballot':b})))
    return state()


def read_contributions():
    with connect() as con:
        rows=con.execute('SELECT seq,payload,previous,hash FROM contributions ORDER BY seq').fetchall()
    result=[]; previous='0'*64
    for seq,payload,prev,h in rows:
        item=json.loads(payload)
        if prev!=previous or h!=digest({'previous':prev,'contribution':item}): raise ValueError('Contribution ledger integrity failure')
        result.append({'seq':seq,'contribution':item,'previous':prev,'hash':h,'identity':'operator-relayed; unverified'})
        previous=h
    return result


def contribute(item):
    fields={'author','provider','model','project','kind','content'}
    if not isinstance(item,dict) or set(item)!=fields: raise ValueError('Expected author, provider, model, project, kind, content')
    for field in fields:
        if not isinstance(item[field],str) or not 1<=len(item[field].strip())<=(16000 if field=='content' else 160):
            raise ValueError('Invalid contribution field: '+field)
    if item['kind'] not in ['idea','frame','review','experiment','rules-amendment']: raise ValueError('Unknown contribution kind')
    if item['project'] not in ['zyntalic','team-lab']: raise ValueError('Unknown project')
    with LOCK, connect() as con:
        last=con.execute('SELECT hash FROM contributions ORDER BY seq DESC LIMIT 1').fetchone()
        prev=last[0] if last else '0'*64
        con.execute('INSERT INTO contributions(payload,previous,hash) VALUES(?,?,?)',
                    (canonical(item).decode(),prev,digest({'previous':prev,'contribution':item})))
    return state()


class Handler(BaseHTTPRequestHandler):
    def respond(self,status,data,content_type='application/json'):
        body=canonical(data) if content_type=='application/json' else data
        self.send_response(status)
        self.send_header('Content-Type',content_type); self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'")
        self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        path=urlsplit(self.path).path
        try:
            if path=='/api/state': return self.respond(200,state())
            if path=='/api/benchmark': return self.respond(200,benchmark())
            if path=='/health': return self.respond(200,{'ok':True,'mode':'relay-only'})
            if path=='/': path='/static/index.html'
            file=(ROOT/path.lstrip('/')).resolve()
            if not file.is_relative_to(ROOT/'static') or not file.is_file(): return self.respond(404,{'error':'Not found'})
            types={'.html':'text/html; charset=utf-8','.css':'text/css','.js':'text/javascript','.svg':'image/svg+xml','.png':'image/png'}
            return self.respond(200,file.read_bytes(),types.get(file.suffix,'application/octet-stream'))
        except (ValueError,sqlite3.Error): return self.respond(500,{'error':'State integrity or storage failure'})
    def do_POST(self):
        if urlsplit(self.path).path not in ['/api/freeze','/api/relay','/api/contribute']: return self.respond(404,{'error':'Not found'})
        token=os.environ.get('INQUIRY_ADMIN_TOKEN','')
        if not token: return self.respond(503,{'error':'Relay intake disabled: no admin token configured'})
        auth=self.headers.get('Authorization','')
        if not hmac.compare_digest(auth,'Bearer '+token): return self.respond(401,{'error':'Unauthorized'})
        try:
            n=int(self.headers.get('Content-Length','0'))
            if not 0<n<=65536: return self.respond(413,{'error':'Body must be 1–65536 bytes'})
            body=json.loads(self.rfile.read(n))
            return self.respond(200,freeze(body) if urlsplit(self.path).path=='/api/freeze' else contribute(body) if urlsplit(self.path).path=='/api/contribute' else submit(body))
        except (ValueError,TypeError,KeyError,sqlite3.IntegrityError) as e: return self.respond(400,{'error':str(e)})
    def log_message(self,*args): pass

if __name__=='__main__':
    ThreadingHTTPServer(('0.0.0.0',int(os.environ.get('PORT','7860'))),Handler).serve_forever()
