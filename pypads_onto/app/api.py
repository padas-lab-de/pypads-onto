import json
import os
from typing import List

import rdflib
from pydantic import HttpUrl
from pypads.app.api import IApi, cmd
from pypads.model.storage import ArtifactInfo, ParameterInfo, MetricInfo, TagInfo, MetadataModel
from pypads.utils.logging_util import FileFormats
from rdflib import Graph, URIRef
from rdflib.plugin import register, Parser

from pypads_onto.arguments import ontology_uri
from pypads_onto.model.ontology import IdBasedOntologyEntry

register('json-ld', Parser, 'rdflib_jsonld.parser', 'JsonLDParser')


class OntoPadsApi(IApi):
    def __init__(self):
        super().__init__()

    @property
    def pypads(self):
        from pypads.app.pypads import get_current_pads
        return get_current_pads()

    def _convert_meta(self, meta: MetadataModel) -> IdBasedOntologyEntry:
        entry = IdBasedOntologyEntry.from_orm(meta)
        entry.context = self._convert_context(entry.context)

        # TODO Build uris where needed
        if "experiment_name" in entry:
            entry.experiment_name = _get_experiment_uri(entry.experiment_name)
        if "run_id" in meta:
            entry.run_id = _get_run_uri(entry.run_id)
        return entry

    def _convert_context(self, ctx):
        """
        TODO is this still needed in this form?
        :param ctx:
        :return:
        """
        if isinstance(ctx, List):
            context = []
            for c in ctx:
                if isinstance(c, HttpUrl) or isinstance(c, dict):
                    context.append(c)
                else:
                    splits = c.split(os.sep)
                    context.append(self.pypads.backend.download_tmp_artifacts(splits[1], os.sep.join(splits[3:])))
            ctx = context
        else:
            if not (isinstance(ctx, HttpUrl) or isinstance(ctx, dict)):
                splits = ctx.split(os.sep)
                ctx = self.pypads.backend.download_tmp_artifacts(splits[1], os.sep.join(splits[3:]))
        return ctx

    @cmd
    def convert_experiment_to_rdf(self, experiment_id, graph=None, graph_id=ontology_uri):
        if graph is None:
            graph = rdflib.Graph(identifier=graph_id)
        graph.add((
            URIRef(_get_experiment_uri(
                experiment_name=self.pypads.backend.get_experiment(experiment_id=experiment_id).name)),
            URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
            URIRef(f"{ontology_uri}Experiment")))
        return graph

    @cmd
    def convert_run_to_rdf(self, run_id, graph=None, graph_id=ontology_uri):
        if graph is None:
            graph = rdflib.Graph(identifier=graph_id)
        graph.add((URIRef(_get_run_uri(run_id)), URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"),
                   URIRef(f"{ontology_uri}Run")))
        return graph

    @cmd
    def convert_artifact_to_rdf(self, info: ArtifactInfo, graph=None, graph_id=ontology_uri):
        if graph is None:
            graph = rdflib.Graph(identifier=graph_id)

        meta = self._convert_meta(info.meta)
        graph.parse(data=meta.json(by_alias=True), format="json-ld")
        if meta.file_format == FileFormats.json:
            content = info.content()
            if "@context" in content:
                content["@context"] = self._convert_context(content["@context"])
            graph.parse(data=json.dumps(content), format="json-ld")
        # graph.add(_get_run_uri(info.meta.run_id), f"{ontology_uri}resulted_in", info.meta.uri)
        return graph

    @cmd
    def convert_metric_to_rdf(self, info: MetricInfo, graph=None, graph_id=ontology_uri):
        if graph is None:
            graph = rdflib.Graph(identifier=graph_id)
        meta = self._convert_meta(info.meta)
        graph.parse(data=meta.json(by_alias=True), format="json-ld")
        if isinstance(info.content, List):
            # TODO handle lists
            pass
        # TODO node inbetween
        # graph.add(_get_run_uri(info.meta.run_id), f"{ontology_uri}resulted_in", info.content)
        return graph

    @cmd
    def convert_parameter_to_rdf(self, info: ParameterInfo, graph=None, graph_id=ontology_uri):
        if graph is None:
            graph = rdflib.Graph(identifier=graph_id)
        meta = self._convert_meta(info.meta)
        graph.parse(data=meta.json(by_alias=True), format="json-ld")
        if isinstance(info.content, List):
            # TODO handle lists
            pass
        # TODO node inbetween
        # graph.add(_get_run_uri(info.meta.run_id), f"{ontology_uri}parameterized_with", info.content)
        return graph

    @cmd
    def convert_tag_to_rdf(self, info: TagInfo, graph=None, graph_id=ontology_uri):
        if graph is None:
            graph = rdflib.Graph(identifier=graph_id)
        meta = self._convert_meta(info.meta)
        graph.parse(data=meta.json(by_alias=True), format="json-ld")
        if isinstance(info.content, List):
            # TODO handle lists
            pass
        # TODO node inbetween
        # graph.add(_get_run_uri(info.meta.run_id), f"{ontology_uri}tag", info.content)
        return graph

    @cmd
    def convert_to_rdf(self, experiment_id=None, run_id=None, graph=None, graph_id=ontology_uri):
        if graph is None:
            graph = rdflib.Graph(identifier=graph_id)

        if run_id is None:
            # Get all experiments
            if experiment_id is None:
                experiments = self.pypads.backend.list_experiments()
                for e in experiments:
                    self.convert_to_rdf(experiment_id=e.experiment_id, graph=graph, graph_id=graph_id)
                return graph

            # Get all runs
            run_infos = self.pypads.backend.list_run_infos(experiment_id=experiment_id)
            for run in run_infos:
                self.convert_to_rdf(experiment_id=experiment_id, run_id=run.run_id, graph=graph, graph_id=graph_id)
            return graph

        if experiment_id is None:
            run = self.pypads.api.get_run(run_id=run_id)
            experiment_id = run.info.experiment_id

        if True:  # TODO check if already existing
            self.convert_experiment_to_rdf(experiment_id=experiment_id, graph=graph, graph_id=graph_id)

        if True:  # TODO check if already existing
            self.convert_run_to_rdf(run_id=run_id, graph=graph, graph_id=graph_id)

        artifacts = self.pypads.api.get_artifacts(experiment_id=experiment_id, run_id=run_id, path="*")
        for a in artifacts:
            self.convert_artifact_to_rdf(a, graph=graph, graph_id=graph_id)

        metrics = self.pypads.api.get_metrics(experiment_id=experiment_id, run_id=run_id)
        for m in metrics:
            self.convert_metric_to_rdf(m, graph=graph, graph_id=graph_id)

        parameters = self.pypads.api.get_parameters(experiment_id=experiment_id, run_id=run_id)
        for p in parameters:
            self.convert_parameter_to_rdf(p, graph=graph, graph_id=graph_id)

        tags = self.pypads.api.get_tags(experiment_id=experiment_id, run_id=run_id)
        for t in tags:
            self.convert_tag_to_rdf(t, graph=graph, graph_id=graph_id)
        return graph

    @cmd
    def push_rdf(self, experiment_id=None, run_id=None, graph=None, graph_id=None):
        if graph is None:
            from rdflib.plugins.stores import sparqlstore
            store = sparqlstore.SPARQLUpdateStore(self.pypads.config["sparql-query-endpoint"],
                                                  self.pypads.config["sparql-update-endpoint"],
                                                  auth=(self.pypads.config["sparql-auth-name"],
                                                        self.pypads.config["sparql-auth-password"]))
            graph = rdflib.Graph(store, identifier=rdflib.URIRef(
                self.pypads.config["sparql-graph"] if graph_id is None else graph_id))
            graph.open((self.pypads.config["sparql-query-endpoint"], self.pypads.config["sparql-update-endpoint"]))
        self.convert_to_rdf(experiment_id=experiment_id, run_id=run_id, graph=graph)


def _get_experiment_uri(experiment_name):
    return f"{ontology_uri}Experiment#{experiment_name}"


def _get_run_uri(run_id):
    return f"{ontology_uri}Run#{run_id}"


def _parse_additional_data(data):
    if "@rdf" in data:
        return data["@rdf"]
    return data
