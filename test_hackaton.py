"""Isolated acceptance and federation authorization tests. No real event writes."""
import os,tempfile,unittest,asyncio,json,base64,io,secrets
from pathlib import Path
ROOT=tempfile.TemporaryDirectory();os.environ.update(APP_STORAGE_DIR=ROOT.name,INSTANCE_ORIGIN='https://organizer.example',API_BASE_URL='http://unused',APP_TOKEN='test-only')
import service
from domain import Problem,connect,run
from PIL import Image
class HackatonTests(unittest.TestCase):
 def setUp(self):
  service.DB_PATH=Path(ROOT.name)/(secrets.token_hex(8)+'.sqlite3')
 def execute(self,actor,action,b=None,rid=None):return service.execute(action,b or {},actor,False,rid or secrets.token_hex(16))
 def joined(self,actor):
  self.execute(actor,'join');self.execute(actor,'accept');self.execute(actor,'join_card',{'card':'agent-marketplace'})
 def test_onboarding_persistence_and_gates(self):
  self.assertFalse(self.execute('@a','state')['joined'])
  with self.assertRaises(Problem):self.execute('@a','detail',{'card':'agent-marketplace'})
  self.execute('@a','join');self.assertEqual(self.execute('@a','state')['cards'],[])
  with self.assertRaises(Problem):self.execute('@a','join_card',{'card':'agent-marketplace'})
  self.execute('@a','accept');self.assertEqual(len(self.execute('@a','state')['cards']),6)
  self.execute('@a','join_card',{'card':'agent-marketplace'});self.assertTrue(self.execute('@a','state')['cards'][0]['joined'])
 def test_real_programme_has_no_sample_aliases(self):
  self.execute('@a','join');self.execute('@a','accept')
  cards=self.execute('@a','state')['cards']
  self.assertEqual([c['kind'] for c in cards],['flagship']*3+['open']*3)
  self.assertEqual([c['prize'] for c in cards],[1400]*3+[700]*3)
  self.assertEqual(len({c['id'] for c in cards}),6)
  for old in ['01','02','03']:
   with self.assertRaises(Problem) as caught:self.execute('@a','join_card',{'card':old})
   self.assertEqual(caught.exception.status,404)
  for c in cards:
   self.assertTrue(c['deliverables']);self.assertFalse(c['joined']);self.assertEqual(c['count'],0)
  self.assertTrue(self.execute('@a','state')['joined'])
 def test_shared_participants_images_links_and_isolation(self):
  self.joined('@alice');self.joined('@bob')
  im=Image.new('RGB',(2,2));out=io.BytesIO();im.save(out,format='PNG');image='data:image/png;base64,'+base64.b64encode(out.getvalue()).decode()
  p=self.execute('@alice','comment',{'card':'agent-marketplace','text':'My result https://example.org/?a=1&b=2','image':image})
  d=self.execute('@bob','detail',{'card':'agent-marketplace'});self.assertEqual(d['members'],['@alice','@bob']);self.assertEqual(d['posts'][0]['actor'],'@alice');self.assertTrue(d['posts'][0]['has_image'])
  self.assertEqual(self.execute('@bob','image',{'card':'agent-marketplace','id':p['id']})['image'],image)
  with self.assertRaises(Problem):self.execute('@bob','image',{'card':'game-studio','id':p['id']})
  with self.assertRaises(Problem):self.execute('@outsider','detail',{'card':'agent-marketplace'})
 def test_idempotency_and_bad_image(self):
  self.joined('@a');rid=secrets.token_hex(16);body={'card':'agent-marketplace','text':'one'}
  self.assertEqual(self.execute('@a','comment',body,rid),self.execute('@a','comment',body,rid));self.assertEqual(len(self.execute('@a','detail',{'card':'agent-marketplace'})['posts']),1)
  with self.assertRaises(Problem):self.execute('@a','comment',{'card':'agent-marketplace','text':'different'},rid)
  with self.assertRaises(Problem):self.execute('@a','comment',{'card':'agent-marketplace','image':'data:image/svg+xml;base64,AAAA'})
 def test_same_member_can_keep_posting(self):
  self.joined('@builder')
  ids=[self.execute('@builder','comment',{'card':'agent-marketplace','text':text})['id'] for text in ['First bug','Another bug','Follow-up findings']]
  self.assertEqual(len(set(ids)),3)
  posts=self.execute('@builder','detail',{'card':'agent-marketplace'})['posts']
  self.assertEqual([p['text'] for p in posts],['Follow-up findings','Another bug','First bug'])
  self.assertTrue(all(p['actor']=='@builder' for p in posts))
 def test_author_only_edit_delete(self):
  self.joined('@a');self.joined('@b')
  id=self.execute('@a','comment',{'card':'agent-marketplace','text':'First bug'})['id']
  self.assertTrue(self.execute('@a','detail',{'card':'agent-marketplace'})['posts'][0]['mine'])
  self.assertFalse(self.execute('@b','detail',{'card':'agent-marketplace'})['posts'][0]['mine'])
  for action in ['edit_comment','delete_comment']:
   with self.assertRaises(Problem) as caught:self.execute('@b',action,{'card':'agent-marketplace','id':id,'text':'forged','original_text':'First bug'})
   self.assertEqual(caught.exception.status,403)
  self.execute('@a','edit_comment',{'card':'agent-marketplace','id':id,'text':'Corrected bug','original_text':'First bug'})
  self.assertEqual(self.execute('@a','detail',{'card':'agent-marketplace'})['posts'][0]['text'],'Corrected bug')
  with self.assertRaises(Problem):self.execute('@a','edit_comment',{'card':'agent-marketplace','id':id,'text':'stale','original_text':'First bug'})
  rid=secrets.token_hex(16)
  self.execute('@a','delete_comment',{'card':'agent-marketplace','id':id},rid)
  self.assertTrue(self.execute('@a','delete_comment',{'card':'agent-marketplace','id':id},rid)['ok'])
  self.assertEqual(self.execute('@a','detail',{'card':'agent-marketplace'})['posts'],[])
 def test_replies_are_scoped_and_survive_parent_deletion(self):
  self.joined('@a');self.joined('@b')
  parent=self.execute('@a','comment',{'card':'agent-marketplace','text':'A bug'})['id']
  reply=self.execute('@b','comment',{'card':'agent-marketplace','parent_id':parent,'text':'I can reproduce it'})['id']
  nested=self.execute('@a','comment',{'card':'agent-marketplace','parent_id':reply,'text':'Thanks, checking'})['id']
  roots=self.execute('@a','detail',{'card':'agent-marketplace'})['posts'];self.assertEqual(len(roots),1);self.assertEqual(roots[0]['reply_count'],1)
  self.assertEqual(self.execute('@a','replies',{'card':'agent-marketplace','parent_id':parent})['posts'][0]['id'],reply)
  self.assertEqual(self.execute('@b','replies',{'card':'agent-marketplace','parent_id':reply})['posts'][0]['id'],nested)
  self.execute('@a','join_card',{'card':'game-studio'})
  with self.assertRaises(Problem):self.execute('@a','comment',{'card':'game-studio','parent_id':parent,'text':'wrong card'})
  with self.assertRaises(Problem):self.execute('@outsider','replies',{'card':'agent-marketplace','parent_id':parent})
  with self.assertRaises(Problem):self.execute('@a','delete_comment',{'card':'agent-marketplace','id':reply})
  self.execute('@a','delete_comment',{'card':'agent-marketplace','id':parent})
  tombstone=self.execute('@b','detail',{'card':'agent-marketplace'})['posts'][0]
  self.assertTrue(tombstone['deleted']);self.assertEqual(tombstone['text'],'');self.assertEqual(tombstone['actor'],'')
  self.assertEqual(self.execute('@b','replies',{'card':'agent-marketplace','parent_id':parent})['posts'][0]['text'],'I can reproduce it')
  with self.assertRaises(Problem):self.execute('@b','comment',{'card':'agent-marketplace','parent_id':parent,'text':'deleted target'})
 def test_reply_pagination_and_own_edit(self):
  self.joined('@a');parent=self.execute('@a','comment',{'card':'agent-marketplace','text':'Root'})['id']
  for i in range(23):self.execute('@a','comment',{'card':'agent-marketplace','parent_id':parent,'text':str(i)})
  d=self.execute('@a','replies',{'card':'agent-marketplace','parent_id':parent});self.assertEqual(len(d['posts']),20);self.assertTrue(d['more'])
  older=self.execute('@a','replies',{'card':'agent-marketplace','parent_id':parent,'before':d['posts'][-1]['id']});self.assertEqual(len(older['posts']),3)
  r=d['posts'][0];self.execute('@a','edit_comment',{'card':'agent-marketplace','id':r['id'],'text':'Edited reply','original_text':r['text']})
  self.assertEqual(self.execute('@a','replies',{'card':'agent-marketplace','parent_id':parent})['posts'][0]['text'],'Edited reply')
 def test_pagination(self):
  self.joined('@a')
  for i in range(23):self.execute('@a','comment',{'card':'agent-marketplace','text':str(i)})
  d=self.execute('@a','detail',{'card':'agent-marketplace'});self.assertTrue(d['more']);self.assertEqual(len(d['posts']),20)
  d2=self.execute('@a','detail',{'card':'agent-marketplace','before':d['posts'][-1]['id']});self.assertEqual(len(d2['posts']),3)
 def test_federation_proof_and_spoof_rejection(self):
  original_directory,original_peer=service.directory,service.peer
  command={'action':'join','body':{},'actor':'@remote','request_id':secrets.token_hex(16)}
  proof={'digest':service.digest(command),'target':service.HOST,'actor':'@remote','expires':service.time.time()+60}
  async def directory(who):return ['remote.example']
  async def peer(h,path,body=None):return proof
  service.directory,service.peer=directory,peer
  req={'path':'exchange','method':'POST','body':{'sender':'remote.example','proof':'a'*64,'request':command}}
  try:
   self.assertTrue(asyncio.run(service.public_request(req))['ok'])
   req['body']['request']={**command,'actor':'@forged'}
   with self.assertRaises(Problem):asyncio.run(service.public_request(req))
   req['body']['request']=command;proof['expires']=0
   with self.assertRaises(Problem):asyncio.run(service.public_request(req))
   proof['expires']=service.time.time()+60;req['body']['sender']='rogue.example'
   with self.assertRaises(Problem):asyncio.run(service.public_request(req))
  finally:service.directory,service.peer=original_directory,original_peer
if __name__=='__main__':unittest.main()
