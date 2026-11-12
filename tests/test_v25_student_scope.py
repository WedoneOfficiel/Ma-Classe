"""Tests de cloisonnement des comptes élèves et de leurs rendus."""
import json
import os
import tempfile
import unittest

import server


class StudentScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.old_data=server.DATA_FILE
        self.old_uploads=server.UPLOADS
        server.DATA_FILE=os.path.join(self.tmp.name,'maclasse.json')
        server.UPLOADS=os.path.join(self.tmp.name,'uploads')
        os.makedirs(server.UPLOADS)
        self.user={'id':'u1','role':'student','studentId':'s1','name':'Alice'}
        self.data={
            'users':[{'id':'u1','role':'student','studentId':'s1','passwordHash':'secret'}],
            'classes':[{'id':'c1','name':'6A'},{'id':'c2','name':'6B'}],
            'students':[{'id':'s1','classId':'c1','first':'Alice','notes':'note interne confidentielle'},{'id':'s2','classId':'c1','first':'Bob'},{'id':'s3','classId':'c2','first':'Chloé'}],
            'schedule':[{'id':'slot1','classId':'c1','teacherId':'t1'},{'id':'slot2','classId':'c2','teacherId':'t2'}],
            'teachers':[{'id':'t1','first':'Prof A'},{'id':'t2','first':'Prof B'}],
            'lessons':[{'id':'l1','classId':'c1','homework':{'requiresSubmission':True}},{'id':'l1b','classId':'c1','homework':{'requiresSubmission':True}},{'id':'l2','classId':'c2','homework':{'requiresSubmission':True}}],
            'evaluations':[{'id':'e1','classId':'c1','published':True,'grades':[{'studentId':'s1','value':14},{'studentId':'s2','value':7}]},{'id':'e2','classId':'c1','published':False,'grades':[{'studentId':'s1','value':19}]}],
            'attendance':[{'id':'a1','classId':'c1','rows':[{'studentId':'s1','status':'present'},{'studentId':'s2','status':'absent'}]}],
            'bulletins':[{'id':'b1','studentId':'s1','classId':'c1','validated':True,'published':True},{'id':'b2','studentId':'s2','classId':'c1','validated':True,'published':True}],
            'submissions':[{'id':'old','studentId':'s1','lessonId':'l1b','classId':'c1','status':'submitted','corrected':True,'correctionComment':'Prof feedback'},{'id':'other','studentId':'s2','lessonId':'l1','classId':'c1','status':'submitted'}],
            'attachments':[],'conversations':[{'id':'private','participantIds':['s2']}],
            'cloudItems':[{'id':'private','ownerId':'s2'}],'notifications':[],'settings':{'schoolName':'private','terms':[]}
        }
        with open(server.DATA_FILE,'w',encoding='utf-8') as f: json.dump(self.data,f)

    def tearDown(self):
        server.DATA_FILE=self.old_data
        server.UPLOADS=self.old_uploads
        self.tmp.cleanup()

    def test_projection_contains_only_own_student_data_and_published_results(self):
        view=server._student_visible_data(self.data,self.user)
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
