import threading
from typing import Optional, Union, List

from pydantic import Field, Extra, HttpUrl
from pypads import logger
from pypads.app.injections.tracked_object import ParameterTO
from pypads.model.models import ResultType

from pypads_onto.arguments import ontology_uri
from pypads_onto.injections.converter import converter, ObjectConverter
from pypads_onto.model.ontology import rdf, EmbeddedOntologyModel, OntologyModel


@rdf(path="estimator.parameters.model_parameters.@schema")
@rdf(path="estimator.parameters.optimisation_parameters.@schema")
@rdf(path="estimator.parameters.execution_parameters.@schema")
class ParameterOntoEntry(EmbeddedOntologyModel):
    context: Optional[Union[List[Union[str, dict]], str, dict]] = {
        "configures": {
            "@id": f"{ontology_uri}configures"
        },
        "implements": {
            "@id": f"{ontology_uri}configures"
        },
        "optional": {
            "@id": f"{ontology_uri}optional"
        },
        "path": {
            "@id": f"{ontology_uri}path"
        },
        "value_default": {
            "@id": f"{ontology_uri}value_default"
        },
        "value_type": {
            "@id": f"{ontology_uri}value_type"
        }
    }

    is_a: HttpUrl = f"{ontology_uri}/Parameters"
    configures: HttpUrl = ...
    implements: HttpUrl = ...
    optional: bool = ...
    path: str = ...
    value_default: str = ...
    value_type: str = ...
    label: str = ...
    description: str = ...

    class Config:
        allow_population_by_field_name = True


@rdf(path="estimator.parameters.model_parameters.algorithm.@schema")
@rdf(path="estimator.parameters.optimisation_parameters.algorithm.@schema")
@rdf(path="estimator.parameters.execution_parameters.algorithm.@schema")
class AlgorithmParameterSchemaModel(OntologyModel):
    type: str = Field(alias="@type", default=f"{ontology_uri}/Parameters")
    configures: str = Field(alias=f"{ontology_uri}/configures", default=...)
    label: str = Field(alias="rdfs:label", default=...)
    description: str = Field(alias="rdfs:description", default=...)

    class Config:
        extra = Extra.allow
        allow_population_by_field_name = True


@converter
class ParameterConverter(ObjectConverter):
    def __init__(self, *args, **kwargs):
        super().__init__(storage_type=ResultType.parameter, *args, **kwargs)

    def _prepare_insertion(self, entry: ParameterTO, json_ld, graph):
        entry, json_ld, models = super()._prepare_insertion(entry, json_ld, graph)

        onto_entry = ParameterTOOnto(**entry.dict(by_alias=True))

        # TODO check if ontology doesn't contain what we reference here or we reference nothing?
        # TODO build new json_ld entries

        if (onto_entry.is_a, None, None) not in graph:
            logger.warning(
                f"Class {entry.is_a} of parameter was not found in ontology. Extracting a new ontology class for it...")

        return entry, self._re_append_models(json_ld, models), models

    def _convert(self, entry, graph):

        def parse():
            graph.parse(data=entry.json(by_alias=True), format="json-ld")

        threading.Thread(target=parse).start()
