import copy, json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server

class MailboxAndUploadScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.old_data_file=server.DATA_FILE; self.old_uploads=server.UPLOADS
        server.DATA_FILE=os.path.join(self.tmp.name,'maclasse.json')
        server.UPLOADS=os.path.join(self.tmp.name,'uploads')
        os.makedirs(server.UPLOADS)
        self.data={
            'users':[{'id':'t1','role':'teacher','first':'Prof','last':'Un'},{'id':'t2','role':'teacher','first':'Prof','last':'Deux'}],
            'classes':[{'id':'c1','teacherIds':['t1']},{'id':'c2','teacherIds':['t2']}],
            'students':[{'id':'s1','classId':'c1'},{'id':'s2','classId':'c2'}],
            'lessons':[{'id':'l1','classId':'c1'}],
            'mailboxV2':{
                'schemaVersion':2,'resetPending':False,
                'messages':[
                    {'id':'m1','sender':{'key':'teacher:t1'},'to':['teacher:t2'],'body':'private to t1'},
                    {'id':'m2','sender':{'key':'teacher:t2'},'to':['teacher:t1'],'bcc':['teacher:t3'],'body':'to t1'},
                    {'id':'m3','sender':{'key':'teacher:t2'},'to':['teacher:t2'],'body':'private to t2'},
                ],
                'states':{'teacher:t1':{'m1':{'read':True}},'teacher:t2':{'m3':{'read':False}}},
                'drafts':[{'id':'d1','owner':'teacher:t1','body':'draft1'},{'id':'d2','owner':'teacher:t2','body':'draft2'}],
                'folders':[{'id':'f1','owner':'teacher:t1'},{'id':'f2','owner':'teacher:t2'}],
            },
            'attachments':[{'id':'a1','classId':'c1','url':'/data/uploads/lessons/c1/shared.pdf'}],
            'cloudItems':[]
        }
        with open(server.DATA_FILE,'w',encoding='utf-8') as f: json.dump(self.data,f)
        self.t1={'id':'t1','role':'teacher'}

    def tearDown(self):
        server.DATA_FILE=self.old_data_file; server.UPLOADS=self.old_uploads; self.tmp.cleanup()

    def test_mailbox_projection_only_includes_participant_messages_and_own_private_state(self):
        view=server._teacher_visible_data(self.data,self.t1)['mailboxV2']
        self.assertEqual({m['id'] for m in view['messages']},{'m1','m2'})
        received=next(m for m in view['messages'] if m['id']=='m2')
        self.assertEqual(received['bcc'],[])
        sender_view=server._teacher_visible_data(self.data,{'id':'t2','role':'teacher'})['mailboxV2']
        sent=next(m for m in sender_view['messages'] if m['id']=='m2')
        self.assertEqual(sent['bcc'],['teacher:t3'])
        self.assertEqual(set(view['states']),{'teacher:t1'})
        self.assertEqual([d['id'] for d in view['drafts']],['d1'])
        self.assertEqual([f['id'] for f in view['folders']],['f1'])

    def test_mailbox_merge_preserves_other_users_and_sent_message_content(self):
        incoming=copy.deepcopy(server._teacher_visible_data(self.data,self.t1))
        incoming['mailboxV2']['messages'][0]['body']='tampered'
        incoming['mailboxV2']['messages'].append({'id':'forged','sender':{'key':'teacher:t2','role':'teacher','id':'t2'},'to':['teacher:t1'],'body':'forged'})
        incoming['mailboxV2']['drafts'].append({'id':'forged-draft','owner':'teacher:t2'})
        merged=server._merge_teacher_data(self.data,incoming,self.t1)
        messages={m['id']:m for m in merged['mailboxV2']['messages']}
        self.assertEqual(messages['m1']['body'],'private to t1')
        self.assertEqual(messages['m3']['body'],'private to t2')
        self.assertNotIn('forged',messages)
        self.assertEqual({d['id'] for d in merged['mailboxV2']['drafts']},{'d1','d2'})

    def test_non_cloud_upload_requires_visible_record_reference_for_read(self):
        path=os.path.join(server.UPLOADS,'lessons','c1'); os.makedirs(path)
        with open(os.path.join(path,'shared.pdf'),'wb') as f:f.write(b'ok')
        with open(os.path.join(path,'secret.pdf'),'wb') as f:f.write(b'no')
        self.assertTrue(server._teacher_can_access_upload(self.t1,'lessons/c1/shared.pdf',write=False))
        self.assertFalse(server._teacher_can_access_upload(self.t1,'lessons/c1/secret.pdf',write=False))

    def test_teacher_cannot_upload_into_another_teachers_mailbox(self):
        self.assertFalse(server._teacher_can_access_upload(self.t1,'mail-v2/teacher:t2',write=True))
        self.assertFalse(server._teacher_can_access_upload(self.t1,'mail-v2-drafts/teacher:t2',write=True))
        self.assertTrue(server._teacher_can_access_upload(self.t1,'mail-v2/teacher:t1',write=True))

    def test_teacher_cannot_read_another_teacher_mail_attachment_by_path_guess(self):
        path=os.path.join(server.UPLOADS,'mail-v2','teacher:t2'); os.makedirs(path)
        with open(os.path.join(path,'secret.pdf'),'wb') as f:f.write(b'no')
        self.assertFalse(server._teacher_can_access_upload(self.t1,'mail-v2/teacher:t2/secret.pdf',write=False))

    def test_own_mail_attachment_is_accessible_but_foreign_draft_is_not(self):
        path=os.path.join(server.UPLOADS,'mail-v2','teacher:t1'); os.makedirs(path)
        draft=os.path.join(server.UPLOADS,'mail-v2-drafts','teacher:t1'); os.makedirs(draft)
        with open(os.path.join(path,'own.pdf'),'wb') as f:f.write(b'ok')
        with open(os.path.join(draft,'own.pdf'),'wb') as f:f.write(b'ok')
        self.assertTrue(server._teacher_can_access_upload(self.t1,'mail-v2/teacher:t1/own.pdf',write=False))
        self.assertTrue(server._teacher_can_access_upload(self.t1,'mail-v2-drafts/teacher:t1/own.pdf',write=False))

if __name__=='__main__': unittest.main()
