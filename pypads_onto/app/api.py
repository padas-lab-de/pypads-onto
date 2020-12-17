from typing import Deque

import rdflib
from pypads.app.api import IApi, cmd

from pypads_onto.arguments import ontology_uri
from pypads_onto.injections.converter import rdf_converters


class OntoPadsApi(IApi):
    def __init__(self):
        super().__init__()

    @property
    def pypads(self):
        from pypads.app.pypads import get_current_pads
        return get_current_pads()

    @cmd
    def convert_to_rdf(self, obj, graph=None, graph_id=ontology_uri):
        """
        This function converts a given object into a rdf graph.
        :param obj:
        :param graph:
        :param graph_id:
        :return:
        """
        from pypads_onto.injections.converter import ObjectConverter
        from pypads.app.pypads import get_current_pads
        if graph is None:
            graph = rdflib.Graph(identifier=graph_id)
        converters_: Deque[ObjectConverter] = getattr(get_current_pads(), "pypads_onto_converters", rdf_converters)
        converters_ = converters_.copy()

        for c in converters_:
            if c.is_applicable(obj):
                c(obj, graph)
                break
        return graph

    # TODO function to store additional information about the run
    @cmd
    def log_rdf(self):
        pass
