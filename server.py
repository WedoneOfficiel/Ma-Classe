#!/usr/bin/env python3
import json, os, shutil, re, time, glob, urllib.request, urllib.error, datetime, math, unicodedata, threading, zipfile, io, secrets, hashlib, hmac, tempfile, stat, ipaddress
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

APP_VERSION='25.0.7'
HOST=os.environ.get('MACLASSE_HOST','127.0.0.1')
PORT=int(os.environ.get('MACLASSE_PORT','8765'))
DATA_LOCK=threading.RLock()
SESSIONS={}
LOGIN_ATTEMPTS={}
SESSION_TTL=12*60*60
ROOT=os.path.dirname(os.path.abspath(__file__))
BACKUP_RETENTION_DAYS=30
BACKUP_INTERVAL_SECONDS=6*60*60
DATA_DIR=os.path.join(ROOT,'data')
DATA_FILE=os.path.join(DATA_DIR,'maclasse.json')
UPLOADS=os.path.join(DATA_DIR,'uploads')
os.makedirs(UPLOADS,exist_ok=True)
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE,'w',encoding='utf-8') as f: json.dump({},f,ensure_ascii=False)

PASSWORD_KDF_ITERATIONS=310000
PASSWORD_KDF_NAME='pbkdf2_sha256'

def _password_hash(password):
    salt=secrets.token_bytes(16)
    digest=hashlib.pbkdf2_hmac('sha256',password.encode('utf-8'),salt,PASSWORD_KDF_ITERATIONS)
    return f"{PASSWORD_KDF_NAME}${PASSWORD_KDF_ITERATIONS}${salt.hex()}${digest.hex()}"

def _password_verify(password, stored):
    stored=str(stored or '')
    if stored.startswith(PASSWORD_KDF_NAME+'$'):
        try:
            _,iterations,salt_hex,digest_hex=stored.split('$',3)
            iterations=int(iterations)
            if iterations<100000 or iterations>2000000:return False,False
            salt=bytes.fromhex(salt_hex); expected=bytes.fromhex(digest_hex)
            actual=hashlib.pbkdf2_hmac('sha256',password.encode('utf-8'),salt,iterations)
            return hmac.compare_digest(actual,expected),False
        except Exception:return False,False
    # Migration transparente des anciens SHA-256 non salés.
    legacy=hashlib.sha256(password.encode('utf-8')).hexdigest()
    return hmac.compare_digest(stored,legacy),True

def _ensure_bootstrap_accounts():
    try:
        with open(DATA_FILE,encoding='utf-8') as f: data=json.load(f)
    except Exception: data={}
    if not isinstance(data,dict): data={}
    users=data.get('users') if isinstance(data.get('users'),list) else []
    if not any(isinstance(u,dict) and u.get('role')=='admin' for u in users):
        users.append({'id':'u-admin','role':'admin','username':'admin','passwordHash':hashlib.sha256(b'admin').hexdigest(),'name':'Direction','active':True})
    if not any(isinstance(u,dict) and u.get('role')=='teacher' for u in users):
        users.append({'id':'u-teacher-local','role':'teacher','username':'enseignant','passwordHash':hashlib.sha256(b'enseignant').hexdigest(),'teacherId':'teacher-local','name':'Enseignant','active':True})
    data['users']=users
    with open(DATA_FILE,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)

_ensure_bootstrap_accounts()











def _safe_upload_path(relative):
    raw=str(relative or '').replace('\\','/')
    if not raw or raw.startswith('/') or re.match(r'^[A-Za-z]:',raw):
        raise ValueError('Chemin invalide')
    parts=raw.split('/')
    if any(part in ('.','..') for part in parts):
        raise ValueError('Chemin invalide')
    root=os.path.realpath(UPLOADS)
    target=os.path.realpath(os.path.join(root,*[part for part in parts if part]))
    if os.path.commonpath([target,root])!=root:
        raise ValueError('Chemin invalide')
    return target

def _uploads_relative(path):
    """Chemin relatif canonique, y compris si macOS résout /var vers /private/var."""
    root=os.path.realpath(UPLOADS)
    target=os.path.realpath(path)
    if os.path.commonpath([target,root])!=root:
        raise ValueError('Chemin hors du stockage des téléversements')
    return os.path.relpath(target,root).replace(os.sep,'/')

def _restore_backup_archive(raw_bytes):
    """Restore an authenticated full ZIP snapshot without trusting its paths."""
    if not isinstance(raw_bytes, (bytes, bytearray)) or not raw_bytes:
        raise ValueError('Archive vide.')
    stage_root = tempfile.mkdtemp(prefix='maclasse-restore-', dir=DATA_DIR)
    stage_data = os.path.join(stage_root, 'data')
    stage_uploads = os.path.join(stage_data, 'uploads')
    os.makedirs(stage_uploads, exist_ok=True)
    old_uploads = os.path.join(stage_root, 'uploads-before-restore')
    old_json = os.path.join(stage_root, 'maclasse-before-restore.json')
    moved_old_uploads = False
    installed_new_uploads = False
    try:
        try:
            archive = zipfile.ZipFile(io.BytesIO(raw_bytes), 'r')
        except (zipfile.BadZipFile, OSError) as exc:
            raise ValueError('Archive ZIP invalide.') from exc
        with archive:
            infos = archive.infolist()
            if not infos or len(infos) > 10000:
                raise ValueError('Archive vide ou contenant trop d’éléments.')
            seen = set()
            total_size = 0
            has_database = False
            for info in infos:
                name = info.filename.replace('\\', '/')
                if name in seen:
                    raise ValueError('Archive contenant des chemins en double.')
                seen.add(name)
                parts = name.split('/')
                if name.startswith('/') or any(part in ('', '.', '..') for part in parts if part != '') or re.match(r'^[A-Za-z]:', name):
                    raise ValueError('Chemin dangereux détecté dans l’archive.')
                if name.rstrip('/') != 'data/maclasse.json' and not name.startswith('data/uploads/'):
                    if info.is_dir() and name.rstrip('/') in ('data', 'data/uploads'):
                        continue
                    raise ValueError('L’archive contient un élément inattendu.')
                mode = (info.external_attr >> 16) & 0xFFFF
                if stat.S_ISLNK(mode):
                    raise ValueError('Les liens symboliques sont interdits dans une sauvegarde.')
                if info.flag_bits & 0x1:
                    raise ValueError('Les archives chiffrées ne sont pas acceptées.')
                total_size += info.file_size
                if total_size > 500 * 1024 * 1024:
                    raise ValueError('Archive décompressée trop volumineuse (500 Mo maximum).')
                if info.file_size > 0 and info.compress_size == 0:
                    raise ValueError('Archive invalide.')
                if info.compress_size and info.file_size / info.compress_size > 200:
                    raise ValueError('Taux de compression anormal détecté.')
                if name == 'data/maclasse.json':
                    has_database = True
                if info.is_dir():
                    continue
                if name == 'data/maclasse.json':
                    destination = os.path.join(stage_data, 'maclasse.json')
                elif name.startswith('data/uploads/'):
                    relative = name[len('data/uploads/'):]
                    if not relative or any(part in ('', '.', '..') for part in relative.split('/')):
                        raise ValueError('Chemin de fichier invalide dans l’archive.')
                    destination = os.path.join(stage_uploads, *relative.split('/'))
                else:
                    raise ValueError('Fichier inattendu dans l’archive.')
                os.makedirs(os.path.dirname(destination), exist_ok=True)
                with archive.open(info, 'r') as source, open(destination, 'xb') as target:
                    shutil.copyfileobj(source, target)
            if not has_database:
                raise ValueError('La sauvegarde ne contient pas data/maclasse.json.')
        staged_json = os.path.join(stage_data, 'maclasse.json')
        try:
            with open(staged_json, encoding='utf-8') as handle:
                restored = json.load(handle)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError('Le fichier de données de la sauvegarde est invalide.') from exc
        if not isinstance(restored, dict):
            raise ValueError('La base de données doit être un objet JSON.')
        for key in ('classes', 'students', 'teachers', 'users'):
            if key in restored and not isinstance(restored[key], list):
                raise ValueError(f'La collection {key} est invalide.')
        os.makedirs(DATA_DIR, exist_ok=True)
        if os.path.exists(UPLOADS):
            os.replace(UPLOADS, old_uploads)
            moved_old_uploads = True
        os.replace(stage_uploads, UPLOADS)
        installed_new_uploads = True
        shutil.copy2(DATA_FILE, old_json) if os.path.exists(DATA_FILE) else None
        os.replace(staged_json, DATA_FILE)
        return {'classes': len(restored.get('classes', []) or []), 'students': len(restored.get('students', []) or []), 'files': sum(1 for base, _, files in os.walk(UPLOADS) for _ in files)}
    except Exception:
        # Roll back the filesystem pair if any final replacement failed.
        try:
            if installed_new_uploads and os.path.exists(UPLOADS):
                shutil.rmtree(UPLOADS)
            if moved_old_uploads and os.path.exists(old_uploads):
                os.replace(old_uploads, UPLOADS)
            if os.path.exists(old_json):
                os.replace(old_json, DATA_FILE)
        except OSError:
            pass
        raise
    finally:
        shutil.rmtree(stage_root, ignore_errors=True)


def _database_revision():
    with open(DATA_FILE,'rb') as f: raw=f.read()
    return hashlib.sha256(raw).hexdigest()


def _load_database():
    try:
        with DATA_LOCK:
            with open(DATA_FILE,encoding='utf-8') as f: data=json.load(f)
        return data if isinstance(data,dict) else {}
    except Exception:
        return {}


def _bulletin_pdf_data(database, bulletin, student_record, class_record, term_record, today=None):
    """Build the printable bulletin from canonical server-side records only."""
    today=today or datetime.date.today().isoformat()
    class_id=str(bulletin.get('classId') or '')
    student_id=str(bulletin.get('studentId') or '')
    term=term_record if isinstance(term_record,dict) else None
    def in_term(e, allow_missing_date=False):
        date=str(e.get('date') or '')
        if not term: return True
        if not date and allow_missing_date: return True
        if not date: return False
        return (not term.get('start') or date>=str(term.get('start'))) and (not term.get('end') or date<=str(term.get('end')))
    def grade_on20(e, grade):
        if not isinstance(grade,dict) or grade.get('value') in ('',None): return None
        try: raw=float(str(grade.get('value')).strip().replace(',','.'))
        except (TypeError,ValueError): return None
        try: maximum=float(e.get('maxScore') or 20)
        except (TypeError,ValueError): maximum=20
        if maximum<=0: maximum=20
        if raw<0 or raw>maximum: return None
        return raw/maximum*20
    def coefficient(e):
        try: value=float(e.get('coefficient') or 1)
        except (TypeError,ValueError): value=1
        return value if value>0 else 1
    def average(items,sid):
        weighted=weight=0.0
        for e in items:
            grade=next((g for g in e.get('grades',[]) or [] if isinstance(g,dict) and str(g.get('studentId'))==str(sid)),None)
            value=grade_on20(e,grade)
            if value is None: continue
            factor=coefficient(e); weighted+=value*factor; weight+=factor
        return weighted/weight if weight else '—'
    evaluations=[e for e in database.get('evaluations',[]) or [] if isinstance(e,dict)]
    students=[s for s in database.get('students',[]) or [] if isinstance(s,dict) and str(s.get('classId') or '')==class_id]
    subjects=sorted({str(e.get('subject')).strip() for e in evaluations if str(e.get('classId') or '')==class_id and str(e.get('subject') or '').strip()} | {str(x.get('subject')).strip() for x in database.get('schedule',[]) or [] if isinstance(x,dict) and str(x.get('classId') or '')==class_id and str(x.get('subject') or '').strip()},key=lambda x:x.casefold())
    def subject_average(sid,subject):
        st=next((x for x in students if str(x.get('id'))==str(sid)),{})
        eligible=[]
        for e in evaluations:
            if str(e.get('classId') or '')!=class_id or str(e.get('subject') or '')!=subject: continue
            if e.get('published') is False or (str(e.get('publishAt') or '') and str(e.get('publishAt'))>today): continue
            if e.get('group') and str(e.get('group'))!=str(st.get('group') or ''): continue
            if not in_term(e): continue
            eligible.append(e)
        return average(eligible,sid)
    def stats(values):
        nums=[]
        for value in values:
            try:
                number=float(value)
                if math.isfinite(number): nums.append(number)
            except (TypeError,ValueError): pass
        return {'avg':sum(nums)/len(nums) if nums else '—','min':min(nums) if nums else '—','max':max(nums) if nums else '—'}
    rows=[]
    subject_data=bulletin.get('subjectData',{}) if isinstance(bulletin.get('subjectData'),dict) else {}
    for subject in subjects:
        record=subject_data.get(subject,{})
        rows.append({'subject':subject,'studentAverage':subject_average(student_id,subject),'classStats':stats([subject_average(st.get('id'),subject) for st in students]),'comment':record.get('comment','') if isinstance(record,dict) else ''})
    overall_evaluations=[e for e in evaluations if str(e.get('classId') or '')==class_id and in_term(e)]
    overall_average=average(overall_evaluations,student_id)
    overall_stats=stats([average(overall_evaluations,st.get('id')) for st in students])
    competency_names=set(); competency_ratings={}
    for e in evaluations:
        if str(e.get('classId') or '')!=class_id or not in_term(e,allow_missing_date=True): continue
        for name in e.get('competencies',[]) or []:
            if not isinstance(name,str) or not name: continue
            competency_names.add(name)
            for grade in e.get('grades',[]) or []:
                if not isinstance(grade,dict) or str(grade.get('studentId'))!=student_id: continue
                try: level=float((grade.get('competencyRatings') or {}).get(name))
                except (TypeError,ValueError): continue
                if 1<=level<=4: competency_ratings.setdefault(name,[]).append((str(e.get('date') or ''),level))
    labels={1:'Insuffisant',2:'Fragile',3:'Bien',4:'Très bien'}
    competencies=[{'name':name,'level':labels.get(sorted(competency_ratings.get(name,[]),key=lambda x:x[0],reverse=True)[0][1],'—') if competency_ratings.get(name) else '—'} for name in sorted(competency_names,key=lambda x:x.casefold())]
    absences=late=0
    for sheet in database.get('attendance',[]) or []:
        if not isinstance(sheet,dict) or str(sheet.get('classId') or '')!=class_id: continue
        date=str(sheet.get('date') or '')
        if term and ((term.get('start') and date<str(term.get('start'))) or (term.get('end') and date>str(term.get('end')))): continue
        for row in sheet.get('rows',[]) or []:
            if not isinstance(row,dict) or str(row.get('studentId'))!=student_id: continue
            if row.get('status')=='absent': absences+=1
            elif row.get('status')=='retard': late+=1
    return {'student':{'name':' '.join(str(student_record.get(k) or '').strip() for k in ('first','last')).strip()},'className':str(class_record.get('name') or '—'),'termName':str((term or {}).get('name') or 'Période'),'published':bulletin.get('published') is True,'publishedAt':str(bulletin.get('publishedAt') or ''),'overall':str(bulletin.get('overall') or ''),'average':overall_average,'overallStats':overall_stats,'rows':rows,'competencies':competencies,'absences':absences,'late':late}


