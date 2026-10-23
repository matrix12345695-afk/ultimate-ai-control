"""Private operator CLI; no secret values or raw provider errors are printed."""
import argparse
import json
from pathlib import Path
import sqlite3
import sys
import metered_provider as provider


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('operation',choices=('status','quote','plan'))
    parser.add_argument('--db',type=Path,required=True)
    parser.add_argument('--policy',type=Path,required=True)
    parser.add_argument('--key-file',type=Path)
    parser.add_argument('--task-file',type=Path)
    parser.add_argument('--request-id')
    args=parser.parse_args()
    try:
        if args.db.resolve()!=args.db.absolute() or not args.db.is_file(): raise provider.ProviderBlocked('existing_database_required')
        with sqlite3.connect(args.db,timeout=15) as conn:
            if args.operation=='status': result=provider.status(conn,args.policy)
            elif args.operation=='quote':
                cfg=provider.policy(args.policy)
                result={'maximum_request_microusd':provider.quote(cfg),'model':cfg['model'],'network_calls':0}
            else:
                if not args.key_file or not args.task_file or not args.request_id: raise provider.ProviderBlocked('plan_arguments_required')
                prompt=provider.private_read(args.task_file,12000).decode()
                result=provider.generate(conn,args.policy,args.key_file,args.request_id,prompt)
                # Untrusted advisory text stays in the private database, not stdout/Actions logs.
                result={k:v for k,v in result.items() if k!='text'}
            print(json.dumps(result,ensure_ascii=False))
    except (Exception,KeyboardInterrupt) as exc:
        code=str(exc) if isinstance(exc,provider.ProviderBlocked) else type(exc).__name__
        print('provider_blocked='+code[:100],file=sys.stderr)
        return 1
    return 0


if __name__=='__main__': raise SystemExit(main())
