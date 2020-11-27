import threading

from pypads.model.models import ResultType

from pypads_onto.injections.converter import converter, ObjectConverter


@converter
class MetricConverter(ObjectConverter):

    def __init__(self, *args, **kwargs):
        super().__init__(storage_type=ResultType.metric, *args, **kwargs)

    def _prepare_insertion(self, entry, json_ld, graph):
        entry, json_ld, models = super()._prepare_insertion(entry, json_ld, graph)
        if json_ld is None:
            # No schema definition was defined by the mapping file for metric TODO trying to extract a Schema
            pass

        return entry, json_ld, models

    def _convert(self, entry, graph):
        # TODO add basic metric t-box. This should be done by parsing additional data
        def parse():
            graph.parse(data=entry.json(by_alias=True), format="json-ld")

        threading.Thread(target=parse).start()