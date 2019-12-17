# Lenticular Lenses

Lenticular Lenses is a tool which allows users to construct linksets between entities 
from different Timbuctoo datasets (so called data-alignment or reconciliation). 
Lenticular Lenses tracks the configuration and the algorithms used in the alignment 
and is also able to report on manual corrections and the amount of manual validation done.

1. [Installation with Docker](#installation-with-docker)
1. [API](#api)
    1. [Default](#default)
    1. [Job creation and updates](#job-creation-and-updates)
    1. [Job processes](#job-processes)
    1. [Data retrieval](#data-retrieval)
    1. [Linksets interaction](#linksets-interaction)
    1. [Export](#export)
1. [Job configuration with JSON](#job-configuration-with-json)
    1. [Resources](#resources)
    1. [Mappings](#mappings)
    1. [Condition groups](#condition-groups)
    1. [Property paths](#property-paths)

## Installation with Docker

1. Make sure Docker and Docker Compose are installed
    * _For Windows and Mac users: install [Docker Desktop]( https://www.docker.com/products/docker-desktop)_
1. Use the provided `docker-compose.yml` as a baseline
1. Run `docker-compose up`
1. Visit http://localhost:8000 in your browser

_Note: This will create a folder `pgdata` with the database data. 
To clean up the database and start from scratch, simply remove this folder._

## API

### Default

**URL**: `/`

**Method**: `GET`

Root page. Will return the GUI for the tool. 

---

**URL**: `/datasets`

**Method**: `GET`

**Parameters**: `endpoint`, `hsid`

Returns all available datasets for a specific Timbuctoo GraphQL `endpoint`. 
If logged in, specify the `hsid` to obtain the private datasets.

_Example: `/datasets?endpoint=https://repository.goldenagents.org/v5/graphql`_

---

**URL**: `/downloads`

**Method**: `GET`

Returns all currently running data downloads and finished data downloads from Timbuctoo.

---

**URL**: `/download`

**Method**: `GET`

**Parameters**: `endpoint`, `hsid`, `dataset_id`, `collection_id`

Starts a data download from Timbuctoo from the given Timbuctoo GraphQL `endpoint`.
If logged in, specify the `hsid` to obtain a private datasets.
Use `dataset_id` to specify from which dataset to download 
and `collection_id` to specify the collection from the dataset to download.

_Example: `/download?endpoint=https://repository.goldenagents.org/v5/graphql&dataset_id=ufab7d657a250e3461361c982ce9b38f3816e0c4b__ecartico_20190805&collection_id=schema_Person`_

---

**URL**: `/association_files`

**Method**: `GET`

Returns all available association_files.

### Job creation and updates

**URL**: `/job/create`

**Method**: `POST`

**JSON**: `job_title`, `job_description`

Creates a new job with the given `job_title` and `job_description`. 
Returns the identifier of this new job.

---

**URL**: `/job/update`

**Method**: `POST`

**JSON**: `job_id`, `job_title`, `job_description`, `job_link`, `resources`, `mappings`

Updates a job with the given `job_id`. 
Updates the `job_title`, `job_description`, `job_link`, `resources` and `mappings`.

---

**URL**: `/job/<job_id>`

**Method**: `GET`

Returns the details of a job with the given `job_id`.

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7`_

### Job processes

**URL**: `/job/<job_id>/alignments`

**Method**: `GET`

Returns the details of all alignment jobs with the given `job_id`.

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7/alignments`_

---

**URL**: `/job/<job_id>/clusterings`

**Method**: `GET`

Returns the details of all clustering jobs with the given `job_id`.

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7/clusterings`_

---

**URL**: `/job/<job_id>/run_alignment/<alignment>`

**Method**: `POST`

**JSON**: `restart`

Start an alignment process for the given `alignment` of a specific `job_id`. 
Specify `restart` to restart the process.

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7/run_alignment/0`_

---

**URL**: `/job/<job_id>/run_clustering/<alignment>`

**Method**: `POST`

**JSON**: `association_file`, `clustering_type`

Start an clustering process for the given `alignment` of a specific `job_id`. 
Specify an `association_file` to reconcile a given cluster.
Specify `clustering_type`, which is `default` by default.

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7/run_clustering/0`_

---

**URL**: `/job/<job_id>/kill_alignment/<alignment>`

**Method**: `POST`

Stop an alignment process for the given `alignment` of a specific `job_id`. 

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7/kill_alignment/0`_

---

**URL**: `/job/<job_id>/kill_clustering/<alignment>`

**Method**: `POST`

Stop an clustering process for the given `alignment` of a specific `job_id`.

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7/kill_clustering/0`_

### Data retrieval

**URL**: `/job/<job_id>/resource/<resource_label>`

**Method**: `GET`

**Parameters**: `total`, `limit`, `offset`

Returns all data for a resource with the label `resource_label` of the given `job_id`.
Use `limit` and `offset` for paging.
Specify `total` to only return the total number of entities.

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7/resource/LimitedPersons`_

---

**URL**: `/job/<job_id>/alignment/<alignment>`

**Method**: `GET`

**Parameters**: `cluster_id`, `limit`, `offset`

Returns the linkset for alignment `alignment` of the given `job_id`.
Use `limit` and `offset` for paging.
Specify `cluster_id` to only return the links of a specific cluster.

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7/alignment/0`_

---

**URL**: `/job/<job_id>/clusters/<alignment>`

**Method**: `GET`

**Parameters**: `association`, `limit`, `offset`

Returns the clusters for alignment `alignment` of the given `job_id`.
Use `limit` and `offset` for paging.
Specify `association` to include reconciliation results with the given association.

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7/clusters/0`_

### Linksets interaction

**URL**: `/job/<job_id>/validate/<alignment>`

**Method**: `POST`

**JSON**: `source`, `target`, `valid`

Validate a link for alignment `alignment` of the given `job_id`.
Specify the uris of the `source` and `target` to identify the link to be validated.
Provide `valid` with either `true` or `false` to validate the link or use `null` to reset.  

---

**URL**: `/job/<job_id>/cluster/<alignment>/<cluster_id>/graph`

**Method**: `GET`

**Parameters**: `get_cluster`, `get_cluster_compact`, `get_reconciliation`

Get the visualization information for a cluster with `cluster_id` for alignment `alignment` of the given `job_id`.
Specify `get_cluster` to obtain the default visualization.
Specify `get_cluster_compact` to obtain the compact visualization.
Specify `get_reconciliation` to obtain the reconciled visualization.

### Export

**URL**: `/job/<job_id>/export/<alignment>/csv`

**Method**: `GET`

**Parameters**: `accepted`, `declined`, `not_validated`

Get a CSV export of the linkset for alignment `alignment` of the given `job_id`.
Specify `accepted` to include the accepted links.
Specify `declined` to include the declined links.
Specify `not_validated` to include the links which were not yet validated.

## Job configuration with JSON

### Resources

Resources is a list of JSON objects that contain the configuration 
of the specific resources to use for a particular job.

```json5
{
    "id": 1,                    // An integer as identifier  
    "label": "My dataset",      // The label of the resource in the GUI
    "description": "",          // A description of this resource by the user; optional field
    "dataset": {                // The data to use from Timbuctoo
        "dataset_id": "ufab7d657a250e3461361c982ce9b38f3816e0c4b__ecartico_20190805",   // The identifier of the dataset to use
        "collection_id": "foaf_Person",                                                 // The identifier of the collection from this dataset to use
        "published": true,                                                              // Whether the dataset is published on Timbuctoo or not
        "timbuctoo_graphql": "https://repository.goldenagents.org/v5/graphql",          // The GraphQL interface of the Timbuctoo instance
        "timbuctoo_hsid": null                                                          // The hsid if the dataset is not published
    },
    "filter": {                 // The filter configuration to obtain only a subset of the data from Timbuctoo; an empty object is allowed to not filter out anything
        "conditions": [{        // The filter is composed of condition groups
            "property": ["foaf_name"],    // The property path to which this condition applies
            "type": 'not_ilike',          // The type of filtering to apply; see table below for allowed values
            "value": "%...%"              // Depends on type of filtering selected; value to use for filtering
        }],
        "type": "AND"
    },
    "limit": -1,                // Apply a limit on the number of entities to obtain; or -1 for no limit
    "random": false,            // Randomize the entities to obtain or not; optional field, defaults to 'false'
    "properties": [             // A list of property paths to use for obtaining sample data
        ["foaf_name"]
    ],
    "related": [],              // Work in progress
    "related_array": false      // Work in progress
}
```        

| Filtering             | Key                   | Value                         |
| :-------------------- | :-------------------- | :---------------------------- | 
| Equal to              | `=`                   | Yes                           |
| Not equal to          | `!=`                  | Yes                           |
| Has no value          | `is_null`             | No                            |
| Has a value           | `not_null`            | No                            |
| Date is within        | `date_is_within`      | Yes _(Use * as a wildcard)_   |
| Date is not within    | `date_is_not_within`  | Yes _(Use * as a wildcard)_   |
| Contains              | `ilike`               | Yes _(Use % as a wildcard)_   |
| Does not contain      | `not_ilike`           | Yes _(Use % as a wildcard)_   |

### Mappings

Mappings is a list of JSON objects that contain the configuration 
of the alignments to perform for a particular job.

```json5
{
    "id": 1,                    // An integer as identifier  
    "label": "My alignment",    // The label of the resource in the GUI
    "description": "",          // A description of this mapping by the user; optional field
    "is_association": false,    // Work in progress
    "match_against": 2,         // The resulting linkset of this alignment should be matched against the resulting linkset of another alignment with the given identifier; optional field
    "sources": [1],             // The identifiers of resources to use as source
    "targets": [1],             // The identifiers of resources to use as targets
    "methods": {                // The matching configuration for finding links; requires at least one condition
        "conditions": [{        // The matching configuration is composed of condition groups
            "method_name": "=",               // The type of matching to apply; see table below for allowed values
            "method_value": {},               // Some types of matching methods require extra configuration
            "sources": [{                     // The source properties to use during matching
                "resource": 1,                      // The identifier of the resource to use
                "property": ["schema_birthDate"],   // The property path to which this condition applies
                "transformers": [{                  // The transformers to apply to transform the value before matching; see table below for allowed values
                    "name": "PARSE_DATE",
                    "parameters": {
                        "format": "YYYY-MM-DD"
                    }
                }]                  
            }],
            "targets": [{                     // The target properties to use during matching
                "resource": 1,
                "property": ["schema_birthDate"],
                "transformers": []
            }]
        }],
        "type": "AND"
    },
    "properties": [{            // A list of property paths to use for obtaining data while reviewing the linkset
        "resource": 1,                        // The identifier of the resource to use
        "property": ["schema_birthDate"]      // The property path
    }]
}
```

| Matching method                   | Key                           | Values                                                                                            |
| :-------------------------------- | :---------------------------- | :------------------------------------------------------------------------------------------------ | 
| Exact Match                       | `=`                           |                                                                                                   |
| Levenshtein distance              | `LEVENSHTEIN`                 | `max_distance` (Maximum distance)                                                                 |
| Approximated Levenshtein          | `LEVENSHTEIN_APPROX`          | `threshold` (Similarity threshold)                                                                |
| Approximated Soundex              | `LL_SOUNDEX`                  | `threshold` (Similarity threshold)                                                                |
| Approximated Bloothooft Reduction | `BLOOTHOOFT_REDUCT`           | `name_type` (First or last name: `first_name`, `family_name`), `threshold` (Similarity threshold) |
| Similar Bloothooft Reduction      | `BLOOTHOOFT_REDUCT_APPROX`    | `name_type` (First or last name: `first_name`, `family_name`), `threshold` (Similarity threshold) |
| Trigram distance                  | `TRIGRAM_DISTANCE`            | `threshold` (Similarity threshold)                                                                |
| Time Delta                        | `TIME_DELTA`                  | `days` (Number of days), `multiplier` (Multiplier)                                                |
| Same Year/Month                   | `SAME_YEAR_MONTH`             | `date_part` (Year, month, or both: `year`, `month`, `year_month`)                                 |
| Distance is between               | `DISTANCE_IS_BETWEEN`         | `distance_start` (Start), `distance_end` (End)                                                    |

| Transformer   | Key           | Values                    |
| :------------ | :------------ | :------------------------ | 
| Parse date    | `PARSE_DATE`  | `format` (Date format)    |
| Prefix        | `PREFIX`      | `prefix` (The prefix)     |
| Suffix        | `SUFFIX`      | `suffix` (The suffix)     |

### Condition groups

Both the resources (using the filter) and the mappings (using the matching methods) apply condition groups
to allow the user the express complex conditions.

```json5
{
    "conditions": [],     // The list of conditions; may contain other condition groups
    "type": "AND"         // Whether ALL conditions in this group should match ('AND') or AT LEAST ONE condition in this group has to match ('OR')
}
```

As conditions may contain other conditions, complex conditions can be expressed.

```json5
{
    "conditions": [{
        "conditions": [{}, {}, {}],
        "type": "OR"
    }, {
        "conditions": [{
            "conditions": [{}],
            "type": "AND"
        }, {}],
        "type": "OR"
    }], 
    "type": "AND"
}
```

### Property paths

A property path is a list of values that expresses the path in the linked data from the entity to a specific property.
The list has at least one value, the property to select on the entity. 
If the property is a reference to another entity, 
you have to specify another value in the list with the id of the entity it points to.
Then you can select the specific property on the referenced entity.
If this is again a reference to another entity, the cycle repeats itself until you reach the required property.

```json5
["property", "entity", "property", "entity", "property"]
```

If you want the reference as a value, rather then selecting a property on the referenced entity, 
there is a special value `__value__` that you can use.

```json5
[
     // Get the name of a person: select the property 'foaf_name'
    ["foaf_name"],                                
    // Get the name of a parent of a person: follow the property 'schema_parent' to the parent entity and select the property 'foaf_name' 
    ["schema_parent", "foaf_Person", "foaf_name"],
    // Get the name of a grandparent of a person: follow the property 'schema_parent' to the parent entity, then follow that property again and then select the property 'foaf_name'
    ["schema_parent", "foaf_Person", "schema_parent", "foaf_Person", "foaf_name"],
    // Get the reference of the parent of a person (the uri of this parent): follow the property 'schema_parent' and use the special value '__value__'
    ["schema_parent", "__value__"]
]
```
