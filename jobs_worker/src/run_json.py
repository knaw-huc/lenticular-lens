import argparse
from linksets_collection import LinksetsCollection

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process reconciliation configs in JSON files.')
    parser.add_argument('-r', '--resources', required=True)
    parser.add_argument('-m', '--mappings', required=True)
    parser.add_argument('--job-id', required=True)
    parser.add_argument('--sql-only', action='store_true')
    parser.add_argument('--resources-only', action='store_true')
    parser.add_argument('--mappings-only', action='store_true')
    args = parser.parse_args()

    with LinksetsCollection(
        resources_filename=args.resources,
        matches_filename=args.mappings,
        job_id=args.job_id,
        resources_only=args.resources_only,
        matches_only=args.mappings_only,
        sql_only=args.sql_only,
    ) as linksets_collection:
        result = linksets_collection.run()
        if result.has_queued_view:
            exit(3)
