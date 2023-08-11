import time
import threading

from ll.util.config_db import conn_pool


class WorkerJob:
    def __init__(self, target):
        self._target = target
        self._killed = False
        self._status = None
        self._exception = None
        self._db_conn = None

    def run(self):
        thread = threading.Thread(target=self.run_in_thread)
        thread.start()

        while not self._killed and thread.is_alive():
            self.watch_process()
            self.watch_kill()
            time.sleep(1)

        if self._killed:
            return

        if self._exception:
            self.on_exception()
        else:
            self.on_finish()

    def run_in_thread(self):
        try:
            self._db_conn = conn_pool.getconn()
            self._target()
            self._db_conn.commit()
        except Exception as e:
            self._exception = e
            raise e
        finally:
            conn_pool.putconn(self._db_conn)
            self._db_conn = None

    def kill(self, reset=True):
        self._killed = True

        if self._db_conn and not self._db_conn.closed:
            self._db_conn.cancel()

        self.on_kill(reset)

    def watch_process(self):
        pass

    def watch_kill(self):
        pass

    def on_kill(self, reset):
        pass

    def on_exception(self):
        pass

    def on_finish(self):
        pass
