"""
This file contains utility functions for writing data to the wikibase instance
"""

from python_wikibase import python_wikibase
from python_wikibase.utils.exceptions import NotFoundError
from SPARQLWrapper import SPARQLWrapper, JSON

WIKIBASE_API_ENDPOINT = "https://wikibase.padre-lab.eu/w/api.php"
SPARQL_ENDPOINT = "https://query.wikidata.org/bigdata/namespace/wdq/sparql"

# TODO: Create property uses_dataset
USES_DATASET_PROP = 'P1234'
PART_OF_PROP = 'P6465'
INSTANCE_OF_PROP = 'P6461'
HAS_VALUE_PROP = 'P6831'
HAS_METRIC_PROP = 'P6832'
EXPERIMENT_ENTITY = 'Q231052'

EXPERIMENTAL_RUN_ENTITY = 'Experimental run'

# Classification metric names
F1_SCORE = "F1 score"
ACCURACY = "Accuracy"
Recall = "Recall"
PRECISION = "Precision"


def create_entity(wikibase_obj, name, description):
    """
    Creates an item in a wikibase instance
    :param wikibase_obj: a python wikibase object that is logged into the wikibase
    :param name: Name of the entity to be created
    :param description: Description of the entity to be created
    :return: entity object
    """

    entity = wikibase_obj.Item().create(name)
    entity.description.set(description, 'en')  # Language is English
    return entity


def link_dataset(wikibase_obj, run_entity, dataset_entity):
    uses_prop = wikibase_obj.Property().get(USES_DATASET_PROP)
    run_entity.claims.add(uses_prop, dataset_entity)


def retrieve_entity(wikibase_obj, entity_id):
    """
    Retrieve an item from wikibase
    :param wikibase_obj:
    :param entity_id:
    :return:
    """
    entity = None
    try:
        entity = wikibase_obj.Item().get(entity_id)
    except NotFoundError:
        return None
    return entity


def query_wikibase_sparql(entity_name):
    sparql = SPARQLWrapper(SPARQL_ENDPOINT)
    # Create query by selecting the objects that contain the item
    query = "PREFIX csv: <http://vocab.sindice.net/csv> \n SELECT * WHERE {?subject ?predicate \"" + \
            entity_name + "\"@en} LIMIT 10"

    # Query the server
    sparql.setQuery(query)

    # Convert the returned data
    sparql.setReturnFormat(JSON)
    results = sparql.query()._convert()

    # populate the results list
    result_list = []
    for result in results["results"]["bindings"]:
        result_list.append(result["subject"]["value"])
    return result_list