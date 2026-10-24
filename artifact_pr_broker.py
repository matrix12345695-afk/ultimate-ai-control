"""Short-lived scoped GitHub App broker. No candidate execution, merge or deployment."""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import quote
import artifact_prs as ledger
import artifact_recovery as private
import github_app_auth_v46 as auth
import task_queue as q

class Pending(RuntimeError): pass
class Blocked(PermissionError): pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): raise Blocked('github_redirect_denied')


def sha(value):
    if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{40}',value): raise Blocked('invalid_github_sha')
    return value


class Client:
    def __init__(self,token,deadline):
        self.token=token;self.deadline=deadline
        self.opener=urllib.request.build_opener(NoRedirect())
        self.read_only=False

    def call(self,method,path,payload=None,missing=False):
        if self.read_only and method!='GET': raise Blocked('refresh_cannot_write_github')
        remaining=self.deadline-time.monotonic()
        if remaining<.5: raise Pending('github_batch_deadline')
        request=urllib.request.Request('https://api.github.com/repos/'+ledger.REPO+path,
            method=method,data=None if payload is None else ledger.canonical(payload).encode(),headers={
            'Authorization':'Bearer '+self.token,'Accept':'application/vnd.github+json',
            'Content-Type':'application/json','X-GitHub-Api-Version':'2022-11-28',
            'User-Agent':'ULTIMATE-Artifact-Draft/4.0'})
        try:
            with self.opener.open(request,timeout=min(4,remaining)) as response:
                if response.geturl()!=request.full_url: raise Blocked('github_destination_changed')
                raw=response.read(1024*1024+1)
            if len(raw)>1024*1024: raise Blocked('github_response_too_large')
            return json.loads(raw)
        except urllib.error.HTTPError as exc:
            if exc.code==404 and missing: return None
            if exc.code in (408,409,422,429) or exc.code>=500: raise Pending('github_reconcile_http_'+str(exc.code)) from None
            raise Blocked('github_denied_http_'+str(exc.code)) from None
        except (OSError,ValueError) as exc:
            raise Pending('github_transport_'+type(exc).__name__) from None


def ci_evidence(data,head):
    if not isinstance(data,dict) or not isinstance(data.get('workflow_runs'),list): raise Blocked('github_ci_shape')
    matching=[]
    for run in data['workflow_runs']:
        if (run.get('head_sha')!=head or run.get('name')!='Safe unit tests' or
                run.get('event')!='pull_request' or run.get('path','').split('@')[0]!='.github/workflows/tests.yml' or
                run.get('repository',{}).get('id')!=1429215344 or
                run.get('head_repository',{}).get('id')!=1429215344): continue
        if type(run.get('id')) is not int or type(run.get('run_attempt')) is not int: continue
        matching.append(run)
    if not matching: return 'pending',[]
    latest=max(matching,key=lambda run:(run.get('updated_at',''),run['id'],run['run_attempt']))
    conclusion=latest.get('conclusion')
    state=('success' if conclusion=='success' else 'failure') if latest.get('status')=='completed' else 'pending'
    return state,[{key:latest.get(key) for key in ('id','run_attempt','head_sha','conclusion')}]


def verify(client,identity,remote,files):
    number=remote['pr_number']
    if type(number) is not int or number<=0: raise Blocked('invalid_pr_number')
    pr=client.call('GET','/pulls/'+str(number))
    if (pr.get('state')!='open' or pr.get('draft') is not True or pr.get('merged') is not False or
            pr.get('html_url')!=remote['pr_url'] or pr.get('head',{}).get('ref')!=identity['branch'] or
            pr.get('head',{}).get('sha')!=remote['head_sha'] or pr.get('base',{}).get('ref')!='main' or
            pr.get('base',{}).get('sha')!=remote['base_sha'] or
            any(pr.get(side,{}).get('repo',{}).get('full_name')!=ledger.REPO for side in ('head','base'))):
        raise Blocked('draft_pr_identity_or_revision_changed')
    compare=client.call('GET','/compare/'+sha(remote['base_sha'])+'...'+sha(remote['head_sha']))
    expected={path:hashlib.sha1(b'blob '+str(len(body.encode())).encode()+b'\0'+body.encode()).hexdigest() for path,body in files.items()}
    rows=compare.get('files')
    if (compare.get('total_commits')!=1 or compare.get('ahead_by')!=1 or compare.get('behind_by')!=0 or
            not isinstance(rows,list) or len(rows)!=len(expected) or
            {row.get('filename'):row.get('sha') for row in rows}!=expected or
            any(row.get('status')!='added' for row in rows)):
        raise Blocked('draft_pr_diff_changed')
    current=client.call('GET','/git/ref/heads/main')
    head=client.call('GET','/git/ref/heads/'+quote(identity['branch'],safe='/'))
    if current['object']['sha']!=remote['base_sha'] or head['object']['sha']!=remote['head_sha']:
        raise Blocked('draft_branch_moved')
    state,runs=ci_evidence(client.call('GET','/actions/runs?head_sha='+sha(remote['head_sha'])+'&per_page=20'),remote['head_sha'])
    return dict(remote,verified=True,ci_state=state,ci_runs=runs,checked_at=time.time())


