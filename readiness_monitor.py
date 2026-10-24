"""Bounded public readiness contract. No database login or application write requests."""
import hashlib
import json
import re
import urllib.error
import urllib.request

TARGET='nova-readiness'
URL='https://novaweb.uz/health'
PROFILE='nova-postgres-readiness-v1'
EXPECTED_VERSION='sales-funnel-v1'
CHECKS=('http_ok','json_contract','application_ready','database_ready','version_matches')
FAILURES={'network_error','read_error','redirect_denied','invalid_json','unexpected_content_type',
          'encoded_response','body_too_large','readiness_contract_failed'}


class RedirectDenied(ValueError): pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise RedirectDenied('readiness redirect denied')


def unique_object(pairs):
    result={}
    for key,value in pairs:
        if key in result: raise ValueError('duplicate JSON key')
        result[key]=value
    return result


def reject_constant(value):
    raise ValueError('non-standard JSON number')


def probe(payload,opener=None):
    if payload!={'target':TARGET}: raise ValueError('readiness target is not enabled')
    result={'target':TARGET,'url':URL,'healthy':False,'detail':'network_error','contract':PROFILE,
            'checks':{name:False for name in CHECKS},'http_status':None,'response_bytes':0,'body_sha256':None}
    opener=opener or urllib.request.build_opener(NoRedirect()).open
    try:
        request=urllib.request.Request(URL,method='GET',headers={'User-Agent':'ULTIMATE-Readiness/4.0',
                                      'Accept':'application/json','Accept-Encoding':'identity'})
        with opener(request,timeout=12) as response:
            if response.geturl()!=URL: raise RedirectDenied('readiness destination changed')
            result['http_status']=response.status
            result['checks']['http_ok']=response.status==200
            if response.status!=200:
                result['detail']='HTTP '+str(response.status);return result
            if response.headers.get('Content-Encoding','identity').strip().lower()!='identity':
                result['detail']='encoded_response';return result
            if response.headers.get('Content-Type','').split(';',1)[0].strip().lower()!='application/json':
                result['detail']='unexpected_content_type';return result
            raw=response.read(8193);result['response_bytes']=len(raw)
            if len(raw)>8192:
                result['detail']='body_too_large';return result
            result['body_sha256']=hashlib.sha256(raw).hexdigest()
            try: data=json.loads(raw,object_pairs_hook=unique_object,parse_constant=reject_constant)
            except (ValueError,UnicodeError,RecursionError):
                result['detail']='invalid_json';return result
            if isinstance(data,dict):
                result['checks'].update(
                    json_contract=type(data.get('ok')) is bool and isinstance(data.get('storage'),str) and isinstance(data.get('version'),str),
                    application_ready=data.get('ok') is True,
                    database_ready=data.get('storage')=='postgres',
                    version_matches=data.get('version')==EXPECTED_VERSION)
            result['healthy']=all(result['checks'].values())
            result['detail']='HTTP 200' if result['healthy'] else 'readiness_contract_failed'
    except urllib.error.HTTPError as exc:
        result['http_status']=exc.code;result['detail']='HTTP '+str(exc.code)
    except RedirectDenied:
        result['detail']='redirect_denied'
    except OSError:
        result['detail']='network_error'
    except (ValueError,UnicodeError):
        result['detail']='read_error'
    return result


def valid_result(result,*,stored=False):
    required={'target','url','healthy','detail','contract','checks','http_status','response_bytes','body_sha256'}
    if not isinstance(result,dict): return False
    extra={'observed_at','resolved_incidents','superseded'} if stored else set()
    if not required<=set(result) or not set(result)<=required|extra: return False
    checks=result['checks'];status=result['http_status'];size=result['response_bytes'];digest=result['body_sha256']
    if (result['target']!=TARGET or result['url']!=URL or result['contract']!=PROFILE or
        type(result['healthy']) is not bool or not isinstance(checks,dict) or set(checks)!=set(CHECKS) or
        any(type(value) is not bool for value in checks.values()) or
        (status is not None and (type(status) is not int or not 100<=status<=599)) or
        type(size) is not int or not 0<=size<=8193 or
        (digest is not None and (not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest)))):
        return False
    if checks['http_ok']!=(status==200) or result['healthy']!=all(checks.values()): return False
    if result['healthy']:
        return result['detail']=='HTTP 200' and 0<size<=8192 and digest is not None
    return (isinstance(result['detail'],str) and
            (result['detail'] in FAILURES or (status!=200 and result['detail']=='HTTP '+str(status))))
