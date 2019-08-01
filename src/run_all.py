import threading

from web_server import app as web_server
from jobs_worker import app as jobs_worker
from timbuctoo_worker import app as timbuctoo_worker

if __name__ == "__main__":
    threading.Thread(target=web_server.app.run).start()
    threading.Thread(target=timbuctoo_worker.run).start()

    jobs_worker.run()