def _teacher_class_ids(data,user):
    tid=str(user.get('teacherId') or '')
    teacher=next((t for t in data.get('teachers',[]) or [] if isinstance(t,dict) and str(t.get('id'))==tid),None)
    return {str(x) for x in (teacher or {}).get('classIds',[]) or []}


def _teacher_subject_keys(data,user):
    tid=str(user.get('teacherId') or '')
    teacher=next((t for t in data.get('teachers',[]) or [] if isinstance(t,dict) and str(t.get('id'))==tid),None)
    subjects=(teacher or {}).get('subjects',[]) or []
    return {str(x).strip().casefold() for x in subjects if str(x).strip()}


# Isolation des données scolaires : une session professeur ne reçoit et ne remplace
# que les enregistrements des classes qui lui sont affectées.
def _teacher_record_class_id(record, data, collection=''):
    if not isinstance(record,dict): return ''
    cid=str(record.get('classId') or '')
    if cid: return cid
    sid=str(record.get('studentId') or '')
    if sid:
        student=next((x for x in data.get('students',[]) or [] if isinstance(x,dict) and str(x.get('id'))==sid),None)
        if student: return str(student.get('classId') or '')
    lid=str(record.get('lessonId') or '')
    if lid:
        lesson=next((x for x in data.get('lessons',[]) or [] if isinstance(x,dict) and str(x.get('id'))==lid),None)
        if lesson: return str(lesson.get('classId') or '')
    return ''


def _mail_user_key(role, ident):
    return f"{role}:{ident}"


def _teacher_visible_mailbox(mailbox, user, data):
    """Projection stricte de la messagerie : messages adressés/partagés au professeur."""
    if not isinstance(mailbox,dict): return {}
    tid=str(user.get('teacherId') or '')
    me=_mail_user_key('teacher',tid)
    messages=mailbox.get('messages') if isinstance(mailbox.get('messages'),list) else []
    visible=[]
    for message in messages:
        if not isinstance(message,dict): continue
        sender=(message.get('sender') or {}).get('key') if isinstance(message.get('sender'),dict) else ''
        recipients=[x for field in ('to','cc','bcc','sharedWith') for x in (message.get(field) or []) if isinstance(x,str)]
        if sender==me or me in recipients:
            if sender==me:
                visible.append(message)
            else:
                # Un destinataire ne doit jamais connaître les autres destinataires BCC.
                safe_message=dict(message)
                safe_message['bcc']=[]
                visible.append(safe_message)
    states=mailbox.get('states') if isinstance(mailbox.get('states'),dict) else {}
    folders=mailbox.get('folders') if isinstance(mailbox.get('folders'),list) else []
    drafts=mailbox.get('drafts') if isinstance(mailbox.get('drafts'),list) else []
    return {
        'schemaVersion':mailbox.get('schemaVersion',2),
        'messages':visible,
        'states':{me:states.get(me,{})} if isinstance(states.get(me,{}),dict) else {me:{}},
        'folders':[x for x in folders if isinstance(x,dict) and str(x.get('owner') or x.get('user') or '')==me],
        'drafts':[x for x in drafts if isinstance(x,dict) and str(x.get('owner') or '')==me],
        'resetPending':bool(mailbox.get('resetPending',False)),
    }


def _teacher_merge_mailbox(current, incoming, user, data):
    """Fusionne uniquement la boîte personnelle du professeur; les messages envoyés sont immuables."""
    old=current.get('mailboxV2') if isinstance(current.get('mailboxV2'),dict) else {}
    new=incoming.get('mailboxV2') if isinstance(incoming.get('mailboxV2'),dict) else {}
    tid=str(user.get('teacherId') or '')
    me=_mail_user_key('teacher',tid)
    old_messages=old.get('messages') if isinstance(old.get('messages'),list) else []
    new_messages=new.get('messages') if isinstance(new.get('messages'),list) else []
    old_by_id={str(x.get('id')):x for x in old_messages if isinstance(x,dict) and x.get('id')}
    new_by_id={str(x.get('id')):x for x in new_messages if isinstance(x,dict) and x.get('id')}
    result_messages=[]
    for ident, original in old_by_id.items():
        updated=new_by_id.get(ident)
        item=dict(original)
        sender=(original.get('sender') or {}).get('key') if isinstance(original.get('sender'),dict) else ''
        visible=sender==me or any(me in (original.get(k) or []) for k in ('to','cc','bcc','sharedWith'))
        if visible and updated is not None:
            # Seul le masquage dans sa propre boîte est modifiable sur un message existant.
            hidden=list(original.get('hiddenFor') or [])
            if me in (updated.get('hiddenFor') or []) and me not in hidden: hidden.append(me)
            if me not in (updated.get('hiddenFor') or []): hidden=[x for x in hidden if x!=me]
            item['hiddenFor']=hidden
        result_messages.append(item)
    allowed_classes=_teacher_class_ids(data,user)
    valid_teachers={str(x.get('id')) for x in data.get('teachers',[]) or [] if isinstance(x,dict)}
    valid_students={str(x.get('id')) for x in data.get('students',[]) or [] if isinstance(x,dict) and str(x.get('classId') or '') in allowed_classes}
    for ident,message in new_by_id.items():
        if ident in old_by_id: continue
        sender=message.get('sender') if isinstance(message.get('sender'),dict) else {}
        if sender.get('key')!=me or sender.get('role')!='teacher' or str(sender.get('id') or '')!=tid: continue
        recipients=[x for field in ('to','cc','bcc','sharedWith') for x in (message.get(field) or []) if isinstance(x,str)]
        valid=True
        for recipient in recipients:
            role,sep,recipient_id=recipient.partition(':')
            if not sep or (role=='teacher' and recipient_id not in valid_teachers) or (role=='student' and recipient_id not in valid_students) or role not in ('teacher','student'):
                valid=False; break
        if not valid: continue
        # Les pièces jointes de messagerie doivent rester dans le dossier de l'expéditeur.
        for attachment in message.get('attachments') or []:
            if not isinstance(attachment,dict): continue
            url=str(attachment.get('url') or '').replace('\\','/')
            if '/data/uploads/' in url:
                rel=url.split('/data/uploads/',1)[1]
                if not rel.startswith(f'mail-v2/teacher:{tid}/'): valid=False; break
        if valid: result_messages.append(message)
    old_states=old.get('states') if isinstance(old.get('states'),dict) else {}
    new_states=new.get('states') if isinstance(new.get('states'),dict) else {}
    states=dict(old_states); states[me]=new_states.get(me,{}) if isinstance(new_states.get(me,{}),dict) else {}
    old_drafts=old.get('drafts') if isinstance(old.get('drafts'),list) else []
    new_drafts=new.get('drafts') if isinstance(new.get('drafts'),list) else []
    drafts=[x for x in old_drafts if isinstance(x,dict) and str(x.get('owner') or '')!=me]
    drafts.extend(x for x in new_drafts if isinstance(x,dict) and str(x.get('owner') or '')==me)
    old_folders=old.get('folders') if isinstance(old.get('folders'),list) else []
    new_folders=new.get('folders') if isinstance(new.get('folders'),list) else []
    folders=[x for x in old_folders if isinstance(x,dict) and str(x.get('owner') or x.get('user') or '')!=me]
    folders.extend(x for x in new_folders if isinstance(x,dict) and str(x.get('owner') or x.get('user') or '')==me)
    return {'schemaVersion':2,'messages':result_messages,'states':states,'drafts':drafts,'folders':folders,'resetPending':bool(old.get('resetPending',False) and new.get('resetPending',False))}


def _teacher_can_access_upload(user, relative, write=False):
    """Les fichiers non-Cloud ne sont lisibles que s'ils sont référencés dans le périmètre visible."""
    try:
        rel=str(relative or '').replace('\\','/').lstrip('/')
        target=_safe_upload_path(rel)
        rel=_uploads_relative(target)
        if rel.startswith('cloud/'):
            return _cloud_path_allowed(user,rel,write=write)
        if user.get('role')=='admin': return True
        if user.get('role')!='teacher': return False
        tid=str(user.get('teacherId') or '')
        own_mail=(f'mail-v2/teacher:{tid}',f'mail-v2-drafts/teacher:{tid}')
        if rel in own_mail or any(rel.startswith(prefix+'/') for prefix in own_mail):
            return True
        if rel.startswith(('mail-v2/','mail-v2-drafts/')): return False
        if write: return rel.split('/',1)[0] in ('general','lessons','submissions','corrections')
        data=_load_database(); visible=_teacher_visible_data(data,user)
        mailbox=_teacher_visible_mailbox(data.get('mailboxV2',{}),user,data)
        needle='/data/uploads/'+rel
        def contains(value):
            if isinstance(value,dict): return any(contains(v) for v in value.values())
            if isinstance(value,list): return any(contains(v) for v in value)
            if isinstance(value,str): return value==rel or needle in value or value.endswith('/'+rel)
            return False
        return contains(visible) or contains(mailbox)
    except (ValueError,OSError):
        return False


