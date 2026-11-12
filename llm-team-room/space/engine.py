"""Deterministic relay election. Never treats a claimed model name as verified identity."""
import hashlib
import json
from collections import Counter, defaultdict


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def validate_manifest(m):
    if set(m) != {'title', 'participants', 'candidates', 'rules'}:
        raise ValueError('Unexpected or missing manifest fields')
    if not isinstance(m['title'], str) or not 1 <= len(m['title']) <= 200:
        raise ValueError('Title required')
    if m['rules'] != {'within_min': 2, 'across_min': 3, 'weights': [3, 2, 1]}:
        raise ValueError('This version supports only the displayed 2 / 3 quorum and 3–2–1 rules')
    ps=m['participants']; cs=m['candidates']
    if not isinstance(ps, list) or not 6 <= len(ps) <= 30:
        raise ValueError('Register 6–30 participants before freezing')
    if not isinstance(cs, list) or not 2 <= len(cs) <= 20:
        raise ValueError('Register 2–20 candidates')
    for rows, fields in [(ps, {'id','provider','model'}), (cs, {'id','name','asset','sha256','authors'})]:
        ids=[]
        for r in rows:
            if not isinstance(r, dict) or set(r) != fields:
                raise ValueError('Unexpected roster/candidate fields')
            if not isinstance(r['id'], str) or not r['id'].isalnum() or len(r['id']) > 40:
                raise ValueError('IDs must be short alphanumeric strings')
            ids.append(r['id'])
        if len(ids) != len(set(ids)): raise ValueError('Duplicate IDs')
    identities=[]
    for p in ps:
        for field in ('provider','model'):
            if not isinstance(p[field], str) or not p[field].strip() or len(p[field])>160:
                raise ValueError('Every slot needs an actual provider and model identifier')
        if p['provider'] != p['provider'].strip().lower():
            raise ValueError('Use canonical lowercase provider names')
        identities.append((p['provider'],p['model']))
    if len(identities)!=len(set(identities)): raise ValueError('Same provider/model cannot occupy two slots')
    counts=Counter(p['provider'] for p in ps)
    if sum(n>=2 for n in counts.values())<3:
        raise ValueError('At least three providers need two distinct model slots each')
    for c in cs:
        if not isinstance(c['name'], str) or not 1<=len(c['name'])<=160: raise ValueError('Candidate name required')
        if not isinstance(c['asset'], str) or not c['asset'].startswith('/static/') or '..' in c['asset'] or '?' in c['asset']:
            raise ValueError('Candidate must reference a bundled, reviewed local asset')
        if not isinstance(c['sha256'],str) or len(c['sha256'])!=64 or any(x not in '0123456789abcdef' for x in c['sha256']):
            raise ValueError('Candidate SHA-256 required')
        if not isinstance(c['authors'], list) or any(a not in {p['id'] for p in ps} for a in c['authors']):
            raise ValueError('Authors must be registered participant IDs')
    return m


def validate_ballot(m, ballot, seen):
    fields={'participant','manifest_hash','ranking','abstain','reason','raw_response'}
    if not isinstance(ballot,dict) or set(ballot)!=fields: raise ValueError('Unexpected or missing ballot fields')
    roster={p['id']:p for p in m['participants']}
    pid=ballot['participant']
    if not isinstance(pid,str) or pid not in roster: raise ValueError('Unregistered participant')
    if pid in seen: raise ValueError('Duplicate participant; first ballot is final')
    if ballot['manifest_hash']!=digest(m): raise ValueError('Manifest mismatch: stale candidates/rules')
    if type(ballot['abstain']) is not bool: raise ValueError('abstain must be boolean')
    ranking=ballot['ranking']; cs={c['id']:c for c in m['candidates']}
    if not isinstance(ranking,list) or any(not isinstance(c,str) for c in ranking): raise ValueError('Invalid ranking')
    if len(set(ranking))!=len(ranking): raise ValueError('Repeated candidate')
    if ballot['abstain']:
        if ranking: raise ValueError('Abstention must have an empty ranking')
    elif not 1<=len(ranking)<=min(3,len(cs)):
        raise ValueError('Rank one to three candidates')
    for c in ranking:
        if c not in cs: raise ValueError('Unknown candidate')
        if pid in cs[c]['authors']: raise ValueError('Self-vote')
    for f, maximum in [('reason',4000),('raw_response',24000)]:
        if not isinstance(ballot[f],str) or not 1<=len(ballot[f].strip())<=maximum:
            raise ValueError(f'{f} required; limit {maximum} characters')
    return roster[pid]


