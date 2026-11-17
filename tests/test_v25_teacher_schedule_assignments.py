"""Teacher assignment management is restricted to the teacher's own schedule slots."""
import copy, os, sys
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server


def fixture():
    return {
        'users':[
            {'id':'teacher-1','role':'teacher','first':'Alice','last':'Martin','active':True},
            {'id':'teacher-2','role':'teacher','first':'Benoit','last':'Durand','active':True},
            {'id':'admin-1','role':'admin','active':True},
        ],
        'classes':[
            {'id':'class-1','teacherIds':['teacher-1']},
            {'id':'class-2','teacherIds':['teacher-2']},
        ],
        'schedule':[
            {'id':'slot-1','classId':'class-1','subject':'Mathématiques','teacherId':'teacher-1','teacherIds':['teacher-1']},
            {'id':'slot-2','classId':'class-2','subject':'Français','teacherId':'teacher-2','teacherIds':['teacher-2']},
        ],
        'teacherAssignments':[
            {'id':'admin-assignment','scheduleId':'slot-1','classId':'class-1','subject':'Mathématiques','teacherId':'teacher-2','startDate':'2026-11-01','endDate':'2026-12-01','type':'replacement','supersedesTeacherId':'teacher-1'}
        ],
        'students':[], 'lessons':[], 'evaluations':[], 'attendance':[], 'bulletins':[],
        'attachments':[], 'submissions':[], 'conversations':[], 'cloudItems':[],
        'notifications':[], 'mailFolders':[], 'settings':{}
    }


def run():
    current=fixture()
    incoming=copy.deepcopy(current)
    incoming['teacherAssignments'].append({
        'id':'teacher-assignment','scheduleId':'slot-1','classId':'class-1',
        'subject':'Mathématiques','teacherId':'teacher-2','startDate':'2026-11-20',
        'endDate':'2026-12-20','type':'replacement','supersedesTeacherId':'teacher-1'
    })
    merged=server._merge_teacher_data(current,incoming,{'id':'teacher-1','role':'teacher'})
    created=next(x for x in merged['teacherAssignments'] if x['id']=='teacher-assignment')
    assert created['createdBy']=='teacher-1'
    assert created['classId']=='class-1' and created['subject']=='Mathématiques'
    assert any(x['id']=='admin-assignment' for x in merged['teacherAssignments']), 'teacher must not delete a Direction assignment'

    malicious=copy.deepcopy(current)
    malicious['teacherAssignments'].append({
        'id':'forbidden-assignment','scheduleId':'slot-2','classId':'class-2',
        'subject':'Français','teacherId':'teacher-1','startDate':'2026-11-20',
        'endDate':'2026-12-20','type':'replacement','supersedesTeacherId':'teacher-2'
    })
    merged=server._merge_teacher_data(current,malicious,{'id':'teacher-1','role':'teacher'})
    assert not any(x['id']=='forbidden-assignment' for x in merged['teacherAssignments'])
    self_replace=copy.deepcopy(current)
    self_replace['teacherAssignments'].append({
        'id':'self-replacement','scheduleId':'slot-1','classId':'class-1',
        'subject':'Mathématiques','teacherId':'teacher-1','startDate':'2026-11-20',
        'endDate':'2026-12-20','type':'replacement','supersedesTeacherId':'teacher-1'
    })
    merged=server._merge_teacher_data(current,self_replace,{'id':'teacher-1','role':'teacher'})
    assert not any(x['id']=='self-replacement' for x in merged['teacherAssignments'])

    visible=server._teacher_visible_data(fixture(),{'id':'teacher-1','role':'teacher'})
    assert {x['id'] for x in visible['teachers']}=={'teacher-1','teacher-2'}
    assert any(x['id']=='admin-assignment' for x in visible['teacherAssignments'])
    print('OK — affectations limitées aux cours du professeur, annuaire minimal et protection des affectations Direction.')


if __name__=='__main__':
    run()