def advance(client,identity,remote,files,save,created_at):
    remote=dict(remote)
    metadata=client.call('GET','')
    if (metadata.get('id')!=1429215344 or metadata.get('full_name')!=ledger.REPO or
            metadata.get('owner',{}).get('id')!=250530390 or metadata.get('private') is not False or
            metadata.get('fork') is not False or metadata.get('default_branch')!='main'):
        raise Blocked('github_repository_identity_changed')
    current=sha(client.call('GET','/git/ref/heads/main')['object']['sha'])
    if remote.get('base_sha') and remote['base_sha']!=current: raise Blocked('draft_base_moved')
    if not remote.get('base_sha'):
        remote.update(base_sha=current,commit_date=datetime.fromtimestamp(created_at,timezone.utc).replace(microsecond=0).isoformat());save(remote)
    tree=client.call('GET','/git/trees/'+current+'?recursive=1')
    if tree.get('truncated') is not False or not isinstance(tree.get('tree'),list): raise Blocked('base_tree_incomplete')
    if set(files)&{row.get('path') for row in tree['tree']}: raise Blocked('draft_would_overwrite_existing_path')
    if not remote.get('tree_sha'):
        result=client.call('POST','/git/trees',{'base_tree':sha(tree['sha']),'tree':[
            {'path':path,'mode':'100644','type':'blob','content':body} for path,body in sorted(files.items())]})
        remote['tree_sha']=sha(result['sha']);save(remote)
    if not remote.get('head_sha'):
        author={'name':'ULTIMATE AI CONTROL','email':'ultimate-ai-control@users.noreply.github.com','date':remote['commit_date']}
        result=client.call('POST','/git/commits',{'message':'Review tested UAC artifact '+str(identity['artifact_id'])+' '+identity['source_digest'],
            'tree':sha(remote['tree_sha']),'parents':[current],'author':author,'committer':author})
        remote['head_sha']=sha(result['sha']);save(remote)
    commit=client.call('GET','/git/commits/'+sha(remote['head_sha']))
    if commit.get('tree',{}).get('sha')!=remote['tree_sha'] or [p.get('sha') for p in commit.get('parents',[])]!=[current]:
        raise Blocked('draft_commit_changed')
    branch='/git/ref/heads/'+quote(identity['branch'],safe='/')
    found=client.call('GET',branch,missing=True)
    if found is None: client.call('POST','/git/refs',{'ref':'refs/heads/'+identity['branch'],'sha':remote['head_sha']})
    elif found.get('object',{}).get('sha')!=remote['head_sha']: raise Blocked('draft_branch_conflict')
    if not remote.get('pr_number'):
        matches=client.call('GET','/pulls?state=all&base=main&head=matrix12345695-afk:'+quote(identity['branch'],safe='/')+'&per_page=10')
        if not isinstance(matches,list) or len(matches)>1: raise Blocked('draft_pr_lookup_ambiguous')
        if matches: result=matches[0]
        else:
            result=client.call('POST','/pulls',{'head':identity['branch'],'base':'main','draft':True,
                'title':'Draft: tested UAC artifact '+str(identity['artifact_id'])+' · '+identity['recipe'],
                'body':'Prepared by the VPS from immutable artifact '+str(identity['artifact_id'])+'.\n\nSource SHA-256: '+identity['source_digest']
                       +'\nIndependent acceptance: '+identity['acceptance_profile']+' / '+identity['harness_sha256']
                       +'\n\nTwo review-only recipe files. No active application source, merge or deployment. Local tests passed; GitHub CI is verified separately for the exact head.'})
        number=result.get('number')
        if type(number) is not int or number<=0 or result.get('html_url')!='https://github.com/'+ledger.REPO+'/pull/'+str(number):
            raise Blocked('draft_pr_url_invalid')
        remote.update(pr_number=number,pr_url=result['html_url']);save(remote)
    remote=verify(client,identity,remote,files);save(remote)
    if remote['ci_state']=='pending': raise Pending('draft_ci_pending')
    return remote