def _teacher_visible_data(data,user):
    if user.get('role')=='admin': return data
    if user.get('role')!='teacher': return {}
    tids=str(user.get('teacherId') or '')
    class_ids=_teacher_class_ids(data,user)
    student_ids={str(x.get('id')) for x in data.get('students',[]) or [] if isinstance(x,dict) and str(x.get('classId') or '') in class_ids}
    lesson_ids={str(x.get('id')) for x in data.get('lessons',[]) or [] if isinstance(x,dict) and str(x.get('classId') or '') in class_ids}
    student_class_by_id={str(x.get('id')):str(x.get('classId') or '') for x in data.get('students',[]) or [] if isinstance(x,dict) and x.get('id')}
    lesson_class_by_id={str(x.get('id')):str(x.get('classId') or '') for x in data.get('lessons',[]) or [] if isinstance(x,dict) and x.get('id')}
    def related_record_visible(record):
        if not isinstance(record,dict): return False
        related=[]
        cid=str(record.get('classId') or '')
        sid=str(record.get('studentId') or '')
        lid=str(record.get('lessonId') or '')
        if cid: related.append(cid)
        if sid:
            student_class=student_class_by_id.get(sid)
            if not student_class: return False
            related.append(student_class)
        if lid:
            lesson_class=lesson_class_by_id.get(lid)
            if not lesson_class: return False
            related.append(lesson_class)
        return bool(related) and len(set(related))==1 and related[0] in class_ids
    # Seuls les référentiels explicitement partagés sont transmis aux professeurs.
    # Une nouvelle clé ajoutée à la base reste privée par défaut jusqu'à validation.
    shared_keys=('subjects','competencyLibrary','evaluationTemplates','evaluationCriteriaLibrary','schemaVersion','schemaMigratedAt')
    out={key:data[key] for key in shared_keys if key in data}
    settings=data.get('settings')
    if isinstance(settings,dict):
        shared_settings=('rooms','termMode','terms','competencyLevels','courseAppearanceMigrationV205')
        out['settings']={key:settings[key] for key in shared_settings if key in settings}
    out['classes']=[x for x in data.get('classes',[]) or [] if isinstance(x,dict) and str(x.get('id')) in class_ids]
    out['students']=[x for x in data.get('students',[]) or [] if isinstance(x,dict) and str(x.get('id')) in student_ids]
    out['teachers']=[x for x in data.get('teachers',[]) or [] if isinstance(x,dict) and str(x.get('id'))==tids]
    # Le professeur peut connaître son profil, jamais récupérer son empreinte d'authentification.
    out['users']=[{k:v for k,v in x.items() if k not in ('passwordHash','password')} for x in data.get('users',[]) or [] if isinstance(x,dict) and str(x.get('id'))==str(user.get('id'))]
    out['schedule']=[x for x in data.get('schedule',[]) or [] if isinstance(x,dict) and str(x.get('classId') or '') in class_ids]
    out['lessons']=[x for x in data.get('lessons',[]) or [] if isinstance(x,dict) and str(x.get('classId') or '') in class_ids]
    evaluations=[]
    for item in data.get('evaluations',[]) or []:
        if not isinstance(item,dict) or str(item.get('classId') or '') not in class_ids: continue
        evaluation_class=str(item.get('classId') or '')
        copy=dict(item); copy['grades']=[g for g in item.get('grades',[]) or [] if isinstance(g,dict) and student_class_by_id.get(str(g.get('studentId') or ''))==evaluation_class]; evaluations.append(copy)
    out['evaluations']=evaluations
    attendance=[]
    for item in data.get('attendance',[]) or []:
        if not isinstance(item,dict) or str(item.get('classId') or '') not in class_ids: continue
        attendance_class=str(item.get('classId') or '')
        copy=dict(item); copy['rows']=[r for r in item.get('rows',[]) or [] if isinstance(r,dict) and student_class_by_id.get(str(r.get('studentId') or ''))==attendance_class]; attendance.append(copy)
    out['attendance']=attendance
    out['bulletins']=[x for x in data.get('bulletins',[]) or [] if related_record_visible(x)]
    out['attachments']=[x for x in data.get('attachments',[]) or [] if related_record_visible(x)]
    out['submissions']=[x for x in data.get('submissions',[]) or [] if related_record_visible(x)]
    out['conversations']=[x for x in data.get('conversations',[]) or [] if isinstance(x,dict) and (str(x.get('teacherId') or '')==tids or str(x.get('classId') or '') in class_ids or tids in {str(v) for v in x.get('participantIds',[]) or []})]
    out['cloudItems']=[x for x in data.get('cloudItems',[]) or [] if isinstance(x,dict) and _cloud_path_allowed(user,x.get('serverName',''),write=False)]
    out['notifications']=[x for x in data.get('notifications',[]) or [] if isinstance(x,dict) and (str(x.get('studentId') or '') in student_ids or str(x.get('teacherId') or '')==tids)]
    out['mailFolders']=[x for x in data.get('mailFolders',[]) or [] if isinstance(x,dict) and (str(x.get('teacherId') or '')==tids or str(x.get('ownerId') or '')==tids)]
    out['mailboxV2']=_teacher_visible_mailbox(data.get('mailboxV2',{}),user,data)
    out['auditLog']=[]
    return out


def _student_can_access_upload(user,relative,write=False):
    try:
        sid=str(user.get('studentId') or '')
        rel=str(relative or '').replace(chr(92),'/').lstrip('/')
        target=_safe_upload_path(rel)
        rel=_uploads_relative(target)
        if not sid or rel.startswith('cloud/'):
            return False
        data=_load_database()
        student_record=next((x for x in data.get('students',[]) or [] if isinstance(x,dict) and str(x.get('id'))==sid),None)
        if not student_record: return False
        if write:
            prefix=f'submissions/{sid}/'
            if not rel.startswith(prefix): return False
            return any(isinstance(sub,dict) and str(sub.get('studentId') or '')==sid and sub.get('status')=='draft' and any(isinstance(f,dict) and (str(f.get('name') or '')==rel or str(f.get('url') or '')=='/data/uploads/'+rel) for f in (sub.get('files') or [])) for sub in data.get('submissions',[]) or [])
        visible=_student_visible_data(data,user)
        needle='/data/uploads/'+rel
        def contains(value):
            if isinstance(value,dict): return any(contains(v) for v in value.values())
            if isinstance(value,list): return any(contains(v) for v in value)
            if isinstance(value,str): return value==rel or needle in value or value.endswith('/'+rel)
            return False
        return contains(visible)
    except (ValueError,OSError):
        return False


def _merge_student_data(current,incoming,user):
    """N'accepte que les brouillons/rendus de l'élève authentifié."""
    if user.get('role')!='student': raise PermissionError('Rôle non autorisé')
    sid=str(user.get('studentId') or '')
    student_record=next((x for x in current.get('students',[]) or [] if isinstance(x,dict) and str(x.get('id'))==sid),None)
    if not student_record: raise PermissionError('Profil élève introuvable')
    class_id=str(student_record.get('classId') or '')
    allowed_lessons={str(x.get('id')) for x in current.get('lessons',[]) or [] if isinstance(x,dict) and str(x.get('classId') or '')==class_id and (not x.get('group') or str(x.get('group'))==str(student_record.get('group') or ''))}
    merged=dict(current)
    old=[x for x in current.get('submissions',[]) or [] if isinstance(x,dict)]
    incoming_rows=[x for x in incoming.get('submissions',[]) or [] if isinstance(x,dict)]
    old_own={str(x.get('id')):x for x in old if str(x.get('studentId') or '')==sid}
    new_own={}
    for entry in incoming_rows:
        ident=str(entry.get('id') or '')
        previous=old_own.get(ident)
        lesson_id=str(previous.get('lessonId') if previous else entry.get('lessonId') or '')
        if not ident or str(entry.get('studentId') or '')!=sid or lesson_id not in allowed_lessons:
            continue
        if previous and previous.get('status')!='draft':
            # Un rendu déjà envoyé est immuable côté élève ; le professeur seul le corrige.
            new_own[ident]=dict(previous)
            continue
        lesson=next((x for x in current.get('lessons',[]) or [] if isinstance(x,dict) and str(x.get('id'))==lesson_id),None)
        if not lesson or not isinstance(lesson.get('homework'),dict) or not lesson['homework'].get('requiresSubmission'):
            continue
        safe=dict(previous or {})
        safe.update({'id':ident,'studentId':sid,'lessonId':str(lesson.get('id')),'classId':class_id})
        if not previous:
            safe['createdAt']=str(entry.get('createdAt') or datetime.datetime.now(datetime.timezone.utc).isoformat())
        files=entry.get('files') if isinstance(entry.get('files'),list) else []
        safe_files=[]
        for item in files:
            if not isinstance(item,dict): continue
            name=str(item.get('name') or '').replace(chr(92),'/').lstrip('/')
            if not name.startswith(f'submissions/{sid}/'): continue
            try:
                file_path=_safe_upload_path(name)
                if not os.path.isfile(file_path) or os.path.islink(file_path): continue
            except (ValueError,OSError): continue
            safe_files.append({'name':name,'url':'/data/uploads/'+name,'size':os.path.getsize(file_path)})
        safe['files']=safe_files
        safe['file']=safe_files[0] if safe_files else None
        safe['status']='submitted' if entry.get('status')=='submitted' and safe_files else 'draft'
        if safe['status']=='submitted':
            safe['submittedAt']=str(entry.get('submittedAt') or datetime.datetime.now(datetime.timezone.utc).isoformat())
        else:
            safe.pop('submittedAt',None)
        new_own[ident]=safe
    # Un élève ne peut ni effacer un rendu déjà envoyé ni le faire disparaître en
    # l'omettant du JSON qu'il renvoie.
    for ident,previous in old_own.items():
        if previous.get('status')!='draft':
            new_own.setdefault(ident,dict(previous))
    merged['submissions']=[x for x in old if str(x.get('studentId') or '')!=sid]+list(new_own.values())
    return merged


def _student_visible_data(data,user):
    """Projection strictement limitée à l'élève authentifié ; aucune donnée de camarade."""
    sid=str(user.get('studentId') or '')
    student_record=next((x for x in data.get('students',[]) or [] if isinstance(x,dict) and str(x.get('id'))==sid),None)
    if not student_record:
        return {}
    class_id=str(student_record.get('classId') or '')
    out={}
    shared=('subjects','competencyLibrary','evaluationTemplates','evaluationCriteriaLibrary','schemaVersion','schemaMigratedAt')
    for key in shared:
        if key in data: out[key]=data[key]
    settings=data.get('settings')
    if isinstance(settings,dict):
        out['settings']={k:settings[k] for k in ('rooms','termMode','terms','competencyLevels') if k in settings}
    out['classes']=[x for x in data.get('classes',[]) or [] if isinstance(x,dict) and str(x.get('id'))==class_id]
    out['students']=[dict(student_record)]
    out['users']=[{k:v for k,v in x.items() if k not in ('passwordHash','password')} for x in data.get('users',[]) or [] if isinstance(x,dict) and str(x.get('id'))==str(user.get('id'))]
    out['schedule']=[x for x in data.get('schedule',[]) or [] if isinstance(x,dict) and str(x.get('classId') or '')==class_id and (not x.get('group') or str(x.get('group'))==str(student_record.get('group') or ''))]
    teacher_ids={str(x.get('teacherId')) for x in out['schedule'] if x.get('teacherId')}
    teacher_ids.update(str(x.get('teacherId')) for x in data.get('lessons',[]) or [] if isinstance(x,dict) and str(x.get('classId') or '')==class_id and x.get('teacherId'))
    out['teachers']=[x for x in data.get('teachers',[]) or [] if isinstance(x,dict) and str(x.get('id')) in teacher_ids]
    out['lessons']=[x for x in data.get('lessons',[]) or [] if isinstance(x,dict) and str(x.get('classId') or '')==class_id and (not x.get('group') or str(x.get('group'))==str(student_record.get('group') or ''))]
    out['evaluations']=[]
    for item in data.get('evaluations',[]) or []:
        if not isinstance(item,dict) or str(item.get('classId') or '')!=class_id or item.get('published') is not True: continue
        if item.get('group') and str(item.get('group'))!=str(student_record.get('group') or ''): continue
        copy=dict(item)
        copy['grades']=[g for g in item.get('grades',[]) or [] if isinstance(g,dict) and str(g.get('studentId') or '')==sid]
        out['evaluations'].append(copy)
    out['attendance']=[]
    for item in data.get('attendance',[]) or []:
        if not isinstance(item,dict) or str(item.get('classId') or '')!=class_id: continue
        copy=dict(item)
        copy['rows']=[r for r in item.get('rows',[]) or [] if isinstance(r,dict) and str(r.get('studentId') or '')==sid]
        out['attendance'].append(copy)
    out['bulletins']=[x for x in data.get('bulletins',[]) or [] if isinstance(x,dict) and str(x.get('studentId') or '')==sid and x.get('published') is True and x.get('validated') is True]
    lesson_ids={str(x.get('id')) for x in out['lessons'] if x.get('id')}
    out['attachments']=[x for x in data.get('attachments',[]) or [] if isinstance(x,dict) and ((str(x.get('studentId') or '')==sid) or (str(x.get('classId') or '')==class_id and (not x.get('lessonId') or str(x.get('lessonId')) in lesson_ids)))]
    out['submissions']=[x for x in data.get('submissions',[]) or [] if isinstance(x,dict) and str(x.get('studentId') or '')==sid and str(x.get('lessonId') or '') in lesson_ids]
    # Les conversations ne sont pas encore exposées aux comptes élèves : le modèle
    # historique ne permet pas de prouver proprement les droits message par message.
    out['conversations']=[]
    out['cloudItems']=[]
    out['notifications']=[x for x in data.get('notifications',[]) or [] if isinstance(x,dict) and str(x.get('studentId') or '')==sid]
    out['mailFolders']=[]
    out['mailboxV2']={}
    out['auditLog']=[]
    return out


