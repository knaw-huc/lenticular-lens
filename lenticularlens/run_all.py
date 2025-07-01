import sys
import signal
import threading

from lenticularlens.run_web import app as webapp, socketio
from lenticularlens.workers.timbuctoo.worker import TimbuctooWorker
from lenticularlens.workers.linkset.worker import LinksetWorker
from lenticularlens.workers.lens.worker import LensWorker
from lenticularlens.workers.clustering.worker import ClusteringWorker
from lenticularlens.workers.sparql_classes.worker import SPARQLClassesWorker
from lenticularlens.workers.sparql_properties.worker import SPARQLPropertiesWorker

if __name__ == "__main__":
    def teardown(signum=0, stack=None):
        timbuctoo_worker.teardown()
        linkset_worker.teardown()
        lens_worker.teardown()
        clustering_worker.teardown()
        sys.exit(signum)


    signal.signal(signal.SIGTERM, teardown)
    signal.signal(signal.SIGINT, teardown)

    timbuctoo_worker = TimbuctooWorker()
    linkset_worker = LinksetWorker()
    lens_worker = LensWorker()
    clustering_worker = ClusteringWorker()
    sparql_classes_worker = SPARQLClassesWorker()
    sparql_properties_worker = SPARQLPropertiesWorker()

    threading.Thread(target=timbuctoo_worker.run).start()
    threading.Thread(target=linkset_worker.run).start()
    threading.Thread(target=lens_worker.run).start()
    threading.Thread(target=clustering_worker.run).start()
    threading.Thread(target=sparql_classes_worker.run).start()
    threading.Thread(target=sparql_properties_worker.run).start()

    socketio.run(webapp)
