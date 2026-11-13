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
        status,_,body=call(base,'/api/auth/setup-status')
        assert status==200 and json.loads(body)['setupRequired'] is True
        assert call(base,'/api/data')[0]==401
        assert call(base,'/api/auth/session',extra_headers={'Host':'attacker.invalid'})[0]==403
        assert call(base,'/api/upload','POST',{},send_origin=False)[0]==403
        assert call(base,'/api/auth/login','POST',{'username':'admin','password':'admin'},send_origin=False)[0]==403
        assert call(base,'/api/auth/login','POST',{'username':'admin','password':'admin'})[0]==401
        assert call(base,'/api/auth/setup','POST',{'name':'Direction','username':'direction','password':'court'})[0]==400
        initial_admin_password='unMotDePasseAdminTresSolide!'
        status,headers,body=call(base,'/api/auth/setup','POST',{'first':'Camille','last':'Durand','username':'direction','password':initial_admin_password})
        assert status==201 and json.loads(body)['user']['role']=='admin' and json.loads(body)['user']['first']=='Camille' and json.loads(body)['user']['last']=='Durand'
        admin=headers.get('Set-Cookie').split(';')[0]
        assert json.loads(call(base,'/api/auth/setup-status')[2])['setupRequired'] is False
        assert call(base,'/api/auth/setup','POST',{'name':'Autre','username':'autre','password':'unAutreMotDePasseTresSolide!'})[0]==409
        assert call(base,'/api/data',cookie=admin)[0]==200
        saved=json.loads((app/'data'/'maclasse.json').read_text())
        assert len(saved['users'])==1 and saved['users'][0]['role']=='admin' and 'teachers' not in saved
        assert 'passwordHash' not in json.loads(call(base,'/api/data',cookie=admin)[2])['users'][0]
        status,other_headers,_=call(base,'/api/auth/login','POST',{'username':'direction','password':initial_admin_password})
        assert status==200
        other_admin=other_headers.get('Set-Cookie').split(';')[0]
        assert call(base,'/api/auth/change-password','POST',{'currentPassword':initial_admin_password,'newPassword':'unMotDePasseAdminEncorePlusFort!'},admin)[0]==200
        assert call(base,'/api/data',cookie=other_admin)[0]==401
        assert call(base,'/api/data',cookie=admin)[0]==200
        assert call(base,'/api/cloud-delete','POST',{'path':'../outside'},admin)[0]==400
        uploads=app/'data'/'uploads'; outside=app/'outside-secret.txt'; outside.write_text('secret')
        try:
            (uploads/'escape-link').symlink_to(outside)
            assert call(base,'/data/uploads/escape-link',cookie=admin)[0]==404
        finally:
            (uploads/'escape-link').unlink(missing_ok=True)
        (uploads/'general').mkdir(parents=True,exist_ok=True)
        (uploads/'general'/'untrusted.html').write_text('<script>document.body.textContent="xss"</script>')
        status,upload_headers,_=call(base,'/data/uploads/general/untrusted.html',cookie=admin)
        assert status==200
        assert 'sandbox' in upload_headers.get('Content-Security-Policy','').lower()
        assert "default-src 'none'" in upload_headers.get('Content-Security-Policy','')
        saved=json.loads((app/'data'/'maclasse.json').read_text())
        admin_record=next(u for u in saved['users'] if u['username']=='direction')
        assert admin_record['passwordHash'].startswith('pbkdf2_sha256$')
        assert len(admin_record['passwordHash'].split('$'))==4
        assert admin_record['first']=='Camille' and admin_record['last']=='Durand'
        teacher_password='unMotDePasseProfTresSolide!'
        status,created_headers,created_body=call(base,'/api/admin/teacher','POST',{'first':'Alice','last':'Martin','username':'alice.martin','email':'alice@example.test','phone':'','subjects':['Mathématiques'],'profileNotes':'','password':teacher_password,'classIds':[],'ppIds':[]},admin)
        assert status==201
        created=json.loads(created_body)['user']; teacher_id=created['id']
        assert created['role']=='teacher' and created['mustChangePassword'] is True
        # Une création sans mot de passe fourni génère un provisoire aléatoire affiché une fois.
        status,_,automatic_teacher_body=call(base,'/api/admin/teacher','POST',{'first':'Benoit','last':'Petit','username':'benoit.petit','email':'','phone':'','subjects':[],'profileNotes':'','password':'','classIds':[],'ppIds':[]},admin)
        assert status==201
        automatic_teacher=json.loads(automatic_teacher_body)['user']
        assert len(automatic_teacher['temporaryPassword'])>=8 and automatic_teacher['mustChangePassword'] is True
        automatic_record=next(u for u in json.loads((app/'data'/'maclasse.json').read_text())['users'] if u['id']==automatic_teacher['id'])
        assert automatic_record['passwordHash'].startswith('pbkdf2_sha256$') and 'temporaryPassword' not in automatic_record
        auto_login_status,auto_login_headers,auto_login_body=call(base,'/api/auth/login','POST',{'username':'benoit.petit','password':automatic_teacher['temporaryPassword']})
        assert auto_login_status==200 and json.loads(auto_login_body)['user']['mustChangePassword'] is True
        saved=json.loads((app/'data'/'maclasse.json').read_text())
        teacher_record=next(u for u in saved['users'] if u['id']==teacher_id)
        assert teacher_record['first']=='Alice' and teacher_record['last']=='Martin' and 'teacherId' not in teacher_record
        assert 'teachers' not in saved and teacher_record['passwordHash'].startswith('pbkdf2_sha256$')
        status,headers,body=call(base,'/api/auth/login','POST',{'username':'alice.martin','password':teacher_password})
        assert status==200 and json.loads(body)['user']['mustChangePassword']
        teacher=headers.get('Set-Cookie').split(';')[0]
        assert call(base,'/api/auth/change-password','POST',{'currentPassword':teacher_password,'newPassword':'unMotDePasseProfEncorePlusFort!'},teacher)[0]==200
        status,_,profile_body=call(base,'/api/teacher/profile','POST',{'first':'Alicia','last':'Martin','username':'alicia.martin','email':'alicia@example.test','phone':'0102030405','subjects':['Mathématiques','Physique'],'profileNotes':'Profil mis à jour'},teacher)
        assert status==200 and json.loads(profile_body)['user']['first']=='Alicia'
        saved=json.loads((app/'data'/'maclasse.json').read_text())
        teacher_record=next(u for u in saved['users'] if u['id']==teacher_id)
        assert teacher_record['first']=='Alicia' and teacher_record['username']=='alicia.martin' and 'teacherId' not in teacher_record
        assert teacher_record['subjects']==['Mathématiques','Physique'], 'Teachers must be able to manage their own subjects'
        assert call(base,'/api/auth/login','POST',{'username':'alice.martin','password':'unMotDePasseProfEncorePlusFort!'})[0]==401
        status,new_login_headers,new_login_body=call(base,'/api/auth/login','POST',{'username':'alicia.martin','password':'unMotDePasseProfEncorePlusFort!'})
        assert status==200 and not json.loads(new_login_body)['user'].get('mustChangePassword')
        second_teacher=new_login_headers.get('Set-Cookie').split(';')[0]
        status,_,_=call(base,'/api/admin/user-status','POST',{'id':teacher_id,'active':False},admin)
        assert status==200
        assert call(base,'/api/data',cookie=teacher)[0]==401 and call(base,'/api/data',cookie=second_teacher)[0]==401
        status,_,_=call(base,'/api/admin/user-status','POST',{'id':teacher_id,'active':True},admin)
        assert status==200
        status,new_login_headers,_=call(base,'/api/auth/login','POST',{'username':'alicia.martin','password':'unMotDePasseProfEncorePlusFort!'})
        assert status==200
        teacher=new_login_headers.get('Set-Cookie').split(';')[0]
        assert call(base,'/api/reset','POST',{},teacher)[0]==403
        assert call(base,'/api/reset','POST',{},admin)[0]==200
        # Vérification HTTP de la projection professeur et de la fusion sans écrasement.
        seeded={
            'users':[],
            'classes':[{'id':'c1','name':'6A'},{'id':'c2','name':'6B'}],
            'students':[{'id':'s1','classId':'c1','first':'Alice','notes':'note interne confidentielle'},{'id':'s2','classId':'c2','first':'Bob'},{'id':'s3','classId':'c1','first':'Camille'}],
            'lessons':[{'id':'l1','classId':'c1','homework':{'title':'Exercice','requiresSubmission':True}},{'id':'l2','classId':'c2','homework':{'title':'Devoir','requiresSubmission':True}}],
            'evaluations':[{'id':'e1','classId':'c1','published':True,'grades':[{'studentId':'s1','value':15},{'studentId':'s3','value':8}]},{'id':'e2','classId':'c2','published':True,'grades':[{'studentId':'s2','value':18}]},{'id':'e3','classId':'c1','published':False,'grades':[{'studentId':'s1','value':19}]}],
            'attendance':[{'id':'a1','classId':'c1','rows':[{'studentId':'s1','status':'present'},{'studentId':'s3','status':'absent'}]}], 'bulletins':[{'id':'b1','studentId':'s1','classId':'c1','termId':'term1','validated':True,'published':True,'publishedAt':'2026-11-01T10:00:00Z'},{'id':'b2','studentId':'s2','classId':'c2','termId':'term1','validated':True,'published':True,'publishedAt':'2026-11-01T10:00:00Z'},{'id':'b3','studentId':'s1','classId':'c1','termId':'term1','validated':True,'published':False},{'id':'b4','studentId':'s3','classId':'c1','termId':'term1','validated':True,'published':True,'publishedAt':'2026-11-01T10:00:00Z'}], 'attachments':[], 'submissions':[{'id':'sub3','studentId':'s3','lessonId':'l1','status':'submitted'}], 'schedule':[], 'conversations':[{'id':'private-mail','participantIds':['s3']}], 'cloudItems':[{'id':'private-cloud','ownerId':'s3'}], 'notifications':[], 'mailFolders':[], 'settings':{'schoolName':'Test','terms':[{'id':'term1','name':'Trimestre 1'}]}
        }
        # Conserver les comptes authentifiés pendant le test de cloisonnement.
        seeded['users']=[admin_record,teacher_record]
        seeded['classes'][0]['teacherIds']=[teacher_record['id']]
        seeded['classes'][1]['teacherIds']=[]
        (app/'data'/'maclasse.json').write_text(json.dumps(seeded))
        # Un professeur crée une fiche dans une classe qui lui est attribuée ; la sauvegarde doit la conserver.
        status,teacher_data_headers,teacher_data_body=call(base,'/api/data',cookie=teacher)
        assert status==200
        teacher_data=json.loads(teacher_data_body)
        teacher_data['students'].append({'id':'s4','first':'Nina','last':'Durand','classId':'c1','group':'','birth':'','sex':'','email':'','phone':'','notes':''})
        status,_,_=call(base,'/api/save','POST',teacher_data,teacher,extra_headers={'If-Match':teacher_data_headers.get('X-MaClasse-Revision','')})
        assert status==200
        saved=json.loads((app/'data'/'maclasse.json').read_text())
        assert any(x['id']=='s4' and x['classId']=='c1' for x in saved['students'])
        status,_,missing_pdf=call(base,'/api/bulletin-pdf','POST',{'bulletinId':'absent'},teacher)
        assert status==404
        status,_,foreign_pdf=call(base,'/api/bulletin-pdf','POST',{'bulletinId':'b2'},teacher)
        assert status==403
        status,_,draft_pdf=call(base,'/api/bulletin-pdf','POST',{'bulletinId':'b3'},teacher)
        assert status==403
        status,_,valid_pdf=call(base,'/api/bulletin-pdf','POST',{'bulletinId':'b1'},teacher)
        assert status==200 and valid_pdf.startswith(b'%PDF')
        status,read_headers,raw=call(base,'/api/data',cookie=teacher)
        assert status==200
        view=json.loads(raw)
        assert [x['id'] for x in view['classes']]==['c1']
        assert [x['id'] for x in view['students']]==['s1','s3','s4']
        assert [g['studentId'] for g in view['evaluations'][0]['grades']]==['s1','s3']
        view['students'][0]['first']='Alicia'
        view['students'][-1]['first']='Nouveau'
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
        assert next(x for x in persisted['students'] if x['id']=='s4')['first']=='Nouveau'
        # Un professeur peut créer un accès pour un élève de sa classe, pas pour une autre classe.
        assert call(base,'/api/admin/student-account','POST',{'studentId':'s2','username':'bob'},teacher)[0]==403
        status,_,teacher_student_body=call(base,'/api/admin/student-account','POST',{'studentId':'s4','username':'nouveau'},teacher)
        assert status==200
        teacher_student=json.loads(teacher_student_body)['user']
        assert len(teacher_student['temporaryPassword'])>=8 and teacher_student['mustChangePassword'] is True
        teacher_data=json.loads(call(base,'/api/data',cookie=teacher)[2])
        visible_student_account=next(u for u in teacher_data['users'] if u.get('studentId')=='s4')
        assert visible_student_account['username']=='nouveau' and 'passwordHash' not in visible_student_account
        status,student_login_headers,student_login_body=call(base,'/api/auth/login','POST',{'username':'nouveau','password':teacher_student['temporaryPassword']})
        assert status==200 and json.loads(student_login_body)['user']['mustChangePassword']
        student_session=student_login_headers.get('Set-Cookie').split(';')[0]
        assert call(base,'/api/auth/change-password','POST',{'currentPassword':teacher_student['temporaryPassword'],'newPassword':'MotDePasseEleveTresSolide!'},student_session)[0]==200
        assert call(base,'/api/admin/student-account-reset','POST',{'studentId':'s2'},teacher)[0]==403
        status,_,reset_body=call(base,'/api/admin/student-account-reset','POST',{'studentId':'s4'},teacher)
        assert status==200
        reset_user=json.loads(reset_body)['user']
        assert len(reset_user['temporaryPassword'])>=8 and reset_user['mustChangePassword'] is True
        assert call(base,'/api/data',cookie=student_session)[0]==401
        status,reset_login_headers,reset_login_body=call(base,'/api/auth/login','POST',{'username':'nouveau','password':reset_user['temporaryPassword']})
        assert status==200 and json.loads(reset_login_body)['user']['mustChangePassword']
        reset_session=reset_login_headers.get('Set-Cookie').split(';')[0]
        assert call(base,'/api/admin/student-account-status','POST',{'studentId':'s4','active':False},teacher)[0]==200
        assert call(base,'/api/data',cookie=reset_session)[0]==401
        assert call(base,'/api/auth/login','POST',{'username':'nouveau','password':reset_user['temporaryPassword']})[0]==401
        assert call(base,'/api/admin/student-account-status','POST',{'studentId':'s4','active':True},teacher)[0]==200
        assert call(base,'/api/auth/login','POST',{'username':'nouveau','password':reset_user['temporaryPassword']})[0]==200
        assert next(x for x in persisted['classes'] if x['id']=='c2')['name']=='6B'
        # La direction crée un compte élève ; le serveur génère directement une empreinte PBKDF2.
        status,_,created_account=call(base,'/api/admin/student-account','POST',{'studentId':'s1','username':'alice','password':'eleveTestTresFort!'},admin)
        assert status==200 and json.loads(created_account)['user']['mustChangePassword']
        created_record=json.loads((app/'data'/'maclasse.json').read_text())
        student_record=next(u for u in created_record['users'] if u.get('role')=='student')
        assert student_record['passwordHash'].startswith('pbkdf2_sha256')
        assert call(base,'/api/admin/student-account','POST',{'studentId':'s1','username':'alice2','password':'eleveTestTresFort!'},admin)[0]==409
        status,student_headers,student_body=call(base,'/api/auth/login','POST',{'username':'alice','password':'eleveTestTresFort!'})
        assert status==200 and json.loads(student_body)['user']['role']=='student' and json.loads(student_body)['user']['mustChangePassword']
        student_cookie=student_headers.get('Set-Cookie').split(';')[0]
        assert call(base,'/api/data',cookie=student_cookie)[0]==428
        assert call(base,'/api/auth/change-password','POST',{'currentPassword':'eleveTestTresFort!','newPassword':'unMotDePasseEleveTresSolide!'},student_cookie)[0]==200
        status,student_read_headers,student_raw=call(base,'/api/data',cookie=student_cookie)
        assert status==200
        student_view=json.loads(student_raw)
        assert [x['id'] for x in student_view['students']]==['s1']
        assert 'notes' not in student_view['students'][0]
        assert [x['id'] for x in student_view['classes']]==['c1']
        assert [x['id'] for x in student_view['lessons']]==['l1']
        assert [x['id'] for x in student_view['evaluations']]==['e1']
        assert [g['studentId'] for g in student_view['evaluations'][0]['grades']]==['s1']
        assert [r['studentId'] for r in student_view['attendance'][0]['rows']]==['s1']
        assert [x['id'] for x in student_view['bulletins']]==['b1']
        assert student_view['submissions']==[]
        assert student_view['conversations']==[] and student_view['cloudItems']==[]
        assert all('passwordHash' not in u and 'password' not in u for u in student_view['users'])
        # L'élève peut déposer dans son dossier de rendu, mais pas dans celui d'un camarade.
        upload_request=urllib.request.Request(base+'/api/upload',data=b'travail fictif',headers={'Cookie':student_cookie,'Origin':base,'X-Filename':'travail.txt','X-Upload-Folder':'submissions/s1'},method='POST')
        with urllib.request.urlopen(upload_request,timeout=5) as response:
            assert response.status==200
            uploaded=json.loads(response.read())
        student_view['students'][0]['first']='Usurpation'
        student_view['submissions'].append({'id':'sub-s1','studentId':'s1','lessonId':'l1','status':'submitted','submittedAt':'2026-11-12T12:00:00Z','files':[uploaded],'correctionComment':'commentaire forgé','corrected':True})
        status,student_save_headers,_=call(base,'/api/save','POST',student_view,student_cookie,extra_headers={'If-Match':student_read_headers.get('X-MaClasse-Revision')})
        assert status==200
        persisted_student=json.loads((app/'data'/'maclasse.json').read_text())
        assert next(x for x in persisted_student['students'] if x['id']=='s1')['first']=='Alicia'
        saved_submission=next(x for x in persisted_student['submissions'] if x['id']=='sub-s1')
        assert saved_submission['status']=='submitted' and saved_submission['studentId']=='s1'
        assert 'correctionComment' not in saved_submission and not saved_submission.get('corrected')
        assert call(base,'/data/uploads/'+uploaded['name'],cookie=student_cookie)[0]==200
        (uploads/'submissions'/'s3').mkdir(parents=True,exist_ok=True)
        (uploads/'submissions'/'s3'/'autre.txt').write_text('fichier privé')
        assert call(base,'/data/uploads/submissions/s3/autre.txt',cookie=student_cookie)[0]==403
        bad_upload=urllib.request.Request(base+'/api/upload',data=b'non',headers={'Cookie':student_cookie,'Origin':base,'X-Filename':'autre.txt','X-Upload-Folder':'submissions/s3'},method='POST')
        try:
            urllib.request.urlopen(bad_upload,timeout=5)
            raise AssertionError('Un élève ne doit pas déposer dans le dossier d’un autre.')
        except urllib.error.HTTPError as error:
            assert error.code==403
        assert call(base,'/api/data',cookie=teacher)[0]==200
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
        print('OK — authentification HTTP, révocation des sessions, projections professeur/élève, cloisonnement des données, conflits, rôles et restauration ZIP admin.')
    finally:
        process.terminate(); process.wait(timeout=5); shutil.rmtree(temp,ignore_errors=True)