def _merge_teacher_data(current,incoming,user):
    """Fusionne le périmètre professeur sans remplacer les données hors périmètre."""
    if user.get('role')=='admin': return incoming
    if user.get('role')!='teacher': raise PermissionError('Rôle non autorisé')
    allowed=_teacher_class_ids(current,user)
    tid=str(user.get('teacherId') or '')
    merged=dict(current)
    # Seules ces collections sont modifiables par un professeur.
    scoped=('students','schedule','lessons','evaluations','attendance','bulletins','attachments','submissions','conversations','cloudItems','notifications','mailFolders')
    for key in scoped:
        old=[x for x in current.get(key,[]) or [] if isinstance(x,dict)]
        new=[x for x in incoming.get(key,[]) or [] if isinstance(x,dict)]
        def in_scope(x):
            ident=str(x.get('id') or '')
            stored=next((z for z in old if ident and str(z.get('id') or '')==ident),None)
            scope_record=stored or x
            if key=='cloudItems':
                x=scope_record
                return _cloud_path_allowed(user,x.get('serverName',''),write=True) or _cloud_grant(x,user,current,write=True)
            if key=='conversations':
                return str(scope_record.get('teacherId') or '')==tid or str(scope_record.get('classId') or '') in allowed or tid in {str(v) for v in scope_record.get('participantIds',[]) or []}
            if key=='notifications':
                sid=str(scope_record.get('studentId') or '')
                return sid in {str(z.get('id')) for z in current.get('students',[]) or [] if isinstance(z,dict) and str(z.get('classId') or '') in allowed} or str(scope_record.get('teacherId') or '')==tid
            if key=='mailFolders': return str(scope_record.get('teacherId') or '')==tid or str(scope_record.get('ownerId') or '')==tid
            if key=='bulletins':
                ident=str(x.get('id') or '')
                previous=next((z for z in current.get('bulletins',[]) or [] if isinstance(z,dict) and str(z.get('id') or '')==ident),None)
                return _teacher_record_class_id(previous or scope_record,current,key) in allowed
            if key in ('evaluations','attendance','submissions'):
                ident=str(x.get('id') or '')
                previous=next((z for z in current.get(key,[]) or [] if isinstance(z,dict) and str(z.get('id') or '')==ident),None)
                return _teacher_record_class_id(previous or x,current,key) in allowed
            return _teacher_record_class_id(scope_record,current,key) in allowed
        old_scope={str(x.get('id')):x for x in old if x.get('id') and in_scope(x)}
        new_scope={str(x.get('id')):x for x in new if x.get('id') and in_scope(x)}
        # Une entrée soumise avec un ID existant hors périmètre ne peut jamais la modifier.
        result=[x for x in old if not (x.get('id') and str(x.get('id')) in old_scope and not (key=='bulletins' and x.get('published') is True))]
        student_ids={str(z.get('id')) for z in current.get('students',[]) or [] if isinstance(z,dict) and str(z.get('classId') or '') in allowed}
        lesson_ids={str(z.get('id')) for z in current.get('lessons',[]) or [] if isinstance(z,dict) and str(z.get('classId') or '') in allowed}
        safe_new=[]
        for entry in new_scope.values():
            item=dict(entry)
            previous=None
            if key=='conversations':
                previous=next((x for x in old if str(x.get('id') or '')==str(item.get('id') or '')),None)
                if previous:
                    # Une conversation existante ne peut pas être réaffectée ni voir
                    # ses participants/messages réécrits par un enseignant.
                    for field in ('teacherId','classId','participantIds','type','title','createdAt'):
                        if field in previous: item[field]=previous[field]
                        else: item.pop(field,None)
                    # Dans l'ancien modèle, seul l'état de lecture personnel est modifiable.
                    incoming_messages=item.get('messages') if isinstance(item.get('messages'),list) else []
                    incoming_by_id={str(m.get('id')):m for m in incoming_messages if isinstance(m,dict) and m.get('id')}
                    safe_messages=[]
                    for original_message in previous.get('messages',[]) or []:
                        if not isinstance(original_message,dict): continue
                        message=dict(original_message)
                        update=incoming_by_id.get(str(message.get('id') or ''))
                        if update is not None:
                            read_by=list(message.get('readBy') or [])
                            updated_read=list(update.get('readBy') or [])
                            if tid in updated_read and tid not in read_by: read_by.append(tid)
                            if tid not in updated_read: read_by=[x for x in read_by if str(x)!=tid]
                            message['readBy']=read_by
                        safe_messages.append(message)
                    item['messages']=safe_messages
                    # Les états d'archivage/classement restent strictement personnels.
                    for field in ('archivedBy','deletedBy','starredBy'):
                        before=list(previous.get(field) or [])
                        after=list(item.get(field) or [])
                        if tid in after and tid not in before: before.append(tid)
                        if tid not in after: before=[x for x in before if str(x)!=tid]
                        item[field]=before
                    old_folders=previous.get('folderByUser') if isinstance(previous.get('folderByUser'),dict) else {}
                    new_folders=item.get('folderByUser') if isinstance(item.get('folderByUser'),dict) else {}
                    folders=dict(old_folders)
                    if tid in new_folders: folders[tid]=new_folders[tid]
                    else: folders.pop(tid,None)
                    item['folderByUser']=folders
            if key in ('students','schedule','lessons','attendance','attachments','bulletins','evaluations','submissions'):
                previous=next((x for x in old if str(x.get('id') or '')==str(item.get('id') or '')),None)
                if previous:
                    # Les liens de périmètre d'un enregistrement existant ne sont pas modifiables
                    # par le professeur : classe, élève, séance et période restent canoniques.
                    fields={
                        'students':('classId',),
                        'schedule':('classId',),
                        'lessons':('classId',),
                        'attendance':('classId',),
                        'attachments':('classId','studentId','lessonId'),
                        'bulletins':('studentId','classId','termId'),
                        'evaluations':('classId',),
                        'submissions':('studentId','lessonId','classId')
                    }[key]
                    for field in fields:
                        if field in previous: item[field]=previous[field]
                        else: item.pop(field,None)
            if item.get('studentId') and str(item.get('studentId')) not in student_ids: continue
            if key=='submissions':
                lesson=next((l for l in current.get('lessons',[]) or [] if isinstance(l,dict) and str(l.get('id'))==str(item.get('lessonId') or '')),None)
                if not lesson or str(lesson.get('classId') or '') not in allowed: 
                    if previous: safe_new.append(dict(previous))
                    continue
                lesson_class=str(lesson.get('classId') or '')
                student=next((st for st in current.get('students',[]) or [] if isinstance(st,dict) and str(st.get('id'))==str(item.get('studentId') or '')),None)
                if item.get('studentId') and (not student or str(student.get('classId') or '')!=lesson_class):
                    if previous: safe_new.append(dict(previous))
                    continue
                if item.get('classId') and str(item.get('classId'))!=lesson_class:
                    if previous: safe_new.append(dict(previous))
                    continue
                item['classId']=lesson_class
            if key=='evaluations':
                # Les notes doivent concerner des élèves de la classe exacte de l'évaluation,
                # pas simplement d'une autre classe également attribuée au professeur.
                evaluation_class=str(item.get('classId') or '')
                item['grades']=[g for g in item.get('grades',[]) or [] if isinstance(g,dict) and str(g.get('studentId') or '') in student_ids and any(isinstance(st,dict) and str(st.get('id'))==str(g.get('studentId')) and str(st.get('classId') or '')==evaluation_class for st in current.get('students',[]) or [])]
            if key=='attendance':
                attendance_class=str(item.get('classId') or '')
                item['rows']=[r for r in item.get('rows',[]) or [] if isinstance(r,dict) and str(r.get('studentId') or '') in student_ids and any(isinstance(st,dict) and str(st.get('id'))==str(r.get('studentId')) and str(st.get('classId') or '')==attendance_class for st in current.get('students',[]) or [])]
            if key=='bulletins':
                class_record=next((c for c in current.get('classes',[]) or [] if isinstance(c,dict) and str(c.get('id'))==str((previous or item).get('classId') or '')),None)
                is_principal=bool(class_record and str(class_record.get('principalTeacherId') or '')==tid)
                if previous and previous.get('published') is True:
                    # Le bulletin publié est déjà conservé dans result, même si le client le supprime.
                    continue
                else:
                    # Les appréciations de matière sont limitées aux matières affectées au professeur.
                    allowed_subjects=_teacher_subject_keys(current,user)
                    old_subject_data=previous.get('subjectData',{}) if previous and isinstance(previous.get('subjectData'),dict) else {}
                    new_subject_data=item.get('subjectData',{}) if isinstance(item.get('subjectData'),dict) else {}
                    filtered_subject_data={}
                    for subject,value in new_subject_data.items():
                        if str(subject).strip().casefold() in allowed_subjects:
                            filtered_subject_data[subject]=value
                        elif subject in old_subject_data:
                            filtered_subject_data[subject]=old_subject_data[subject]
                    for subject,value in old_subject_data.items():
                        if str(subject).strip().casefold() not in allowed_subjects:
                            filtered_subject_data.setdefault(subject,value)
                    item['subjectData']=filtered_subject_data
                    if not is_principal:
                        # Seul le PP peut valider, publier ou modifier l'appréciation générale.
                        for field in ('validated','validatedAt','published','publishedAt','overall','overallUpdatedAt'):
                            if previous and field in previous: item[field]=previous[field]
                            elif field in ('validated','published'): item[field]=False
                            else: item.pop(field,None)
            safe_new.append(item)
        result.extend(safe_new)
        merged[key]=result
    if 'mailboxV2' in current or 'mailboxV2' in incoming:
        merged['mailboxV2']=_teacher_merge_mailbox(current,incoming,user,current)
    # Les professeurs ne peuvent pas modifier les comptes, profils des collègues,
    # classes, matières, paramètres globaux ou journaux de direction.
    for key in ('classes','teachers','subjects','users','settings','auditLog'):
        if key in current: merged[key]=current[key]
    # Ne pas permettre d'ajouter des clés globales inconnues via une sauvegarde professeur.
    for key in list(merged):
        if key not in current and key not in scoped: merged.pop(key,None)
    return merged

def _cloud_grant(item,user,data,write=False):
    role=str(user.get('role') or '')
    tid=str(user.get('teacherId') or '')
    by_id={str(x.get('id')):x for x in (data.get('cloudItems') or []) if isinstance(x,dict) and x.get('id')}
    current=item; seen=set()
    while isinstance(current,dict) and str(current.get('id')) not in seen:
        seen.add(str(current.get('id')))
        grants=current.get('shares') if isinstance(current.get('shares'),list) else []
        for grant in grants:
            if not isinstance(grant,dict): continue
            if write and grant.get('role','view')!='edit': continue
            typ=grant.get('type')
            if typ=='teacher' and role=='teacher' and str(grant.get('id'))==tid: return True
            if typ=='class' and role=='teacher' and str(grant.get('classId')) in _teacher_class_ids(data,user): return True
            if typ=='group' and role=='teacher' and str(grant.get('classId')) in _teacher_class_ids(data,user): return True
        current=by_id.get(str(current.get('parentId') or ''))
    return False

def _cloud_scope_allowed(user,space,owner_id='',class_id='',group='',data=None,write=False):
    if user.get('role')=='admin': return True
    if user.get('role')!='teacher': return False
    data=data if isinstance(data,dict) else _load_database()
    tid=str(user.get('teacherId') or '')
    if space=='personal': return str(owner_id)==tid
    if space in ('class','group'):
        return bool(class_id) and str(class_id) in _teacher_class_ids(data,user) and (not write or str(owner_id)==tid)
    return False