def run(conn,envelope,data,client_factory=Client,token_issuer=auth.installation_token):
    if not isinstance(envelope,dict) or set(envelope)!={'job_id','lease_token'}: raise Blocked('invalid_pr_envelope')
    ident=envelope['job_id'];token=envelope['lease_token']
    if type(ident) is not int or ident<=0 or not isinstance(token,str) or not re.fullmatch('[0-9a-f]{48}',token):
        raise Blocked('invalid_pr_lease')
    q._owned(conn,ident,token,time.time())
    row=conn.execute('SELECT project,kind,payload,attempts FROM agent_jobs WHERE id=?',(ident,)).fetchone()
    job={'id':ident,'lease_token':token,'project':row[0],'kind':row[1],'payload':json.loads(row[2]),'attempt':row[3]}
    request,identity,files=ledger.prepare(conn,job,data)
    cfg=json.loads(private.private_read(Path(data)/'artifact-pr-policy.json',4096))
    if cfg!={'enabled':True,'mode':'draft_only','repository':ledger.REPO,'recipes':['safe-paths','sha-check']}:
        raise Blocked('artifact_pr_policy_disabled')
    folder=Path.home()/'.config/ultimate-review'
    marker=Path(data)/'review-executor-activation-approved'
    private.private_read(marker,4096)
    deadline=time.monotonic()+21
    opener=urllib.request.build_opener(NoRedirect())
    def scoped_open(request,timeout=15):
        remaining=deadline-time.monotonic()
        if remaining<.5: raise Pending('github_auth_deadline')
        return opener.open(request,timeout=min(4,remaining))
    credential=token_issuer(folder/'github-app.pem',opener=scoped_open)
    client=client_factory(credential,deadline)
    _,remote,row=ledger.record(conn,request)
    remote=dict(remote,verified=False);ledger.save_remote(conn,job,request,remote)
    if job['payload'].get('refresh'):
        client.read_only=True
        if not remote.get('pr_number'): raise Blocked('draft_pr_not_created')
        remote=verify(client,identity,remote,files);ledger.save_remote(conn,job,request,remote)
        if remote['ci_state']=='pending': raise Pending('draft_ci_pending')
    else:
        remote=advance(client,identity,remote,files,lambda state:ledger.save_remote(conn,job,request,state),row[5])
    return {'artifact_pr_id':request,'artifact_id':identity['artifact_id'],'source_digest':identity['source_digest'],
            'pr_url':remote['pr_url'],'head_sha':remote['head_sha'],'base_sha':remote['base_sha'],
            'ci_state':remote['ci_state'],'draft':True,'merged':False,'published':False}


def main():
    if len(sys.argv)!=3 or sys.argv[1]!='--once': raise SystemExit(2)
    data=Path.home()/'.ultimate-review-data/live'
    if Path(sys.argv[2])!=data/'control.db': raise SystemExit(2)
    try:
        raw=sys.stdin.buffer.read(2001)
        if len(raw)>2000: raise Blocked('pr_request_too_large')
        with sqlite3.connect(data/'control.db',timeout=10) as conn:
            result=run(conn,json.loads(raw),data)
        print(json.dumps({'ok':True,'result':result}))
    except Exception as exc:
        print(json.dumps({'ok':False,'pending':isinstance(exc,Pending),'code':str(exc) if isinstance(exc,(Pending,Blocked)) else type(exc).__name__}))


if __name__=='__main__': main()
