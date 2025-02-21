import os
import sys
import locale
import signal
import importlib

from types import FrameType
from typing import Optional
from lenticularlens.util.config_logging import config_logger

locale.setlocale(locale.LC_ALL, '')

if __name__ == '__main__':
    def teardown(signum: int = 0, frame: Optional[FrameType] = None) -> None:
        worker.teardown()
        sys.exit(signum)


    config_logger()

    worker_type = os.environ['WORKER_TYPE'].lower()
    worker_module = importlib.import_module(f'lenticularlens.workers.{worker_type}.worker')
    worker_class = getattr(worker_module, f'{worker_type.capitalize()}Worker')
    worker = worker_class()

    signal.signal(signal.SIGTERM, teardown)
    signal.signal(signal.SIGINT, teardown)

    worker.run()
