from typing import Union

import rdflib
from pypads.app.results import IResults, result
from pypads.model.models import ResultType

from pypads_onto.arguments import ontology_uri


class OntoPadsResults(IResults):
    def __init__(self):
        super().__init__()

    @property
    def pypads(self):
        from pypads.app.pypads import get_current_pads
        return get_current_pads()

    @result
    def list_to_rdf(self, storage_type: Union[str, ResultType], graph=None, experiment_name=None, experiment_id=None,
                    run_id=None,
                    logger_id=None, output_id=None, tracked_object_id=None, search_dict=None, graph_id=ontology_uri):
        """
        Get an rdf representation of the entries found by listing
        """
        if graph is None:
            graph = rdflib.Graph(identifier=graph_id)
        for o in self.pypads.results.list(storage_type=storage_type, experiment_name=experiment_name,
                                          experiment_id=experiment_id, run_id=run_id,
                                          logger_id=logger_id, output_id=output_id,
                                          tracked_object_id=tracked_object_id,
                                          search_dict=search_dict):
            self.pypads.api.convert_to_rdf(o, graph)
        return graph
