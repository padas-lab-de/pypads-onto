from pypads.bindings.event_types import event_types

DEFAULT_PADRE_EVENT_TYPES = []


def init_event_types():
    if not all([a.name in event_types for a in DEFAULT_PADRE_EVENT_TYPES]):
        raise Exception("There seems to be an issues with adding the anchors")


init_event_types()
