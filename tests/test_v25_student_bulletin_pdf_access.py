"""Student bulletin PDF authorization: own bulletin only, without widening roles."""
import os, sys
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server


def run():
    database={
        'classes':[{'id':'class-1','teacherIds':['teacher-1']}],
        'users':[{'id':'teacher-1','role':'teacher'}],
    }
    own={'id':'b1','studentId':'student-1','classId':'class-1','published':True,'validated':True}
    other={'id':'b2','studentId':'student-2','classId':'class-1','published':True,'validated':True}
    assert server._bulletin_pdf_access_allowed(database,{'role':'student','studentId':'student-1'},own)
    assert not server._bulletin_pdf_access_allowed(database,{'role':'student','studentId':'student-1'},other)
    assert server._bulletin_pdf_access_allowed(database,{'role':'teacher','id':'teacher-1'},own)
    assert not server._bulletin_pdf_access_allowed(database,{'role':'teacher','id':'teacher-2'},own)
    assert server._bulletin_pdf_access_allowed(database,{'role':'admin','id':'admin-1'},other)
    assert not server._bulletin_pdf_access_allowed(database,{'role':'student','studentId':'student-1'}, {'id':'b3','classId':'class-1'})
    source=open(server.__file__,encoding='utf-8').read()
    assert "'/api/bulletin-pdf'" in source
    gate="allowed_roles=('admin','teacher','student') if path in ('/api/data','/api/save','/api/upload','/api/delete-upload','/api/bulletin-pdf')"
    assert gate in source, 'student role must pass the generic POST gate for bulletin PDF only'
    print('OK — PDF bulletin : élève propriétaire autorisé, autres élèves et enseignants non affectés refusés.')

if __name__=='__main__':
    run()
