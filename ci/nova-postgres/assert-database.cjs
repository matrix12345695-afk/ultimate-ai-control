'use strict';
const assert=require('node:assert/strict');
const {Pool}=require(process.cwd()+'/node_modules/pg');
(async()=>{
 const pool=new Pool({connectionString:process.env.TEST_POSTGRES_URL,max:1,connectionTimeoutMillis:3000,query_timeout:3000});
 try {
  const version=await pool.query("SELECT current_setting('server_version_num')::int AS n");
  assert.equal(Math.floor(version.rows[0].n/10000),16);
  const leads=await pool.query("SELECT status,data FROM public.nova_leads WHERE id LIKE 'NWCI%'");
  assert.equal(leads.rowCount,1);assert.equal(leads.rows[0].status,'working');assert.equal(leads.rows[0].data.history.length,2);
  const events=await pool.query("SELECT count(*)::int AS n FROM public.nova_lead_events WHERE lead_id LIKE 'NWCI%'");
  assert.equal(events.rows[0].n,2);
  const restored=await pool.query("SELECT data FROM nova_restore_sandbox.nova_leads WHERE id='NWBACKUP001'");
  assert.equal(restored.rowCount,1);assert.equal(restored.rows[0].data.note,'Internal test');
  assert.equal(restored.rows[0].data.quotedAmount,1500000);
  console.log(JSON.stringify({postgres_major:16,persisted_status_history:true,restored_fields:true}));
 } finally {await pool.end();}
})().catch(()=>{console.error('NOVA isolated database assertions failed');process.exitCode=1;});
