"""Hackaton domain: transactions own membership, visibility and author-owned comments."""
import sqlite3, json, time, re, base64, io
from PIL import Image
class Problem(Exception):
    def __init__(self,status,message): self.status=status; self.message=message

def require(ok,message,status=400):
    if not ok: raise Problem(status,message)
def handle(value):
    require(isinstance(value,str) and re.fullmatch(r'@?[a-zA-Z0-9_-]{1,64}',value),'Invalid Möbius handle.')
    return '@'+value.lstrip('@').lower()
def connect(path):
    db=sqlite3.connect(path,timeout=10);db.row_factory=sqlite3.Row
    db.executescript('''
    CREATE TABLE IF NOT EXISTS people(actor TEXT PRIMARY KEY, accepted INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS members(card TEXT,actor TEXT,PRIMARY KEY(card,actor));
    CREATE TABLE IF NOT EXISTS posts(id INTEGER PRIMARY KEY,card TEXT,actor TEXT,text TEXT,image TEXT,created REAL);
    CREATE TABLE IF NOT EXISTS receipts(id TEXT PRIMARY KEY,digest TEXT,result TEXT);
    CREATE TABLE IF NOT EXISTS proofs(id TEXT PRIMARY KEY,document TEXT,expires REAL);
    ''')
    db.execute('BEGIN IMMEDIATE')
    columns={r[1] for r in db.execute('PRAGMA table_info(posts)')}
    if 'parent_id' not in columns:db.execute('ALTER TABLE posts ADD COLUMN parent_id INTEGER')
    if 'deleted' not in columns:db.execute('ALTER TABLE posts ADD COLUMN deleted INTEGER NOT NULL DEFAULT 0')
    db.execute('CREATE INDEX IF NOT EXISTS posts_thread ON posts(card,parent_id,id)')
    db.commit()
    return db
