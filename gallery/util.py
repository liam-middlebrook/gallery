from addict import Dict
from flask import session
from functools import wraps
import hashlib
import os

from gallery.ldap import ldap_is_eboard
from gallery.ldap import ldap_is_rtp
from gallery.ldap import ldap_convert_uuid_to_displayname

from gallery.models import Directory
from gallery.models import File

DEFAULT_THUMBNAIL_NAME = 'reedphoto'
ROOT_DIR_ID = 1

def get_dir_file_contents(dir_id):
    contents = [f for f in File.query.filter(File.parent == dir_id).all()]
    contents.sort(key=lambda x: x.get_name())
    contents.sort(key=lambda x: x.date_uploaded)
    return contents

def get_full_dir_path(dir_id):
    path_stack = []
    dir_model = Directory.query.filter(Directory.id == dir_id).first()
    path_stack.append(dir_model.name)
    while dir_model.parent is not None:
        dir_model = Directory.query.filter(Directory.id == dir_model.parent).first()
        path_stack.append(dir_model.name)
    path_stack.pop()
    path = ""

    while not len(path_stack) == 0:
        path = os.path.join(path, path_stack.pop())

    return os.path.join('/', path)

def get_files_tagged(uuids):
    for uuid in uuids:
        if tags:
            tags = Tag.query.filter(
                Tag.file_id.in_(files),
                Tag.uuid == uuid
            )
        else:
            tags = Tag.query.filter(Tag.uuid == uuid)
    return tags


def convert_bytes_to_utf8(dic):
    for key in dic:
        if isinstance(key, bytes):
            try:
                k = key.decode('utf-8')
            except Exception as e:
                print(e)
            v = dic[key]
            del dic[key]
            dic[k] = v
        if isinstance(dic[key], bytes):
            try:
                v = dic[key].decode('utf-8')
            except Exception as e:
                print(e)
            dic[key] = v
    return dic

def gallery_auth(func):
    @wraps(func)
    def wrapped_function(*args, **kwargs):
        uuid = str(session['userinfo'].get('sub', ''))
        uid = str(session['userinfo'].get('preferred_username', ''))
        name = ldap_convert_uuid_to_displayname(uuid)
        is_eboard = ldap_is_eboard(uid)
        is_rtp = ldap_is_rtp(uid)

        auth_dict = {}
        auth_dict['uuid'] = uuid
        auth_dict['uid'] = uid
        auth_dict['name'] = name
        auth_dict['is_eboard'] = is_eboard
        auth_dict['is_rtp'] = is_rtp
        kwargs['auth_dict'] = auth_dict
        return func(*args, **kwargs)
    return wrapped_function

def hash_file(fname):
    m = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            m.update(chunk)
    return m.hexdigest()
