import argparse
from linksets_collection import LinksetsCollection

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process reconciliation configs in JSON files.')
    parser.add_argument('-r', '--resources', required=True)
    parser.add_argument('-m', '--mappings', required=True)
    parser.add_argument('--sql-only', action='store_true')
    parser.add_argument('--resources-only', action='store_true')
    parser.add_argument('--mappings-only', action='store_true')
    args = parser.parse_args()

    with LinksetsCollection(
        resources_filename=args.resources,
        matches_filename=args.mappings,
        resources_only=args.resources_only,
        matches_only=args.mappings_only,
        sql_only=args.sql_only,
    ) as linksets_collection:
        linksets_collection.run()
