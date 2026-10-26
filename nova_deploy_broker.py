"""Dry-run-only broker; reads GitHub CI, never loads a Render credential."""
import json,re,sqlite3,sys,time,urllib.request
from pathlib import Path
import artifact_pr_broker as broker
import artifact_recovery as private
import github_app_auth_v46 as auth
import locked_build_ci as ci
import nova_deploy as plans
import nova_deploy_fixture as fixture
import task_queue as q


def run(conn,envelope,data,client_factory=broker.Client,token_issuer=auth.installation_token):
    if (not isinstance(envelope,dict) or set(envelope)!={'job_id','lease_token'} or type(envelope['job_id']) is not int or envelope['job_id']<=0 or not isinstance(envelope['lease_token'],str) or not re.fullmatch('[0-9a-f]{48}',envelope['lease_token'])): raise broker.Blocked('publication_plan_envelope_invalid')
    q._owned(conn,envelope['job_id'],envelope['lease_token'],time.time())
    row=conn.execute('SELECT project,kind,payload FROM agent_jobs WHERE id=?',(envelope['job_id'],)).fetchone()
    job=dict(id=envelope['job_id'],lease_token=envelope['lease_token'],project=row[0],kind=row[1],payload=json.loads(row[2]));plans.scope(job)
    expected={'enabled':True,'profile':plans.PROFILE,'mode':'dry_run_only','definition_sha256':plans.definition_digest()}
    if json.loads(private.private_read(Path(data)/'nova-deploy-plan-policy.json',4096))!=expected: raise broker.Blocked('publication_plan_policy_disabled')
    private.private_read(Path(data)/'review-executor-activation-approved',4096)
    opener=urllib.request.build_opener(broker.NoRedirect());deadline=time.monotonic()+21
    def scoped_open(request,timeout=15):
        remaining=deadline-time.monotonic()
        if remaining<.5: raise broker.Pending('publication_plan_auth_deadline')
        return opener.open(request,timeout=min(4,remaining))
    token=token_issuer(Path.home()/'.config/ultimate-review/github-app.pem',opener=scoped_open,read_only=True)
    client=client_factory(token,deadline);client.read_only=True
    evidence=ci.observe(client)
    report=plans.report_for(evidence,time.time(),fixture.acceptance())
    return plans.save(conn,job,report)


def main():
    data=Path.home()/'.ultimate-review-data/live'
    if len(sys.argv)!=3 or sys.argv[1]!='--once' or Path(sys.argv[2])!=data/'control.db': raise SystemExit(2)
    try:
        raw=sys.stdin.buffer.read(2001)
        if len(raw)>2000: raise broker.Blocked('publication_plan_envelope_too_large')
        with sqlite3.connect(data/'control.db',timeout=10) as conn: result=run(conn,json.loads(raw),data)
        print(json.dumps({'ok':True,'result':result}))
    except Exception as exc:
        print(json.dumps({'ok':False,'pending':isinstance(exc,broker.Pending),'code':str(exc) if isinstance(exc,(broker.Pending,broker.Blocked)) else type(exc).__name__}))


if __name__=='__main__': main()
