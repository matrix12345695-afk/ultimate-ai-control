"""Credential-free, bounded OGG/Opus -> preview text. Never executes the text."""
import io
import array
import json
from pathlib import Path
import tempfile
import unicodedata
import wave
import local_voice as runner
import voice_assets as assets
from ai_gateway_v30 import SECRET

MAX_BYTES=262144
MAX_SECONDS=10
LANGUAGES=('ru','uz')
POLICY='voice-owner-policy-v1.json'

class VoiceError(ValueError): pass

def policy(path,*,check_assets=True):
    path=assets.regular(Path(path),True)
    if not 1<=path.stat().st_size<=4096:raise VoiceError('voice_policy_unavailable')
    cfg=json.loads(path.read_text())
    if (not isinstance(cfg,dict) or set(cfg)!={'enabled','mode','runtime','contract_sha256','max_bytes','max_seconds','languages'}
        or cfg['enabled'] is not True or cfg['mode']!='owner_preview'
        or not isinstance(cfg['runtime'],str) or not Path(cfg['runtime']).is_absolute()
        or cfg['contract_sha256']!=assets.contract_sha() or cfg['max_bytes']!=MAX_BYTES or type(cfg['max_bytes']) is not int
        or cfg['max_seconds']!=MAX_SECONDS or type(cfg['max_seconds']) is not int or cfg['languages']!=list(LANGUAGES)):
        raise VoiceError('voice_policy_unavailable')
    if check_assets:
        cfg['manifest']=assets.verify(Path(cfg['runtime']))
        cfg['bwrap']=runner.isolation.load_policy(Path(path).with_name('sandbox-policy.json'))['binary']
    return cfg

def validate_audio(data):
    if not isinstance(data,bytes) or not 60<=len(data)<=MAX_BYTES: raise VoiceError('voice_audio_size')
    offset=0;serial=None;sequence=0;first=None;pages=0
    while offset<len(data):
        page=data[offset:offset+27]
        if len(page)!=27 or page[:5]!=b'OggS\0': raise VoiceError('voice_ogg_header')
        n=page[26];lace=data[offset+27:offset+27+n]
        if len(lace)!=n or not n: raise VoiceError('voice_ogg_segments')
        end=offset+27+n+sum(lace)
        if end>len(data): raise VoiceError('voice_ogg_truncated')
        current=int.from_bytes(page[14:18],'little');seq=int.from_bytes(page[18:22],'little')
        if serial is None:
            serial=current
            if not page[5]&2 or lace[0]!=19: raise VoiceError('voice_opus_header')
            first=data[offset+27+n:offset+27+n+19]
            if len(first)!=19 or first[:8]!=b'OpusHead' or first[8]!=1 or first[9]!=1 or first[18]!=0:
                raise VoiceError('voice_mono_opus_required')
        if current!=serial or seq!=sequence or (sequence and page[5]&2): raise VoiceError('voice_chained_stream')
        granule=int.from_bytes(page[6:14],'little')
        if granule!=2**64-1 and granule>MAX_SECONDS*48000+5760: raise VoiceError('voice_duration_exceeded')
        offset=end;sequence+=1;pages+=1
        if pages>1024: raise VoiceError('voice_page_limit')
    return data

def clean_text(text):
    if not isinstance(text,str) or any(unicodedata.category(ch) in ('Cc','Cf') and ch not in '\r\n\t' for ch in text):
        raise VoiceError('voice_invalid_text')
    text=' '.join(text.split())
    if not 1<=len(text)<=2000 or SECRET.search(text): raise VoiceError('voice_empty_large_or_sensitive_text')
    return text

def transcribe(data,language,path):
    # English is used only by the fixed-fixture acceptance; owner intake allows RU/UZ.
    if language not in (*LANGUAGES,'en'): raise VoiceError('voice_language')
    validate_audio(data);cfg=policy(path)
    with tempfile.TemporaryDirectory(prefix='uac-owner-voice-') as name:
        root=Path(name);source=root/'input.ogg';source.write_bytes(data);source.chmod(0o400)
        pcm,decode_seconds=runner._execute(cfg,source,['/runtime/opusdec','--quiet','--rate','16000','--no-dither','/input','-'],limit=MAX_SECONDS*32000,seconds=4)
        if len(pcm)%2 or not 1600<=len(pcm)<=MAX_SECONDS*32000: raise VoiceError('voice_decoded_duration')
        samples=array.array('h');samples.frombytes(pcm)
        if max(abs(x) for x in samples)<=32:raise VoiceError('voice_silent_audio')
        wav=root/'input.wav'
        with wave.open(str(wav),'wb') as writer:
            writer.setnchannels(1);writer.setsampwidth(2);writer.setframerate(16000);writer.writeframes(pcm)
        wav.chmod(0o400)
        raw,seconds=runner._execute(cfg,wav,['/runtime/whisper-cli','-m','/runtime/model.bin','-f','/input','-t','1','-p','1','-bo','1','-bs','1','-ng','-np','-nt','-nf','-l',language],limit=16000,seconds=18)
        try: text=clean_text(raw.decode('utf-8'))
        except UnicodeError: raise VoiceError('voice_invalid_text') from None
    return {'text':text,'receipt':{'schema':'voice-recognition-v1','status':'transcribed','audio_sha256':assets.digest(data),
            'audio_bytes':len(data),'language':language,'decoded_seconds':len(pcm)/32000,
            'decode_seconds':decode_seconds,'recognize_seconds':seconds,'transcript_sha256':assets.digest(text.encode()),
            'model_sha256':cfg['manifest']['files']['model.bin']['sha256'],'contract_sha256':assets.contract_sha(),
            'manifest_sha256':runner.util.digest(cfg['manifest']),'network':False,'paid_calls':0,'published':False}}

def valid_receipt(report):
    import re
    try:
        return (set(report)=={'schema','status','audio_sha256','audio_bytes','language','decoded_seconds','decode_seconds','recognize_seconds','transcript_sha256','model_sha256','contract_sha256','manifest_sha256','network','paid_calls','published'}
                and report['schema']=='voice-recognition-v1' and report['status']=='transcribed' and report['language'] in (*LANGUAGES,'en')
                and type(report['audio_bytes']) is int and 60<=report['audio_bytes']<=MAX_BYTES
                and all(isinstance(report[k],str) and re.fullmatch('[0-9a-f]{64}',report[k]) for k in ('audio_sha256','transcript_sha256','manifest_sha256'))
                and report['model_sha256']==assets.contract()['downloads'][2]['sha256'] and report['contract_sha256']==assets.contract_sha()
                and all(type(report[k]) in (int,float) and 0<report[k]<=limit for k,limit in [('decoded_seconds',10),('decode_seconds',4),('recognize_seconds',18)])
                and report['network'] is False and report['published'] is False and type(report['paid_calls']) is int and report['paid_calls']==0)
    except (KeyError,TypeError,ValueError): return False
