import time
import threading

from ll.util.config_db import get_conn, return_conn


class Job:
    def __init__(self, target):
        self.target = target
        self.killed = False
        self.status = None
        self.exception = None
        self.db_conn = None

    def run(self):
        thread = threading.Thread(target=self.run_in_thread)
        thread.start()

        while not self.killed and thread.is_alive():
            self.watch_process()
            self.watch_kill()
            time.sleep(1)

        if self.killed:
            return

        if self.exception:
            self.on_exception()
        else:
            self.on_finish()

    def run_in_thread(self):
        try:
            self.db_conn = get_conn()
            self.target()
            self.db_conn.commit()
        except Exception as e:
            self.exception = e
        finally:
            return_conn(self.db_conn)
            self.db_conn = None

    def kill(self, reset=True):
        self.killed = True

        if self.db_conn and not self.db_conn.closed:
            self.db_conn.cancel()

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