def _cloud_path_allowed(user,relative,write=False):
    try:
        rel=str(relative or '').replace('\\','/')
        target=_safe_upload_path(rel)
        rel=_uploads_relative(target)
        parts=rel.split('/')
        # Cette fonction ne valide que des chemins Cloud : tout autre espace
        # doit être refusé par défaut, jamais considéré comme autorisé.
        if not parts or parts[0]!='cloud': return False
        if user.get('role')=='admin': return True
        data=_load_database(); items=data.get('cloudItems') if isinstance(data.get('cloudItems'),list) else []
        # Le dossier racine peut ne pas avoir de métadonnée : contrôler son espace.
        root_access=False
        if len(parts)>=4 and parts[1]=='personal' and parts[2]=='users':
            root_access=_cloud_scope_allowed(user,'personal',owner_id=parts[3],data=data,write=write)
        elif len(parts)>=4 and parts[1] in ('class','group') and parts[2]=='classes':
            root_access=_cloud_scope_allowed(user,parts[1],owner_id=user.get('teacherId',''),class_id=parts[3],data=data,write=write)
        else: return False
        # Appliquer ensuite les partages de l'élément/dossier le plus proche.
        candidates=[]
        for item in items:
            if not isinstance(item,dict): continue
            ip=str(item.get('serverName') or '').replace('\\','/').strip('/')
            if ip and (rel==ip or rel.startswith(ip+'/')): candidates.append((len(ip),item))
        if candidates:
            item=max(candidates,key=lambda z:z[0])[1]
            owner=str(item.get('ownerId') or '')==str(user.get('teacherId') or '')
            if owner: return True
            if not write and item.get('space') in ('class','group') and str(item.get('classId') or '') in _teacher_class_ids(data,user): return True
            return _cloud_grant(item,user,data,write=write)
        # Sans métadonnée d'élément, seul le propriétaire ou le membre de la classe peut créer/accéder à la racine.
        return root_access
    except (ValueError,OSError):
        return False

def _cloud_expected_root(item):
    safe=lambda value: re.sub(r'[^a-zA-Z0-9_-]+','_',str(value or ''))[:120] or 'root'
    space=str(item.get('space') or 'personal')
    if space=='personal': return 'cloud/personal/users/'+safe(item.get('ownerId'))
    if space in ('class','group'):
        root='cloud/'+space+'/classes/'+safe(item.get('classId'))
        if space=='group' and item.get('group'): root+='/groups/'+safe(item.get('group'))
        return root
    return ''

def _cloud_item_path_matches_scope(item):
    path=str(item.get('serverName') or '').replace('\\','/').strip('/')
    root=_cloud_expected_root(item)
    return bool(path and root and (path==root or path.startswith(root+'/')))

def _cloud_known_item_path(relative):
    rel=str(relative or '').replace('\\','/').strip('/')
    data=_load_database()
    return any(isinstance(x,dict) and str(x.get('serverName') or '').replace('\\','/').strip('/')==rel for x in (data.get('cloudItems') or []))

def _validate_cloud_item_changes(current,updated,user):
    if user.get('role')=='admin': return True
    old={str(x.get('id')):x for x in (current.get('cloudItems') or []) if isinstance(x,dict) and x.get('id')}
    new={str(x.get('id')):x for x in (updated.get('cloudItems') or []) if isinstance(x,dict) and x.get('id')}
    for ident in set(old)|set(new):
        before,after=old.get(ident),new.get(ident)
        if before==after: continue
        item=before or after
        if after is not None and not _cloud_item_path_matches_scope(after): return False
        if before:
            path=str(before.get('serverName') or '')
            owner=str(before.get('ownerId') or '')==str(user.get('teacherId') or '')
            can_write=owner or _cloud_grant(before,user,current,write=True)
            # Les éléments hors périmètre ou partagés en lecture seule sont absents
            # de la projection : leur absence ne constitue pas une suppression.
            if after is None and not can_write: continue
            if not can_write: return False
            # Seul le propriétaire peut changer les droits de partage.
            if after is not None and before.get('shares')!=after.get('shares') and not owner: return False
        else:
            if not _cloud_scope_allowed(user,after.get('space','personal'),owner_id=after.get('ownerId',''),class_id=after.get('classId',''),group=after.get('group',''),data=current,write=True): return False
        if after is not None and before is not None:
            # Empêcher le déplacement d'un élément vers un espace non autorisé.
            if (after.get('space'),after.get('ownerId'),after.get('classId'),after.get('group')) != (before.get('space'),before.get('ownerId'),before.get('classId'),before.get('group')): return False
    return True

def _norm_text(x):
    return unicodedata.normalize('NFKD',str(x or '')).encode('ascii','ignore').decode('ascii').lower().strip()

def _date_parse_fr(text, today=None):
    s=_norm_text(text)
    today=today or datetime.date.today()
    months={'janvier':1,'fevrier':2,'mars':3,'avril':4,'mai':5,'juin':6,'juillet':7,'aout':8,'septembre':9,'octobre':10,'novembre':11,'decembre':12}
    m=re.search(r'\b(\d{1,2})\s+(janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|octobre|novembre|decembre)(?:\s+(\d{4}))?\b',s)
    if m:
        y=int(m.group(3) or today.year); mo=months[m.group(2)]; d=int(m.group(1))
        try:return datetime.date(y,mo,d)
        except Exception:return None
    m=re.search(r'\b(\d{4})-(\d{2})-(\d{2})\b',s)
    if m:
        try:return datetime.date(int(m.group(1)),int(m.group(2)),int(m.group(3)))
        except Exception:return None
    days={'lundi':0,'mardi':1,'mercredi':2,'jeudi':3,'vendredi':4,'samedi':5,'dimanche':6}
    for name,wd in days.items():
        if re.search(r'\b'+name+r'\b',s):
            delta=(wd-today.weekday())%7
            if 'prochain' in s or 'semaine prochaine' in s:
                delta=delta or 7; delta+=7
            elif delta==0 and ('aujourd' not in s):
                delta=7
            return today+datetime.timedelta(days=delta)
    return None

def _find_teacher_allowed(ctx, class_name):
    classes=(ctx.get('profile') or {}).get('classes') or []
    wanted=_norm_text(class_name)
    if not wanted:return None
    exact=next((c for c in classes if _norm_text(c.get('name'))==wanted),None)
    if exact:return exact
    return next((c for c in classes if wanted in _norm_text(c.get('name')) or _norm_text(c.get('name')) in wanted),None)

def _date_matches_schedule(slot, date_obj):
    ds=date_obj.strftime('%Y-%m-%d')
    start=str(slot.get('startDate') or '1900-01-01'); end=str(slot.get('endDate') or '2999-12-31')
    if ds<start or ds>end or ds in (slot.get('exceptions') or []):return False
    if str(slot.get('recurrence') or 'weekly')=='once':return ds==start
    if date_obj.weekday()!=int(slot.get('day') or 0):return False
    try:diff=(date_obj-datetime.datetime.strptime(start,'%Y-%m-%d').date()).days
    except Exception:diff=0
    if diff<0:return False
    rec=slot.get('recurrence') or 'weekly'
    if rec=='biweekly':return diff%14==0
    if rec=='triweekly':return diff%21==0
    if rec=='custom':return diff%(max(1,int(slot.get('intervalWeeks') or 4))*7)==0
    return True

def _mins(v):
    try:
        h,m=str(v or '').split(':')[:2];return int(h)*60+int(m)
    except Exception:return -1

def _schedule_slot_conflicts(db,date_obj,start_time,end_time,class_id,teacher_id='',room='',ignore_id=''):
    a,b=_mins(start_time),_mins(end_time);out=[]
    if a<0 or b<=a:return out
    for s in db.get('schedule',[]) or []:
        if str(s.get('id'))==str(ignore_id) or not _date_matches_schedule(s,date_obj):continue
        x=_mins(s.get('time'));y=_mins(s.get('endTime'))
        if x<0:continue
        if y<=x:y=x+60
        same_class=bool(class_id) and str(s.get('classId'))==str(class_id)
        same_teacher=bool(teacher_id) and str(s.get('teacherId') or '')==str(teacher_id)
        same_room=bool(room) and bool(s.get('room')) and _norm_text(s.get('room'))==_norm_text(room)
        if (same_class or same_teacher or same_room) and a<y and b>x:
            reason='classe déjà occupée' if same_class else ('professeur déjà occupé' if same_teacher else 'salle déjà occupée')
            out.append({'schedule':s,'reason':reason})
    return out

def _find_free_schedule_slot(db,class_id,teacher_id,duration=60,weekday=None,wanted_date='',room=''):
    today=datetime.date.today();dates=[]
    if wanted_date:
        try:dates=[datetime.datetime.strptime(wanted_date,'%Y-%m-%d').date()]
        except Exception:dates=[]
    else:
        for i in range(56):
            d=today+datetime.timedelta(days=i)
            if weekday is None or d.weekday()==int(weekday):dates.append(d)
            if len(dates)>=8:break
    for d in dates:
        if weekday is not None and d.weekday()!=int(weekday):continue
        for minute in range(8*60,18*60,15):
            end_min=minute+duration
            if end_min>18*60:continue
            st=f'{minute//60:02d}:{minute%60:02d}';et=f'{end_min//60:02d}:{end_min%60:02d}'
            if not _schedule_slot_conflicts(db,d,st,et,class_id,teacher_id,room):return d,st,et
    return None

def _occurrences_for_schedule(db,slot,limit=90):
    out=[];start=str(slot.get('startDate') or datetime.date.today().isoformat());end=str(slot.get('endDate') or '')
    try:d=datetime.datetime.strptime(start,'%Y-%m-%d').date()
    except Exception:d=datetime.date.today()
    stop=datetime.datetime.strptime(end,'%Y-%m-%d').date() if end else d+datetime.timedelta(days=365)
    while d<=stop and len(out)<limit:
        if _date_matches_schedule(slot,d):
            ov=(slot.get('overrides') or {}).get(d.isoformat(),{})
            out.append((d,ov))
        d+=datetime.timedelta(days=1)
    return out

def _find_schedule_occurrence(db,args,ctx=None):
    class_name=str(args.get('className') or '').strip();subject=str(args.get('subject') or '').strip();title=str(args.get('title') or '').strip();wanted_date=str(args.get('date') or '').strip();wanted_time=str(args.get('time') or '').strip();sid=str(args.get('scheduleId') or '').strip()
    c=_find_teacher_allowed(ctx or {},class_name) if class_name else None;cid=c.get('id') if c else str(args.get('classId') or '')
    if not cid and ctx and len((ctx.get('profile') or {}).get('classes') or [])==1:cid=(ctx.get('profile') or {}).get('classes')[0].get('id')
    date_obj=None
    if wanted_date:
        try:date_obj=datetime.datetime.strptime(wanted_date,'%Y-%m-%d').date()
        except Exception:date_obj=None
    candidates=[]
    for s in db.get('schedule',[]) or []:
        if sid and str(s.get('id'))!=sid:continue
        if cid and str(s.get('classId'))!=str(cid):continue
        if subject and _norm_text(s.get('subject'))!=_norm_text(subject):continue
        if wanted_time and str(s.get('time',''))[:5]!=wanted_time[:5]:continue
        if date_obj and not _date_matches_schedule(s,date_obj):continue
        if title:
            ls=[l for l in db.get('lessons',[]) or [] if str(l.get('scheduleId'))==str(s.get('id')) and (not wanted_date or l.get('date')==wanted_date)]
            if not any(_norm_text(title) in _norm_text(l.get('title')) for l in ls):continue
        candidates.append(s)
    if not candidates:return None
    candidates.sort(key=lambda s:(0 if s.get('recurrence')=='once' else 1,str(s.get('startDate') or ''),str(s.get('time') or '')))
    s=candidates[0]
    if not date_obj:
        occ=_occurrences_for_schedule(db,s,60)
        if occ:date_obj=occ[0][0]
    return s,date_obj

def _lesson_for_occurrence(db,schedule_id,date_value):
    return next((l for l in db.get('lessons',[]) or [] if str(l.get('scheduleId'))==str(schedule_id) and str(l.get('date'))==str(date_value)),None)









def _cloud_search(data, query):
    norm=lambda x:unicodedata.normalize('NFKD',str(x or '')).encode('ascii','ignore').decode('ascii').lower(); q=norm(re.sub(r'\s+',' ',str(query or '').strip())); tokens=[x for x in re.findall(r'[a-z0-9-]+',q) if len(x)>2]; out=[]
    for item in data.get('cloudItems',[]) or []:
        if item.get('type')!='file':continue
        hay=norm(' '.join(str(item.get(k) or '') for k in ('name','title','path','serverName'))); score=sum(1 for t in tokens if t in hay); content=''; physical=str(item.get('serverName') or '')
        if physical:
            path=_safe_upload_path(physical)
            try:
                if os.path.isfile(path) and path.lower().endswith('.pdf') and os.path.getsize(path)<=8*1024*1024:
                    from pypdf import PdfReader
                    content='\n'.join((pg.extract_text() or '')[:20000] for pg in PdfReader(path).pages[:20]); score+=sum(1 for t in tokens if t in norm(content))*2
            except Exception:pass
        if score:out.append({'score':score,'name':item.get('name') or 'Document','snippet':re.sub(r'\s+',' ',content)[:280],'content':content})
    return sorted(out,key=lambda x:(-x['score'],x['name'].lower()))[:8]

