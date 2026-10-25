"""GET-only exact-commit hosted CI identity/gate checks shared by fixed profiles."""
import artifact_pr_broker as broker


def inspect(client,contract):
    # Client is constrained to this repository and rejects every non-GET request.
    if client.read_only is not True: raise broker.Blocked('nova_ci_requires_read_only')
    head=contract['harness_commit']
    listing=client.call('GET','/actions/runs?head_sha='+head+'&per_page=20')
    if not isinstance(listing,dict) or not isinstance(listing.get('workflow_runs'),list): raise broker.Blocked('nova_ci_listing_shape')
    matches=[run for run in listing['workflow_runs'] if run.get('head_sha')==head and run.get('event')=='push'
             and run.get('name')==contract['workflow_name'] and run.get('path','').split('@')[0]==contract['workflow_path']
             and run.get('repository',{}).get('id')==1429215344 and run.get('head_repository',{}).get('id')==1429215344
             and type(run.get('id')) is int and run['id']>0 and type(run.get('run_attempt')) is int and run['run_attempt']>0]
    if not matches: raise broker.Pending('nova_ci_exact_run_missing')
    run=max(matches,key=lambda row:(row.get('updated_at',''),row['id'],row['run_attempt']))
    if run.get('status')!='completed': raise broker.Pending('nova_ci_not_completed')
    ident=run['id'];attempt=run['run_attempt']
    jobs=client.call('GET',f'/actions/runs/{ident}/attempts/{attempt}/jobs?per_page=100')
    if not isinstance(jobs,dict) or jobs.get('total_count')!=1 or not isinstance(jobs.get('jobs'),list) or len(jobs['jobs'])!=1: raise broker.Blocked('nova_ci_jobs_incomplete')
    job=jobs['jobs'][0]
    if (job.get('name')!=contract['workflow_name'] or job.get('run_id')!=ident or job.get('head_sha')!=head or
            type(job.get('id')) is not int or job['id']<=0 or job.get('status')!='completed' or
            job.get('runner_group_name')!='GitHub Actions' or 'ubuntu-24.04' not in job.get('labels',[]) or 'self-hosted' in job.get('labels',[])):
        raise broker.Blocked('nova_ci_job_identity_changed')
    steps=job.get('steps')
    if not isinstance(steps,list): raise broker.Blocked('nova_ci_steps_missing')
    gates=[step for step in steps if step.get('name')==contract.get('gate_step','Run and verify all NOVA tests')]
    passed=(run.get('conclusion')=='success' and job.get('conclusion')=='success' and len(gates)==1
            and gates[0].get('status')=='completed' and gates[0].get('conclusion')=='success')
    if run.get('conclusion')=='success' and not passed: raise broker.Blocked('nova_ci_success_without_required_gate')
    # Detect a rerun/transition between listing and reading the exact-attempt jobs.
    final=client.call('GET','/actions/runs/'+str(ident))
    if any(final.get(key)!=run.get(key) for key in ('id','run_attempt','head_sha','status','conclusion','event','path')):
        raise broker.Pending('nova_ci_changed_during_observation')
    return run,job,passed
