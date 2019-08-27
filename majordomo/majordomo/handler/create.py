# coding=utf-8
# __author__ = 'Mio'
import tempfile
import shutil
import pathlib

from tornado.log import app_log
from tornado.web import authenticated

from majordomo.handler import ApiHandler
from majordomo.utils.error_code import ERR_ARG


class UploadHandler(ApiHandler):
    @authenticated
    def post(self):
        print(self.current_user)
        if self.request.files:
            data = self.request.files.get('data', ERR_ARG)
            if data:
                data = data[0]
            else:
                self.write_error_response('need data', ERR_ARG)
                return
        else:
            self.write_error_response('need data file', ERR_ARG)
            return

        with tempfile.NamedTemporaryFile() as fp:
            fp.write(data.body)
            try:
                shutil.unpack_archive(fp.name, pathlib.Path('/Users/moto/Life/moto/target'), format=data.filename.rsplit('.', 1)[-1])
            except ValueError as e:
                app_log.error(e)
                self.write_error_response(str(e), ERR_ARG)
                return
            else:
                print(pathlib.Path('/Users/moto/Life/moto/target').exists())
            # zf.extractall()


