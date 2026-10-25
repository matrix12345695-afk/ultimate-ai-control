'use strict';
const assert=require('node:assert/strict');
const {Pool}=require(process.cwd()+'/node_modules/pg');
const URL='postgresql://postgres:postgres@127.0.0.1:15432/novaweb_test';
assert.equal(process.env.DATABASE_URL,URL);
(async()=>{
 const pool=new Pool({connectionString:URL,max:1,connectionTimeoutMillis:2000,query_timeout:2000});
 try{
  const action=process.argv[2];
  if(['baseline','candidate'].includes(action)){
   const index=action==='baseline'?1:2,id='NWREHEARSAL00'+index,at='2099-01-01T00:00:00.000Z';
   const data={id,name:'Rehearsal Fixture',contact:'TEST_ONLY_NO_DELIVERY',type:'START',notes:'Isolated fixture only',status:'new',createdAt:at,updatedAt:at,history:[{at,status:'new'}],source:'ci',campaign:'rollback'};
   const c=await pool.connect();
   try{
    await c.query('BEGIN');
    await c.query('INSERT INTO nova_leads(id,data,status,created_at,updated_at) VALUES($1,$2::jsonb,$3,$4,$4)',[id,JSON.stringify(data),'new',at]);
    await c.query('INSERT INTO nova_lead_events(lead_id,status) VALUES($1,$2)',[id,'new']);
    await c.query('INSERT INTO nova_telegram_updates(update_id) VALUES($1)',[999990+index]);
    await c.query('INSERT INTO nova_daily_reminders(day) VALUES($1)',['2099-10-0'+index]);
    await c.query('COMMIT');
   }catch(e){await c.query('ROLLBACK');throw e}finally{c.release()}
  }else assert.equal(action,'snapshot');
  const n=await pool.query("SELECT current_setting('server_version_num')::int AS n");assert.equal(Math.floor(n.rows[0].n/10000),16);
  const rows={};
  for(const [name,key] of [['nova_leads','id'],['nova_lead_events','event_id'],['nova_telegram_updates','update_id'],['nova_daily_reminders','day']]){
   rows[name]=(await pool.query('SELECT row_to_json(t) AS row FROM '+name+' t ORDER BY '+key)).rows.map(x=>x.row);
  }
  console.log(JSON.stringify({postgres_major:16,rows}));
 }finally{await pool.end()}
})().catch(()=>{console.error('Isolated fixture assertion failed');process.exitCode=1;});
