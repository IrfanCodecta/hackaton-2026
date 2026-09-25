"""Cross-installation routing with real isolated databases and proof exchange.
Only directory/network transport are replaced; no live event writes.
"""
import asyncio, contextlib, os, secrets, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('APP_STORAGE_DIR', tempfile.gettempdir())
os.environ.setdefault('INSTANCE_ORIGIN', 'https://test.example')
os.environ.setdefault('API_BASE_URL', 'http://unused')
os.environ.setdefault('APP_TOKEN', 'test-only')
import service

class SharedEventTests(unittest.TestCase):
 def test_two_installations_share_counts_comments_and_preserve_local_data(self):
  with tempfile.TemporaryDirectory() as tmp:
   organizer=service.EVENT_HOST
   hosts={organizer:'@organizer','alice.example':'@alice','bob.example':'@bob'}
   paths={host:Path(tmp)/f'{i}.sqlite3' for i,host in enumerate(hosts)}
   @contextlib.contextmanager
   def machine(host):
    with patch.object(service,'HOST',host),patch.object(service,'DB_PATH',paths[host]):yield
   async def profile():return {'handle':hosts[service.HOST],'user_id':'fixture'}
   async def directory(actor):return [host for host,handle in hosts.items() if handle==actor]
   async def peer(host,path,body=None):
    with machine(host):return await service.public_request({'method':'POST' if body is not None else 'GET','path':path,'body':body})
   async def command(host,action,body=None,target=None):
    payload={'action':action,'body':body or {},'request_id':secrets.token_hex(16)}
    if target:payload['host']=target
    with machine(host):return await service.main({'schema':1,'actor':{'scope':'app'},'method':'POST','path':'command','body':payload})
   async def scenario():
    # Earlier local activity stays intact when the default changes.
    for action,body in [('join',{}),('accept',{}),('join_card',{'card':'01'}),('comment',{'card':'01','text':'Private old copy'})]:
     await command('alice.example',action,body,target='alice.example')
    for host in ['alice.example','bob.example']:
     with machine(host):
      context=await service.main({'schema':1,'actor':{'scope':'app'},'method':'GET','path':'context'})
      self.assertEqual(context['event_host'],organizer);self.assertEqual(context['host'],host)
     for action,body in [('join',{}),('accept',{}),('join_card',{'card':'01'})]:await command(host,action,body)
    post=await command('alice.example','comment',{'card':'01','text':'Shared finding'})
    d=await command('bob.example','detail',{'card':'01'})
    self.assertEqual(d['members'],['@alice','@bob']);self.assertEqual(d['posts'][0]['text'],'Shared finding')
    reply=await command('bob.example','comment',{'card':'01','parent_id':post['id'],'text':'Shared reply'})
    d=await command('alice.example','replies',{'card':'01','parent_id':post['id']})
    self.assertEqual(d['posts'][0]['id'],reply['id'])
    for host in ['alice.example','bob.example']:
     d=await command(host,'state');self.assertEqual(d['cards'][0]['count'],2)
    old=await command('alice.example','detail',{'card':'01'},target='alice.example')
    self.assertEqual(old['posts'][0]['text'],'Private old copy');self.assertEqual(old['members'],['@alice'])
   with patch.object(service,'profile',profile),patch.object(service,'directory',directory),patch.object(service,'peer',peer):asyncio.run(scenario())

if __name__=='__main__':unittest.main()
