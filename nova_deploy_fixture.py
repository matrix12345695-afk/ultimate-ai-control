"""In-memory provider simulation, with no HTTP or credential support."""
import sqlite3
import time
import approval
import nova_deploy_machine as m


class FixtureRender:
    environment='fixture'
    def __init__(self):
        self.settings=dict(m.BEFORE);self.live_id=m.BASE_DEPLOY;self.calls=[];self.deploys={};self.timeout_action=None
        self.bad_candidate=False;self.bad_rollback=False;self.build_failed=False;self.pending=0;self.read_errors=0
        self.frame_changes={};self.stale=False;self.configure_gate=None;self.configure_started=None
    def observe(self,now):
        return {'workspace':m.WORKSPACE,'service':m.SERVICE,'repository':m.REPOSITORY,'main':m.BASE,'candidate':m.CANDIDATE,
                'settings':dict(self.settings),'live_id':self.live_id,'queue_empty':True,'runtime_compatible':True,
                'retained_build_verified':True,'backup_verified':True,'observed_at':now-60 if self.stale else now,**self.frame_changes}
    def mutate(self,method,path,payload):
        action=next((a for a in ('configure','deploy','rollback') if m.request(m.fixture_scope(1),a)==(method,path,payload)),None)
        if not action: raise m.Blocked('fixture_request_denied')
        self.calls.append((action,method,path,payload))
        if action=='configure':
            if self.configure_started: self.configure_started.set()
            if self.configure_gate and not self.configure_gate.wait(3): raise TimeoutError('Fixture gate')
            self.settings=dict(m.AFTER);result={'accepted':True}
        else:
            ident='dep-fixturecandidate1' if action=='deploy' else 'dep-fixturerollback1'
            self.deploys[ident]={'id':ident,'commit':m.CANDIDATE if action=='deploy' else m.BASE,'status':'created'};result={'id':ident}
        if self.timeout_action==action: raise TimeoutError('Synthetic lost response')
        return result
    def deployment(self,ident):
        if self.read_errors: self.read_errors-=1;raise TimeoutError('Synthetic GET failure')
        row=self.deploys[ident]
        if self.pending: self.pending-=1;return dict(row,status='queued')
        if self.build_failed and row['commit']==m.CANDIDATE: return dict(row,status='build_failed')
        self.live_id=ident;row['status']='live';return dict(row)
    def http(self,baseline):
        html=m.OLD_HTML if baseline else m.NEW_HTML
        if (baseline and self.bad_rollback) or (not baseline and self.bad_candidate): html='f'*40
        return {'public_html':html,'origin_html':html,'health':{'ok':True,'storage':'postgres','version':'sales-funnel-v1'},'orders_enabled':True,'actual_read':True}


def prepared(conn,now=None):
    now=time.time() if now is None else now;m.initialize(conn);scope=m.fixture_scope(now);ident=m.create(conn,scope,now)
    aid=m.request_approval(conn,ident,now);approval.decide(conn,aid,'fixture-owner','fixture-owner',True)
    return ident,scope,FixtureRender()


def finish(conn,ident,provider,now=None):
    for _ in range(24):
        state=m.advance(conn,ident,provider,now)
        if state in ('succeeded','rolled_back','failed_no_cutover','blocked','ambiguous'): return state
    raise AssertionError('Fixture finite-step limit')


def acceptance():
    outcomes=[]
    for kind in ('success','rollback','ambiguous'):
        with sqlite3.connect(':memory:') as conn:
            ident,scope,provider=prepared(conn)
            if kind=='rollback': provider.bad_candidate=True
            if kind=='ambiguous': provider.timeout_action='deploy'
            state=finish(conn,ident,provider)
            expected={'success':'succeeded','rollback':'rolled_back','ambiguous':'ambiguous'}[kind]
            assert state==expected
            if kind=='ambiguous':
                before=len(provider.calls)
                for _ in range(3): assert m.advance(conn,ident,provider)=='ambiguous'
                assert len(provider.calls)==before
            assert all(row[2].startswith('/services/'+m.SERVICE) for row in provider.calls)
            outcomes.append({'scenario':kind,'state':state,'mutations_simulated':len(provider.calls)})
    return {'cases':len(outcomes),'pass':len(outcomes),'fail':0,'outcomes':outcomes,
            'provider':'in_memory_fixture','real_Render_calls':0,'production_mutations':0,'published':False}
