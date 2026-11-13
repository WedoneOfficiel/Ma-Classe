import json
import os
import tempfile
import unittest
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server


class CloudPermissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_data_file = server.DATA_FILE
        self.old_uploads = server.UPLOADS
        server.DATA_FILE = os.path.join(self.tmp.name, 'maclasse.json')
        server.UPLOADS = os.path.join(self.tmp.name, 'uploads')
        os.makedirs(server.UPLOADS)
        self.data = {
            'users': [
                {'id': 't1', 'role': 'teacher', 'first': 'Prof', 'last': 'Un'},
                {'id': 't2', 'role': 'teacher', 'first': 'Prof', 'last': 'Deux'},
            ],
            'classes': [{'id':'c1','teacherIds':['t1']},{'id':'c2','teacherIds':['t2']}],
            'cloudItems': [
                {'id': 'personal1', 'type': 'file', 'space': 'personal', 'ownerId': 't1', 'serverName': 'cloud/personal/users/t1/a.pdf', 'shares': []},
                {'id': 'class1', 'type': 'file', 'space': 'class', 'ownerId': 't1', 'classId': 'c1', 'serverName': 'cloud/class/classes/c1/a.pdf', 'shares': []},
                {'id': 'shared1', 'type': 'file', 'space': 'personal', 'ownerId': 't1', 'serverName': 'cloud/personal/users/t1/shared.pdf', 'shares': [{'type': 'teacher', 'id': 't2', 'role': 'view'}]},
                {'id': 'shared_edit', 'type': 'file', 'space': 'personal', 'ownerId': 't1', 'serverName': 'cloud/personal/users/t1/edit.pdf', 'shares': [{'type': 'teacher', 'id': 't2', 'role': 'edit'}]},
            ],
        }
        with open(server.DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f)
        self.t1 = {'id': 't1', 'role': 'teacher'}
        self.t2 = {'id': 't2', 'role': 'teacher'}

    def tearDown(self):
        server.DATA_FILE = self.old_data_file
        server.UPLOADS = self.old_uploads
        self.tmp.cleanup()

    def test_cloud_paths_use_real_upload_root_when_base_path_is_a_symlink(self):
        # macOS peut exposer /var comme un lien vers /private/var.
        # Les chemins relatifs doivent utiliser le même chemin réel.
        self.assertEqual(
            server._uploads_relative(server._safe_upload_path('cloud/personal/users/t1/a.pdf')),
            'cloud/personal/users/t1/a.pdf'
        )
        self.assertTrue(server._cloud_path_allowed(self.t1, 'cloud/personal/users/t1/a.pdf'))

    def test_non_cloud_path_is_never_authorized_as_cloud(self):
        self.assertFalse(server._cloud_path_allowed(self.t1, 'general/secret.pdf'))
        self.assertFalse(server._cloud_path_allowed(self.t2, 'lessons/private.pdf'))

    def test_personal_space_is_private(self):
        self.assertTrue(server._cloud_path_allowed(self.t1, 'cloud/personal/users/t1/a.pdf'))
        self.assertFalse(server._cloud_path_allowed(self.t2, 'cloud/personal/users/t1/a.pdf'))

    def test_class_space_read_only_for_non_owner_teacher(self):
        self.assertTrue(server._cloud_path_allowed(self.t1, 'cloud/class/classes/c1/a.pdf', write=True))
        self.assertFalse(server._cloud_path_allowed(self.t2, 'cloud/class/classes/c1/a.pdf'))

    def test_shared_permissions_respect_view_and_edit(self):
        self.assertTrue(server._cloud_path_allowed(self.t2, 'cloud/personal/users/t1/shared.pdf', write=False))
        self.assertFalse(server._cloud_path_allowed(self.t2, 'cloud/personal/users/t1/shared.pdf', write=True))
        self.assertTrue(server._cloud_path_allowed(self.t2, 'cloud/personal/users/t1/edit.pdf', write=True))

    def test_shared_folder_grants_access_to_descendants(self):
        self.data['cloudItems'].append({'id': 'shared_folder', 'type': 'folder', 'space': 'personal', 'ownerId': 't1', 'serverName': 'cloud/personal/users/t1/shared-folder', 'shares': [{'type': 'teacher', 'id': 't2', 'role': 'edit'}]})
        self.data['cloudItems'].append({'id': 'child_file', 'type': 'file', 'space': 'personal', 'ownerId': 't1', 'parentId': 'shared_folder', 'serverName': 'cloud/personal/users/t1/shared-folder/child.pdf', 'shares': []})
        with open(server.DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f)
        self.assertTrue(server._cloud_path_allowed(self.t2, 'cloud/personal/users/t1/shared-folder/child.pdf', write=True))

    def test_unregistered_physical_item_cannot_be_renamed_or_deleted(self):
        self.assertFalse(server._cloud_known_item_path('cloud/personal/users/t1/not-in-db.pdf'))
        self.assertTrue(server._cloud_known_item_path('cloud/personal/users/t1/a.pdf'))

    def test_teacher_cannot_forge_personal_cloud_owner(self):
        updated = dict(self.data)
        updated['cloudItems'] = list(self.data['cloudItems']) + [
            {'id': 'fake', 'type': 'file', 'space': 'personal', 'ownerId': 't2', 'serverName': 'cloud/personal/users/t2/fake.pdf', 'shares': []}
        ]
        self.assertFalse(server._validate_cloud_item_changes(self.data, updated, self.t1))

    def test_teacher_cannot_repoint_owned_item_to_another_personal_space(self):
        updated = dict(self.data)
        updated['cloudItems'] = [dict(x) for x in self.data['cloudItems']]
        updated['cloudItems'][0]['serverName'] = 'cloud/personal/users/t2/stolen.pdf'
        self.assertFalse(server._validate_cloud_item_changes(self.data, updated, self.t1))

    def test_teacher_can_create_in_assigned_class_only(self):
        allowed = {'cloudItems': [{'id': 'new', 'space': 'class', 'ownerId': 't1', 'classId': 'c1', 'serverName': 'cloud/class/classes/c1/new.pdf'}]}
        denied = {'cloudItems': [{'id': 'new', 'space': 'class', 'ownerId': 't1', 'classId': 'c2', 'serverName': 'cloud/class/classes/c2/new.pdf'}]}
        self.assertTrue(server._validate_cloud_item_changes({'users': self.data['users'], 'classes': self.data['classes'], 'cloudItems': []}, allowed, self.t1))
        self.assertFalse(server._validate_cloud_item_changes({'users': self.data['users'], 'classes': self.data['classes'], 'cloudItems': []}, denied, self.t1))


if __name__ == '__main__':
    unittest.main()
