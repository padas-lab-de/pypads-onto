import os
from typing import Union, List, Optional
from urllib.parse import quote

from pydantic import BaseModel, HttpUrl, root_validator, Field, validator, Extra
from pypads.model.models import ResultType, BaseIdModel, AbstractionType
from pypads.utils.logging_util import FileFormats
from pypads.utils.util import persistent_hash

from pypads_onto.arguments import ontology_uri

DEFAULT_CONTEXT = {
    "@context": {
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "padre": f"{ontology_uri}",
        "uri": "@id",
        "is_a": "@type",
        "experiment": {
            "@id": f"{ontology_uri}contained_in",
            "@type": f"{ontology_uri}Experiment"
        },
        "run": {
            "@id": f"{ontology_uri}contained_in",
            "@type": f"{ontology_uri}Run"
        },
        "created_at": {
            "@id": f"{ontology_uri}created_at",
            "@type": "http://www.w3.org/2001/XMLSchema#dateTime"
        },
        "name": {
            "@id": f"{ontology_uri}label",
            "@type": "http://www.w3.org/2001/XMLSchema#string"
        },
        "in_context": {
            "@id": f"{ontology_uri}relates_to",
            "@type": f"{ontology_uri}Context"
        },
        "reference": {
            "@id": f"{ontology_uri}represents",
            "@type": "http://www.w3.org/2001/XMLSchema#string"
        },
        "produced_by": {
            "@id": f"{ontology_uri}produced_by",
            "@type": f"{ontology_uri}LoggerCall"
        },
        "failed": {
            "@id": f"{ontology_uri}failure",
            "@type": "http://www.w3.org/2001/XMLSchema#boolean"
        }
    }
}
default_ctx_path = None


def get_default_ctx_path():
    """
    Function to persist the default context and get it's location.
    :return:
    """
    try:
        global default_ctx_path
        from pypads.app.pypads import get_current_pads
        pads = get_current_pads()
        if not default_ctx_path:
            obj = pads.schema_repository.get_object(uid=persistent_hash(str(DEFAULT_CONTEXT)))
            default_ctx_path = obj.log_mem_artifact("pypads_context_default", DEFAULT_CONTEXT,
                                                    write_format=FileFormats.json, write_meta=False)
            obj.set_tag("pypads.schema_name", "pypads_context_default")
        return os.path.join(default_ctx_path)
    except Exception as e:
        # Return context itself instead
        return DEFAULT_CONTEXT['@context']


class OntologyModel(BaseModel):
    """
    Object representing an (potential) entry in a knowledge base
    """
    uri: HttpUrl = ...
    context: Union[List[Union[str, dict]], str, dict] = Field(alias='@context', default=None)

    @root_validator
    def add_context(cls, values):
        if ('storage_type' in values
            and values['storage_type'] not in {ResultType.embedded, ResultType.repository_entry}) and not (
                'abstraction_type' in values and values['abstraction_type'] == AbstractionType.reference):
            if values['context'] is None:
                values['context'] = get_default_ctx_path()
            elif isinstance(values['context'], List):
                if len(values['context']) > 0:
                    if values['context'][0] != get_default_ctx_path():
                        values['context'].append(get_default_ctx_path())
            elif values['context'] != get_default_ctx_path():
                values['context'] = [get_default_ctx_path(), values['context']]
        return values


class IdBasedOntologyModel(OntologyModel, BaseIdModel):
    """
    An ontology entry getting its uri build via is_a and id combination.
    """
    is_a: HttpUrl = None
    uri: HttpUrl = None
    category: Optional[str]  # Human readable class representation. This will be converted in ontology entries.
    name: Optional[str]  # Alternative Human readable instance representation.

    @root_validator
    def set_default_uri(cls, values):
        if values['is_a'] is None:
            if 'category' in values and values['category'] is not None:
                values['is_a'] = f"{ontology_uri}{quote(values['category'])}"
            elif 'name' in values and values['name'] is not None:
                values['is_a'] = f"{ontology_uri}{quote(values['name'])}"
            else:
                raise ValueError("Value for is_a is not given and can't be derived")
        if values['uri'] is None:
            values['uri'] = f"{values['is_a']}#{values['uid']}"
        return values

    class Config:
        orm_mode = True


