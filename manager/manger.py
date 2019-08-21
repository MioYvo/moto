# coding=utf-8
# __author__ = 'Mio'
import logging
import signal
from pathlib import Path

import tornado.escape
import tornado.ioloop
import tornado.web
import uvloop
from tornado.options import define, options, parse_command_line

from Manager.model import DBPool, dbpool
from Manager.settings import ioloop
from Manager.urls import urls

define("port", default=8888, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")


class MatildaApp(tornado.web.Application):
    def __init__(self):
        super(MatildaApp, self).__init__(
            handlers=urls,
            cookie_secret="Vhp1qJHkFnbP4OqsoGMgVYkpu4d7tNwh",
            # xsrf_cookies=True,
            login_url="/login",
            template_path=Path("templates").absolute(),
            static_path=Path("static").absolute(),
            debug=options.debug,
        )
        self.pool = None

    # noinspection PyAttributeOutsideInit


app = MatildaApp()


def signal_handler(sig, frame):
    """Triggered when a signal is received from system."""
    _ioloop = tornado.ioloop.IOLoop.current()

    def shutdown():
        """Force server and ioloop shutdown."""
        logging.info('Shutting down server')
        logging.info('Terminating db connection pool')
        if app.pool:
            app.pool.terminate()
            logging.info('Terminated db connection pool')
        _ioloop.stop()
        logging.info('Bye')

    logging.warning('Caught signal: %s', sig)
    _ioloop.add_callback_from_signal(shutdown)


def main():
    parse_command_line()
    ioloop.run_sync(dbpool.make_pool)
    app.pool = dbpool.pool
    app.listen(options.port)
    logging.info(f"App run on: http://localhost:{options.port}")
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    ioloop.start()


if __name__ == "__main__":
    main()
