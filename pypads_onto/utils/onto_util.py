import uuid


def uuid_based_uri_generator(is_a):
    def _generate_uuid_based_uri():
        return "#".join([is_a, str(uuid.uuid4())])
    return _generate_uuid_based_uri
