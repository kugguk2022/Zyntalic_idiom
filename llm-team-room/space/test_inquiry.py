import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from engine import benchmark, digest, tally, validate_manifest, validate_ballot

class ElectionTests(unittest.TestCase):
    def setUp(self):
        self.m=json.loads(Path('manifest.example.json').read_text())
        for i,p in enumerate(self.m['participants']): p['model']='test-'+str(i)
    def b(self,i,ranking=None,abstain=False):
        return {'participant':self.m['participants'][i]['id'],'manifest_hash':digest(self.m),'ranking':ranking if ranking is not None else ['A','E'],'abstain':abstain,'reason':'test','raw_response':'test fixture'}
    def test_no_quorum_no_winner(self):
        self.assertFalse(tally(self.m,[])['relay_quorum'])
        self.assertIsNone(tally(self.m,[self.b(0),self.b(1)])['winner'])
    def test_two_levels_and_provider_equal_weight(self):
        self.assertEqual(tally(self.m,[self.b(i) for i in range(6)])['winner'],'A')
        for i in range(6,16): self.m['participants'].append({'id':'extra'+str(i),'provider':'google','model':'extra'+str(i)})
        bs=[self.b(i,['E','A'] if i>=4 else ['A','E']) for i in range(16)]
        self.assertEqual(tally(self.m,bs)['provider_votes'],{'A':2,'E':1})
        self.assertEqual(tally(self.m,bs)['winner'],'A')
    def test_abstention_is_not_participation(self):
        r=tally(self.m,[self.b(i,[],True) for i in range(6)])
        self.assertEqual(len(r['abstentions']),6);self.assertFalse(r['relay_quorum'])
    def test_tied_provider_stays_in_majority_denominator(self):
        bs=[self.b(0),self.b(1),self.b(2,['E','A']),self.b(3,['E','A']),self.b(4),self.b(5,['E','A'])]
        r=tally(self.m,bs); self.assertTrue(r['relay_quorum']); self.assertIsNone(r['winner'])
    def test_invalid_ballots(self):
        cases=[dict(self.b(0),participant='madeup'),dict(self.b(0),manifest_hash='bad'),dict(self.b(0),ranking=['A','A']),dict(self.b(0),ranking=['UNKNOWN']),dict(self.b(0),abstain='false'),dict(self.b(0),provider='spoof')]
        for b in cases:
            with self.subTest(b=b),self.assertRaises(ValueError):validate_ballot(self.m,b,set())
        with self.assertRaises(ValueError):validate_ballot(self.m,self.b(0),{self.b(0)['participant']})
    def test_self_vote_and_frozen_authorship(self):
        self.m['candidates'][0]['authors']=[self.m['participants'][0]['id']]
        with self.assertRaises(ValueError):validate_ballot(self.m,self.b(0),set())
    def test_roster_needs_actual_models(self):
        m=copy.deepcopy(self.m);m['participants'][0]['model']=None
        with self.assertRaises(ValueError):validate_manifest(m)
        m=copy.deepcopy(self.m);m['participants'][1]['model']=m['participants'][0]['model']
        with self.assertRaises(ValueError):validate_manifest(m)
        validate_manifest(self.m)
    def test_synthetic_benchmark_and_exposed_limit(self):
        b=benchmark();self.assertTrue(all(x['passed'] for x in b['cases']))
        self.assertFalse(b['known_limit']['identity_verified'])
        self.assertEqual(b['known_limit']['forged_relay']['winner'],'B')
    def test_ledger_freeze_restart_tampering_and_separation(self):
        import app
        with tempfile.TemporaryDirectory() as td:
            old=app.DB;app.DB=Path(td)/'test.sqlite3'
            try:
                app.freeze(self.m)
                with self.assertRaises(ValueError):app.freeze(self.m)
                app.submit(self.b(0));head=app.state()['head']
                benchmark();self.assertEqual(len(app.state()['events']),1)
                self.assertEqual(app.state()['head'],head)
                with self.assertRaises(ValueError):app.submit(self.b(0))
                with app.connect() as con:con.execute("UPDATE events SET hash='changed'")
                with self.assertRaises(ValueError):app.state()
            finally:app.DB=old
    def test_contributions_do_not_create_ballots(self):
        import app
        with tempfile.TemporaryDirectory() as td:
            old=app.DB;app.DB=Path(td)/'test.sqlite3'
            try:
                item={'author':'test','provider':'test','model':'test','project':'team-lab','kind':'idea','content':'Unverified test contribution'}
                app.contribute(item)
                st=app.state();self.assertEqual(len(st['contributions']),1);self.assertEqual(st['events'],[]);self.assertIsNone(st['result'])
                with app.connect() as con:con.execute("UPDATE contributions SET hash='tampered'")
                with self.assertRaises(ValueError):app.state()
            finally:app.DB=old
    def test_contributions_are_strictly_structured(self):
        import app
        with self.assertRaises(ValueError):app.contribute({'content':'incomplete'})

    def test_asset_bytes_are_bound(self):
        import app
        m=copy.deepcopy(self.m);m['candidates'][0]['sha256']='0'*64
        with self.assertRaises(ValueError):app.check_assets(m)

if __name__=='__main__':unittest.main()
