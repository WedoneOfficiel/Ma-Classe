import copy, os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

class TeacherDataScopeTests(unittest.TestCase):
    def setUp(self):
        self.data={
            'settings':{'schoolName':'École test'},
            'classes':[{'id':'c1','name':'6A','principalTeacherId':'t2'},{'id':'c2','name':'6B','principalTeacherId':'t2'}],
            'teachers':[{'id':'t1','classIds':['c1'],'subjects':['Maths']},{'id':'t2','classIds':['c2'],'subjects':['Français']}],
            'users':[{'id':'u1','role':'teacher','teacherId':'t1'},{'id':'u2','role':'teacher','teacherId':'t2'}],
            'students':[{'id':'s1','classId':'c1','first':'Alice'},{'id':'s2','classId':'c2','first':'Bob'}],
            'lessons':[{'id':'l1','classId':'c1'},{'id':'l2','classId':'c2'}],
            'evaluations':[{'id':'e1','classId':'c1','grades':[{'studentId':'s1','value':15},{'studentId':'s2','value':2}]},{'id':'e2','classId':'c2','grades':[{'studentId':'s2','value':18}]}],
            'attendance':[{'id':'a1','classId':'c1','rows':[{'studentId':'s1'},{'studentId':'s2'}]},{'id':'a2','classId':'c2','rows':[{'studentId':'s2'}]}],
            'submissions':[{'id':'sub1','lessonId':'l1','studentId':'s1'},{'id':'sub2','lessonId':'l2','studentId':'s2'}],
            'cloudItems':[], 'auditLog':[{'id':'audit'}]
        }
        self.user={'id':'u1','role':'teacher','teacherId':'t1'}

    def test_projection_only_exposes_assigned_class(self):
        view=server._teacher_visible_data(self.data,self.user)
        self.assertEqual([x['id'] for x in view['classes']],['c1'])
        self.assertEqual([x['id'] for x in view['students']],['s1'])
        self.assertEqual([x['id'] for x in view['lessons']],['l1'])
        self.assertEqual([x['id'] for x in view['evaluations']],['e1'])
        self.assertEqual([g['studentId'] for g in view['evaluations'][0]['grades']],['s1'])
        self.assertEqual([r['studentId'] for r in view['attendance'][0]['rows']],['s1'])
        self.assertEqual([x['id'] for x in view['submissions']],['sub1'])
        self.assertEqual(view['users'],[self.data['users'][0]])
        self.assertEqual(view['auditLog'],[])

    def test_teacher_projection_never_exposes_password_material(self):
        data=copy.deepcopy(self.data)
        data['users'][0].update({'passwordHash':'pbkdf2_sha256$310000$salt$digest','password':'legacy-secret'})
        view=server._teacher_visible_data(data,self.user)
        self.assertEqual(len(view['users']),1)
        self.assertEqual(view['users'][0]['id'],'u1')
        self.assertNotIn('passwordHash',view['users'][0])
        self.assertNotIn('password',view['users'][0])

    def test_teacher_save_merges_only_assigned_class(self):
        view=server._teacher_visible_data(copy.deepcopy(self.data),self.user)
        view['students'][0]['first']='Alicia'
        view['students'].append({'id':'s3','classId':'c1','first':'Chloé'})
        view['lessons'].append({'id':'l3','classId':'c1','title':'Nouveau'})
        merged=server._merge_teacher_data(self.data,view,self.user)
        self.assertEqual(next(x for x in merged['students'] if x['id']=='s1')['first'],'Alicia')
        self.assertTrue(any(x['id']=='s3' for x in merged['students']))
        self.assertTrue(any(x['id']=='s2' for x in merged['students']))
        self.assertTrue(any(x['id']=='l2' for x in merged['lessons']))
        self.assertEqual(merged['classes'],self.data['classes'])
        self.assertEqual(merged['users'],self.data['users'])
        self.assertEqual(merged['auditLog'],self.data['auditLog'])

    def test_teacher_cannot_create_record_for_unassigned_class(self):
        view=server._teacher_visible_data(copy.deepcopy(self.data),self.user)
        view['lessons'].append({'id':'forged','classId':'c2','title':'Nope'})
        merged=server._merge_teacher_data(self.data,view,self.user)
        self.assertFalse(any(x.get('id')=='forged' for x in merged['lessons']))

    def test_teacher_cannot_inject_foreign_student_into_nested_records(self):
        view=server._teacher_visible_data(copy.deepcopy(self.data),self.user)
        view['evaluations'][0]['grades'].append({'studentId':'s2','value':20})
        view['attendance'][0]['rows'].append({'studentId':'s2','status':'absent'})
        view['submissions'].append({'id':'forged-sub','lessonId':'l1','studentId':'s2'})
        merged=server._merge_teacher_data(self.data,view,self.user)
        self.assertEqual([g['studentId'] for g in next(x for x in merged['evaluations'] if x['id']=='e1')['grades']],['s1'])
        self.assertEqual([r['studentId'] for r in next(x for x in merged['attendance'] if x['id']=='a1')['rows']],['s1'])
        self.assertFalse(any(x.get('id')=='forged-sub' for x in merged['submissions']))

    def test_non_principal_teacher_cannot_validate_publish_or_change_overall(self):
        data=copy.deepcopy(self.data)
        data['bulletins']=[{'id':'b1','studentId':'s1','classId':'c1','termId':'t1','subjectData':{'Maths':{'comment':'Ancienne appréciation'}},'overall':'Avis du PP','validated':False,'published':False}]
        view=copy.deepcopy(server._teacher_visible_data(data,self.user))
        view['bulletins'][0].update({'overall':'Avis falsifié','validated':True,'validatedAt':'2026-11-12','published':True,'publishedAt':'2026-11-12'})
        view['bulletins'][0]['subjectData']['Maths']['comment']='Appréciation modifiée'
        view['bulletins'][0]['classId']='c2'
        view['bulletins'][0]['studentId']='s2'
        merged=server._merge_teacher_data(data,view,self.user)
        saved=merged['bulletins'][0]
        self.assertEqual(saved['classId'],'c1')
        self.assertEqual(saved['studentId'],'s1')
        self.assertEqual(saved['overall'],'Avis du PP')
        self.assertFalse(saved['validated'])
        self.assertFalse(saved['published'])
        self.assertNotIn('publishedAt',saved)
        self.assertEqual(saved['subjectData']['Maths']['comment'],'Appréciation modifiée')

    def test_non_principal_teacher_cannot_delete_published_bulletin(self):
        data=copy.deepcopy(self.data)
        original={'id':'b1','studentId':'s1','classId':'c1','termId':'t1','subjectData':{'Maths':{'comment':'Officiel'}},'overall':'Avis officiel','validated':True,'published':True,'publishedAt':'2026-11-12'}
        data['bulletins']=[original]
        view=server._teacher_visible_data(data,self.user)
        view['bulletins']=[]
        merged=server._merge_teacher_data(data,view,self.user)
        self.assertEqual(merged['bulletins'],[original])

    def test_non_principal_teacher_cannot_edit_published_bulletin(self):
        data=copy.deepcopy(self.data)
        original={'id':'b1','studentId':'s1','classId':'c1','termId':'t1','subjectData':{'Maths':{'comment':'Officiel'}},'overall':'Avis officiel','validated':True,'published':True,'publishedAt':'2026-11-12'}
        data['bulletins']=[original]
        view=copy.deepcopy(server._teacher_visible_data(data,self.user))
        view['bulletins'][0]['overall']='Falsifié'
        view['bulletins'][0]['subjectData']['Maths']['comment']='Falsifié'
        merged=server._merge_teacher_data(data,view,self.user)
        self.assertEqual(merged['bulletins'][0],original)

    def test_teacher_cannot_move_existing_evaluation_to_another_assigned_class(self):
        data=copy.deepcopy(self.data)
        data['classes'][1]['teacherIds']=['t1']
        data['teachers'][0]['classIds']=['c1','c2']
        data['evaluations']=[{'id':'e1','classId':'c1','subject':'Maths','grades':[{'studentId':'s1','value':15}]}]
        user={'id':'u1','role':'teacher','teacherId':'t1'}
        view=copy.deepcopy(server._teacher_visible_data(data,user))
        view['evaluations'][0]['classId']='c2'
        view['evaluations'][0]['grades'].append({'studentId':'s2','value':20})
        merged=server._merge_teacher_data(data,view,user)
        saved=merged['evaluations'][0]
        self.assertEqual(saved['classId'],'c1')
        self.assertEqual(saved['grades'],[{'studentId':'s1','value':15}])

    def test_teacher_cannot_add_other_assigned_class_student_to_evaluation(self):
        data=copy.deepcopy(self.data)
        data['classes'][1]['teacherIds']=['t1']
        data['teachers'][0]['classIds']=['c1','c2']
        user={'id':'u1','role':'teacher','teacherId':'t1'}
        data['evaluations']=[{'id':'e1','classId':'c1','grades':[{'studentId':'s1','value':15}]}]
        view=copy.deepcopy(server._teacher_visible_data(data,user))
        view['evaluations'][0]['grades'].append({'studentId':'s2','value':20})
        merged=server._merge_teacher_data(data,view,user)
        self.assertEqual([g['studentId'] for g in merged['evaluations'][0]['grades']],['s1'])

    def test_teacher_can_only_edit_assigned_bulletin_subjects(self):
        data=copy.deepcopy(self.data)
        data['bulletins']=[{'id':'b1','studentId':'s1','classId':'c1','termId':'t1','subjectData':{'Maths':{'comment':'Ancien Maths'},'Français':{'comment':'Ancien Français'}},'overall':'Avis PP','validated':False,'published':False}]
        view=copy.deepcopy(server._teacher_visible_data(data,self.user))
        view['bulletins'][0]['subjectData']['Maths']['comment']='Nouveau Maths'
        view['bulletins'][0]['subjectData']['Français']['comment']='Falsification Français'
        view['bulletins'][0]['subjectData']['Histoire']={'comment':'Matière non affectée'}
        merged=server._merge_teacher_data(data,view,self.user)
        saved=merged['bulletins'][0]['subjectData']
        self.assertEqual(saved['Maths']['comment'],'Nouveau Maths')
        self.assertEqual(saved['Français']['comment'],'Ancien Français')
        self.assertNotIn('Histoire',saved)

    def test_teacher_cannot_modify_global_settings(self):
        view=server._teacher_visible_data(copy.deepcopy(self.data),self.user)
        view['settings']={'schoolName':'Falsifié'}
        merged=server._merge_teacher_data(self.data,view,self.user)
        self.assertEqual(merged['settings'],{'schoolName':'École test'})


    def test_projection_exposes_only_explicitly_shared_top_level_keys(self):
        data=copy.deepcopy(self.data)
        data.update({
            'subjects':[{'id':'math'}],
            'competencyLibrary':[{'id':'comp'}],
            'evaluationTemplates':[{'id':'template'}],
            'evaluationCriteriaLibrary':[{'id':'criteria'}],
            'settings':{'rooms':['Salle A'],'termMode':'trimestres','terms':[],'competencyLevels':['Fragile','Bien'],'privateApiKey':'do-not-expose'},
            'privateFutureCollection':[{'secret':'private'}],
            'secretConfig':{'apiToken':'do-not-expose'}
        })
        view=server._teacher_visible_data(data,self.user)
        self.assertEqual(view['subjects'],data['subjects'])
        self.assertEqual(view['competencyLibrary'],data['competencyLibrary'])
        self.assertEqual(view['evaluationTemplates'],data['evaluationTemplates'])
        self.assertEqual(view['evaluationCriteriaLibrary'],data['evaluationCriteriaLibrary'])
        self.assertEqual(view['settings'],{'rooms':['Salle A'],'termMode':'trimestres','terms':[],'competencyLevels':['Fragile','Bien']})
        self.assertNotIn('privateApiKey',view['settings'])
        self.assertNotIn('privateFutureCollection',view)
        self.assertNotIn('secretConfig',view)

if __name__=='__main__': unittest.main()
