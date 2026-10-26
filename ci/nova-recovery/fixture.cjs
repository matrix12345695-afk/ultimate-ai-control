'use strict';
const assert=require('node:assert/strict');
const {Pool}=require(process.cwd()+'/node_modules/pg');
const action=process.argv[2];const database=process.argv[3];
assert.ok(['nova_recovery_source','nova_recovery_target','nova_recovery_negative'].includes(database));
assert.equal(process.env.DATABASE_URL,'postgresql://postgres:postgres@127.0.0.1:15432/'+database);
const pool=new Pool({connectionString:process.env.DATABASE_URL,max:2,connectionTimeoutMillis:3000,query_timeout:10000});
async function rows(){const result={};for(const [table,key] of [['nova_leads','id'],['nova_lead_events','event_id'],['nova_telegram_updates','update_id'],['nova_daily_reminders','day']])result[table]=(await pool.query('SELECT md5(string_agg(row_to_json(t)::text,\'|\' ORDER BY '+key+')) AS digest,count(*)::int AS n FROM '+table+' t')).rows[0];return result;}
(async()=>{try{
 const version=(await pool.query("SELECT current_setting('server_version_num')::int AS n")).rows[0].n;assert.equal(Math.floor(version/10000),18);
 if(action==='init'){
  const crm=require(process.cwd()+'/crm');await crm.init();
  await pool.query(`INSERT INTO nova_leads(id,data,status,created_at,updated_at)
  SELECT 'NWRECOVERY'||lpad(g::text,6,'0'),jsonb_build_object('id','NWRECOVERY'||lpad(g::text,6,'0'),'name','Fixture only','contact','NO_DELIVERY','notes','Синтетические данные','note','ichki qayd','task','audit','due','2099-12-30','quotedAmount',1500000,'source','ci','campaign','recovery','history',jsonb_build_array(jsonb_build_object('status','new','at','2099-01-01T00:00:00.000Z')),'createdAt','2099-01-01T00:00:00.000Z','updatedAt','2099-01-01T00:00:00.000Z','status','new'),'new','2099-01-01','2099-01-01' FROM generate_series(1,5003) AS g`);
  await pool.query("INSERT INTO nova_lead_events(lead_id,status,recorded_at) SELECT id,'new','2099-01-01' FROM nova_leads ORDER BY id");
  await pool.query('INSERT INTO nova_telegram_updates(update_id) VALUES(9007199254740990),(9007199254740991)');
  await pool.query("INSERT INTO nova_daily_reminders(day) VALUES('2099-01-01'),('2099-01-02')");
  const all=await crm.all();const data=require(process.cwd()+'/backup').buildBackup(all,'postgres','2099-01-01T00:00:00Z');const legacy=JSON.parse(data);
  assert.equal(all.length,5000);assert.equal(legacy.count,5000);assert.ok(!Object.hasOwn(legacy,'nova_telegram_updates'));assert.ok(!Object.hasOwn(legacy,'nova_daily_reminders'));
  console.log(JSON.stringify({legacy_export_count:legacy.count,source_count:5003,tables:await rows()}));
 } else if(action==='later'){
  await pool.query("INSERT INTO nova_leads(id,data,status) VALUES('NWRECOVERYLATER','{\"id\":\"NWRECOVERYLATER\",\"fixture\":true}','new')");
  await pool.query("INSERT INTO nova_lead_events(lead_id,status) VALUES('NWRECOVERYLATER','new')");console.log(JSON.stringify(await rows()));
 } else if(action==='verify'){
  const before=await rows();assert.equal(before.nova_leads.n,5003);assert.equal(before.nova_lead_events.n,5003);assert.equal(before.nova_telegram_updates.n,2);assert.equal(before.nova_daily_reminders.n,2);
  const item=(await pool.query("SELECT data FROM nova_leads WHERE id='NWRECOVERY000001'")).rows[0].data;assert.equal(item.quotedAmount,1500000);assert.equal(item.note,'ichki qayd');assert.equal(item.notes,'Синтетические данные');
  const old=(await pool.query('SELECT max(event_id)::text AS max FROM nova_lead_events')).rows[0].max;
  await pool.query("INSERT INTO nova_leads(id,data,status) VALUES('NWRECOVERYNEW','{\"id\":\"NWRECOVERYNEW\",\"fixture\":true}','new')");
  const next=(await pool.query("INSERT INTO nova_lead_events(lead_id,status) VALUES('NWRECOVERYNEW','new') RETURNING event_id::text AS id")).rows[0].id;assert.ok(BigInt(next)>BigInt(old));
  const dup=await pool.query('INSERT INTO nova_telegram_updates(update_id) VALUES(9007199254740991) ON CONFLICT DO NOTHING');assert.equal(dup.rowCount,0);
  const reminder=await pool.query("INSERT INTO nova_daily_reminders(day) VALUES('2099-01-01') ON CONFLICT DO NOTHING");assert.equal(reminder.rowCount,0);
  await assert.rejects(pool.query("INSERT INTO nova_lead_events(lead_id,status) VALUES('MISSING','new')"),{code:'23503'});
  console.log(JSON.stringify({tables:before,sequence_preserved:true,dedup_preserved:true,reminder_preserved:true,foreign_key_preserved:true,operational_fields_preserved:true}));
 } else if(action==='snapshot') console.log(JSON.stringify(await rows()));
 else if(action==='hold'){
  await pool.end();const backup=new Pool({connectionString:'postgresql://nova_backup:fixture@127.0.0.1:15432/'+database,max:1});const c=await backup.connect();
  await c.query('BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY');const id=(await c.query('SELECT pg_export_snapshot() AS id')).rows[0].id;
  console.log(JSON.stringify({snapshot:id,tables_read_only:true}));
  await new Promise(resolve=>{process.stdin.once('data',resolve);process.stdin.resume()});await c.query('ROLLBACK');c.release();await backup.end();return;
 } else throw Error('unknown fixture action');
 }finally{await pool.end().catch(()=>{})}
})().then(()=>process.exit(0)).catch(e=>{console.error('Recovery fixture failed',e.code||e.name);process.exit(1)});
