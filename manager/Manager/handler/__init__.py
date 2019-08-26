# coding=utf-8
# __author__ = 'Mio'
import hashlib
import uuid
import ujson as json
import tornado.web

from Manager.model.tenant import Tenant
from Manager.utils.web import BaseRequestHandler

from cryptography import fernet

FERNET_KEY = "Psyf8Ss-f06GPReu-Ogt2qeKZLcjiZYHDfCf-Zpr-XU="
f = fernet.Fernet(FERNET_KEY)


class ApiHandler(BaseRequestHandler):
    def get_current_user(self):
        token = self.request.headers.get('token', None)
        if token:
            try:
                data = f.decrypt(bytes(token, 'utf8'))
                user = json.loads(data)
            except Exception as e:
                print(e)
                raise tornado.web.HTTPError(403)
            else:
                return user
        else:
            return None


class LoginHandler(BaseRequestHandler):
    def get(self):
        self.write('<html><body><form action="/login" method="post">'
                   'Name: <input type="text" name="name">'
                   '<input type="submit" value="Sign in">'
                   'Name: <input type="password" name="password">'
                   '<input type="submit" value="password">'
                   '</form></body></html>')

    def post(self):
        password = self.get_body_argument('password')
        name = self.get_body_argument('name')
        password_hashed = hashlib.sha256(bytes(password, 'utf8')).hexdigest()
        user = Tenant.get_by_name(name)
        if user and user == password_hashed:
            token = f.encrypt(json.dumps(dict(user)).encode())
            self.set_header('token', token)
            self.redirect("/")
        else:
            raise tornado.web.HTTPError(403)
