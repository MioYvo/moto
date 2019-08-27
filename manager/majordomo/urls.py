# coding=utf-8
# __author__ = 'Mio'
from majordomo.handler import LoginHandler
from majordomo.handler.create import UploadHandler

urls = [
    (r"/upload", UploadHandler),
    (r"/login", LoginHandler),
]