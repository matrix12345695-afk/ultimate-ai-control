"""Durable publication protocol simulator. No network/credential/live execution path."""
import json
import secrets
import time
import approval
import artifact_prs as util
import task_queue as q

PROJECT='nova';REPOSITORY='matrix12345695-afk/nova-web-agency'
WORKSPACE='tea-d52kjcur433s73ca9810';SERVICE='srv-dbbhm5k9v7es73f9kf10'
CANDIDATE='a3c3e77e0e74d33241935d25dd3bdfdd306ccd90'
BASE='1a23239a0a9c7d79905c91505a8741d8350d7e75';BASE_DEPLOY='dep-dbchlhqvcj2c738paun0'
BEFORE={'auto_deploy':'commit','health':'','build':'npm install --omit=dev'}
AFTER={'auto_deploy':'off','health':'/health','build':'npm ci --omit=dev --ignore-scripts --no-audit --no-fund'}
OLD_HTML='00d76b471b3675ab052bbe30526fb0f2e350ac42';NEW_HTML='3453ee7fa6794d207c5f9f41967752da1bba1f47'
PENDING={'created','queued','build_in_progress','pre_deploy_in_progress','update_in_progress'}
FAILED={'build_failed','pre_deploy_failed','update_failed','canceled','deactivated'}
LIVE_PUBLICATION_ENABLED=False


class Blocked(PermissionError): pass


def initialize(conn):
    approval.init_approvals(conn)
    conn.executescript('''CREATE TABLE IF NOT EXISTS nova_deploy_simulations(
      id INTEGER PRIMARY KEY,scope TEXT NOT NULL,scope_sha256 TEXT NOT NULL,state TEXT NOT NULL,
      approval_id TEXT,operation_id TEXT,rollback_id TEXT,nonce TEXT,lease_until REAL,
      read_attempts INTEGER NOT NULL DEFAULT 0,code TEXT,updated_at REAL NOT NULL);
    CREATE TABLE IF NOT EXISTS nova_deploy_simulation_events(
      id INTEGER PRIMARY KEY,run_id INTEGER NOT NULL,state TEXT NOT NULL,code TEXT,at REAL NOT NULL);''');conn.commit()


def fixture_scope(now):
    return {'schema':'nova-publication-scope-v1','mode':'simulation','project':PROJECT,'workspace':WORKSPACE,'service':SERVICE,
            'repository':REPOSITORY,'candidate':CANDIDATE,'base':BASE,'base_deploy':BASE_DEPLOY,
            'before':dict(BEFORE),'after':dict(AFTER),'candidate_html':NEW_HTML,'base_html':OLD_HTML,
            'ci_run':40270398506,'ci_attempt':1,'ci_harness':'7d4081e9bdc86cdc620656b44cadb40067d12331',
            'archive_digest':'sha256:ab2beb587d10fef44c010ac9b4b3402d9e8cdb0a9c75b06065c7c802166d8953',
            'lock_sha256':'9db9b93b90b4fbeabb5fb780eefe6345e5f87a08d9e2b530cd93335f46efafcf',
            'observed_at':now,'approval_until':now+900,'operation_until':now+3600,
            'conditional_rollback':True,'backup_verified':True,'retained_build_verified':True,
            'provider_access_verified':True,'queue_verified_empty':True,'runtime_compatible':True}


def valid_scope(scope):
    if not isinstance(scope,dict): return False
    expected=fixture_scope(scope.get('observed_at',0))
    if set(scope)!=set(expected): return False
    if any(scope[k]!=expected[k] for k in expected if k not in ('approval_until','operation_until')): return False
    if any(scope[k] is not True for k in ('conditional_rollback','backup_verified','retained_build_verified','provider_access_verified','queue_verified_empty','runtime_compatible')): return False
    return (type(scope['observed_at']) in (int,float) and scope['observed_at']>0 and
            type(scope['approval_until']) in (int,float) and type(scope['operation_until']) in (int,float) and
            scope['observed_at']<scope['approval_until']<=scope['observed_at']+900 and
            scope['approval_until']<scope['operation_until']<=scope['observed_at']+3600)


def request(scope,action):
    if not valid_scope(scope): raise Blocked('scope_changed')
    prefix='/services/'+SERVICE
    if action=='configure': return 'PATCH',prefix,{'autoDeployTrigger':'off','serviceDetails':{'healthCheckPath':'/health','envSpecificDetails':{'buildCommand':AFTER['build']}}}
    if action=='deploy': return 'POST',prefix+'/deploys',{'commitId':CANDIDATE}
    if action=='rollback': return 'POST',prefix+'/rollback',{'deployId':BASE_DEPLOY}
    raise Blocked('operation_outside_scope')


def create(conn,scope,now):
    if not valid_scope(scope) or not scope['observed_at']<=now<scope['approval_until']: raise Blocked('scope_not_ready')
    with q._write(conn):
        ident=conn.execute("INSERT INTO nova_deploy_simulations(scope,scope_sha256,state,updated_at) VALUES(?,?,'prepared',?)",(util.canonical(scope),util.digest(scope),now)).lastrowid
        note(conn,ident,'prepared',None,now)
    return ident