if __name__=='__main__': run()
)
        assert not any(x.get('role')=='student' for x in saved['users'])
        status,student_headers,student_login_body=call(base,'/api/auth/login','POST',{'username':'nina.durand','password':student_access['temporaryPassword']})
        assert status==200 and json.loads(student_login_body)['user']['id']=='s1'
        student_cookie=student_headers.get('Set-Cookie').split(';')[0]
        assert json.loads(student_login_body)['user']['mustChangePassword'] is True
        assert call(base,'/api/auth/change-password','POST',{'currentPassword':student_access['temporaryPassword'],'newPassword':'MotDePasseEleveTresSolide!'},student_cookie)[0]==200
        assert call(base,'/api/auth/login','POST',{'username':'alice.student','password':'MotDePasseEleveTresSolide!'})[0]==200
        status,_,student_data_body=call(base,'/api/data',cookie=student_cookie)
        assert status==200 and any(x['id']=='s4' for x in json.loads(student_data_body)['students'])
        assert 'passwordHash' not in json.loads(student_data_body)['students'][0]
        assert call(base,'/api/admin/student-account-reset','POST',{'studentId':'s4'},teacher)[0]==200

        status,_,missing_pdf=call(base,'/api/bulletin-pdf','POST',{'bulletinId':'absent'},teacher)
        assert status==404
        status,_,foreign_pdf=call(base,'/api/bulletin-pdf','POST',{'bulletinId':'b2'},teacher)
        assert status==403
        status,_,draft_pdf=call(base,'/api/bulletin-pdf','POST',{'bulletinId':'b3'},teacher)
        assert status==403
        status,_,valid_pdf=call(base,'/api/bulletin-pdf','POST',{'bulletinId':'b1'},teacher)
        assert status==200 and valid_pdf.startswith(b'%PDF')
        status,read_headers,raw=call(base,'/api/data',cookie=teacher)
        assert status==200
        view=json.loads(raw)
        assert [x['id'] for x in view['classes']]==['c1']
        assert [x['id'] for x in view['students']]==['s1','s3']
        assert [g['studentId'] for g in view['evaluations'][0]['grades']]==['s1','s3']
        view['students'][0]['first']='Alicia'
        view['students'].append({'id':'s4','classId':'c1','first':'Nouveau','last':'Eleve'})
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
        assert next(x for x in persisted['students'] if x['id']=='s4')['first']=='Nouveau'
        # Un professeur peut créer un accès pour un élève de sa classe, pas pour une autre classe.
        assert call(base,'/api/admin/student-account','POST',{'studentId':'s2','username':'bob'},teacher)[0]==403
        status,_,teacher_student_body=call(base,'/api/admin/student-account','POST',{'studentId':'s4','username':'nouveau'},teacher)
        assert status==200
        teacher_student=json.loads(teacher_student_body)['user']
        assert len(teacher_student['temporaryPassword'])>=8 and teacher_student['mustChangePassword'] is True
        teacher_data=json.loads(call(base,'/api/data',cookie=teacher)[2])
        visible_student_account=next(u for u in teacher_data['users'] if u.get('studentId')=='s4')
        assert visible_student_account['username']=='nouveau' and 'passwordHash' not in visible_student_account
        status,student_login_headers,student_login_body=call(base,'/api/auth/login','POST',{'username':'nouveau','password':teacher_student['temporaryPassword']})
        assert status==200 and json.loads(student_login_body)['user']['mustChangePassword']
        student_session=student_login_headers.get('Set-Cookie').split(';')[0]
        assert call(base,'/api/admin/student-account-reset','POST',{'studentId':'s2'},teacher)[0]==403
        status,_,reset_body=call(base,'/api/admin/student-account-reset','POST',{'studentId':'s4'},teacher)
        assert status==200
        reset_user=json.loads(reset_body)['user']
        assert len(reset_user['temporaryPassword'])>=8 and reset_user['mustChangePassword'] is True
        assert call(base,'/api/data',cookie=student_session)[0]==401
        status,reset_login_headers,reset_login_body=call(base,'/api/auth/login','POST',{'username':'nouveau','password':reset_user['temporaryPassword']})
        assert status==200 and json.loads(reset_login_body)['user']['mustChangePassword']
        reset_session=reset_login_headers.get('Set-Cookie').split(';')[0]
        assert call(base,'/api/admin/student-account-status','POST',{'studentId':'s4','active':False},teacher)[0]==200
        assert call(base,'/api/data',cookie=reset_session)[0]==401
        assert call(base,'/api/auth/login','POST',{'username':'nouveau','password':reset_user['temporaryPassword']})[0]==401
        assert call(base,'/api/admin/student-account-status','POST',{'studentId':'s4','active':True},teacher)[0]==200
        assert call(base,'/api/auth/login','POST',{'username':'nouveau','password':reset_user['temporaryPassword']})[0]==200
        assert next(x for x in persisted['classes'] if x['id']=='c2')['name']=='6B'
        # La direction crée un compte élève ; le serveur génère directement une empreinte PBKDF2.
        status,_,created_account=call(base,'/api/admin/student-account','POST',{'studentId':'s1','username':'alice','password':'eleveTestTresFort!'},admin)
        assert status==200 and json.loads(created_account)['user']['mustChangePassword']
        created_record=json.loads((app/'data'/'maclasse.json').read_text())
        student_record=next(u for u in created_record['users'] if u.get('role')=='student')
        assert student_record['passwordHash'].startswith('pbkdf2_sha256')
        assert call(base,'/api/admin/student-account','POST',{'studentId':'s1','username':'alice2','password':'eleveTestTresFort!'},admin)[0]==409
        status,student_headers,student_body=call(base,'/api/auth/login','POST',{'username':'alice','password':'eleveTestTresFort!'})
        assert status==200 and json.loads(student_body)['user']['role']=='student' and json.loads(student_body)['user']['mustChangePassword']
        student_cookie=student_headers.get('Set-Cookie').split(';')[0]
        assert call(base,'/api/data',cookie=student_cookie)[0]==428
        assert call(base,'/api/auth/change-password','POST',{'currentPassword':'eleveTestTresFort!','newPassword':'unMotDePasseEleveTresSolide!'},student_cookie)[0]==200
        status,student_read_headers,student_raw=call(base,'/api/data',cookie=student_cookie)
        assert status==200
        student_view=json.loads(student_raw)
        assert [x['id'] for x in student_view['students']]==['s1']
        assert 'notes' not in student_view['students'][0]
        assert [x['id'] for x in student_view['classes']]==['c1']
        assert [x['id'] for x in student_view['lessons']]==['l1']
        assert [x['id'] for x in student_view['evaluations']]==['e1']
        assert [g['studentId'] for g in student_view['evaluations'][0]['grades']]==['s1']
        assert [r['studentId'] for r in student_view['attendance'][0]['rows']]==['s1']
        assert [x['id'] for x in student_view['bulletins']]==['b1']
        assert student_view['submissions']==[]
        assert student_view['conversations']==[] and student_view['cloudItems']==[]
        assert all('passwordHash' not in u and 'password' not in u for u in student_view['users'])
        # L'élève peut déposer dans son dossier de rendu, mais pas dans celui d'un camarade.
        upload_request=urllib.request.Request(base+'/api/upload',data=b'travail fictif',headers={'Cookie':student_cookie,'Origin':base,'X-Filename':'travail.txt','X-Upload-Folder':'submissions/s1'},method='POST')
        with urllib.request.urlopen(upload_request,timeout=5) as response:
            assert response.status==200
            uploaded=json.loads(response.read())
        student_view['students'][0]['first']='Usurpation'
        student_view['submissions'].append({'id':'sub-s1','studentId':'s1','lessonId':'l1','status':'submitted','submittedAt':'2026-11-12T12:00:00Z','files':[uploaded],'correctionComment':'commentaire forgé','corrected':True})
        status,student_save_headers,_=call(base,'/api/save','POST',student_view,student_cookie,extra_headers={'If-Match':student_read_headers.get('X-MaClasse-Revision')})
        assert status==200
        persisted_student=json.loads((app/'data'/'maclasse.json').read_text())
        assert next(x for x in persisted_student['students'] if x['id']=='s1')['first']=='Alicia'
        saved_submission=next(x for x in persisted_student['submissions'] if x['id']=='sub-s1')
        assert saved_submission['status']=='submitted' and saved_submission['studentId']=='s1'
        assert 'correctionComment' not in saved_submission and not saved_submission.get('corrected')
        assert call(base,'/data/uploads/'+uploaded['name'],cookie=student_cookie)[0]==200
        (uploads/'submissions'/'s3').mkdir(parents=True,exist_ok=True)
        (uploads/'submissions'/'s3'/'autre.txt').write_text('fichier privé')
        assert call(base,'/data/uploads/submissions/s3/autre.txt',cookie=student_cookie)[0]==403
        bad_upload=urllib.request.Request(base+'/api/upload',data=b'non',headers={'Cookie':student_cookie,'Origin':base,'X-Filename':'autre.txt','X-Upload-Folder':'submissions/s3'},method='POST')
        try:
            urllib.request.urlopen(bad_upload,timeout=5)
            raise AssertionError('Un élève ne doit pas déposer dans le dossier d’un autre.')
        except urllib.error.HTTPError as error:
            assert error.code==403
        assert call(base,'/api/data',cookie=teacher)[0]==200
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
        print('OK — authentification HTTP, révocation des sessions, projections professeur/élève, cloisonnement des données, conflits, rôles et restauration ZIP admin.')
    finally:
        process.terminate(); process.wait(timeout=5); shutil.rmtree(temp,ignore_errors=True)

if __name__=='__main__': run()
