import threading
from typing import Optional, Union, List

from pydantic import Field, Extra, HttpUrl
from pypads import logger
from pypads.app.injections.tracked_object import Parameter
from pypads.model.models import ResultType

from pypads_onto.arguments import ontology_uri
from pypads_onto.injections.converter import converter, ObjectConverter, _pop_model_by_data_path, _append_model
from pypads_onto.model.ontology import rdf, EmbeddedOntologyModel, OntologyModel


@rdf(path="estimator.parameters.model_parameters.@schema")
@rdf(path="estimator.parameters.optimisation_parameters.@schema")
@rdf(path="estimator.parameters.execution_parameters.@schema")
class ParameterOntoModel(EmbeddedOntologyModel):
    """
    A representation of an ontology entry for the parameter in json-ld. This doesn't include the value of the parameter
    setting, but only the concept of the parameter. For an ontology parameters should be split in a-box and t-box
    """
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
    configures: Union['AlgorithmOntoModel', HttpUrl] = ...
    implements: Union['AlgorithmParameterOntoModel', HttpUrl] = ...
    optional: bool = ...
    path: str = ...
    value_default: str = ...
    value_type: str = ...
    label: str = ...
    description: str = ...

    class Config:
        allow_population_by_field_name = True


class ParameterOntoSetting(EmbeddedOntologyModel):
    context: Optional[Union[List[Union[str, dict]], str, dict]] = {}
    type: Union['ParameterOntoModel', HttpUrl] = ...  # Reference to the ParameterOntoModel described
    value: str = ...  # Str representation of the value


class AlgorithmOntoModel(OntologyModel):
    """
    A representation of the abstract / generic / conceptual representation of the mathematical concept of an algorithm.
    """
    type: HttpUrl = Field(alias="@type", default=f"{ontology_uri}/Algorithm")
    solves: Union[HttpUrl] = Field(alias=f"{ontology_uri}/solves",
                                   default=...)  # A reference to a task to be solved. TODO add Task model
    label: str = Field(alias="rdfs:label", default=...)
    description: str = Field(alias="rdfs:description", default=...)

    class Config:
        extra = Extra.allow
        allow_population_by_field_name = True


@rdf(path="estimator.parameters.model_parameters.algorithm.@schema")
@rdf(path="estimator.parameters.optimisation_parameters.algorithm.@schema")
@rdf(path="estimator.parameters.execution_parameters.algorithm.@schema")
class AlgorithmParameterOntoModel(OntologyModel):
    """
    A representation of the abstract / generic / conceptual representation of the parameter for a mathematical concept.
    """
    type: str = Field(alias="@type", default=f"{ontology_uri}/Parameters")
    configures: str = Field(alias=f"{ontology_uri}/configures", default=...)
    label: str = Field(alias="rdfs:label", default=...)
    description: str = Field(alias="rdfs:description", default=...)
    # Reference to other AlgorithmParameterOntoModels. Some parameters might group others together into a single value.
    includes: Optional[Union[HttpUrl, 'AlgorithmParameterOntoModel']] = Field(alias=f"{ontology_uri}/includes")

    class Config:
        extra = Extra.allow
        allow_population_by_field_name = True


@converter
class ParameterConverter(ObjectConverter):

    def __init__(self, *args, **kwargs):
        super().__init__(storage_type=ResultType.parameter, *args, **kwargs)

    def _prepare_insertion(self, entry: Parameter, json_ld, graph):
        entry, json_ld, models = super()._prepare_insertion(entry, json_ld, graph)

        onto_entry = ParameterOntoModel(**entry.dict(by_alias=True))

        algorithm_model = _pop_model_by_data_path(models, AlgorithmOntoModel, default=None)
        if algorithm_model is None:
            logger.warning(f"Algorithm model couldn't be found for {entry} in mapping provided data."
                           f" Trying to extract something...")
            # TODO add validators on OntoModel trying to extract information by looking into the current environment.
            #  These will be called here but also in the preceding model extraction.
            #  This allows to check and fill missing values in user provided data.
            # noinspection PyTypeChecker
            algorithm_model = AlgorithmOntoModel(uri=f"{ontology_uri}/Algorithm#Dummy",
                                                 solves=f"{ontology_uri}/Task#Dummy", label="Unknown algorithm",
                                                 description="Algorithm was extracted.")

            models = _append_model(models, algorithm_model)

        algorithm_parameter_model = _pop_model_by_data_path(models, AlgorithmParameterOntoModel, default=None)
        if algorithm_parameter_model is None:
            logger.warning(
                "Algorithm parameter model couldn't be found in mapping provided data. Trying to extract something...")
            # noinspection PyTypeChecker
            algorithm_parameter_model = AlgorithmParameterOntoModel(uri=f"{ontology_uri}/AlgorithmParameter#Dummy",
                                                                    configures=f"{ontology_uri}/AlgorithmParameter#Dummy",
                                                                    label="Unknown algorithm parameter",
                                                                    description="Algorithm parameter was extracted.",
                                                                    includes=None)

            models = _append_model(models, algorithm_parameter_model)

        parameter_model = _pop_model_by_data_path(models, ParameterOntoModel, default=None)
        if parameter_model is None:
            logger.warning("Parameter model couldn't be found in mapping provided data. Trying to extract something...")
            # noinspection PyTypeChecker
            parameter_model = ParameterOntoModel(configures=f"{ontology_uri}/AlgorithmImplementation#Dummy",
                                                 implements=f"{ontology_uri}/AlgorithmParameter#Dummy",
                                                 optional="Unknown",
                                                 path="Unknown", value_default="Unknown",
                                                 value_type="Unknown", label="Unknown",
                                                 description="Unknown")  # TODO fill with dummy values
            models = _append_model(models, parameter_model)

        if (onto_entry.is_a, None, None) not in graph:
            logger.warning(
                f"Class {entry.is_a} of parameter was not found in ontology. Extracting a new ontology class for it...")

        return entry, self._re_append_models(json_ld, models), models

    def _convert(self, entry, graph):
        def parse():
            graph.parse(data=entry.json(by_alias=True), format="json-ld")

        threading.Thread(target=parse).start()