def load(conn,ident):
    row=conn.execute('SELECT scope,scope_sha256,state,approval_id,operation_id,rollback_id,nonce,lease_until,read_attempts FROM nova_deploy_simulations WHERE id=?',(ident,)).fetchone()
    if not row: raise Blocked('run_missing')
    scope=json.loads(row[0])
    if not valid_scope(scope) or util.digest(scope)!=row[1]: raise Blocked('stored_scope_changed')
    return scope,dict(zip(('state','approval_id','operation_id','rollback_id','nonce','lease_until','read_attempts'),row[2:]))


def request_approval(conn,ident,now):
    with q._write(conn):
        scope,row=load(conn,ident)
        if row['state']!='prepared' or row['approval_id'] or now>=scope['approval_until']: raise Blocked('approval_not_requestable')
        aid=approval.request_approval(conn,ident,'nova.publish.exact','Render:'+SERVICE,scope,ttl_minutes=15,commit=False)
        conn.execute('UPDATE nova_deploy_simulations SET approval_id=? WHERE id=?',(aid,ident))
    return aid


def note(conn,ident,state,code,now):
    conn.execute('INSERT INTO nova_deploy_simulation_events(run_id,state,code,at) VALUES(?,?,?,?)',(ident,state,code,now))


def move(conn,ident,expected,state,now,code=None,**fields):
    if set(fields)-{'operation_id','rollback_id','nonce','lease_until','read_attempts'}: raise Blocked('invalid_transition_field')
    with q._write(conn):
        scope,row=load(conn,ident)
        if row['state']!=expected: raise Blocked('concurrent_transition')
        sets={'state':state,'updated_at':now,'code':code,**fields}
        conn.execute('UPDATE nova_deploy_simulations SET '+','.join(k+'=?' for k in sets)+' WHERE id=?',(*sets.values(),ident))
        note(conn,ident,state,code,now)
    return state


def authorized(conn,ident,scope,row,now,safety=False):
    if now>=scope['operation_until'] or (not safety and now>=scope['approval_until']): raise Blocked('scope_expired')
    record=conn.execute('SELECT task_id,action,environment,artifact_sha256,status,expires_at FROM approvals WHERE id=?',(row['approval_id'],)).fetchone()
    if not record or record[:5]!=(ident,'nova.publish.exact','Render:'+SERVICE,approval.canonical_digest(scope),'approved'): raise Blocked('exact_owner_approval_missing')
    if not safety and not approval.is_authorized(conn,row['approval_id'],ident,'nova.publish.exact','Render:'+SERVICE,scope): raise Blocked('owner_approval_expired')


def observation_matches(frame,scope,settings,live_id):
    return (isinstance(frame,dict) and frame.get('workspace')==WORKSPACE and frame.get('service')==SERVICE and
            frame.get('repository')==REPOSITORY and frame.get('main')==BASE and frame.get('candidate')==CANDIDATE and
            frame.get('settings')==settings and frame.get('live_id')==live_id and frame.get('queue_empty') is True and
            frame.get('runtime_compatible') is True and frame.get('retained_build_verified') is True and frame.get('backup_verified') is True)


def check_frame(frame,scope,settings,live_id,now):
    if not observation_matches(frame,scope,settings,live_id): raise Blocked('platform_or_evidence_changed')
    at=frame.get('observed_at')
    if type(at) not in (int,float) or not now-30<=at<=now: raise Blocked('platform_observation_stale')


def verify_http(proof,scope,baseline=False):
    return (isinstance(proof,dict) and set(proof)=={'public_html','origin_html','health','orders_enabled','actual_read'} and
            proof['actual_read'] is True and proof['public_html']==proof['origin_html']==scope['base_html' if baseline else 'candidate_html'] and
            proof['health']=={'ok':True,'storage':'postgres','version':'sales-funnel-v1'} and proof['health']['ok'] is True and proof['orders_enabled'] is True)


