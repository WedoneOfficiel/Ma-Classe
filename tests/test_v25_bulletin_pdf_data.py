"""Server-side bulletin PDF calculations must honor publication, period, class and group."""
import copy, math, os, sys
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

def close(a,b):
    assert math.isclose(float(a),b,rel_tol=1e-9,abs_tol=1e-9), (a,b)

def run():
    db={
        'students':[
            {'id':'s1','classId':'c1','group':'A','first':'Alice','last':'Martin'},
            {'id':'s2','classId':'c1','group':'B','first':'Bob','last':'Durand'},
            {'id':'s3','classId':'c2','group':'A','first':'Charlie','last':'Autre'}
        ],
        'classes':[{'id':'c1','name':'6A'},{'id':'c2','name':'6B'}],
        'settings':{'terms':[{'id':'t1','name':'Trimestre 1','start':'2026-09-01','end':'2026-12-31'}]},
        'schedule':[{'id':'sc1','classId':'c1','subject':'Mathématiques'}],
        'evaluations':[
            {'id':'e1','classId':'c1','subject':'Mathématiques','date':'2026-10-01','published':True,'coefficient':1,'maxScore':20,'competencies':['Lecture'],'grades':[{'studentId':'s1','value':18,'competencyRatings':{'Lecture':3}},{'studentId':'s2','value':10,'competencyRatings':{'Lecture':2}}]},
            {'id':'e2','classId':'c1','subject':'Mathématiques','date':'2026-10-02','published':False,'coefficient':1,'maxScore':20,'competencies':['Brouillon'],'grades':[{'studentId':'s1','value':0,'competencyRatings':{'Brouillon':4}},{'studentId':'s2','value':0}]},
            {'id':'e3','classId':'c1','subject':'Mathématiques','group':'B','date':'2026-10-03','published':True,'coefficient':1,'maxScore':20,'competencies':['Groupe B'],'grades':[{'studentId':'s1','value':0,'competencyRatings':{'Groupe B':4}},{'studentId':'s2','value':16,'competencyRatings':{'Groupe B':4}}]},
            {'id':'e4','classId':'c1','subject':'Sciences','group':'A','date':'2026-10-04','published':True,'coefficient':1,'maxScore':20,'competencies':['Expression'],'grades':[{'studentId':'s1','value':16,'competencyRatings':{'Expression':4}}]},
            {'id':'e5','classId':'c1','subject':'Sciences','group':'B','date':'2026-10-05','published':True,'coefficient':1,'maxScore':20,'competencies':['Expression'],'grades':[{'studentId':'s2','value':8,'competencyRatings':{'Expression':2}}]},
            {'id':'e6','classId':'c1','subject':'Mathématiques','date':'2026-10-06','published':True,'publishAt':'2026-12-01','coefficient':1,'maxScore':20,'grades':[{'studentId':'s1','value':0}]},
            {'id':'e7','classId':'c2','subject':'Mathématiques','date':'2026-10-07','published':True,'coefficient':1,'maxScore':20,'grades':[{'studentId':'s1','value':0}]},
            {'id':'e8','classId':'c1','subject':'Mathématiques','date':'2027-01-02','published':True,'coefficient':1,'maxScore':20,'grades':[{'studentId':'s1','value':0}]}
            ,{'id':'e9','classId':'c1','subject':'Mathématiques','date':'2026-10-15','published':True,'coefficient':'Infinity','maxScore':20,'grades':[{'studentId':'s1','value':'NaN'}]}
        ],
        'attendance':[
            {'id':'a1','classId':'c1','date':'2026-10-10','rows':[{'studentId':'s1','status':'absent'},{'studentId':'s2','status':'present'}]},
            {'id':'a2','classId':'c2','date':'2026-10-11','rows':[{'studentId':'s1','status':'absent'}]},
            {'id':'a3','classId':'c1','date':'2027-01-02','rows':[{'studentId':'s1','status':'retard'}]},
            {'id':'a4','classId':'c1','date':'2026-10-12','rows':[{'studentId':'s1','status':'retard'}]}
        ]
    }
    bulletin={'id':'b1','studentId':'s1','classId':'c1','termId':'t1','validated':True,'published':True,'publishedAt':'2026-11-01T10:00:00Z','overall':'Très bon travail','subjectData':{'Mathématiques':{'comment':'Bon travail'}}}
    result=server._bulletin_pdf_data(db,bulletin,db['students'][0],db['classes'][0],db['settings']['terms'][0],today='2026-11-13')
    close(result['average'],17)
    close(result['overallStats']['avg'],(17+(34/3))/2)
    close(result['overallStats']['min'],34/3)
    close(result['overallStats']['max'],17)
    math_row=next(x for x in result['rows'] if x['subject']=='Mathématiques')
    science_row=next(x for x in result['rows'] if x['subject']=='Sciences')
    close(math_row['studentAverage'],18)
    close(math_row['classStats']['avg'],15.5)
    close(science_row['studentAverage'],16)
    close(science_row['classStats']['avg'],12)
    assert result['competencies']==[
        {'name':'Expression','level':'Très bien'},
        {'name':'Lecture','level':'Bien'}
    ]
    assert result['absences']==1 and result['late']==1
    assert math_row['comment']=='Bon travail'
    nonfinite=copy.deepcopy(db)
    nonfinite['evaluations'].append({'id':'e10','classId':'c1','subject':'Mathématiques','date':'2026-10-16','published':True,'coefficient':'Infinity','maxScore':20,'grades':[{'studentId':'s1','value':10}]})
    finite_result=server._bulletin_pdf_data(nonfinite,bulletin,nonfinite['students'][0],nonfinite['classes'][0],nonfinite['settings']['terms'][0],today='2026-11-13')
    close(finite_result['average'],(18+16+10)/3)
    print('OK — PDF officiel : notes publiées, date de publication, période, classe et groupes appliqués côté serveur.')

if __name__=='__main__':
    run()