def tally(m, ballots):
    seen=set(); groups=defaultdict(list); rejected=[]; abstentions=[]
    for b in ballots:
        try: p=validate_ballot(m,b,seen)
        except (ValueError,TypeError) as e:
            rejected.append(str(e)); continue
        seen.add(b['participant'])
        if b['abstain']: abstentions.append(b['participant'])
        else: groups[p['provider']].append(b)
    families={}; provider_votes=Counter()
    for provider,bs in sorted(groups.items()):
        scores=Counter()
        for b in bs:
            for weight,c in zip(m['rules']['weights'],b['ranking']): scores[c]+=weight
        leaders=sorted(c for c,n in scores.items() if n==max(scores.values()))
        qualified=len(bs)>=m['rules']['within_min']
        winner=leaders[0] if qualified and len(leaders)==1 else None
        families[provider]={'valid_votes':len(bs),'quorum':qualified,'scores':dict(scores),'leaders':leaders,'winner':winner}
        if winner: provider_votes[winner]+=1
    # A tied provider does not silently disappear to reduce the winning threshold.
    qualified=sum(f['quorum'] for f in families.values())
    quorum=qualified>=m['rules']['across_min']
    leaders=sorted(c for c,n in provider_votes.items() if n==max(provider_votes.values())) if provider_votes else []
    winner=leaders[0] if quorum and len(leaders)==1 and provider_votes[leaders[0]]>qualified/2 else None
    return {'evidence':'operator-relayed; model identity not independently verified','manifest_hash':digest(m),
            'accepted':len(seen),'abstentions':abstentions,'rejected':rejected,'families':families,
            'provider_votes':dict(provider_votes),'qualified_families':qualified,'relay_quorum':quorum,
            'winner':winner,'status':'provisional relay result' if winner else ('runoff required' if quorum else 'waiting for quorum')}


def benchmark():
    """Synthetic attack fixtures, never submitted to the real ledger."""
    m={'title':'SIMULATION ONLY','participants':[{'id':f'p{i}','provider':f'family{i//2}','model':f'synthetic{i}'} for i in range(6)],
       'candidates':[{'id':c,'name':c,'asset':'/static/demo.svg','sha256':'0'*64,'authors':[]} for c in ['A','B','C']],
       'rules':{'within_min':2,'across_min':3,'weights':[3,2,1]}}
    def ballot(i,ranking):
        return {'participant':f'p{i}','manifest_hash':digest(m),'ranking':ranking,'abstain':False,
                'reason':'Synthetic fixture','raw_response':'Synthetic fixture, not a model response'}
    clean=[ballot(i,['A','B','C']) for i in range(6)]
    def naive(bs):
        # Intentionally vulnerable: trusts every row and ignores roster, hashes and authorship.
        count=Counter(b['ranking'][0] for b in bs if b.get('ranking'))
        return {'winner':count.most_common(1)[0][0] if count else None,'claimed_votes':sum(count.values())}
    scenarios=[]
    cases=[('Duplicate voter spam',m,clean+[ballot(0,['B','A','C']) for _ in range(9)]),
           ('Invented provider identities',m,clean+[dict(ballot(0,['B','A','C']),participant=f'fake{i}',provider='claimed-independent') for i in range(9)]),
           ('Changed candidate set',m,[dict(ballot(i,['B','A','C']),manifest_hash='stale') for i in range(6)]),
           ('Ballot stuffing with unknown candidate',m,[ballot(i,['INVENTED']) for i in range(6)]),
           ('Missing families disguised as quorum',m,clean[:2]),
           ('Tie hidden by first-row ordering',m,[ballot(i,['A','B']) if i%2==0 else ballot(i,['B','A']) for i in range(6)])]
    owned=json.loads(json.dumps(m)); owned['candidates'][1]['authors']=['p0','p1','p2','p3','p4','p5']
    cases.append(('Self-voting',owned,[dict(ballot(i,['B','A']),manifest_hash=digest(owned)) for i in range(6)]))
    for name,manifest,bs in cases:
        guarded=tally(manifest,bs)
        expected='A' if name in ['Duplicate voter spam','Invented provider identities'] else None
        scenarios.append({'scenario':name,'synthetic':True,'vulnerable':naive(bs),'guarded':guarded,
                          'expected_guarded_winner':expected,'passed':guarded['winner']==expected})
    # Deliberately expose a limit: forged relays for valid slots pass structural checks.
    forged=[ballot(i,['B','A','C']) for i in range(6)]
    return {'label':'SYNTHETIC attack demonstration — not observed LLM cheating',
            'baseline':tally(m,clean),'cases':scenarios,
            'known_limit':{'description':'An operator can invent plausible responses for registered slots. Structural validation cannot prove origin.',
                           'forged_relay':tally(m,forged),'identity_verified':False}}
