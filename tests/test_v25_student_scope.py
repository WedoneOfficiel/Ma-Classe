"""Tests de cloisonnement des comptes élèves et de leurs rendus."""
import json
import datetime
import os
import tempfile
import unittest
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import server


class StudentScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.old_data=server.DATA_FILE
        self.old_uploads=server.UPLOADS
        server.DATA_FILE=os.path.join(self.tmp.name,'maclasse.json')
        server.UPLOADS=os.path.join(self.tmp.name,'uploads')
        os.makedirs(server.UPLOADS)
        self.user={'id':'s1','role':'student','studentId':'s1','name':'Alice'}
        self.data={
            'users':[{'id':'t1','role':'teacher','first':'Prof','last':'A'},{'id':'t2','role':'teacher','first':'Prof','last':'B'}],
            'classes':[{'id':'c1','name':'6A','teacherIds':['t1']},{'id':'c2','name':'6B','teacherIds':['t2']}],
            'students':[{'id':'s1','classId':'c1','first':'Alice','username':'alice','role':'student','active':True,'passwordHash':'secret','notes':'note interne confidentielle'},{'id':'s2','classId':'c1','first':'Bob'},{'id':'s3','classId':'c2','first':'Chloé'}],
            'schedule':[{'id':'slot1','classId':'c1','teacherId':'t1'},{'id':'slot2','classId':'c2','teacherId':'t2'}],
            'lessons':[{'id':'l1','classId':'c1','homework':{'requiresSubmission':True}},{'id':'l1b','classId':'c1','homework':{'requiresSubmission':True}},{'id':'l2','classId':'c2','homework':{'requiresSubmission':True}}],
            'evaluations':[{'id':'e1','classId':'c1','published':True,'grades':[{'studentId':'s1','value':14},{'studentId':'s2','value':7}]},{'id':'e2','classId':'c1','published':False,'grades':[{'studentId':'s1','value':19}]}],
            'attendance':[{'id':'a1','classId':'c1','rows':[{'studentId':'s1','status':'present'},{'studentId':'s2','status':'absent'}]}],
            'bulletins':[{'id':'b1','studentId':'s1','classId':'c1','validated':True,'published':True},{'id':'b2','studentId':'s2','classId':'c1','validated':True,'published':True}],
            'submissions':[{'id':'old','studentId':'s1','lessonId':'l1b','classId':'c1','status':'submitted','corrected':True,'correctionComment':'Prof feedback'},{'id':'other','studentId':'s2','lessonId':'l1','classId':'c1','status':'submitted'}],
            'attachments':[],'conversations':[{'id':'private','participantIds':['s2']}],
            'cloudItems':[{'id':'private','ownerId':'s2'}],'notifications':[],'settings':{'schoolName':'private','terms':[],'subjectColors':{'francais':'#123456'}}
        }
        with open(server.DATA_FILE,'w',encoding='utf-8') as f: json.dump(self.data,f)

    def tearDown(self):
        server.DATA_FILE=self.old_data
        server.UPLOADS=self.old_uploads
        self.tmp.cleanup()

    def test_projection_contains_only_own_student_data_and_published_results(self):
        view=server._student_visible_data(self.data,self.user)
        self.assertEqual(view['settings']['subjectColors'],{'francais':'#123456'})
        self.assertNotIn('schoolName',view['settings'])
        self.assertEqual([x['id'] for x in view['students']],['s1'])
        self.assertNotIn('notes',view['students'][0])
        self.assertEqual([x['id'] for x in view['classes']],['c1'])
        self.assertEqual([x['id'] for x in view['lessons']],['l1','l1b'])
        self.assertEqual([x['id'] for x in view['evaluations']],['e1'])
        self.assertEqual([x['studentId'] for x in view['evaluations'][0]['grades']],['s1'])
        self.assertEqual([x['studentId'] for x in view['attendance'][0]['rows']],['s1'])
        self.assertEqual([x['id'] for x in view['bulletins']],['b1'])
        self.assertEqual([x['id'] for x in view['submissions']],['old'])
        self.assertEqual(view['conversations'],[])
        self.assertEqual(view['cloudItems'],[])
        self.assertNotIn('passwordHash',view['users'][0])
        self.assertEqual([x['id'] for x in view['teachers']],['t1'])

    def test_student_mailbox_projection_is_private_and_hides_other_bcc_recipients(self):
        self.data['mailboxV2']={
            'schemaVersion':2,
            'messages':[
                {'id':'teacher-to-s1','sender':{'key':'teacher:t1','role':'teacher','id':'t1'},'to':['student:s1'],'bcc':['student:s2'],'subject':'Pour Alice'},
                {'id':'teacher-to-s2','sender':{'key':'teacher:t1','role':'teacher','id':'t1'},'to':['student:s2'],'subject':'Pour Bob'},
                {'id':'student-sent','sender':{'key':'student:s1','role':'student','id':'s1'},'to':['teacher:t1'],'subject':'Question'},
                {'id':'unrelated-teacher','sender':{'key':'teacher:t2','role':'teacher','id':'t2'},'to':['student:s1'],'subject':'Hors périmètre'}
            ],
            'states':{'student:s1':{'teacher-to-s1':{'read':False}},'student:s2':{'teacher-to-s2':{'read':False}},'teacher:t1':{'x':{}}},
            'folders':[{'id':'own-folder','owner':'student:s1'},{'id':'other-folder','owner':'student:s2'}],
            'drafts':[{'id':'own-draft','owner':'student:s1'},{'id':'other-draft','owner':'student:s2'}],
            'resetPending':False
        }
        view=server._student_visible_data(self.data,self.user)
        mailbox=view['mailboxV2']
        self.assertEqual({x['id'] for x in mailbox['messages']},{'teacher-to-s1','student-sent'})
        incoming=next(x for x in mailbox['messages'] if x['id']=='teacher-to-s1')
        self.assertEqual(incoming['bcc'],[])
        self.assertEqual(set(mailbox['states']),{'student:s1'})
        self.assertEqual([x['id'] for x in mailbox['folders']],['own-folder'])
        self.assertEqual([x['id'] for x in mailbox['drafts']],['own-draft'])

    def test_student_mailbox_merge_accepts_only_own_messages_to_accessible_teachers(self):
        original={'id':'incoming','sender':{'key':'teacher:t1','role':'teacher','id':'t1'},'to':['student:s1'],'subject':'Original','body':'Immuable'}
        self.data['mailboxV2']={'schemaVersion':2,'messages':[original],'states':{'student:s1':{},'student:s2':{'keep':'private'}},'drafts':[],'folders':[],'resetPending':False}
        incoming=server._student_visible_data(self.data,self.user)
        incoming['mailboxV2']['messages'][0]['body']='Tentative de falsification'
        incoming['mailboxV2']['messages'].extend([
            {'id':'valid-outgoing','sender':{'key':'student:s1','role':'student','id':'s1'},'to':['teacher:t1'],'subject':'Question','body':'Bonjour'},
            {'id':'forged-peer','sender':{'key':'student:s1','role':'student','id':'s1'},'to':['student:s2'],'subject':'Falsifié'},
            {'id':'forged-teacher','sender':{'key':'teacher:t1','role':'teacher','id':'t1'},'to':['student:s1'],'subject':'Usurpation'}
        ])
        incoming['mailboxV2']['states']={'student:s1':{'incoming':{'read':True}},'student:s2':{'incoming':{'read':True}}}
        incoming['mailboxV2']['drafts']=[{'id':'own','owner':'student:s1'},{'id':'other','owner':'student:s2'}]
        merged=server._merge_student_data(self.data,incoming,self.user)
        mailbox=merged['mailboxV2']
        by_id={x['id']:x for x in mailbox['messages']}
        self.assertEqual(by_id['incoming']['body'],'Immuable')
        self.assertIn('valid-outgoing',by_id)
        self.assertNotIn('forged-peer',by_id)
        self.assertNotIn('forged-teacher',by_id)
        self.assertEqual(mailbox['states']['student:s1'],{'incoming':{'read':True}})
        self.assertEqual(mailbox['states']['student:s2'],{'keep':'private'})
        self.assertEqual([x['id'] for x in mailbox['drafts']],['own'])

    def test_student_projection_hides_future_scheduled_evaluation_until_publish_time(self):
        now=datetime.datetime.now(datetime.timezone.utc)
        self.data['evaluations']=[
            {'id':'future','classId':'c1','published':True,'publishAt':(now+datetime.timedelta(hours=1)).isoformat(),
             'grades':[{'studentId':'s1','value':18}]},
            {'id':'due','classId':'c1','published':True,'publishAt':(now-datetime.timedelta(minutes=1)).isoformat(),
             'grades':[{'studentId':'s1','value':14}]}
        ]
        view=server._student_visible_data(self.data,self.user)
        self.assertEqual([x['id'] for x in view['evaluations']],['due'])
        self.assertEqual(view['evaluations'][0]['grades'],[{'studentId':'s1','value':14}])

    def test_scheduled_evaluation_publication_uses_exact_datetime(self):
        now=datetime.datetime(2026,11,15,12,0,tzinfo=datetime.timezone.utc)
        self.assertFalse(server._evaluation_publication_due('2026-11-15T12:01:00Z',now))
        self.assertTrue(server._evaluation_publication_due('2026-11-15T11:59:00Z',now))
        self.assertTrue(server._evaluation_publication_due('2026-11-15',now))
        self.assertFalse(server._evaluation_publication_due('not-a-date',now))

    def test_student_can_only_create_own_submission_and_cannot_change_profile_or_correction(self):
        upload_dir=os.path.join(server.UPLOADS,'submissions','s1')
        os.makedirs(upload_dir)
        file_path=os.path.join(upload_dir,'work.txt')
        with open(file_path,'w') as f: f.write('travail')
        incoming=server._student_visible_data(self.data,self.user)
        incoming['students'][0]['first']='Falsification'
        incoming['submissions']=[]  # même omis du JSON, un rendu envoyé doit rester conservé
        incoming['submissions'].append({'id':'new','studentId':'s1','lessonId':'l1','status':'submitted','files':[{'name':'submissions/s1/work.txt','url':'/data/uploads/submissions/s2/private.txt','size':7}],'corrected':True,'correctionComment':'fake'})
        incoming['submissions'].append({'id':'forged','studentId':'s2','lessonId':'l1','status':'submitted'})
        merged=server._merge_student_data(self.data,incoming,self.user)
        self.assertEqual(next(x for x in merged['students'] if x['id']=='s1')['first'],'Alice')
        created=next(x for x in merged['submissions'] if x['id']=='new')
        self.assertEqual(created['studentId'],'s1')
        self.assertEqual(created['status'],'submitted')
        self.assertEqual(created['files'][0]['url'],'/data/uploads/submissions/s1/work.txt')
        self.assertNotIn('corrected',created)
        self.assertNotIn('correctionComment',created)
        self.assertFalse(any(x['id']=='forged' for x in merged['submissions']))
        original=next(x for x in merged['submissions'] if x['id']=='old')
        self.assertEqual(original['correctionComment'],'Prof feedback')
        self.assertTrue(any(x['id']=='old' for x in merged['submissions']))

    def test_student_cannot_modify_schedule_or_lesson_content(self):
        incoming=server._student_visible_data(self.data,self.user)
        incoming['schedule'][0]['subject']='Cours falsifié'
        incoming['schedule'].append({'id':'forged-slot','classId':'c1','subject':'Cours ajouté'})
        incoming['lessons'][0]['content']='Contenu falsifié'
        incoming['lessons'].append({'id':'forged-lesson','classId':'c1','content':'Séance ajoutée'})
        merged=server._merge_student_data(self.data,incoming,self.user)
        self.assertEqual(merged['schedule'],self.data['schedule'])
        self.assertEqual(merged['lessons'],self.data['lessons'])

    def test_student_file_access_is_limited_to_referenced_own_files(self):
        folder=os.path.join(server.UPLOADS,'submissions','s1')
        os.makedirs(folder)
        own=os.path.join(folder,'own.txt')
        with open(own,'w') as f: f.write('own')
        other_folder=os.path.join(server.UPLOADS,'submissions','s2')
        os.makedirs(other_folder)
        other=os.path.join(other_folder,'other.txt')
        with open(other,'w') as f: f.write('other')
        self.data['submissions'].append({'id':'draft','studentId':'s1','lessonId':'l1','classId':'c1','status':'draft','files':[{'name':'submissions/s1/own.txt','url':'/data/uploads/submissions/s1/own.txt'}]})
        with open(server.DATA_FILE,'w',encoding='utf-8') as f: json.dump(self.data,f)
        self.assertTrue(server._student_can_access_upload(self.user,'submissions/s1/own.txt',write=False))
        self.assertTrue(server._student_can_access_upload(self.user,'submissions/s1/own.txt',write=True))
        self.assertFalse(server._student_can_access_upload(self.user,'submissions/s2/other.txt',write=False))
        self.assertFalse(server._student_can_access_upload(self.user,'submissions/s2/other.txt',write=True))


if __name__=='__main__':
    unittest.main()
