import sys
import signal
import threading

from web_server import app as web_server
from worker.app import Worker, WorkerType

if __name__ == "__main__":
    def teardown(signum=0, stack=None):
        timbuctoo_worker.teardown()
        alignments_worker.teardown()
        clustering_worker.teardown()
        sys.exit(signum)


    signal.signal(signal.SIGTERM, teardown)
    signal.signal(signal.SIGINT, teardown)

    timbuctoo_worker = Worker(WorkerType.TIMBUCTOO)
    alignments_worker = Worker(WorkerType.ALIGNMENTS)
    clustering_worker = Worker(WorkerType.CLUSTERINGS)

    threading.Thread(target=timbuctoo_worker.run).start()
    threading.Thread(target=alignments_worker.run).start()
    threading.Thread(target=clustering_worker.run).start()

    threading.Thread(target=web_server.app.run).start()
