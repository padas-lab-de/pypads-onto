import argparse

# Initialize parser
import configparser
import os
from pypads import logger
from pypads.arguments import PYPADS_FOLDER


def parse_configfile(path, parsed_args):
    """
    Function that parse passed argument and configure default env varialbles.
    """
    config = configparser.ConfigParser()
    config.read(path)

    SPARQL = config['SPARQL']

    # MLflow & Mongo DB related env variables
    pypads_envs = {"SPARQL_GRAPH": parsed_args.OntologyUri,
                   "SPARQL_QUERY_ENDPOINT": parsed_args.SPARQL_QUERY_ENDPOINT,
                   "SPARQL_UPDATE_ENDPOINT": parsed_args.SPARQL_UPDATE_ENDPOINT,
                   "SPARQL_AUTH_NAME": parsed_args.SPARQL_AUTH_NAME,
                   "SPARQL_AUTH_PASSWORD": parsed_args.SPARQL_AUTH_PASSWORD}

    # Set the env variables
    for k, v in pypads_envs.items():
        if v is None:
            if k in SPARQL.keys():
                os.environ[k] = SPARQL[k]
        else:
            os.environ[k] = v


parser = argparse.ArgumentParser()

# Adding optional argument
parser.add_argument("-c", "--config", default=os.path.join(PYPADS_FOLDER, ".config"),
                    help="Path to a config file.")
parser.add_argument("-o", "--OntologyUri", default="https://www.padre-lab.eu/onto/",
                    help="Set the base URI for concepts defined in an ontology.")
parser.add_argument("--SPARQL_QUERY_ENDPOINT", default=None,
                    help="Set the url of the query Sparql endpoint.")
parser.add_argument("--SPARQL_UPDATE_ENDPOINT", default=None,
                    help="Set the url of the update Sparql endpoint.")
parser.add_argument("--SPARQL_AUTH_NAME", default=None,
                    help="Set the user name for the sparql store.")
parser.add_argument("--SPARQL_AUTH_PASSWORD", default=None,
                    help="Set the Password for the sparql store.")

# Read arguments from command line
args, _ = parser.parse_known_args()

if args.OntologyUri:
    logger.info("Setting PyPads base ontology URI to: %s" % args.OntologyUri)

config_file = args.config
ontology_uri = args.OntologyUri

parse_configfile(config_file, args)
