import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const {eventHost,readThread,watchVisible}=await import('data:text/javascript;base64,'+Buffer.from(await readFile(new URL('./refresh.js',import.meta.url))).toString('base64'));
test('fresh installations share the organizer; explicit alternate hosts survive',()=>{
 const context={host:'participant.example',event_host:'organizer.example'};
 assert.equal(eventHost(null,context),'organizer.example');
 assert.equal(eventHost({host:'another.example'},context),'another.example');
 assert.equal(eventHost({host:'participant.example'},context),'participant.example');
});
test('refresh rereads all visible pages including edits and deletions',async()=>{
 const calls=[];const pages=[{posts:[{id:8,text:'new'},{id:7,text:'edited'}],more:true,members:['a','b']},{posts:[{id:4,text:'kept'}],more:false,members:['a','b']}];
 const result=await readThread(async(action,body)=>{calls.push(body);return pages.shift()},'detail',{card:'01'},4);
 assert.deepEqual(result.posts.map(p=>p.id),[8,7,4]);assert.equal(result.posts[1].text,'edited');assert.equal(result.more,false);assert.deepEqual(calls,[{card:'01'},{card:'01',before:7}]);assert.equal(result.members.length,2);
});
test('one page is one request and an empty thread clears stale posts',async()=>{
 let n=0;const result=await readThread(async()=>{n++;return {posts:[],more:false}},'replies',{card:'01',parent_id:1},10);assert.equal(n,1);assert.deepEqual(result.posts,[]);
});
test('visible refresh serializes reads, stops hidden/offline, resumes and cleans up',async()=>{
 const doc=new EventTarget(),win=new EventTarget();doc.hidden=false;
 const previous={document:globalThis.document,window:globalThis.window,navigator:globalThis.navigator,setTimeout:globalThis.setTimeout,clearTimeout:globalThis.clearTimeout};
 Object.defineProperty(globalThis,'navigator',{value:{onLine:true},configurable:true});globalThis.document=doc;globalThis.window=win;
 let next=0;const timers=new Map();globalThis.setTimeout=(fn)=>{timers.set(++next,fn);return next};globalThis.clearTimeout=id=>timers.delete(id);
 let reads=0,resolve,signal;const errors=[];
 const flush=async()=>{await Promise.resolve();await Promise.resolve();await Promise.resolve()};
 try{
  const stop=watchVisible(s=>{reads++;signal=s;return new Promise(r=>resolve=r)},e=>errors.push(e));
  assert.equal(reads,1);win.dispatchEvent(new Event('focus'));assert.equal(reads,1);
  resolve();await flush();assert.equal(timers.size,1);
  doc.hidden=true;doc.dispatchEvent(new Event('visibilitychange'));assert.equal(timers.size,0);
  win.dispatchEvent(new Event('focus'));assert.equal(reads,1);
  doc.hidden=false;doc.dispatchEvent(new Event('visibilitychange'));assert.equal(reads,2);
  resolve();await flush();navigator.onLine=false;win.dispatchEvent(new Event('offline'));assert.equal(timers.size,0);
  navigator.onLine=true;win.dispatchEvent(new Event('online'));assert.equal(reads,3);
  stop();assert.equal(signal.aborted,true);resolve();await flush();assert.equal(timers.size,0);
  win.dispatchEvent(new Event('focus'));assert.equal(reads,3);assert.deepEqual(errors,[]);
 }finally{globalThis.document=previous.document;globalThis.window=previous.window;Object.defineProperty(globalThis,'navigator',{value:previous.navigator,configurable:true});globalThis.setTimeout=previous.setTimeout;globalThis.clearTimeout=previous.clearTimeout}
});