class EmbeddedOntologyModel(IdBasedOntologyModel):
    storage_type: Union[ResultType, str] = None  # This object should not be stored as separate object
    context: Optional[Union[List[Union[str, dict]], str, dict]]

    @validator('storage_type', pre=True, always=True)
    def default_ts_modified(cls, v, *, values, **kwargs):
        return v or ResultType.embedded


mapping_json_ld = {}


def rdf(path):
    def class_wrapper(_cls):
        mapping_json_ld[path] = _cls
        if not hasattr(_cls, "_path"):
            setattr(_cls, "_path", [])
        setattr(_cls, "_path", getattr(_cls, "_path").append(path))
        return _cls

    return class_wrapper


# Metrics
@rdf(path="metric.algorithm.@schema")
class MetricAlgorithmSchemaModel(EmbeddedOntologyModel):
    type: str = Field(alias="@type", default=f"{ontology_uri}/MetricAlgorithm")
    label: str = Field(alias="rdfs:label", default=...)
    description: str = Field(alias="rdfs:description", default=...)
    documentation: str = Field(alias=f"{ontology_uri}/documentation", default=...)

    class Config:
        extra = Extra.allow
        allow_population_by_field_name = True


@rdf(path="metric.@schema")
class MetricImplementationModel(EmbeddedOntologyModel):
    type: str = Field(alias="@type", default=f"{ontology_uri}/MetricImplementation")
    label: str = Field(alias="rdfs:label", default=...)
    description: str = Field(alias="rdfs:description", default=...)
    documentation: str = Field(alias=f"{ontology_uri}/documentation", default=...)
    implements: str = Field(alias=f"{ontology_uri}/implements", default=...)

    class Config:
        extra = Extra.allow
        allow_population_by_field_name = True


# Datasets
@rdf(path="metric.@schema")
class DatasetSchemaModel(EmbeddedOntologyModel):
    type: str = Field(alias="@type", default=f"{ontology_uri}/Dataset")
    label: str = Field(alias="rdfs:label", default=...)
    description: str = Field(alias="rdfs:description", default=...)
    documentation: str = Field(alias=f"{ontology_uri}/documentation", default=...)
    author: str = Field(alias=f"{ontology_uri}/author", default=...)
    has_characteristic: str = Field(alias=f"{ontology_uri}/hasCharacteristic")
    has_feature: str = Field(alias=f"{ontology_uri}/hasFeature", default=...)

    class Config:
        extra = Extra.allow
        allow_population_by_field_name = True


class CharacteristicSchemaModel(EmbeddedOntologyModel):
    """
    Model for a class of characteristics
    """
    type: str = Field(alias="@type", default=f"{ontology_uri}/Characteristic")
    label: str = Field(alias="rdfs:label", default=...)
    description: str = Field(alias="rdfs:description", default=...)

    class Config:
        extra = Extra.allow
        allow_population_by_field_name = True


class CharacteristicModel(EmbeddedOntologyModel):
    """
    Model for an arbitrary characteristic
    """
    type: str = Field(alias="@type", default=f"{ontology_uri}/Characteristic")
    label: str = Field(alias="rdfs:label", default=...)
    has_data: str = Field(alias=f"{ontology_uri}/hasData")
    data_type: str = Field(alias=f"{ontology_uri}/dataType", default=...)

    class Config:
        extra = Extra.allow
        allow_population_by_field_name = True


class FeatureModel(EmbeddedOntologyModel):
    """
    Model for feature column in a dataset.
    """
    type: str = Field(alias="@type", default=f"{ontology_uri}/Feature")
    label: str = Field(alias="rdfs:label", default=...)
    unit: str = Field(alias=f"{ontology_uri}/unit")
    unit_type: str = Field(alias=f"{ontology_uri}/unitType")
    data_type: str = Field(alias=f"{ontology_uri}/dataType", default=...)
    measurement: str = Field(alias=f"{ontology_uri}/measurement", default=...)

    class Config:
        extra = Extra.allow
        allow_population_by_field_name = True
