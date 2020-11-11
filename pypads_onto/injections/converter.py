import os
import threading
from abc import ABCMeta, abstractmethod
from json import dumps
from typing import List

import rdflib
from pydantic import HttpUrl, Extra, BaseModel
from pypads import logger
from pypads.app.backends.mlflow import MLFlowBackend, MLFlowBackendFactory
from pypads.app.misc.mixins import CallableMixin
from pypads.model.metadata import ModelObject
from pypads.model.models import ResultType
from pypads.utils.logging_util import data_path
from pypads.utils.util import dict_merge, persistent_hash
from rdflib.plugin import register, Parser

from pypads_onto.arguments import ontology_uri
from pypads_onto.model.ontology import IdBasedOntologyModel, EmbeddedOntologyModel

register('json-ld', Parser, 'rdflib_jsonld.parser', 'JsonLDParser')


class OntologyMLFlowBackendFactory:

    @staticmethod
    def make(uri) -> MLFlowBackend:
        backend = MLFlowBackendFactory.make(uri)

        # noinspection PyAbstractClass
        class OntologySupportedBackend(backend.__class__):

            # noinspection PyMissingConstructor
            def __init__(self, backend: MLFlowBackend):
                self._backend = backend

            def __getattr__(self, name):
                if name not in ["_backend", "log"] and hasattr(self._backend, name):
                    return getattr(self._backend, name)
                else:
                    return object.__getattribute__(self, name)

            def __setattr__(self, name, value):
                if name not in ["_backend"] and hasattr(self._backend, name):
                    setattr(self._backend, name, value)
                else:
                    return object.__setattr__(self, name, value)

            def log(self, obj):
                from rdflib.plugins.stores import sparqlstore
                store = sparqlstore.SPARQLUpdateStore(os.environ["SPARQL_QUERY_ENDPOINT"],
                                                      os.environ["SPARQL_UPDATE_ENDPOINT"],
                                                      auth=(os.environ["SPARQL_AUTH_NAME"],
                                                            os.environ["SPARQL_AUTH_PASSWORD"]))
                graph = rdflib.Graph(store, identifier=rdflib.URIRef(os.environ["SPARQL_GRAPH"]))
                graph.open((os.environ["SPARQL_QUERY_ENDPOINT"], os.environ["SPARQL_UPDATE_ENDPOINT"]))

                """
                TODO check type and generate missing data.

                If we log a parameter look at additional data and generate entries by converting the estimator: model_parameter: etc. structure?
                If we log an estimator look at ...
                If we log an metric look at ... 

                """
                self._backend.pypads.api.convert_to_rdf(obj, graph)
                return self._backend.log(obj)

        # noinspection PyTypeChecker
        backend: MLFlowBackend = OntologySupportedBackend(backend)
        return backend


# Set containing the hashes of stored rdf data / objects.
# This allows for better performance by not converting to rdf for every single log call.
storage_hash_set = set()


def store_hash(*args):
    """
    Store a hash of an ontology obj
    :param args: Arguments to convert to a id hash
    :return: True if not existing else False
    """
    obj_hash = persistent_hash(tuple(args))
    if obj_hash not in storage_hash_set:
        storage_hash_set.add(obj_hash)
        return True
    return False


class ExtendedIdBasedOntologyModel(IdBasedOntologyModel):
    class Config:
        extra = Extra.allow


class ExtendedEmbeddedOntologyModel(EmbeddedOntologyModel):
    class Config:
        extra = Extra.allow


def _extend_dict(obj_dict):
    """
    Used to extend the given with uris.
    :return:
    """
    out = {}
    for k, v in obj_dict.items():
        out[k] = _extend_helper(v)
    return out


# Hacky solution to add missing URI values into references etc.
def _extend_helper(v):
    if isinstance(v, dict):
        if ('category' in v and (v['category'] == 'Experiment' or v['category'] == 'Run')) or 'storage_type' in v:
            return _extend_dict(ExtendedEmbeddedOntologyModel(**v).dict())
        return _extend_dict(v)
    elif isinstance(v, list):
        array = []
        for entry in v:
            array = _extend_helper(entry)
        return array
    else:
        return v


