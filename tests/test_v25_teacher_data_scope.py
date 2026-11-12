import copy, os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

class TeacherDataScopeTests(unittest.TestCase):
    def setUp(self):
        self.data={
            'settings':{'schoolName':'École test'},
            'classes':[{'id':'c1','name':'6A'},{'id':'c2','name':'6B'}],
            'teachers':[{'id':'t1','classIds':['c1']},{'id':'t2','classIds':['c2']}],
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
