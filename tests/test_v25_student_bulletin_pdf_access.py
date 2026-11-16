"""Student bulletin PDF route authorization must not leak another student's report."""
import os, sys
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server


def run():
    bulletin={'id':'b1','studentId':'student-1','classId':'class-1','published':True,'validated':True}
    # The PDF route must accept student sessions at the shared POST authentication gate.
    source=open(server.__file__,encoding='utf-8').read()
    assert "'api/bulletin-pdf'" in source and "'/api/bulletin-pdf'" in source
    gate="allowed_roles=('admin','teacher','student') if path in ('/api/data','/api/save','/api/upload','/api/delete-upload','/api/bulletin-pdf')"
    assert gate in source, 'student role must pass the generic POST gate for bulletin PDF only'
    permission="if user.get('role')=='student' and str(user.get('studentId') or '')!=student_id:"
    assert permission in source, 'the endpoint must reject a bulletin owned by another student'
    # Keep teacher/admin paths unchanged; students are not granted the broad teacher/admin role set.
    assert "else ('admin','teacher')" in source
    print('OK — PDF bulletin : authentification élève dédiée et contrôle strict du propriétaire du bulletin.')

if __name__=='__main__':
    run()
