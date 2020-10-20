import glob
import os

from pypads.app import base
from pypads.bindings import events
from pypads.bindings import hooks
from pypads.importext import mappings
from pypads.model.models import ResultType
from pypads.utils.util import dict_merge

from pypads_onto.app.actuators import OntoPadsActuators
from pypads_onto.app.api import OntoPadsApi
from pypads_onto.app.decorators import OntoPadsDecorators
from pypads_onto.app.results import OntoPadsResults
from pypads_onto.app.validators import OntoPadsValidators
from pypads_onto.arguments import ontology_uri
from pypads_onto.bindings.anchors import init_anchors
from pypads_onto.bindings.event_types import init_event_types
from pypads_onto.bindings.events import DEFAULT_ONTO_LOGGING_FNS
# --- Pypads App ---
from pypads_onto.bindings.hooks import DEFAULT_ONTO_HOOK_MAPPING
from pypads_onto.injections.converter import OntologyMLFlowBackendFactory, ParameterConverter, IgnoreConversion, \
    EstimatorConverter, MetricConverter, TagConverter, ArtifactConverter

DEFAULT_ONTO_SETUP_FNS = {}

# Extended config.
# Pypads mapping files shouldn't interact directly with the logging functions,
# but define events on which different logging functions can listen.
# This config defines such a listening structure.
DEFAULT_ONTO_CONFIG = {"sparql-query-endpoint": "http://rdf.padre-lab.eu/pypads/query",
                       "sparql-update-endpoint": "http://rdf.padre-lab.eu/pypads/update",
                       "sparql-auth-name": "admin",
                       "sparql-auth-password": "7gaUOSf0jNWlxre",
                       "sparql-graph": ontology_uri}

DEFAULT_ONTO_CONVERTERS = [ParameterConverter(), TagConverter(), MetricConverter(),
                           ArtifactConverter(), IgnoreConversion(storage_type=ResultType.logger_call)]


def configure_plugin(pypads, *args, converters=None, **kwargs):
    """
    This function can be used to configure the plugin. It should be called at least once to allow for the usage of the
    plugin. Multiple executions should be possible.
    :return:
    """
    if converters is None:
        converters = []
    actuators = OntoPadsActuators()
    validators = OntoPadsValidators()
    decorators = OntoPadsDecorators()
    results = OntoPadsResults()
    api = OntoPadsApi()

    converters.extend(DEFAULT_ONTO_CONVERTERS)
    setattr(pypads, "rdf_converters", converters)

    mappings.default_mapping_file_paths.extend(
        glob.glob(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bindings",
                                               "resources", "mapping", "**.json"))))
    base.DEFAULT_SETUP_FNS.update(DEFAULT_ONTO_SETUP_FNS)
    base.DEFAULT_CONFIG = dict_merge(base.DEFAULT_CONFIG, DEFAULT_ONTO_CONFIG)
    events.DEFAULT_LOGGING_FNS = dict_merge(events.DEFAULT_LOGGING_FNS, DEFAULT_ONTO_LOGGING_FNS)
    hooks.DEFAULT_HOOK_MAPPING = dict_merge(hooks.DEFAULT_HOOK_MAPPING, DEFAULT_ONTO_HOOK_MAPPING)
    init_event_types()
    init_anchors()
    return actuators, validators, decorators, api, results


# Overwrite the default BackendFactory of PyPads to produce Ontology support
from pypads.app.backends import mlflow

mlflow.MLFlowBackendFactory = OntologyMLFlowBackendFactory
