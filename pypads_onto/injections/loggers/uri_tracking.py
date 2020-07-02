import sys
import os
from python_wikibase import PyWikibase
from pypads.app.injections.base_logger import LoggingFunction
from pypads.injections.analysis.call_tracker import LoggingEnv
from pypads.utils.logging_util import WriteFormats, try_write_artifact
from pypads.importext.mappings import LibSelector
from pypads_onto.utils.wikibase_util import WIKIBASE_API_ENDPOINT


def initialize_wikibase(user, password):
    config = {
        "api_url": WIKIBASE_API_ENDPOINT,
        "login_credentials": {'bot_username': user, 'bot_password': password},
        "is_bot": True,
        "summary": "Modified using wikibase-api for Python"
    }
    py_wb = PyWikibase(**config)


class URILogger(LoggingFunction):


    @staticmethod
    def _needed_packages():
        pass

    def __pre__(self, ctx, *args, _pypads_write_format=WriteFormats.pickle, _pypads_env, _args, _kwargs, **kwargs):
        for i in range(len(args)):
            arg = args[i]
            name = os.path.join(_pypads_env.call.to_folder(),
                                "args",
                                str(i) + "_" + str(id(_pypads_env.callback)))
            try_write_artifact(name, arg, _pypads_write_format)

        for (k, v) in kwargs.items():
            name = os.path.join(_pypads_env.call.to_folder(),
                                "kwargs",
                                str(k) + "_" + str(id(_pypads_env.callback)))
            try_write_artifact(name, v, _pypads_write_format)

    def __post__(self, ctx, *args, _pypads_env:LoggingEnv,
                 _pypads_pre_return, _pypads_result, _args, _kwargs, **kwargs):
        """

        :param ctx:
        :param args:
        :param _pypads_env:
        :param _pypads_pre_return:
        :param _pypads_result:
        :param _args:
        :param _kwargs:
        :param kwargs:
        :return:
        """

        from pypads.app.pypads import get_current_pads
        pads = get_current_pads()