def _format_day_name(d):
    return d.strftime('%A %d/%m/%Y')






class Handler(SimpleHTTPRequestHandler):
    def _session_user(self):
        raw=self.headers.get('Cookie','')
        token=''
        for part in raw.split(';'):
            k,_,v=part.strip().partition('=')
            if k=='mc_session': token=v
        entry=SESSIONS.get(token)
        if not entry: return None
        if entry['expires']<time.time():
            SESSIONS.pop(token,None); return None
        # Revalider le compte à chaque requête : une désactivation, suppression
        # ou modification de rôle prend effet sans attendre l'expiration du cookie.
        session_user=entry.get('user') if isinstance(entry.get('user'),dict) else {}
        user_id=str(session_user.get('id') or '')
        data=_load_database()
        current=next((u for u in data.get('users',[]) or [] if isinstance(u,dict) and str(u.get('id'))==user_id and u.get('active') is not False and u.get('role') in ('admin','teacher','student')),None)
        if not current:
            SESSIONS.pop(token,None); return None
        if current.get('role')=='student':
            student_id=str(current.get('studentId') or '')
            linked=next((x for x in data.get('students',[]) or [] if isinstance(x,dict) and str(x.get('id'))==student_id),None)
            if not linked:
                SESSIONS.pop(token,None); return None
        safe_user={k:current.get(k,'') for k in ('id','role','teacherId','studentId','name')}
        entry['user']=safe_user
        entry['expires']=time.time()+SESSION_TTL
        return safe_user
    def _require_auth(self, roles=('admin','teacher')):
        user=self._session_user()
        if not user:
            self._json({'error':'Connexion requise.'},401); return None
        token='';
        for part in self.headers.get('Cookie','').split(';'):
            k,_,v=part.strip().partition('=')
            if k=='mc_session': token=v
        if SESSIONS.get(token,{}).get('must_change'):
            self._json({'error':'Changement du mot de passe obligatoire.','code':'PASSWORD_CHANGE_REQUIRED'},428); return None
        if user.get('role') not in roles:
            self._json({'error':'Droits insuffisants.'},403); return None
        return user
    def _set_session_cookie(self, token):
        self.send_header('Set-Cookie',f'mc_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age={SESSION_TTL}')
    def _origin_allowed(self):
        host=self.headers.get('Host','').strip().lower()
        expected=f'{HOST}:{PORT}'.lower()
        allowed={expected}
        if HOST in ('127.0.0.1','localhost','::1'):
            allowed.update({f'127.0.0.1:{PORT}',f'localhost:{PORT}',f'[::1]:{PORT}'})
        # Refuser les Host arbitraires (notamment les tentatives de DNS rebinding).
        if host not in allowed:
            return False
        origin=self.headers.get('Origin')
        if not origin:
            return self.command in ('GET','HEAD','OPTIONS')
        return origin in (f'http://{host}', f'https://{host}')
    def _require_local_origin(self):
        if self._origin_allowed():
            return True
        self._json({'error':'Origine web refusée par MaClasse.'},403)
        return False
    def end_headers(self):
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','same-origin')
        self.send_header('X-Frame-Options','DENY')
        # Les fichiers importés/téléversés ne doivent jamais pouvoir exécuter
        # du HTML/JavaScript actif sur l'origine de l'application.
        if urlparse(getattr(self,'path','')).path.startswith('/data/uploads/'):
            self.send_header('Content-Security-Policy',"sandbox; default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'")
        super().end_headers()
    def _safe_static_path(self,path):
        if path in ('/','/index.html','/_all.js'):
            return True
        return path.startswith('/data/uploads/')
    def _backup_dir(self):
        d=os.path.join(DATA_DIR,'backups'); os.makedirs(d,exist_ok=True); return d
    def _create_backup(self, force=False):
        if not os.path.exists(DATA_FILE): return None
        current=None
        with open(DATA_FILE,encoding='utf-8') as f: current=json.load(f)
        if current is None: return None
        backup_dir=self._backup_dir()
        now=time.time()
        backups=sorted(glob.glob(os.path.join(backup_dir,'maclasse-*.json')),key=os.path.getmtime,reverse=True)
        if not force and backups and now-os.path.getmtime(backups[0])<BACKUP_INTERVAL_SECONDS:
            return None
        stamp=time.strftime('%Y%m%d-%H%M%S') + f'-{time.time_ns()%1000000:06d}'
        backup_path=os.path.join(backup_dir,f'maclasse-{stamp}.json')
        shutil.copy2(DATA_FILE,backup_path)
        # Complete portable snapshot: database JSON plus physical uploads.
        archive_path=os.path.join(backup_dir,f'maclasse-{stamp}.zip')
        with zipfile.ZipFile(archive_path,'w',compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(DATA_FILE,'data/maclasse.json')
            if os.path.isdir(UPLOADS):
                for base,_,files in os.walk(UPLOADS):
                    for filename in files:
                        full=os.path.join(base,filename)
                        archive.write(full,os.path.relpath(full,ROOT))
        cutoff=now-BACKUP_RETENTION_DAYS*86400
        for pattern in ('maclasse-*.json','maclasse-*.zip'):
            for stale in glob.glob(os.path.join(backup_dir,pattern)):
                try:
                    if os.path.getmtime(stale)<cutoff: os.remove(stale)
                except OSError: pass
        return os.path.basename(archive_path)
    def _json(self,obj,status=200,headers=None):
        raw=json.dumps(obj,ensure_ascii=False).encode('utf-8')
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(raw)))
        for key,value in (headers or {}).items(): self.send_header(key,str(value))
        self.end_headers(); self.wfile.write(raw)
    def do_OPTIONS(self):
        if not self._require_local_origin(): return
        self.send_response(204); self.end_headers()
    def do_GET(self):
        path=urlparse(self.path).path
        if not self._require_local_origin(): return
        if path=='/api/auth/session':
            user=self._session_user()
            token='';
            for part in self.headers.get('Cookie','').split(';'):
                k,_,v=part.strip().partition('=')
                if k=='mc_session': token=v
            if user: user={**user,'mustChangePassword':bool(SESSIONS.get(token,{}).get('must_change'))}
            return self._json({'authenticated':bool(user),'user':user})
        if path.startswith('/api/') or path.startswith('/data/uploads/'):
            allowed_roles=('admin','teacher','student') if path=='/api/data' or path.startswith('/data/uploads/') else ('admin','teacher')
            if not self._require_auth(roles=allowed_roles): return
        if path.startswith('/data/uploads/'):
            rel=path[len('/data/uploads/'):]
            try: _safe_upload_path(rel)
            except ValueError: return self.send_error(404)
            current_user=self._session_user() or {}
            allowed=_student_can_access_upload(current_user,rel,write=False) if current_user.get('role')=='student' else _teacher_can_access_upload(current_user,rel,write=False)
            if not allowed: return self.send_error(403)
        if path=='/api/data':
            try:
                with DATA_LOCK:
                    with open(DATA_FILE,encoding='utf-8') as f: data=json.load(f)
                    revision=_database_revision()
            except Exception: data={}; revision=_database_revision()
            session_user=self._session_user() or {}
            visible=_teacher_visible_data(data,session_user) if session_user.get('role')=='teacher' else (_student_visible_data(data,session_user) if session_user.get('role')=='student' else data)
            return self._json(visible,headers={'X-MaClasse-Revision':revision})
        if not self._safe_static_path(path):
            return self.send_error(404)
        return super().do_GET()
    def do_POST(self):
        if not self._require_local_origin(): return
        path=urlparse(self.path).path
        try: length=int(self.headers.get('Content-Length','0'))
        except ValueError: return self._json({'error':'Taille de requête invalide.'},400)
        if length<0 or length>100*1024*1024: return self._json({'error':'Requête trop volumineuse (100 Mo maximum).'},413)
        body=self.rfile.read(length)
        if path=='/api/auth/login':
            try: obj=json.loads(body.decode('utf-8'))
            except Exception: return self._json({'error':'Requête invalide.'},400)
            ip=self.client_address[0] if self.client_address else 'unknown'; now=time.time()
            attempts=[t for t in LOGIN_ATTEMPTS.get(ip,[]) if now-t<300]
            if len(attempts)>=10: return self._json({'error':'Trop de tentatives. Réessaie dans cinq minutes.'},429)
            username=str(obj.get('username') or '').strip().lower(); password=str(obj.get('password') or '')
            if not username or not password or len(password)>1024: return self._json({'error':'Identifiant ou mot de passe incorrect.'},401)
            try:
                with DATA_LOCK:
                    with open(DATA_FILE,encoding='utf-8') as f: data=json.load(f)
                    user=next((u for u in data.get('users',[]) if isinstance(u,dict) and str(u.get('username','')).lower()==username and u.get('active') is not False and u.get('role') in ('admin','teacher','student') and (u.get('role')!='student' or any(isinstance(st,dict) and str(st.get('id'))==str(u.get('studentId') or '') for st in data.get('students',[]) or []))),None)
                    valid,legacy=_password_verify(password,user.get('passwordHash','') if user else '')
                    if not user or not valid:
                        user=None
                    else:
                        must_change=password in ('admin','enseignant') or user.get('mustChangePassword') is True
                        if legacy:
                            user['passwordHash']=_password_hash(password)
                            tmp=f'{DATA_FILE}.{threading.get_ident()}.tmp'
                            with open(tmp,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)
                            os.replace(tmp,DATA_FILE)
            except Exception: user=None; must_change=False
            if not user:
                attempts.append(now); LOGIN_ATTEMPTS[ip]=attempts
                return self._json({'error':'Identifiant ou mot de passe incorrect.'},401)
            LOGIN_ATTEMPTS.pop(ip,None)
            token=secrets.token_urlsafe(32); safe_user={k:user.get(k,'') for k in ('id','role','teacherId','studentId','name')}
            SESSIONS[token]={'user':safe_user,'expires':now+SESSION_TTL,'must_change':must_change}
            public_user={**safe_user,'mustChangePassword':must_change}
            self.send_response(200); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Cache-Control','no-store'); self._set_session_cookie(token); self.end_headers(); self.wfile.write(json.dumps({'ok':True,'user':public_user},ensure_ascii=False).encode('utf-8')); return
        if path=='/api/auth/change-password':
            user=self._session_user()
            if not user: return self._json({'error':'Connexion requise.'},401)
            token='';
            for part in self.headers.get('Cookie','').split(';'):
                k,_,v=part.strip().partition('=')
                if k=='mc_session': token=v
            try: obj=json.loads(body.decode('utf-8'))
            except Exception: return self._json({'error':'Requête invalide.'},400)
            current_password=str(obj.get('currentPassword') or ''); new_password=str(obj.get('newPassword') or '')
            if not current_password or len(current_password)>1024 or len(new_password)<12 or len(new_password)>1024:
                return self._json({'error':'Le nouveau mot de passe doit contenir entre 12 et 1024 caractères.'},400)
            new_hash=_password_hash(new_password)
            try:
                with DATA_LOCK:
                    with open(DATA_FILE,encoding='utf-8') as f: data=json.load(f)
                    target=next((u for u in data.get('users',[]) if isinstance(u,dict) and str(u.get('id'))==str(user.get('id'))),None)
                    if not target or not _password_verify(current_password,target.get('passwordHash',''))[0]: return self._json({'error':'Mot de passe actuel incorrect.'},401)
                    target['passwordHash']=new_hash
                    target['mustChangePassword']=False
                    tmp=f'{DATA_FILE}.{threading.get_ident()}.tmp'
                    with open(tmp,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)
                    os.replace(tmp,DATA_FILE)
                # Un changement de mot de passe invalide toutes les autres sessions
                # du compte ; seule la session ayant effectué l'opération reste ouverte.
                for other_token,session in list(SESSIONS.items()):
                    other_user=session.get('user') if isinstance(session,dict) else {}
                    if other_token!=token and str((other_user or {}).get('id') or '')==str(user.get('id') or ''):
                        SESSIONS.pop(other_token,None)
                if token in SESSIONS:
                    SESSIONS[token]['must_change']=False
                return self._json({'ok':True})
            except Exception as e: return self._json({'error':'Modification impossible : '+str(e)},500)
        if path=='/api/auth/logout':
            raw=self.headers.get('Cookie',''); token=''
            for part in raw.split(';'):
                k,_,v=part.strip().partition('=')
                if k=='mc_session': token=v
            SESSIONS.pop(token,None)
            self.send_response(200); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Set-Cookie','mc_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0'); self.end_headers(); self.wfile.write(b'{"ok":true}'); return
        allowed_roles=('admin','teacher','student') if path in ('/api/data','/api/save','/api/upload','/api/delete-upload') else ('admin','teacher')
        user=self._require_auth(roles=allowed_roles)
        if not user: return
        if path=='/api/backup/restore':
            if user.get('role')!='admin': return self._json({'error':'La restauration complète est réservée à la direction.'},403)
            if length>100*1024*1024: return self._json({'error':'Archive trop volumineuse (100 Mo maximum).'},413)
            try:
                with DATA_LOCK:
                    backup_name=self._create_backup(force=True) if os.path.exists(DATA_FILE) else None
                    restored=_restore_backup_archive(body)
                    revision=_database_revision()
                return self._json({'ok':True,'backup':backup_name,'restored':restored},headers={'X-MaClasse-Revision':revision})
            except Exception as exc:
                return self._json({'error':'Restauration refusée : '+str(exc)},400)
        if path=='/api/bulletin-pdf':
            try:
                payload=json.loads(body.decode('utf-8'))
                if not isinstance(payload,dict): return self._json({'error':'Données de bulletin invalides.'},400)
                bulletin_id=str(payload.get('bulletinId') or '')
                database=_load_database()
                bulletin=next((x for x in database.get('bulletins',[]) or [] if isinstance(x,dict) and str(x.get('id'))==bulletin_id),None)
                if not bulletin: return self._json({'error':'Bulletin introuvable.'},404)
                if bulletin.get('validated') is not True or bulletin.get('published') is not True or not bulletin.get('publishedAt'):
                    return self._json({'error':'Seul un bulletin validé et officiellement publié peut être exporté.'},403)
                student_id=str(bulletin.get('studentId') or '')
                class_id=str(bulletin.get('classId') or '')
                student_record=next((x for x in database.get('students',[]) or [] if isinstance(x,dict) and str(x.get('id'))==student_id),None)
                class_record=next((x for x in database.get('classes',[]) or [] if isinstance(x,dict) and str(x.get('id'))==class_id),None)
                if not student_record or not class_record or str(student_record.get('classId') or '')!=class_id:
                    return self._json({'error':'Bulletin incohérent ou élève introuvable.'},409)
                if user.get('role')=='teacher' and class_id not in _teacher_class_ids(database,user):
                    return self._json({'error':'Ce bulletin ne relève pas de vos classes.'},403)
                term_id=str(bulletin.get('termId') or '')
                term_record=next((x for x in (database.get('settings',{}).get('terms',[]) if isinstance(database.get('settings'),dict) else []) or [] if isinstance(x,dict) and str(x.get('id'))==term_id),None)
                # Tout le contenu métier du PDF est recalculé depuis la base serveur.
                # Le navigateur ne fournit que l'identifiant du bulletin.
                payload=_bulletin_pdf_data(database,bulletin,student_record,class_record,term_record)
                from io import BytesIO
                from datetime import datetime
                from reportlab.lib import colors
                from reportlab.lib.pagesizes import A4
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.enums import TA_CENTER, TA_RIGHT
                from reportlab.lib.units import mm
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                regular='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
                bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
                if os.path.exists(regular) and os.path.exists(bold):
                    pdfmetrics.registerFont(TTFont('MCDejaVu',regular)); pdfmetrics.registerFont(TTFont('MCDejaVu-Bold',bold)); font='MCDejaVu'; font_bold='MCDejaVu-Bold'
                else: font='Helvetica'; font_bold='Helvetica-Bold'
                buf=BytesIO()
                doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=12*mm,leftMargin=12*mm,topMargin=12*mm,bottomMargin=12*mm,title='Bulletin scolaire MaClasse')
                styles=getSampleStyleSheet()
                styles.add(ParagraphStyle(name='MCBody',parent=styles['BodyText'],fontName=font,fontSize=8,leading=10,textColor=colors.HexColor('#243247'),spaceAfter=2))
                styles.add(ParagraphStyle(name='MCTitle',parent=styles['Title'],fontName=font_bold,fontSize=17,leading=20,textColor=colors.HexColor('#2456a6'),alignment=0,spaceAfter=3))
                styles.add(ParagraphStyle(name='MCSection',parent=styles['Heading2'],fontName=font_bold,fontSize=10,leading=12,textColor=colors.HexColor('#2456a6'),spaceBefore=9,spaceAfter=5))
                styles.add(ParagraphStyle(name='MCSmall',parent=styles['BodyText'],fontName=font,fontSize=7,leading=8,textColor=colors.HexColor('#475569')))
                def esc(v):
                    from xml.sax.saxutils import escape
                    return escape(str(v if v is not None else '')).replace('\n','<br/>')
                def nfmt(v): return '—' if v is None or v=='' or v=='—' else (f'{float(v):.2f}'.replace('.',',') if isinstance(v,(int,float)) else esc(v))
                story=[]
                head=Table([[Paragraph('MA CLASSE',styles['MCTitle']),Paragraph(esc(payload.get('termName','Bulletin')),ParagraphStyle('period',parent=styles['MCBody'],fontName=font_bold,fontSize=10,alignment=TA_RIGHT,textColor=colors.HexColor('#2456a6')))]],colWidths=[110*mm,75*mm])
                head.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LINEBELOW',(0,0),(-1,-1),2,colors.HexColor('#2456a6')),('BOTTOMPADDING',(0,0),(-1,-1),8)]));story.extend([head,Spacer(1,5*mm)])
                ident=Table([[Paragraph('<b>ÉLÈVE</b><br/>'+esc(payload.get('student',{}).get('name','')),styles['MCBody']),Paragraph('<b>CLASSE</b><br/>'+esc(payload.get('className','—')),styles['MCBody']),Paragraph('<b>PÉRIODE</b><br/>'+esc(payload.get('termName','—')),styles['MCBody'])]],colWidths=[85*mm,48*mm,52*mm])
                ident.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f1f5f9')),('BOX',(0,0),(-1,-1),.5,colors.HexColor('#dbe3ee')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]));story.extend([ident,Spacer(1,4*mm)])
                osx=payload.get('overallStats') or {}
                avgbox=Table([[[Paragraph('<b>MOYENNE GÉNÉRALE</b>',styles['MCSmall']),Paragraph('<font color="#2456a6">'+esc(nfmt(payload.get('average')))+' / 20</font>',ParagraphStyle('MCMainAvg',parent=styles['MCBody'],fontName=font_bold,fontSize=17,leading=20))],Paragraph('<b>MOYENNE DE CLASSE</b><br/>'+esc(nfmt(osx.get('avg'))),styles['MCBody']),Paragraph('<b>PLUS BASSE</b><br/>'+esc(nfmt(osx.get('min'))),styles['MCBody']),Paragraph('<b>PLUS HAUTE</b><br/>'+esc(nfmt(osx.get('max'))),styles['MCBody'])]],colWidths=[65*mm,40*mm,40*mm,40*mm])
                avgbox.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#edf3ff')),('BOX',(0,0),(-1,-1),.5,colors.HexColor('#c8d8f5')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story.extend([avgbox,Paragraph('Résultats par matière',styles['MCSection'])])
                data=[[Paragraph('<b>Matière</b>',styles['MCSmall']),Paragraph('<b>Élève</b>',styles['MCSmall']),Paragraph('<b>Moy. classe</b>',styles['MCSmall']),Paragraph('<b>Min.</b>',styles['MCSmall']),Paragraph('<b>Max.</b>',styles['MCSmall']),Paragraph('<b>Appréciation</b>',styles['MCSmall'])]]
                for row in payload.get('rows',[]):
                    st=row.get('classStats') or {}
                    data.append([Paragraph(esc(row.get('subject','')),styles['MCSmall']),Paragraph(esc(nfmt(row.get('studentAverage'))),styles['MCSmall']),Paragraph(esc(nfmt(st.get('avg'))),styles['MCSmall']),Paragraph(esc(nfmt(st.get('min'))),styles['MCSmall']),Paragraph(esc(nfmt(st.get('max'))),styles['MCSmall']),Paragraph(esc(row.get('comment','')),styles['MCSmall'])])
                tab=Table(data,colWidths=[34*mm,19*mm,23*mm,17*mm,17*mm,75*mm],repeatRows=1,hAlign='LEFT')
                tab.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eaf0f8')),('TEXTCOLOR',(0,0),(-1,0),colors.HexColor('#334155')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#d5deea')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#fafbfd')])]))
                story.append(tab);story.append(Paragraph('Appréciation générale',styles['MCSection']));story.append(Paragraph(esc(payload.get('overall','')) or '—',styles['MCBody']))
                comps=payload.get('competencies') or []
                if comps:
                    story.append(Paragraph('Compétences',styles['MCSection']))
                    cd=[[Paragraph('<b>Compétence</b>',styles['MCSmall']),Paragraph('<b>Niveau</b>',styles['MCSmall'])]]+[[Paragraph(esc(x.get('name','')),styles['MCSmall']),Paragraph(esc(x.get('level','—')),styles['MCSmall'])] for x in comps]
                    ct=Table(cd,colWidths=[140*mm,45*mm],repeatRows=1);ct.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eaf0f8')),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#d5deea')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]));story.append(ct);story.append(Paragraph('Nomenclature : Très bien · Bien · Fragile · Insuffisant',styles['MCSmall']))
                story.extend([Spacer(1,5*mm),Paragraph('Absences : '+esc(payload.get('absences',0))+' · Retards : '+esc(payload.get('late',0)),styles['MCSmall'])])
                if payload.get('published') and payload.get('publishedAt'):
                    try: pub=datetime.fromisoformat(str(payload['publishedAt']).replace('Z','+00:00')).astimezone().strftime('%d/%m/%Y')
                    except Exception: pub=''
                    if pub: story.append(Paragraph('Bulletin publié officiellement le '+pub,styles['MCSmall']))
                def footer(canvas,document):
                    canvas.saveState();canvas.setStrokeColor(colors.HexColor('#d5deea'));canvas.line(12*mm,9*mm,A4[0]-12*mm,9*mm);canvas.setFont(font,7);canvas.setFillColor(colors.HexColor('#64748b'));canvas.drawString(12*mm,5.5*mm,'Document généré par MaClasse');canvas.drawRightString(A4[0]-12*mm,5.5*mm,'Page %s'%document.page);canvas.restoreState()
                doc.build(story,onFirstPage=footer,onLaterPages=footer)
                raw=buf.getvalue();self.send_response(200);self.send_header('Content-Type','application/pdf');self.send_header('Content-Disposition','attachment; filename="bulletin.pdf"');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw);return
            except Exception as e:
                return self._json({'error':'Génération PDF impossible: '+str(e)},500)

        if path=='/api/data' or path=='/api/save':
            try: data=json.loads(body.decode('utf-8'))
            except Exception: return self._json({'error':'JSON invalide'},400)
            if not isinstance(data, dict): return self._json({'error':'Les données MaClasse doivent être un objet JSON.'},400)
            # V21.14 : sauvegarde par paliers. Une copie est conservée avant écrasement,
            # au maximum toutes les 6 h, avec une rétention de 30 jours.
            with DATA_LOCK:
                try:
                    current = None
                    if os.path.exists(DATA_FILE):
                        with open(DATA_FILE, encoding='utf-8') as f: current = json.load(f)
                    current_revision=_database_revision()
                    supplied_revision=str(self.headers.get('If-Match') or '').strip().strip('"')
                    if not supplied_revision:
                        return self._json({'error':'Version de données manquante. Recharge MaClasse avant d’enregistrer.','code':'REVISION_REQUIRED'},428,headers={'X-MaClasse-Revision':current_revision})
                    if not hmac.compare_digest(supplied_revision,current_revision):
                        return self._json({'error':'Les données ont été modifiées depuis votre dernier chargement. Recharge MaClasse avant de réessayer.','code':'REVISION_CONFLICT'},409,headers={'X-MaClasse-Revision':current_revision})
                    if current is not None and current != data:
                        if user.get('role')=='student':
                            try: data=_merge_student_data(current,data,user)
                            except PermissionError: return self._json({'error':'Périmètre élève non autorisé.'},403)
                        elif user.get('role')!='admin':
                            if not _validate_cloud_item_changes(current,data,user):
                                return self._json({'error':'Modification Cloud non autorisée.'},403)
                            try: data=_merge_teacher_data(current,data,user)
                            except PermissionError: return self._json({'error':'Périmètre professeur non autorisé.'},403)
                        self._create_backup(force=False)
                except (OSError, ValueError, TypeError) as e:
                    return self._json({'error': f'Sauvegarde de sécurité impossible : {e}'}, 500)
                tmp=f'{DATA_FILE}.{threading.get_ident()}.tmp'
                try:
                    with open(tmp,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)
                    os.replace(tmp,DATA_FILE)
                    saved_revision=_database_revision()
                except Exception:
                    try:
                        if os.path.exists(tmp): os.remove(tmp)
                    except OSError: pass
                    raise
            return self._json({'ok':True},headers={'X-MaClasse-Revision':saved_revision})

        if path=='/api/cloud-mkdir':
            try:
                obj=json.loads(body.decode('utf-8')); name=os.path.basename(str(obj.get('name','')).strip())
                if not _cloud_scope_allowed(user,str(obj.get('space','personal')),owner_id=obj.get('ownerId',''),class_id=obj.get('classId',''),group=obj.get('group',''),write=True): return self._json({'error':'Accès à cet espace Cloud refusé.'},403)
                if not name or name in ('.','..'): return self._json({'error':'Nom de dossier invalide'},400)
                safe=lambda x: re.sub(r'[^a-zA-Z0-9_-]+','_',str(x or ''))[:120] or 'root'
                space=safe(obj.get('space','personal')); owner=safe(obj.get('ownerId','teacher-local')); cid=safe(obj.get('classId','')); group=safe(obj.get('group',''))
                parts=['cloud',space]
                if space=='personal': parts += ['users',owner]
                else:
                    if cid: parts += ['classes',cid]
                    if group: parts += ['groups',group]
                parent_path=str(obj.get('parentPath','')).replace('\\','/').lstrip('/')
                if parent_path:
                    if not parent_path.startswith('cloud/') or not _cloud_path_allowed(user,parent_path,write=True): return self._json({'error':'Création dans ce dossier refusée.'},403)
                    pp=[x for x in parent_path.split('/') if x not in ('','.','..')]
                    base=_safe_upload_path(parent_path)
                    if not os.path.isdir(base): return self._json({'error':'Dossier parent introuvable.'},400)
                    target_dir=os.path.realpath(os.path.join(base,safe(obj.get('name','folder'))))
                    uploads_root=os.path.realpath(UPLOADS)
                    if os.path.commonpath([target_dir,uploads_root])!=uploads_root: return self._json({'error':'Chemin invalide'},400)
                    os.makedirs(target_dir,exist_ok=False)
                    return self._json({'ok':True,'path':_uploads_relative(target_dir)})
                parts += ['folders',safe(obj.get('id','folder'))]
                target_dir=_safe_upload_path('/'.join(parts)); os.makedirs(target_dir,exist_ok=False)
                return self._json({'ok':True,'path':'/'.join(parts)})
            except FileExistsError: return self._json({'error':'Ce dossier physique existe déjà.'},409)
            except Exception as e: return self._json({'error':str(e)},400)
        if path=='/api/cloud-rename':
            try:
                obj=json.loads(body.decode('utf-8')); rel=str(obj.get('path','')).replace('\\','/').lstrip('/'); new=os.path.basename(str(obj.get('name','')).strip())
                if not _cloud_path_allowed(user,rel,write=True) or not _cloud_known_item_path(rel): return self._json({'error':'Modification de ce fichier refusée.'},403)
                if not rel or not new or new in ('.','..') or '/' in new or '\\' in new: return self._json({'error':'Nom invalide'},400)
                parts=[x for x in rel.split('/') if x not in ('','.','..')]
                target=_safe_upload_path(rel); base=os.path.dirname(target); dest=_safe_upload_path(_uploads_relative(base)+'/'+new)
                if not os.path.exists(target): return self._json({'error':'Le fichier physique est introuvable.'},404)
                if os.path.exists(dest): return self._json({'error':'Un fichier portant ce nom existe déjà.'},409)
                os.rename(target,dest)
                newrel=_uploads_relative(dest)
                return self._json({'ok':True,'path':newrel})
            except Exception as e: return self._json({'error':str(e)},400)

        if path=='/api/cloud-move':
            try:
                obj=json.loads(body.decode('utf-8')); source=str(obj.get('source','')).replace('\\','/').lstrip('/'); destination=str(obj.get('destination','')).replace('\\','/').lstrip('/'); name=os.path.basename(str(obj.get('name','')).strip())
                if not source or not destination or not name or '/' in name or '\\' in name: return self._json({'error':'Chemin invalide'},400)
                if not _cloud_path_allowed(user,source,write=True) or not _cloud_known_item_path(source) or not _cloud_path_allowed(user,destination,write=True): return self._json({'error':'Déplacement Cloud non autorisé.'},403)
                clean=lambda r:[x for x in r.split('/') if x not in ('','.','..')]
                sp=_safe_upload_path(source); dp=_safe_upload_path(destination+'/'+name)
                if not os.path.exists(sp): return self._json({'error':'Source physique introuvable.'},404)
                if os.path.exists(dp): return self._json({'error':'Un élément porte déjà ce nom dans le dossier destination.'},409)
                os.makedirs(os.path.dirname(dp),exist_ok=True); os.rename(sp,dp)
                return self._json({'ok':True,'path':_uploads_relative(dp)})
            except Exception as e: return self._json({'error':str(e)},400)

        if path=='/api/cloud-copy':
            try:
                obj=json.loads(body.decode('utf-8')); source=str(obj.get('source','')).replace('\\','/').lstrip('/'); destination=str(obj.get('destination','')).replace('\\','/').lstrip('/'); name=os.path.basename(str(obj.get('name','')).strip())
                if not source or not destination or not name or '/' in name or '\\' in name:return self._json({'error':'Chemin invalide'},400)
                if not _cloud_path_allowed(user,source,write=False) or not _cloud_known_item_path(source) or not _cloud_path_allowed(user,destination,write=True): return self._json({'error':'Copie Cloud non autorisée.'},403)
                clean=lambda r:[x for x in r.split('/') if x not in ('','.','..')]
                spath=_safe_upload_path(source); dpath=_safe_upload_path(destination+'/'+name)
                if not os.path.exists(spath):return self._json({'error':'Source physique introuvable.'},404)
                if os.path.exists(dpath):return self._json({'error':'Un élément porte déjà ce nom dans le dossier destination.'},409)
                os.makedirs(os.path.dirname(dpath),exist_ok=True)
                if os.path.isdir(spath):shutil.copytree(spath,dpath)
                else:shutil.copy2(spath,dpath)
                return self._json({'ok':True,'path':_uploads_relative(dpath)})
            except Exception as e:return self._json({'error':str(e)},400)

        if path=='/api/cloud-delete':
            try:
                obj=json.loads(body.decode('utf-8')); rel=str(obj.get('path','')).replace('\\','/').lstrip('/')
                if not rel:return self._json({'error':'Chemin invalide'},400)
                target=_safe_upload_path(rel)
                if not _cloud_path_allowed(user,rel,write=True) or not _cloud_known_item_path(rel): return self._json({'error':'Suppression Cloud non autorisée.'},403)
                clean=lambda r:[x for x in r.split('/') if x not in ('','.','..')]
                parts=clean(rel)
                if not parts: return self._json({'error':'Chemin invalide'},400)
                if not os.path.exists(target):return self._json({'ok':True,'missing':True})
                if os.path.isdir(target):shutil.rmtree(target)
                else:os.remove(target)
                return self._json({'ok':True})
            except Exception as e:return self._json({'error':str(e)},400)

        if path=='/api/delete-upload':
            try:
                obj=json.loads(body.decode('utf-8')); name=str(obj.get('name','')).replace('\\','/').lstrip('/')
                parts=[x for x in name.split('/') if x not in ('','.','..')]
                target=_safe_upload_path(name) if parts else ''
                if not parts: return self._json({'error':'Chemin invalide.'},400)
                can_write=_student_can_access_upload(user,name,write=True) if user.get('role')=='student' else _teacher_can_access_upload(user,name,write=True)
                can_read=_student_can_access_upload(user,name,write=False) if user.get('role')=='student' else _teacher_can_access_upload(user,name,write=False)
                if name.startswith('cloud/') or not can_write or not can_read:
                    return self._json({'error':'Suppression de ce fichier non autorisée. Utilisez la commande Cloud dédiée pour les éléments Cloud.'},403)
                if os.path.exists(target): shutil.rmtree(target) if os.path.isdir(target) else os.remove(target)
                return self._json({'ok':True})
            except Exception:
                return self._json({'ok':False},400)
        if path=='/api/reset':
            if user.get('role')!='admin': return self._json({'error':'Réservé à la direction.'},403)
            # V19.7: jamais de réinitialisation sans copie de sécurité préalable.
            try:
                with DATA_LOCK:
                    backup_name = None
                    if os.path.exists(DATA_FILE):
                        with open(DATA_FILE,encoding='utf-8') as f: current = json.load(f)
                        if current:
                            backup_name = self._create_backup(force=True)
                    tmp=f'{DATA_FILE}.{threading.get_ident()}.tmp'
                    with open(tmp,'w',encoding='utf-8') as f: json.dump({},f,ensure_ascii=False)
                    os.replace(tmp,DATA_FILE)
                return self._json({'ok':True,'backup':backup_name})
            except Exception as e:
                try:
                    if os.path.exists(DATA_FILE+'.tmp'): os.remove(DATA_FILE+'.tmp')
                except OSError: pass
                return self._json({'error':f'Réinitialisation annulée : copie de sécurité impossible ({e}).'},500)
        if path=='/api/upload':
            if length>50*1024*1024: return self._json({'error':'Fichier trop volumineux (50 Mo maximum).'},413)
            raw_name=self.headers.get('X-Filename','fichier') or 'fichier'
            name=os.path.basename(raw_name).strip() or 'fichier'
            raw_folder=self.headers.get('X-Upload-Folder','general') or 'general'
            folder='/'.join(x for x in re.split(r'[/\\]+',raw_folder) if x not in ('','.','..'))
            if user.get('role')=='student':
                sid=str(user.get('studentId') or '')
                if folder!=f'submissions/{sid}': return self._json({'error':'Les élèves peuvent uniquement déposer des fichiers dans leur propre espace de rendu.'},403)
            elif not _teacher_can_access_upload(user,folder,write=True):
                return self._json({'error':'Téléversement dans ce dossier non autorisé.'},403)
            target_dir=_safe_upload_path(folder) if folder else os.path.realpath(UPLOADS)
            os.makedirs(target_dir,exist_ok=True)
            base,ext=os.path.splitext(name); candidate=name; n=1
            while os.path.exists(os.path.join(target_dir,candidate)):
                candidate=f'{base}_{n}{ext}'; n+=1
            target=os.path.join(target_dir,candidate)
            with open(target,'wb') as f: f.write(body)
            rel='/'.join([folder,candidate]) if folder else candidate
            return self._json({'name':rel,'url':'/data/uploads/'+rel,'size':len(body)})
        self.send_error(404)

