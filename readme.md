# Lenticular Lens

Lenticular Lens is a tool which allows users to construct linksets between entities from different Timbuctoo datasets (
so called data-alignment or reconciliation). Lenticular Lens tracks the configuration and the algorithms used in the
alignment and is also able to report on manual corrections and the amount of manual validation done.

1. [Installation with Docker](#installation-with-docker)
1. [Definition of terms](#definition-of-terms)
1. [API](#api)
    1. [Default](#default)
    1. [Authentication and authorization](#authentication-and-authorization)
    1. [Job creation and updates](#job-creation-and-updates)
    1. [Job processes](#job-processes)
    1. [Data retrieval](#data-retrieval)
    1. [Linksets interaction](#linksets-interaction)
    1. [Export](#export)
1. [Job configuration with JSON](#job-configuration-with-json)
    1. [Entity-type selections](#entity-type-selections)
    1. [Linkset specs](#linkset-specs)
    1. [Lens specs](#lens-specs)
    1. [Views](#views)
    1. [Logic boxes](#logic-boxes)
    1. [Property paths](#property-paths)
    1. [Fuzzy logic](#fuzzy-logic)

## Installation with Docker

1. Make sure Docker and Docker Compose are installed
    * _For Windows and Mac users: install [Docker Desktop](https://www.docker.com/products/docker-desktop)_
1. Use the provided `docker-compose.yml` as a baseline
1. Run `docker-compose up`
1. Visit http://localhost:8000 in your browser

_Note: This will create a folder `pgdata` with the database data. To clean up the database and start from scratch,
simply remove this folder._

## Configuration

Misc. configuration:

- `APP_DOMAIN`: The application domain; defaults to `http://localhost`
- `SECRET_KEY`: The secret key used for session signing
- `LOG_LEVEL`: The logging level; defaults to `INFO`
- `WORKER_TYPE`: For a worker instance, the type of the worker to run:
    - `TIMBUCTOO`
    - `LINKSET`
    - `LENS`
    - `CLUSTERING`
    - `RECONCILIATION`

Database configuration:

- `DATABASE_HOST`: The database host; defaults to `localhost`
- `DATABASE_PORT`: The database port; defaults to `5432`
- `DATABASE_DB`: The database name; defaults to `postgres`
- `DATABASE_USER`: The database user; defaults to `postgres`
- `DATABASE_PASSWORD`: The database password; defaults to `postgres`

OpenID Connect authentication configuration:

- `OIDC_SERVER`: The OpenID Connect provider server; leave empty to disable authentication
- `OIDC_CLIENT_ID`: The OpenID Connect client id
- `OIDC_CLIENT_SECRET`: The OpenID Connect client secret

## Definition of terms

![](./docs/schema.png)

* **Job**

  A **job** encloses a research question, which highlights the scope/context in which _linksets_ and _lenses_ are
  created, analysed, validated and exported.

* **Entity-type selection**

  An **entity-type selection** is a selection of entities (stemmed from a dataset) of a certain type based on zero or
  more filters. The set of _entity-type selections_ in a _job_ comprises the entities of interest for a research
  question.

* **Linkset specification**

  A **linkset specification** is the specification determining how entities from one or more _entity-type selections_
  should be matched using one or more entity matching algorithms. Running a _linkset specification_ will result in a _
  linkset_.

* **Linkset**

  A **linkset** is a set of paired resources (URIs) that matched according to a _linkset specification_.

* **Lens specification**

  A **lens specification** is the specification that specifies one or more modifications (union, intersection, ...) over
  a number of _linksets_ or _lenses_. The _lens_ inherits the specifications of all _ linksets_ and _lenses_ it
  originates from.

* **Lens**

  A **lens** is a set of paired resources (URIs) resulting from one or more modifications according to a _lens
  specification_.

* **Clustering**

  A **clustering** is the partitioning of the resources (URIs) in a _linkset_ or _lens_ into _clusters_ based on
  transitivity of the links in the _linkset_ or _lens_.

* **Cluster**

  A **cluster** is a set of potentially similar resources (URIs). As a _cluster_ originates from the _clustering_ of a _
  linkset_ or a _lens_, the _cluster_ holds only with respect to their _linkset specifications_.

## API

### Default

**URL**: `/`\
**Method**: `GET`

Root page. Will return the GUI for the tool.

---

**URL**: `/datasets`\
**Method**: `GET`\
**Parameters**: `endpoint`

Returns all available datasets for a specific Timbuctoo GraphQL `endpoint`.

_Example: `/datasets?endpoint=https://repository.goldenagents.org/v5/graphql`_

---

**URL**: `/downloads`\
**Method**: `GET`

Returns all currently running data downloads and finished data downloads from Timbuctoo.

---

**URL**: `/download`\
**Method**: `GET`\
**Parameters**: `endpoint`, `dataset_id`, `collection_id`

Starts a data download from Timbuctoo from the given Timbuctoo GraphQL `endpoint`. Use `dataset_id` to specify from
which dataset to download and `collection_id` to specify the collection from the dataset to download.

_
Example: `/download?endpoint=https://repository.goldenagents.org/v5/graphql&dataset_id=ufab7d657a250e3461361c982ce9b38f3816e0c4b__ecartico_20190805&collection_id=schema_Person`_

---

**URL**: `/stopwords/<dictionary>`\
**Method**: `GET`

Returns the stopwords for the given `dictionary`.

### Authentication and authorization

**URL**: `/login`\
**Method**: `GET`\
**Parameters**: `redirect-uri`

Allow the user to login and then redirect back to the given `redirect-uri`.

_Example: `/login?redirect-uri=https://lenticularlens.org`_

---

**URL**: `/user_info`\
**Method**: `GET`

Returns the user information of the logged-in user.

### Job creation and updates

**URL**: `/job/create`\
**Method**: `POST`\
**Form data**: `job_title`, `job_description`

Creates a new job with the given `job_title` and `job_description`. Returns the identifier of this new job.

---

**URL**: `/job/update`\
**Method**: `POST`\
**JSON**: `job_id`, `job_title`, `job_description`, `job_link`, `entity_type_selections`, `linkset_specs`, `lens_specs`
, `views`

Updates a job with the given `job_id`. Updates the `job_title`, `job_description`, `job_link`, `entity_type_selections`
, `linkset_specs`, `lens_specs` and `views`.

---

**URL**: `/job/<job_id>`\
**Method**: `GET`

Returns the details of a job with the given `job_id`.

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7`_

### Job processes

**URL**: `/job/<job_id>/linksets`\
**Method**: `GET`

Returns the details of all linksets with the given `job_id`.

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7/linksets`_

---

**URL**: `/job/<job_id>/lenses`\
**Method**: `GET`

Returns the details of all lenses with the given `job_id`.

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7/lenses`_

---

**URL**: `/job/<job_id>/clusterings`\
**Method**: `GET`

Returns the details of all clustering jobs with the given `job_id`.

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7/clusterings`_

---

**URL**: `/job/<job_id>/run/<type>/<linkset>`\
**Method**: `POST`\
**Form data**: `restart`

Start a process for the given spec of `type` (`linkset` or `lens`) of a specific `job_id`. Specify `restart` to restart
the process.

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7/run/linkset/0`_

---

**URL**: `/job/<job_id>/run_clustering/<type>/<id>`\
**Method**: `POST`

Start a clustering process of `type` (`linkset` or `lens`) for the linkset/lens with the given `id` of a
specific `job_id`.

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7/run_clustering/linkset/0`_

---

**URL**: `/job/<job_id>/kill/<type>/<linkset>`\
**Method**: `POST`

Stop a process for the given spec of `type` (`linkset` or `lens`) of a specific `job_id`.

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7/kill/linkset/0`_

---

**URL**: `/job/<job_id>/kill_clustering/<type>/<id>`\
**Method**: `POST`

Stop a clustering process of `type` (`linkset` or `lens`)
for the linkset/lens with the given `id` of a specific `job_id`.

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7/kill_clustering/lens/0`_

---

**URL**: `/job/<job_id>/<type>/<id>`\
**Method**: `DELETE`

Deletion of `type` (`linkset` or `lens`) for the linkset/lens with the given `id` of a specific `job_id`.

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7/lens/0`_

### Data retrieval

**URL**: `/job/<job_id>/entity_type_selection_total/<id>`\
**Method**: `GET`

Returns the total number of entities for an entity-type selection with the given `id` of the given `job_id`.

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7/entity_type_selection_total/0`_

---

**URL**: `/job/<job_id>/links_totals/<type>/<id>`\
**Method**: `GET`\
**Parameters**: `apply_filters`, `uri`, `cluster_id`, `min`, `max`

Returns the total number of links of `type` (`linkset` or `lens`) for the linkset/lens with `id` of the given `job_id`.

Specify `apply_filters` to apply the filters specified by the user. Specify `uri` to only return links with the
specified URIs. Specify `cluster_id` to only return the links of specific clusters. Specify `min` and/or `max` to only
return links with a similarity score within the specified minimum and maximum score.

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7/links_totals/linkset/0`_

---

**URL**: `/job/<job_id>/clusters_totals/<type>/<id>`\
**Method**: `GET`\
**Parameters**: `apply_filters`, `uri`, `cluster_id`, `min`, `max`

Returns the total number of clusters of `type` (`linkset` or `lens`) for the linkset/lens with `id` of the
given `job_id`.

Specify `apply_filters` to apply the filters specified by the user. Specify `uri` to only return links with the
specified URIs. Specify `cluster_id` to only return the links of specific clusters. Specify `min` and/or `max` to only
take into account links with a similarity score within the specified minimum and maximum score. Specify `min_size`
and/or `max_size` to only return clusters with a size that is within the specified minimum and maximum size.
Specify `min_count` and/or `max_count` to only return clusters with a links count that is within the specified minimum
and maximum count.

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7/clusters_totals/linkset/0`_

---

**URL**: `/job/<job_id>/entity_type_selection/<id>`\
**Method**: `GET`\
**Parameters**: `limit`, `offset`

Returns all data for an entity-type selection with the given `id` of the given `job_id`. Use `limit` and `offset` for
paging.

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7/entity_type_selection/0`_

---

**URL**: `/job/<job_id>/links/<type>/<id>`\
**Method**: `GET`\
**Parameters**: `with_properties`, `apply_filters`, `valid`, `uri`, `cluster_id`, `min`, `max`, `sort`, `limit`
, `offset`

Returns the links of `type` (`linkset` or `lens`) for the linkset/lens with `id` of the given `job_id`. Use `limit`
and `offset` for paging.

Specify `with_properties` with 'none' to return no property values, 'single' to only return a single property value or '
multiple' to return multiple property values. Specify `apply_filters` to apply the filters specified by the user.
Specify `valid` with `accepted`, `declined`, `not_sure` and/or `not_validated` to only return from the specified
validity types. Specify `uri` to only return links with the specified URIs. Specify `cluster_id` to only return the
links of specific clusters. Specify `min` and/or `max` to only return links with a similarity score within the specified
minimum and maximum score. Specify `sort` if you want to enable sorting on similarity score using `asc` or `desc`.

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7/links/linkset/0`_

---

**URL**: `/job/<job_id>/clusters/<type>/<id>`\
**Method**: `GET`\
**Parameters**: `with_properties`, `apply_filters`, `include_nodes`, `uri`, `cluster_id`, `min`, `max`, `min_size`
, `max_size`, `min_count`, `max_count`, `limit`, `offset`

Returns the clusters of `type` (`linkset` or `lens`) for the linkset/lens with `id` of the given `job_id`. Use `limit`
and `offset` for paging.

Specify `with_properties` with 'none' to return no property values, 'single' to only return a single property value or '
multiple' to return multiple property values. Specify `apply_filters` to apply the filters specified by the user.
Specify `include_nodes` to include all nodes that are part of the cluster in the response. Specify `uri` to only return
links with the specified URIs. Specify `cluster_id` to only return the links of specific clusters. Specify `min`
and/or `max` to only return links with a similarity score within the specified minimum and maximum score.
Specify `min_size` and/or `max_size` to only return clusters with a size that is within the specified minimum and
maximum size. Specify `min_count` and/or `max_count` to only return clusters with a links count that is within the
specified minimum and maximum count.

_Example: `/job/d697ea3869422ce3c7cc1889264d03c7/clusters/0`_

### Linksets interaction

**URL**: `/job/<job_id>/validate/<type>/<id>`\
**Method**: `POST`\
**Form data**: `source`, `target`, `apply_filters`, `valid`, `uri`, `cluster_id`, `min`, `max`, `validation`

Validate a link of `type` (`linkset` or `lens`) for the linkset/lens with `id` of the given `job_id`.

Specify the uris of the `source` and `target` to identify the link to be validated. Or filter the links by
specifying `apply_filters` to apply the filters specified by the user. Specify `valid` with `accepted`, `declined`,
`not_sure` and/or `not_validated` to only return from the specified validity types. Specify `uri` to only return links
with the specified URIs. Specify `cluster_id` to only return the links of specific clusters. Specify `min` and/or `max`
to only return links with a similarity score within the specified minimum and maximum score.

Provide `validation` with either `accepted`, `declined` or `not_sure` to validate the link or use `not_validated` to
reset.

---

**URL**: `/job/<job_id>/motivate/<type>/<id>`\
**Method**: `POST`\
**Form data**: `source`, `target`, `apply_filters`, `valid`, `uri`, `cluster_id`, `min`, `max`, `motivation`

Motivate using `motivation` of `type` (`linkset` or `lens`) for the linkset/lens with `id` of the given `job_id`.

Specify the uris of the `source` and `target` to identify the link to be motivated. Or filter the links by
specifying `apply_filters` to apply the filters specified by the user. Specify `valid` with `accepted`, `declined`,
`not_sure` and/or `not_validated` to only return from the specified validity types. Specify `uri` to only return links
with the specified URIs. Specify `cluster_id` to only return the links of specific clusters. Specify `min` and/or `max`
to only return links with a similarity score within the specified minimum and maximum score.

---

**URL**: `/job/<job_id>/cluster/<type>/<id>/<cluster_id>/graph`\
**Method**: `GET`

Get the visualization information for a cluster with `cluster_id` of `type` (`linkset` or `lens`)
for the linkset/lens with `id` of the given `job_id`.

### Export

**URL**: `/job/<job_id>/csv/<type>/<id>`\
**Method**: `GET`\
**Parameters**: `valid`

Get a CSV export of `type` (`linkset` or `lens`) for the linkset/lens with `id` the given `job_id`.

Specify `valid` with `accepted`, `declined`, `not_sure` and/or `not_validated` to only export from the specified
validity types.

---

**URL**: `/job/<job_id>/rdf/<type>/<id>`\
**Method**: `GET`\
**Parameters**: `valid`, `link_pred_namespace`, `link_pred_shortname`, `export_metadata`,
`export_linkset`, `reification`, `use_graphs`, `creator`, `publisher`

Get a RDF export of `type` (`linkset` or `lens`) for the linkset/lens with `id` the given `job_id`.

Specify `valid` with `accepted`, `declined`, `not_sure` and/or `not_validated` to only export from the specified
validity types.

Specify `link_pred_namespace` and `link_pred_shortname` to configure the predicate to use for the links.

Specify `export_metadata`, `export_linkset` with boolean values to indicate what to include in the RDF export.

Specify `reification` with either `none`, `standard`, `singleton` or `rdf_star` to indicate how the link metadata has to
be included in the RDF export.

Specify `use_graphs` to determine the RDF format to use.

Optionally specify `creator` and/or `publisher` to include extra metadata.

## Job configuration with JSON

### Entity-type selections

Entity-type selections is a list of JSON objects that contain the configuration of the specific entity-type selections
to use for a particular job.

```json5
{
  // An integer as identifier  
  "id": 1,
  // The label of the entity-type selection
  "label": "My dataset",
  // A description of this entity-type selection by the user; optional field
  "description": "",
  // The data to use from Timbuctoo
  "dataset": {
    // The identifier of the dataset to use
    "dataset_id": "ufab7d657a250e3461361c982ce9b38f3816e0c4b__ecartico_20190805",
    // The identifier of the collection from this dataset to use
    "collection_id": "foaf_Person",
    // The GraphQL interface of the Timbuctoo instance
    "timbuctoo_graphql": "https://repository.goldenagents.org/v5/graphql",
  },
  // The filter configuration to obtain only a subset of the data from Timbuctoo; optional field
  "filter": {
    // Whether ALL conditions in this group should match ('AND') or AT LEAST ONE condition in this group has to match ('OR')
    "type": "AND",
    // The filter is composed of a logic box
    "conditions": [
      {
        // The property path to which this condition applies
        "property": [
          "foaf_name"
        ],
        // The type of filtering to apply; see table below for allowed values
        "type": 'minimal_date',
        // Depends on type of filtering selected; value to use for filtering
        "value": "1600",
        // Both the types `minimal_date` and `maximum_date` require a date format for parsing
        "format": "YYYY-MM-DD"
      }
    ]
  },
  // Apply a limit on the number of entities to obtain or -1 for no limit; optional field, defaults to '-1'
  "limit": -1,
  // Randomize the entities to obtain or not; optional field, defaults to 'false'
  "random": false,
  // A list of property paths to use for obtaining sample data; optional field
  "properties": [
    [
      "foaf_name"
    ]
  ]
}
```        

| Filtering             | Key                   | Value                         |
| :-------------------- | :-------------------- | :---------------------------- | 
| Equal to              | `equals`              | Yes                           |
| Not equal to          | `not_equals`          | Yes                           |
| Has no value          | `empty`               | No                            |
| Has a value           | `not_empty`           | No                            |
| Contains              | `contains`            | Yes _(Use % as a wildcard)_   |
| Does not contain      | `not_contains`        | Yes _(Use % as a wildcard)_   |
| Minimal               | `minimal`             | Yes _(An integer)_            |
| Maximum               | `maximum`             | Yes _(An integer)_            |
| Minimal date          | `minimal_date`        | Yes _(Use YYYY-MM-DD)_        |
| Maximum date          | `maximum_date`        | Yes _(Use YYYY-MM-DD)_        |
| Minimal appearances   | `minimal_appearances` | Yes _(An integer)_            |
| Maximum appearances   | `maximum_appearances` | Yes _(An integer)_            |

### Linkset specs

Linkset specs is a list of JSON objects that contain the configuration of the linksets to generate for a particular job.

```json5
{
  // An integer as identifier
  "id": 1,
  // The label of the linkset
  "label": "My linkset",
  // A description of this linkset by the user; optional field
  "description": "",
  // Whether we would like to track progress in the GUI at the cost that matching might run longer; optional field, defaults to 'true'
  "use_counter": true,
  // The identifiers of entity-type selections to use as sources
  "sources": [
    1
  ],
  // The identifiers of entity-type selections to use as targets
  "targets": [
    1
  ],
  // The matching configuration for finding links; requires at least one condition
  "methods": {
    // Whether ALL conditions in this group should match ('AND') or AT LEAST ONE condition in this group has to match ('OR'); T-norms and t-conorms are also allowed: see table below for allowed values
    "type": "AND",
    // The threshold to apply on the similarity score; optional field, defaults to '0' which means it does not apply
    "threshold": 0.8,
    // The matching configuration is composed of a logic box
    "conditions": [
      {
        // The main matching method to apply
        "method": {
          // The type of matching to apply; see table below for allowed values
          "name": "SOUNDEX",
          // Some types of matching methods require extra configuration
          "config": {}
        },
        // The similarity matching to apply; see table below for allowed values; optional field
        "sim_method": {
          // The type of similarity matching to apply; see table below for allowed values
          "name": "SOUNDEX",
          // Some types of similarity matching methods require extra configuration
          "config": {},
          // Whether to apply the similarity matching method on the normalized value; optional field, defaults to 'false'
          "normalized": false,
        },
        // Fuzzy matching configuration; optional field
        "fuzzy": {
          // The t-conorm to apply on the values of this condition; see table below for allowed values; optional field, defaults to 'MAXIMUM_T_CONORM'
          "t_conorm": "MAXIMUM_T_CONORM",
          // The threshold to apply on the similarity score; optional field, defaults to '0' which means it does not apply
          "threshold": 0
        },
        // Perform list matching; optional field
        "list_matching": {
          // The minimum number of intersections; optional field, defaults to '0' which means it does not apply
          "threshold": 8,
          // Whether the threshold number should be interpreted as a percentage; optional field, defaults to 'false'
          "is_percentage": false
        },
        // Sources configuration
        "sources": {
          // The source properties to use during matching per entity-type selection 
          "properties": {
            "1": [
              {
                // The property path to which this condition applies
                "property": [
                  "schema_birthDate"
                ],
                // Whether the transformers of this property should be applied before the source transformers; optional field, defaults to 'false'
                "property_transformer_first": false,
                // The transformers to apply to transform the value before matching; see table below for allowed values
                "transformers": [
                  {
                    "name": "PARSE_DATE",
                    "parameters": {
                      "format": "YYYY-MM-DD"
                    }
                  }
                ]
              }
            ],
          },
          // The transformers to apply to transform the source value before matching; see table below for allowed values
          "transformers": []
        },
        // Targets configuration
        "targets": {
          // The target properties to use during matching per entity-type selection 
          "properties": {
            "1": [
              {
                "property": [
                  "schema_birthDate"
                ],
                "property_transformer_first": false,
                "transformers": []
              }
            ],
          },
          // The transformers to apply to transform the target value before matching; see table below for allowed values
          "transformers": []
        }
      }
    ]
  }
}
```

| Matching method        | Key                      | Accepts a similarity method | Is a similarity method | Values                                                                                                     |
| :--------------------- | :----------------------- | :-------------------------- | :--------------------- | :--------------------------------------------------------------------------------------------------------- | 
| Exact match            | `EXACT`                  | No                          | No                     |                                                                                                            |
| Intermediate dataset   | `INTERMEDIATE`           | No                          | No                     | `entity_type_selection`, `intermediate_source`, `intermediate_target` (Property paths)                     |
| Levenshtein distance   | `LEVENSHTEIN_DISTANCE`   | No                          | Yes                    | `max_distance`                                                                                             |
| Levenshtein normalized | `LEVENSHTEIN_NORMALIZED` | No                          | Yes                    | `threshold`                                                                                                |
| Soundex                | `SOUNDEX`                | Yes                         | No                     | `size`                                                                                                     |
| Gerrit Bloothooft      | `BLOOTHOOFT`             | Yes                         | No                     | `name_type` (First or last name: `first_name`, `family_name`)                                              |
| Word Intersection      | `WORD_INTERSECTION`      | No                          | Yes                    | `ordered`, `approximate`, `stop_symbols`, `threshold`                                                      |
| Metaphone              | `METAPHONE`              | Yes                         | No                     | `max`                                                                                                      |
| Double Metaphone       | `DMETAPHONE`             | Yes                         | No                     |                                                                                                            |
| Trigram                | `TRIGRAM`                | No                          | Yes                    | `threshold`                                                                                                |
| Numbers Delta          | `NUMBERS_DELTA`          | No                          | No                     | `type` (Irrelevant, Source < Target, Target < Source: `<>`, `<`, `>`), `start`, `end`                      |
| Time Delta             | `TIME_DELTA`             | No                          | No                     | `type` (Irrelevant, Source < Target, Target < Source: `<>`, `<`, `>`), `years`, `months`, `days`, `format` |
| Same Year/Month        | `SAME_YEAR_MONTH`        | No                          | No                     | `date_part` (Year, month, or both: `year`, `month`, `year_month`)                                          |
| Jaro                   | `JARO`                   | No                          | Yes                    | `threshold`                                                                                                |
| Jaro-Winkler           | `JARO_WINKLER`           | No                          | Yes                    | `threshold`, `prefix_weight`                                                                               |

| Transformer                        | Key                          | Values                            |
| :--------------------------------- | :--------------------------- | :-------------------------------- | 
| Transform 'last name first' format | `TRANSFORM_LAST_NAME_FORMAT` | `infix`                           |
| Prefix                             | `PREFIX`                     | `prefix`                          |
| Suffix                             | `SUFFIX`                     | `suffix`                          |
| Replace                            | `REPLACE`                    | `from`, `to`                      |
| Unaccent                           | `UNACCENT`                   |                                   |
| Regular expression replace         | `REGEXP_REPLACE`             | `pattern`, `replacement`, `flags` |

### Lens specs

Lens specs is a list of JSON objects that contain the configuration of the lenses to apply on a combination of linksets.

```json5
{
  // An integer as identifier
  "id": 1,
  // The label of the lens
  "label": "My lens",
  // A description of this lens by the user; optional field
  "description": "",
  // The lens configuration; requires groups consisting of two elements
  "specs": {
    // Lens type to apply; see table below for allowed values
    "type": "UNION",
    // The t-conorm to apply on the values of this element; see table below for allowed values; optional field, defaults to 'MAXIMUM_T_CONORM'
    "t_conorm": "",
    // The threshold to apply on the similarity score; optional field, defaults to '0' which means it does not apply
    "threshold": 0.8,
    // The lens configuration is composed of a logic box
    "elements": [
      {
        // The identifier of the linkset/lens to use
        "id": 0,
        // The type (linkset or lens)
        "type": "linkset"
      }
    ]
  }
}
```

| Lens type      | Description                       |
| :------------- | :-------------------------------- |
| UNION          | Union (A ∪ B)                     |
| INTERSECTION   | Intersection (A ∩ B)              |
| DIFFERENCE     | Difference (A - B)                |
| SYM_DIFFERENCE | Symmetric difference (A ∆ B)      |
| IN_SET_AND     | Source and target resources match |
| IN_SET_OR      | Source or target resources match  |
| IN_SET_SOURCE  | Source resources match            |
| IN_SET_TARGET  | Target resources match            |

### Views

Views is a list of JSON objects that contain the properties and filters to examine a linkset or lens for a particular
job.

```json5
{
  // The id of the specification (linkset or lens) to which the view applies
  "id": 1,
  // The type of the specification (linkset or lens) to which the view applies
  "type": "linkset",
  // The property paths to use for obtaining data; optional field
  "properties": [
    {
      // The identifier of the dataset of the properties
      "dataset_id": "ufab7d657a250e3461361c982ce9b38f3816e0c4b__ecartico_20190805",
      // The identifier of the collection of the properties for this dataset
      "collection_id": "foaf_Person",
      // The GraphQL interface of the Timbuctoo instance
      "timbuctoo_graphql": "https://repository.goldenagents.org/v5/graphql",
      // A list of property paths to use for this dataset
      "properties": [
        [
          "foaf_name"
        ]
      ]
    }
  ]
}
```

### Logic boxes

The entity-type selections (using the filter), the linkset specs (using the matching methods)
and the lens specs (using the elements) all apply a logic box to allow the user the express complex conditions.

```json5
{
  // The type that combines these elements (usually AND/OR, but can be of any type)
  "type": "AND",
  // The list of elements; may contain other logic boxes (can have any JSON key)
  "elements": []
}
```

As logic boxes may contain other logic boxes, complex conditions can be expressed.

```json5
{
  "type": "AND",
  "conditions": [
    {
      "type": "OR",
      "conditions": [
        {},
        {},
        {}
      ]
    },
    {
      "type": "OR",
      "conditions": [
        {
          "type": "AND",
          "conditions": [
            {}
          ]
        },
        {}
      ]
    }
  ]
}
```

### Property paths

A property path is a list of values that expresses the path in the linked data from the entity to a specific property.
The list has at least one value: the property to select on the entity. If the property is a reference to another entity,
you have to specify another value in the list with the id of the entity it points to. Then you can select the specific
property on the referenced entity. If this is again a reference to another entity, the cycle repeats itself until you
reach the required property.

```json5
[
  "property",
  "entity",
  "property",
  "entity",
  "property"
]
```

If you want the reference as a value, rather then selecting a property on the referenced entity, there is a special
value `__value__` that you can use.

```json5
[
  // Get the name of a person: select the property 'foaf_name'
  [
    "foaf_name"
  ],
  // Get the name of a parent of a person: follow the property 'schema_parent' to the parent entity and select the property 'foaf_name' 
  [
    "schema_parent",
    "foaf_Person",
    "foaf_name"
  ],
  // Get the name of a grandparent of a person: follow the property 'schema_parent' to the parent entity, then follow that property again and then select the property 'foaf_name'
  [
    "schema_parent",
    "foaf_Person",
    "schema_parent",
    "foaf_Person",
    "foaf_name"
  ],
  // Get the reference of the parent of a person (the uri of this parent): follow the property 'schema_parent' and use the special value '__value__'
  [
    "schema_parent",
    "__value__"
  ]
]
```

### Fuzzy logic

The configuration mentions both t-norms (conjuction / AND) and t-conorms (disjunction / OR) that can be used to
configure how the similarity score is computed:

| T-norm                    | Key                  |
| :------------------------ | :------------------- |
| Minimum t-norm (⊤min)     | `MINIMUM_T_NORM`     |
| Product t-norm (⊤prod)    | `PRODUCT_T_NORM`     |
| Łukasiewicz t-norm (⊤Luk) | `LUKASIEWICZ_T_NORM` |
| Drastic t-norm (⊤D)       | `DRASTIC_T_NORM`     |
| Nilpotent minimum (⊤nM)   | `NILPOTENT_MINIMUM`  |
| Hamacher product (⊤H0)    | `HAMACHER_PRODUCT`   |

| T-conorm                 | Key                 |
| :----------------------- | :------------------ |
| Maximum t-conorm (⊥max)  | `MAXIMUM_T_CONORM`  |
| Probabilistic sum (⊥sum) | `PROBABILISTIC_SUM` |
| Bounded sum (⊥Luk)       | `BOUNDED_SUM`       |
| Drastic t-conorm (⊥D)    | `DRASTIC_T_CONORM`  |
| Nilpotent maximum (⊥nM)  | `NILPOTENT_MAXIMUM` |
| Einstein sum (⊥H2)       | `EINSTEIN_SUM`      |