def advance(conn,ident,transport,now=None):
    # A real provider is intentionally not accepted: current release is a simulator.
    from nova_deploy_fixture import FixtureRender
    if type(transport) is not FixtureRender or transport.environment!='fixture': raise Blocked('live_transport_disabled')
    now=time.time() if now is None else now
    scope,row=load(conn,ident);state=row['state']
    if state in ('succeeded','rolled_back','failed_no_cutover','blocked','ambiguous'): return state
    if state.endswith('_intent'):
        if row['lease_until'] and row['lease_until']>now: return 'busy'
        return move(conn,ident,state,'ambiguous',now,'crash_after_durable_intent',nonce=None,lease_until=None)
    if state in ('prepared','ready_to_deploy','rollback_ready'):
        safety=state=='rollback_ready';authorized(conn,ident,scope,row,now,safety=safety)
        action='configure' if state=='prepared' else 'deploy' if state=='ready_to_deploy' else 'rollback'
        expected_settings=scope['before'] if state=='prepared' else scope['after']
        current=row['operation_id'] if safety else scope['base_deploy']
        frame=transport.observe(now);check_frame(frame,scope,expected_settings,current,now)
        if safety and (not scope['conditional_rollback'] or not row['operation_id']): raise Blocked('rollback_outside_scope')
        nonce=secrets.token_hex(16);intent=action+'_intent'
        # Approval and local scope are re-read under the write lock before reserving a mutation.
        with q._write(conn):
            current_scope,current_row=load(conn,ident)
            if current_scope!=scope or current_row['state']!=state: return 'busy'
            authorized(conn,ident,scope,current_row,now,safety=safety)
            conn.execute('UPDATE nova_deploy_simulations SET state=?,nonce=?,lease_until=?,updated_at=? WHERE id=?',(intent,nonce,now+30,now,ident))
            note(conn,ident,intent,action,now)
        try:
            method,path,payload=request(scope,action)
            response=transport.mutate(method,path,payload)
        except Exception:
            # Includes timeout, HTTP failure and uncertain response. Never blindly retry a write.
            return move(conn,ident,intent,'ambiguous',now,'mutation_response_uncertain',nonce=None,lease_until=None)
        with q._write(conn):
            current_scope,current_row=load(conn,ident)
            if current_scope!=scope or current_row['state']!=intent or current_row['nonce']!=nonce: raise Blocked('mutation_ack_conflict')
            if action=='configure':
                if not isinstance(response,dict) or set(response)!={'accepted'} or response['accepted'] is not True: target='ambiguous';code='configuration_ack_invalid';fields={}
                else: target='configure_verify';code=None;fields={}
            else:
                dep=response.get('id') if isinstance(response,dict) else None
                if not isinstance(dep,str) or not __import__('re').fullmatch('dep-[a-z0-9]+',dep): target='ambiguous';code='deployment_ack_invalid';fields={}
                else: target='deploying' if action=='deploy' else 'rolling_back';code=None;fields={'operation_id' if action=='deploy' else 'rollback_id':dep}
            conn.execute('UPDATE nova_deploy_simulations SET state=?,code=?,nonce=NULL,lease_until=NULL,updated_at=?'+''.join(','+k+'=?' for k in fields)+' WHERE id=?',(target,code,now,*fields.values(),ident))
            note(conn,ident,target,code,now)
        return target
    if now>=scope['operation_until']: return move(conn,ident,state,'blocked',now,'operation_deadline')
    if state=='configure_verify':
        try: check_frame(transport.observe(now),scope,scope['after'],scope['base_deploy'],now)
        except Blocked: return move(conn,ident,state,'blocked',now,'configuration_not_verified')
        except Exception:
            count=row['read_attempts']+1
            return move(conn,ident,state,'blocked' if count>=5 else state,now,'configuration_read_pending',read_attempts=count)
        return move(conn,ident,state,'ready_to_deploy',now)
    if state in ('deploying','rolling_back'):
        dep_id=row['operation_id'] if state=='deploying' else row['rollback_id']
        try: remote=transport.deployment(dep_id)
        except Exception:
            count=row['read_attempts']+1
            return move(conn,ident,state,'blocked' if count>=5 else state,now,'read_retry_limit' if count>=5 else 'read_pending',read_attempts=count)
        if not isinstance(remote,dict): return move(conn,ident,state,'blocked',now,'deployment_response_malformed')
        expected_sha=scope['candidate'] if state=='deploying' else scope['base']
        if remote.get('id')!=dep_id or remote.get('commit')!=expected_sha: return move(conn,ident,state,'blocked',now,'deployment_identity_changed')
        status=remote.get('status')
        if status in PENDING: return state
        if status=='live': return move(conn,ident,state,'verify_candidate' if state=='deploying' else 'verify_rollback',now,read_attempts=0)
        if status in FAILED and state=='deploying':
            frame=transport.observe(now)
            if observation_matches(frame,scope,scope['after'],scope['base_deploy']) and verify_http(transport.http(True),scope,True): return move(conn,ident,state,'failed_no_cutover',now,'candidate_failed_old_version_healthy')
        return move(conn,ident,state,'blocked',now,'deployment_failed_or_unknown_status')
    if state in ('verify_candidate','verify_rollback'):
        baseline=state=='verify_rollback';expected=row['rollback_id'] if baseline else row['operation_id']
        try: check_frame(transport.observe(now),scope,scope['after'],expected,now)
        except Blocked: return move(conn,ident,state,'blocked',now,'foreign_live_deployment_or_config')
        try: okay=verify_http(transport.http(baseline),scope,baseline)
        except Exception: okay=False
        if okay: return move(conn,ident,state,'rolled_back' if baseline else 'succeeded',now)
        count=row['read_attempts']+1
        if count<3: return move(conn,ident,state,state,now,'http_verification_pending',read_attempts=count)
        if not baseline and scope['conditional_rollback']: return move(conn,ident,state,'rollback_ready',now,'candidate_verification_failed',read_attempts=count)
        return move(conn,ident,state,'blocked',now,'rollback_verification_failed',read_attempts=count)
    raise Blocked('unknown_machine_state')