def _assert_loopback_host(host):
    if str(host or '').strip().lower() not in ('127.0.0.1','localhost','::1'):
        raise ValueError('MaClasse V25 reste locale par défaut : utilise le mode réseau privé explicitement documenté pour un test LAN.')


def _assert_server_host(host, allow_lan=False):
    value=str(host or '').strip().lower()
    if value in ('127.0.0.1','localhost','::1'):
        return True
    if not allow_lan:
        raise ValueError('Accès réseau désactivé. Active explicitement MACLASSE_LAN_MODE=1 pour un test privé.')
    try:
        address=ipaddress.ip_address(value)
    except ValueError as exc:
        raise ValueError('En mode réseau, MACLASSE_HOST doit être une adresse IPv4 privée précise.') from exc
    if not isinstance(address,ipaddress.IPv4Address) or not address.is_private or address.is_loopback or address.is_link_local or address.is_multicast or address.is_unspecified:
        raise ValueError('Adresse refusée : utilise uniquement une adresse IPv4 privée du réseau local.')
    return True


if __name__=='__main__':
    os.chdir(ROOT)
    try:
        _assert_server_host(HOST,allow_lan=os.environ.get('MACLASSE_LAN_MODE')=='1')
    except ValueError as error:
        print(f'ERREUR DE SÉCURITÉ : {error}')
        raise SystemExit(2)
    mode='réseau privé — HTTP non chiffré, données fictives uniquement' if HOST not in ('127.0.0.1','localhost','::1') else 'local'
    print(f'MaClasse V{APP_VERSION} — {mode} — http://{HOST}:{PORT}')
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