class ObjectConverter(CallableMixin, metaclass=ABCMeta):
    """
    Converts a given storage_type object or category type object to rdf injected into the relative object. Additionally
    may create new independent entries.
    """

    def __init__(self, *args, category=None, storage_type=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._category = category
        self._storage_type = storage_type

    def __real_call__(self, obj, graph=None, graph_id=ontology_uri, *args, **kwargs):
        if graph is None:
            graph = rdflib.Graph(identifier=graph_id)

        if isinstance(obj, ModelObject):
            data_dict = obj.dict(by_alias=True, validate=False, include={'additional_data'}).get('additional_data',None)
            obj_dict = obj.dict(by_alias=True)
        elif isinstance(obj, BaseModel):
            data_dict = obj.dict(by_alias=True, include={'additional_data'}).get('additional_data',None)
            obj_dict = obj.dict(by_alias=True)
        elif isinstance(obj, dict):
            data_dict = obj['additional_data'] if 'additional_data' in obj else {}
            obj_dict = obj
        else:
            raise Exception(f"Can't convert {obj} to rdf.")

        rdf, json_ld = self._parse_additional_data(data_dict)
        obj_dict = _extend_dict(dict_merge(obj_dict, rdf))
        entry = ExtendedIdBasedOntologyModel(
            **obj_dict)
        if entry.context is not None:
            entry.context = self._convert_context(entry.context)

        entry, json_ld = self._prepare_insertion(entry, json_ld)

        out = self._convert(entry, graph)
        self._add_json_ld(entry, json_ld, graph)
        return out

    def _prepare_insertion(self, entry, json_ld):
        """
        Function to react to missing schema information and add missing values.
        :param entry:
        :param json_ld:
        :return:
        """
        return entry, json_ld

    @abstractmethod
    def _convert(self, obj, graph):
        raise NotImplementedError("Missing implementation for the conversion of the object")

    def _add_json_ld(self, entry, json_ld, graph):
        for j in json_ld:
            if store_hash(graph.identifier, str(j)):
                j["@context"] = self._convert_context(
                    dict_merge(entry.context, j["@context"])) if "@context" in j else entry.context
                try:
                    graph.parse(data=dumps(j), format="json-ld")
                except Exception:
                    logger.warning(f"Couldn't translate {j} to rdf.")

    @classmethod
    def _parse_additional_data(cls, data):
        """
        This function is to be called before converting a metadata model to rdf.
        It extracts rdf information from the additional_data dict and inserts it into the related json-ld document.
        :param data:
        :return:
        """
        rdf = {}
        if data is not None and "@rdf" in data:
            rdf = data["@rdf"]

        json_ld = {}
        if data is not None and "@json-ld" in data:
            array = data["@json-ld"]
            json_ld = []
            for entry in array:
                if isinstance(entry, str):
                    val = data_path(data, *entry.split("."))
                    if val is not None:
                        if isinstance(val, dict):
                            json_ld.append(val)
                        elif isinstance(val, list):
                            json_ld.extend(val)
                        else:
                            logger.warning(
                                f"Found value at {entry} was not valid.")
                    else:
                        logger.warning(
                            f"Mapping file doesn't define a json-ld in additional data at: {entry}.")
                elif isinstance(entry, dict):
                    json_ld.append(entry)
                else:
                    logger.warning(
                        f"Mapping file provided an invalid json-ld: {entry}. "
                        f"Json-ld has to be either an json-ld directly or an json path in additional data.")
        return rdf, json_ld

    @classmethod
    def _convert_context(cls, ctx):
        """
        TODO is this still needed in this form?
        :param ctx:
        :return:
        """
        from pypads.app.pypads import get_current_pads
        pads = get_current_pads()
        if isinstance(ctx, List):
            context = []
            for c in ctx:
                if isinstance(c, HttpUrl) or isinstance(c, dict) or (isinstance(c, str) and os.path.isfile(c)):
                    context.append(c)
                else:
                    splits = c.split(os.sep + "artifacts" + os.sep)
                    run_id = splits[0].split(os.sep)[-1]
                    context.append(pads.backend.download_tmp_artifacts(run_id, os.sep.join(splits[1:])))
            ctx = context
        else:
            if not (isinstance(ctx, HttpUrl) or isinstance(ctx, dict) or (
                    isinstance(ctx, str) and os.path.isfile(ctx))):
                splits = ctx.split(os.sep + "artifacts" + os.sep)
                run_id = splits[0].split(os.sep)[-1]
                ctx = pads.backend.download_tmp_artifacts(run_id, os.sep.join(splits[1:]))
        return ctx

    @property
    def category(self):
        return self._category

    @property
    def storage_type(self):
        return self._storage_type

    def is_applicable(self, obj):
        if isinstance(obj, dict):
            return obj["category"] == self.category if self.category is not None and "category" in obj else False or \
                                                                                                            obj[
                                                                                                                "storage_type"] == self.storage_type if self.storage_type is not None and "storage_type" in obj else False
        else:
            return obj.category == self.category if self.category is not None and hasattr(obj,
                                                                                          "category") else False or obj.storage_type == self.storage_type if self.storage_type is not None and hasattr(
                obj, "storage_type") else False


class IgnoreConversion(ObjectConverter):
    """
    This converter can be implemented if some category or storage type should be ignored.
    """

    async def _convert(self, obj, graph):
        raise NotImplementedError("Store")

    def __real_call__(self, *args, **kwargs):
        return None


class GenericConverter(ObjectConverter):

    def _convert(self, entry, graph):
        def parse():
            graph.parse(data=entry.json(by_alias=True), format="json-ld")

        threading.Thread(target=parse).start()

    def is_applicable(self, obj):
        return True


class ParameterConverter(ObjectConverter):

    def __init__(self, *args, **kwargs):
        super().__init__(storage_type=ResultType.parameter, *args, **kwargs)

    def _prepare_insertion(self, entry, json_ld):

        if json_ld is None:
            # No schema definition was defined by the mapping file for parameter TODO trying to extract a Schema
            pass

        return entry, json_ld

    def _convert(self, entry, graph):
        # TODO add basic parameter t-box. This should be done by parsing additional data
        def parse():
            graph.parse(data=entry.json(by_alias=True), format="json-ld")

        threading.Thread(target=parse).start()


class MetricConverter(ObjectConverter):

    def __init__(self, *args, **kwargs):
        super().__init__(storage_type=ResultType.metric, *args, **kwargs)

    def _prepare_insertion(self, entry, json_ld):

        if json_ld is None:
            # No schema definition was defined by the mapping file for metric TODO trying to extract a Schema
            pass

        return entry, json_ld

    def _convert(self, entry, graph):
        # TODO add basic metric t-box. This should be done by parsing additional data
        def parse():
            graph.parse(data=entry.json(by_alias=True), format="json-ld")

        threading.Thread(target=parse).start()


class TagConverter(ObjectConverter):

    def __init__(self, *args, **kwargs):
        super().__init__(storage_type=ResultType.tag, *args, **kwargs)

    def _convert(self, entry, graph):
        # TODO add basic tag t-box. This should be done by parsing additional data
        def parse():
            graph.parse(data=entry.json(by_alias=True), format="json-ld")

        threading.Thread(target=parse).start()


class ArtifactConverter(ObjectConverter):

    def __init__(self, *args, **kwargs):
        super().__init__(storage_type=ResultType.artifact, *args, **kwargs)

    def _convert(self, entry, graph):
        # TODO add basic artifact t-box. This should be done by parsing additional data
        def parse():
            graph.parse(data=entry.json(by_alias=True), format="json-ld")

        threading.Thread(target=parse).start()
