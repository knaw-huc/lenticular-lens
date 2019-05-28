from datasets_config import DatasetsConfig
from config_db import db_conn


if __name__ == '__main__':
    datasets = DatasetsConfig()

    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT dataset_id, collection_id FROM timbuctoo_tables")
            for tim_table in cur:
                collection = datasets.dataset(tim_table[0]).collection(tim_table[1]).create_view(conn)
