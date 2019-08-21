# coding=utf-8
# __author__ = 'Mio'
from Manager.handler import LoginHandler
from Manager.handler.create import UploadHandler

urls = [
    (r"/upload", UploadHandler),
    (r"/login", LoginHandler),
]