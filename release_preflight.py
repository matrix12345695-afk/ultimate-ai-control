"""Read-only release preflight evidence. Never approves, consumes or publishes."""
import json
import time
import artifact_prs as ledger
import task_queue as q

METHOD='release-preflight-v1'


def save(conn,job,request,data,observed):
    # Revalidate all local material after the remote roundtrip and again under the
    # write lock. A report is historical evidence, never a capability to publish.
    with q._write(conn):
        q._owned(conn,job['id'],job['lease_token'],time.time())
        identity,remote,_=ledger.record(conn,request)
        exact,_=ledger.material(conn,identity['artifact_id'],data)
        if identity!=exact or remote!=observed: raise PermissionError('release_material_changed')
        scope=ledger.release_scope(identity,observed)
        rows=conn.execute('SELECT id,scope,scope_sha256 FROM artifact_release_candidates WHERE request_id=? ORDER BY id DESC LIMIT 1',(request,)).fetchone()
        candidate=None;state='missing'
        if rows:
            candidate=rows[0]
            state='approved' if ledger.release_authorized(conn,candidate,scope) else 'not_authorized'
        report={'schema':METHOD,'request_id':request,'artifact_id':identity['artifact_id'],
                'repository':ledger.REPO,'project':'control','scope':scope,
                'checked_at':time.time(),'candidate_id':candidate,'approval_state':state,
                'checks':{'local_artifact_and_acceptance':'passed','exact_remote_diff':'passed','exact_head_ci':'passed'},
                'rollback_reference':{'repository':ledger.REPO,'base_sha':remote['base_sha'],
                                      'status':'reference_only_not_a_tested_deployment_rollback'},
                'blockers':([] if state=='approved' else ['exact_owner_approval_required'])+['publisher_not_connected','deployment_rollback_not_verified'],
                'publish_allowed':False,'merged':False,'published':False}
        raw=ledger.canonical(report)
        previous=conn.execute('SELECT id,report,report_sha256 FROM artifact_release_checks WHERE job_id=?',(job['id'],)).fetchone()
        if previous:
            # A committed report is immutable. A retry may complete the queue job,
            # but must not replace historical evidence with a newer observation.
            if ledger.digest(json.loads(previous[1]))!=previous[2]: raise PermissionError('release_report_integrity')
            report=json.loads(previous[1]);ident=previous[0]
        else:
            ident=conn.execute('INSERT INTO artifact_release_checks(job_id,request_id,report,report_sha256,created_at) VALUES(?,?,?,?,?)',
                               (job['id'],request,raw,ledger.digest(report),time.time())).lastrowid
            q._event(conn,job['id'],time.time(),'release_preflight_recorded',str(ident))
    return {'release_check_id':ident,'request_id':request,'artifact_id':report['artifact_id'],
            'report_sha256':ledger.digest(report),'pr_url':report['scope']['pr_url'],
            'head_sha':report['scope']['head_sha'],'base_sha':report['scope']['base_sha'],
            'ci_state':'success','approval_state':report['approval_state'],
            'publish_allowed':False,'published':False,'merged':False}


def describe(conn):
    rows=conn.execute('SELECT id,report,report_sha256 FROM artifact_release_checks ORDER BY id DESC LIMIT 3').fetchall()
    lines=['Проверки перед выпуском · только чтение']
    for ident,raw,sha in rows:
        report=json.loads(raw)
        if ledger.digest(report)!=sha:
            lines.append(f'#{ident}: отчёт изменён, использовать нельзя.');continue
        lines.extend([f"#{ident} · PR-заявка {report['request_id']} · {report['scope']['pr_url']}",
                      'Commit: '+report['scope']['head_sha'],
                      'CI: успешно при проверке. Согласование при проверке: '+report['approval_state'],
                      'Время UTC: '+time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(report['checked_at'])),
                      'Исторический отчёт; перед действием нужна новая проверка.'])
    if not rows: lines.append('Отчётов пока нет.')
    lines.append('Запуск: /release_check ID_заявки_PR. Публикация отключена, откат развёртывания ещё не проверен. Решения владельца команда не меняет.')
    return '\n'.join(lines)
