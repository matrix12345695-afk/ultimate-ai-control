'use strict';
// Test-only hook, before pinned NOVA code: no external socket or public listener.
const net=require('node:net');
const connect=net.Socket.prototype.connect;
net.Socket.prototype.connect=function(...args){
 const options=net._normalizeArgs(args)[0];
 if(options.path||!['127.0.0.1','::1','localhost'].includes(options.host||'localhost')||![15432,15434,18765,18766].includes(Number(options.port)))throw Error('Rehearsal external socket denied');
 return connect.apply(this,args);
};
const listen=net.Server.prototype.listen;
net.Server.prototype.listen=function(port,host,...rest){
 if(![18765,18766].includes(Number(port))||host!=='0.0.0.0')throw Error('Rehearsal listener denied');
 return listen.call(this,port,'127.0.0.1',...rest);
};