CARDS=[{'id':'01','title':'Build something useful','tag':'PRODUCT','description':'Sample challenge: turn an everyday friction into a small, working tool. Share what you built and what you learned.'},{'id':'02','title':'Make data tell a story','tag':'DATA','description':'Sample challenge: explore a dataset and surface one surprising insight. Share your visual, method, and findings.'},{'id':'03','title':'Reimagine an interaction','tag':'DESIGN','description':'Sample challenge: rethink a familiar digital interaction. Share a prototype, screenshots, and your reasoning.'}]
RULES=[{'title':'The brief','text':'Placeholder rule text. Replace with the event scope, schedule, and participation requirements.'},{'title':'Working together','text':'Placeholder rule text. Replace with collaboration guidelines, team sizes, and permitted tools.'},{'title':'Sharing your work','text':'Placeholder rule text. Replace with submission requirements, judging criteria, and deadlines.'}]
def run(db,actor,action,b):
    person=db.execute('SELECT * FROM people WHERE actor=?',(actor,)).fetchone()
    if action=='join':
        db.execute('INSERT OR IGNORE INTO people(actor) VALUES(?)',(actor,));return {'ok':True}
    if action=='state':
        return {'joined':bool(person),'accepted':bool(person and person['accepted']),'rules':RULES if person else [],'cards':[{**c,'count':db.execute('SELECT COUNT(*) FROM members WHERE card=?',(c['id'],)).fetchone()[0],'joined':bool(db.execute('SELECT 1 FROM members WHERE card=? AND actor=?',(c['id'],actor)).fetchone())} for c in CARDS] if person and person['accepted'] else []}
    require(person,'Join Hackaton 2026 first.',403)
    if action=='accept':db.execute('UPDATE people SET accepted=1 WHERE actor=?',(actor,));return {'ok':True}
    require(person['accepted'],'Read the event rules first.',403)
    card=b.get('card');require(card in [c['id'] for c in CARDS],'Challenge not found.',404)
    if action=='join_card':db.execute('INSERT OR IGNORE INTO members VALUES(?,?)',(card,actor));return {'ok':True}
    require(db.execute('SELECT 1 FROM members WHERE card=? AND actor=?',(card,actor)).fetchone(),'Join this challenge to see participants and findings.',403)
    if action in ('detail','replies'):
        visible="(p.deleted=0 OR EXISTS(SELECT 1 FROM posts child WHERE child.parent_id=p.id))"
        fields="p.id,p.actor,p.text,p.created,p.parent_id,p.deleted,p.image IS NOT NULL AS has_image,(SELECT COUNT(*) FROM posts child WHERE child.parent_id=p.id AND (child.deleted=0 OR EXISTS(SELECT 1 FROM posts grandchild WHERE grandchild.parent_id=child.id))) AS reply_count"
        if action=='detail':
            before=b.get('before',9223372036854775807);require(isinstance(before,int),'Invalid page.')
            rows=[dict(r) for r in db.execute(f'SELECT {fields} FROM posts p WHERE p.card=? AND p.parent_id IS NULL AND p.id<? AND {visible} ORDER BY p.id DESC LIMIT 21',(card,before))]
        else:
            parent=b.get('parent_id');before=b.get('before',9223372036854775807)
            require(isinstance(parent,int) and isinstance(before,int),'Invalid reply page.')
            require(db.execute('SELECT 1 FROM posts WHERE card=? AND id=?',(card,parent)).fetchone(),'Finding or reply not found.',404)
            rows=[dict(r) for r in db.execute(f'SELECT {fields} FROM posts p WHERE p.card=? AND p.parent_id=? AND p.id<? AND {visible} ORDER BY p.id DESC LIMIT 21',(card,parent,before))]
        result={'posts':[{**r,'mine':not r['deleted'] and r['actor']==actor} for r in rows[:20]],'more':len(rows)>20}
        if action=='detail':result['members']=[r[0] for r in db.execute('SELECT actor FROM members WHERE card=? ORDER BY actor',(card,))]
        return result
    if action=='image':
        row=db.execute('SELECT image FROM posts WHERE card=? AND id=? AND deleted=0',(card,b.get('id'))).fetchone();require(row,'Image not found.',404);return {'image':row[0]}
    if action in ('edit_comment','delete_comment'):
        row=db.execute('SELECT * FROM posts WHERE card=? AND id=?',(card,b.get('id'))).fetchone()
        require(row and not row['deleted'],'Finding or reply not found. It may have been deleted.',404)
        require(row['actor']==actor,'You can only change your own findings and replies.',403)
        if action=='delete_comment':
            db.execute("UPDATE posts SET deleted=1,text='',image=NULL,actor='' WHERE id=?",(row['id'],))
            count=db.execute('SELECT COUNT(*) FROM posts child WHERE child.parent_id=? AND (child.deleted=0 OR EXISTS(SELECT 1 FROM posts grandchild WHERE grandchild.parent_id=child.id))',(row['id'],)).fetchone()[0]
            return {'ok':True,'post':{'id':row['id'],'parent_id':row['parent_id'],'actor':'','text':'','created':row['created'],'has_image':0,'deleted':True,'mine':False,'reply_count':count} if count else None}
        text=b.get('text','');require(isinstance(text,str) and len(text)<=10000,'Keep text under 10,000 characters.')
        remove=b.get('remove_image',False);require(isinstance(remove,bool),'Invalid attachment change.')
        require(text.strip() or (row['image'] and not remove),'Add text or keep the image.')
        require(b.get('original_text')==row['text'],'This finding or reply changed elsewhere. Cancel and refresh before editing again.',409)
        db.execute('UPDATE posts SET text=?,image=? WHERE id=?',(text.strip(),None if remove else row['image'],row['id']))
        return {'ok':True}
    if action=='comment':
        parent=b.get('parent_id')
        if parent is not None:
            require(isinstance(parent,int),'Invalid reply target.')
            require(db.execute('SELECT 1 FROM posts WHERE card=? AND id=? AND deleted=0',(card,parent)).fetchone(),'That finding or reply was deleted. Reply to another entry instead.',404)
        text=b.get('text','');image=b.get('image');require(isinstance(text,str) and len(text)<=10000,'Keep text under 10,000 characters.')
        require(text.strip() or image,'Add text or an image.')
        if image:
            require(isinstance(image,str) and len(image)<=1500000 and re.fullmatch(r'data:image/(png|jpeg|webp);base64,[A-Za-z0-9+/=]+',image),'Use a PNG, JPEG or WebP image under 1 MB.')
            try:
                raw=base64.b64decode(image.split(',',1)[1],validate=True)
                im=Image.open(io.BytesIO(raw));require(im.width*im.height<=20000000,'Image is too large.');im.verify()
            except Problem: raise
            except Exception: raise Problem(400,'This image could not be read.')
        cur=db.execute('INSERT INTO posts(card,actor,text,image,created,parent_id) VALUES(?,?,?,?,?,?)',(card,actor,text.strip(),image,time.time(),parent));return {'id':cur.lastrowid}
    raise Problem(404,'Unknown action.')
