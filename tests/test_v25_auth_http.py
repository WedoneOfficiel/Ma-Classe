"""Test HTTP d'intégration de l'authentification V25. À lancer depuis la racine : python3 tests/test_v25_auth_http.py"""
import hashlib, json, os, shutil, socket, subprocess, tempfile, time, urllib.request, urllib.error, io, zipfile
from pathlib import Path

SOURCE=Path(__file__).resolve().parents[1]

def call(base,path,method='GET',payload=None,cookie=None,send_origin=True,extra_headers=None):
    headers={}
    body=None
    if payload is not None:
        headers['Content-Type']='application/json'; body=json.dumps(payload).encode()
    if cookie: headers['Cookie']=cookie
    if extra_headers: headers.update(extra_headers)
    if send_origin and method in ('POST','PUT','DELETE'): headers['Origin']=base
    request=urllib.request.Request(base+path,data=body,headers=headers,method=method)
    try:
        with urllib.request.urlopen(request,timeout=3) as response:
            return response.status,response.headers,response.read()
    except urllib.error.HTTPError as error:
        return error.code,error.headers,error.read()

def run():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]
    base=f'http://127.0.0.1:{port}'
    temp=Path(tempfile.mkdtemp(prefix='maclasse-v25-auth-'))
    app=temp/'app'; shutil.copytree(SOURCE,app)
    env=os.environ.copy(); env['MACLASSE_HOST']='127.0.0.1'; env['MACLASSE_PORT']=str(port)
    process=subprocess.Popen(['python3','server.py'],cwd=app,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    sha=lambda value: hashlib.sha256(value.encode()).hexdigest()
    try:
        for _ in range(40):
            try: call(base,'/'); break
            except Exception: time.sleep(.1)
        assert call(base,'/api/data')[0]==401
        assert call(base,'/api/upload','POST',{},send_origin=False)[0]==403
        assert call(base,'/api/auth/login','POST',{'username':'admin','password':'admin'},send_origin=False)[0]==403
        status,headers,body=call(base,'/api/auth/login','POST',{'username':'admin','password':'admin'})
        assert status==200 and json.loads(body)['user']['mustChangePassword']
        admin=headers.get('Set-Cookie').split(';')[0]
        assert call(base,'/api/data',cookie=admin)[0]==428
        assert call(base,'/api/auth/change-password','POST',{'currentPassword':'admin','newPassword':'court'},admin)[0]==400
        assert call(base,'/api/auth/change-password','POST',{'currentPassword':'admin','newPassword':'unMotDePasseAdminTresSolide!'},admin)[0]==200
        assert call(base,'/api/data',cookie=admin)[0]==200
        assert call(base,'/api/cloud-delete','POST',{'path':'../outside'},admin)[0]==400
        uploads=app/'data'/'uploads'; outside=app/'outside-secret.txt'; outside.write_text('secret')
        try:
            (uploads/'escape-link').symlink_to(outside)
            assert call(base,'/data/uploads/escape-link',cookie=admin)[0]==404
        finally:
            (uploads/'escape-link').unlink(missing_ok=True)
        saved=json.loads((app/'data'/'maclasse.json').read_text())
        admin_record=next(u for u in saved['users'] if u['username']=='admin')
        assert admin_record['passwordHash'].startswith('pbkdf2_sha256$')
        assert len(admin_record['passwordHash'].split('$'))==4
        status,headers,body=call(base,'/api/auth/login','POST',{'username':'enseignant','password':'enseignant'})
        assert status==200 and json.loads(body)['user']['mustChangePassword']
        teacher=headers.get('Set-Cookie').split(';')[0]
        assert call(base,'/api/auth/change-password','POST',{'currentPassword':'enseignant','newPassword':'unMotDePasseProfTresSolide!'},teacher)[0]==200
        saved=json.loads((app/'data'/'maclasse.json').read_text())
        teacher_record=next(u for u in saved['users'] if u['username']=='enseignant')
        assert teacher_record['passwordHash'].startswith('pbkdf2_sha256$')
        assert call(base,'/api/reset','POST',{},teacher)[0]==403
        assert call(base,'/api/reset','POST',{},admin)[0]==200
        # Vérification HTTP de la projection professeur et de la fusion sans écrasement.
        seeded={
            'users':[],
            'teachers':[{'id':'teacher-local','classIds':['c1']},{'id':'t2','classIds':['c2']}],
            'classes':[{'id':'c1','name':'6A'},{'id':'c2','name':'6B'}],
            'students':[{'id':'s1','classId':'c1','first':'Alice'},{'id':'s2','classId':'c2','first':'Bob'}],
            'lessons':[{'id':'l1','classId':'c1'},{'id':'l2','classId':'c2'}],
            'evaluations':[{'id':'e1','classId':'c1','grades':[{'studentId':'s1','value':15},{'studentId':'s2','value':2}]},{'id':'e2','classId':'c2','grades':[{'studentId':'s2','value':18}]}],
            'attendance':[], 'bulletins':[{'id':'b1','studentId':'s1','classId':'c1','termId':'term1','published':True,'publishedAt':'2026-11-01T10:00:00Z'},{'id':'b2','studentId':'s2','classId':'c2','termId':'term1','published':True,'publishedAt':'2026-11-01T10:00:00Z'}], 'attachments':[], 'submissions':[], 'schedule':[], 'conversations':[], 'cloudItems':[], 'notifications':[], 'mailFolders':[], 'settings':{'schoolName':'Test','terms':[{'id':'term1','name':'Trimestre 1'}]}
        }
        # Conserver les comptes authentifiés pendant le test de cloisonnement.
        seeded['users']=[admin_record,teacher_record]
        (app/'data'/'maclasse.json').write_text(json.dumps(seeded))
        status,_,missing_pdf=call(base,'/api/bulletin-pdf','POST',{'bulletinId':'absent'},teacher)
        assert status==404
        status,_,foreign_pdf=call(base,'/api/bulletin-pdf','POST',{'bulletinId':'b2'},teacher)
        assert status==403
        status,read_headers,raw=call(base,'/api/data',cookie=teacher)
        assert status==200
        view=json.loads(raw)
        assert [x['id'] for x in view['classes']]==['c1']
        assert [x['id'] for x in view['students']]==['s1']
        assert [g['studentId'] for g in view['evaluations'][0]['grades']]==['s1']
        view['students'][0]['first']='Alicia'
        original_revision=read_headers.get('X-MaClasse-Revision')
        status,_,missing=call(base,'/api/save','POST',view,teacher)
        assert status==428 and json.loads(missing)['code']=='REVISION_REQUIRED'
        assert original_revision and len(original_revision)==64
        status,save_headers,_=call(base,'/api/save','POST',view,teacher,extra_headers={'If-Match':original_revision})
        assert status==200 and save_headers.get('X-MaClasse-Revision')!=original_revision
        # Une seconde sauvegarde issue de l'ancien état est refusée, sans écraser la première.
        view['students'][0]['first']='Alice stale'
        status,_,conflict=call(base,'/api/save','POST',view,teacher,extra_headers={'If-Match':original_revision})
        assert status==409 and json.loads(conflict)['code']=='REVISION_CONFLICT'
        persisted=json.loads((app/'data'/'maclasse.json').read_text())
        assert next(x for x in persisted['students'] if x['id']=='s1')['first']=='Alicia'
        assert next(x for x in persisted['students'] if x['id']=='s2')['first']=='Bob'
        assert next(x for x in persisted['classes'] if x['id']=='c2')['name']=='6B'
        # La restauration ZIP complète est réservée à la direction et remplace aussi les uploads.
        archive=io.BytesIO()
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('data/maclasse.json',json.dumps({'classes':[{'id':'restored','name':'Restaurée'}],'students':[{'id':'rs1','classId':'restored'}],'users':[]}))
            z.writestr('data/uploads/restored.txt','fichier restauré')
        def restore(cookie):
            req=urllib.request.Request(base+'/api/backup/restore',data=archive.getvalue(),headers={'Cookie':cookie,'Origin':base,'Content-Type':'application/zip'},method='POST')
            try:
                with urllib.request.urlopen(req,timeout=5) as response:return response.status,response.read()
            except urllib.error.HTTPError as error:return error.code,error.read()
        assert restore(teacher)[0]==403
        status,restore_body=restore(admin)
        assert status==200 and json.loads(restore_body)['restored']['files']==1
        restored=json.loads((app/'data'/'maclasse.json').read_text())
        assert restored['classes'][0]['id']=='restored'
        assert (app/'data'/'uploads'/'restored.txt').read_text()=='fichier restauré'
        # Une restauration qui supprime les comptes doit révoquer les sessions déjà ouvertes.
        assert call(base,'/api/data',cookie=teacher)[0]==401
        assert call(base,'/api/data',cookie=admin)[0]==401
        print('OK — authentification HTTP, révocation des sessions, projection professeur, conflits, rôles et restauration ZIP admin.')
    finally:
        process.terminate(); process.wait(timeout=5); shutil.rmtree(temp,ignore_errors=True)

if __name__=='__main__': run()
