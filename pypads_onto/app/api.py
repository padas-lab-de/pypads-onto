from typing import List

import rdflib
from pypads import logger
from pypads.app.api import IApi, cmd

from pypads_onto.arguments import ontology_uri


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
        from pypads_onto.injections.converter import ObjectConverter, GenericConverter
        if graph is None:
            graph = rdflib.Graph(identifier=graph_id)
        converters_: List[ObjectConverter] = self.pypads.rdf_converters or [] if hasattr(self.pypads,
                                                                                         "rdf_converters") else []
        converters_ = converters_.copy()
        converters_.append(GenericConverter())

        for c in converters_:
            if c.is_applicable(obj):
                try:
                    c(obj, graph)
                except Exception as e:
                    logger.error(f"Couldn't convert {str(obj)} to RDF because of {str(e)}")
                break
        return graph

    # TODO function to store additional information about the run
    @cmd
    def log_rdf(self):
        pass
