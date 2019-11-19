import sys
import signal
import threading

from web import app as webapp
from worker import Worker, WorkerType

if __name__ == "__main__":
    def teardown(signum=0, stack=None):
        timbuctoo_worker.teardown()
        alignment_worker.teardown()
        clustering_worker.teardown()
        sys.exit(signum)


    signal.signal(signal.SIGTERM, teardown)
    signal.signal(signal.SIGINT, teardown)

    timbuctoo_worker = Worker(WorkerType.TIMBUCTOO)
    alignment_worker = Worker(WorkerType.ALIGNMENT)
    clustering_worker = Worker(WorkerType.CLUSTERING)

    threading.Thread(target=timbuctoo_worker.run).start()
    threading.Thread(target=alignment_worker.run).start()
    threading.Thread(target=clustering_worker.run).start()

    webapp.run()
