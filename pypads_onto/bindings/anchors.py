from pypads.bindings.anchors import anchors

DEFAULT_ANCHORS = []


def init_anchors():
    if not all([a.name in anchors for a in DEFAULT_ANCHORS]):
        raise Exception("There seems to be an issues with adding the anchors")


init_anchors()
