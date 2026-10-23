"""Generation only stages a capsule; a separate queue job executes its exact tests."""
import json
from pathlib import Path
import offline_developer
import model_broker
import acceptance_checks


def test_bundle(conn,job,folder,runner=None):
    if job['project']!='control' or job['kind']!='test_release': raise PermissionError('developer test project')
    payload=job['payload']
    if set(payload)!={'target','generation_job_id','source_digest'} or payload['target']!='developer-bundle':
        raise model_broker.BrokerFailed('developer_test_payload')
    parent=payload['generation_job_id']
    if type(parent) is not int or parent<=0: raise model_broker.BrokerFailed('developer_generation_id')
    row=conn.execute('SELECT state,project,kind,result FROM agent_jobs WHERE id=?',(parent,)).fetchone()
    if not row or row[:3]!=('succeeded','control','review_change'): raise model_broker.BrokerFailed('generation_not_committed')
    result=json.loads(row[3])
    if result.get('followup_job_id')!=job['id'] or result.get('source_digest')!=payload['source_digest']:
        raise model_broker.BrokerFailed('developer_followup_mismatch')
    bundle=model_broker.load_bundle(conn,parent,payload['source_digest'])
    provenance={k:bundle[k] for k in ('generation_job_id','provider_request_key','model','generation_elapsed_seconds')}
    kwargs={'runner':runner} if runner else {}
    return offline_developer.prepare_files(conn,job,Path(folder)/'artifacts',Path(folder)/'sandbox-policy.json',
        bundle['files'],engine=bundle['engine'],provenance=provenance,
        acceptance_profile=acceptance_checks.PROFILE if bundle['engine']=='offline_broker_demo' else None,**kwargs)
