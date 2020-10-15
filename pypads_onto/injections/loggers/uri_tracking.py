# import sys
# import os
# from python_wikibase import PyWikibase
# from pypads.app.injections.base_logger import LoggingFunction
# from pypads.injections.analysis.call_tracker import LoggingEnv
# from pypads.utils.logging_util import WriteFormats, try_write_artifact
# from pypads.importext.mappings import LibSelector
# from pypads_onto.utils.wikibase_util import WIKIBASE_API_ENDPOINT, create_entity, query_wikibase_sparql, retrieve_entity
#
# 
# def create_run_entity(wikibase_object, name, description, experiment_name):
#     """
#     Creates a run object in the wikibase and links the basic properties to the run
#     :param wikibase_object: the logged in wikibase object'
#     :param name: name of the run
#     :param description: description of the run
#     :param experiment_name: Name of the experiment the run belongs to
#     :return:
#     """
#     from pypads_onto.utils.wikibase_util import PART_OF_PROP, INSTANCE_OF_PROP, EXPERIMENT_ENTITY, EXPERIMENTAL_RUN_ENTITY
#
#     # Create the run entity
#     run_entity = create_entity(wikibase_object, name, description)
#
#     property_instanceof = wikibase_object.Property().get(INSTANCE_OF_PROP)
#
#     # Get the experiment using the experiment name
#     experiment_entity = query_wikibase_sparql(entity_name=experiment_name)
#     if len(experiment_entity) == 0:
#
#         # Fetch instance of property and experiment entity from Wikibase
#         base_experiment_entity = retrieve_entity(wikibase_object, EXPERIMENT_ENTITY)
#
#         # Create the new experiment and link it to the experiment entity as
#         # the current experiment is an instance of experiment
#         experiment_entity = create_entity(wikibase_object, experiment_name, "Experiment created by PyPads")
#         experiment_entity.claims.add(property_instanceof, base_experiment_entity)
#
#     elif len(experiment_entity) == 1:
#         # link the run entity to the experiment entity
#         experiment_entity = experiment_entity[0]
#     else:
#         # Multiple entities with the same name exists
#         raise ValueError
#
#     # Link the experiment and the run
#     property_partof = wikibase_object.Property().get(PART_OF_PROP)
#     run_entity.claims.add(property_partof, experiment_entity)
#
#     # run_entity is an instance of Run entity
#     experimental_run_entity = query_wikibase_sparql(entity_name=EXPERIMENTAL_RUN_ENTITY)
#     run_entity.claims.add(property_instanceof, experimental_run_entity)
#
#     return run_entity
#
#
# def link_sklearn_estimators(wikibase_object, run_entity, sklearn_estimator):
#     """
#     Links estimator to the run along with all the hyperparameters as references
#     :param wikibase_object: Python wikibase object
#     :param run_entity:
#     :param sklearn_estimator:
#     :return:
#     """
#     # Get all hyperparameters of the estimator
#     # Get all values of the hyperparameters for the run
#     # TODO: How will we add hyperparameters
#     # Run has estimator, has hyperparameter which then has value. So it is two levels deep.
#     pass
#
#
# def link_run_metrics(wikibase_object, run_entity, metric_name, value):
#     """
#     Links an experimental run with a metric
#     :param wikibase_object:
#     :param run_entity:
#     :param metric_name:
#     :param value:
#     :return:
#     """
#     from pypads_onto.utils.wikibase_util import HAS_METRIC_PROP, HAS_VALUE_PROP
#     metric_entity = query_wikibase_sparql(entity_name=metric_name)
#     if len(metric_entity) == 0:
#         pass
#     elif len(metric_entity) == 1:
#         metric_entity = metric_entity[0]
#     else:
#         pass
#
#     has_metric_prop = wikibase_object.Property().get(HAS_METRIC_PROP)
#     has_value_prop = wikibase_object.Property().get(HAS_VALUE_PROP)
#     claim = run_entity.claims.add(has_metric_prop, metric_entity)
#     qualifier = claim.qualifiers.add(has_value_prop, value)
#
#
# class URILogger(LoggingFunction):
#
#     _wikibase_object = None
#
#     def __init__(self, username, password):
#         self._wikibase_object = self.initialize_wikibase(username, password)
#
#     def wikibase_object(self):
#         return self._wikibase_object
#
#     @staticmethod
#     def _needed_packages():
#         pass
#
#     def initialize_wikibase(self, username, password):
#         config = {
#             "api_url": WIKIBASE_API_ENDPOINT,
#             "login_credentials": {'bot_username': username, 'bot_password': password},
#             "is_bot": True,
#             "summary": "Modified using wikibase-api for Python"
#         }
#         py_wb = PyWikibase(**config)
#         return py_wb
#
#     def __pre__(self, ctx, *args, _pypads_write_format=WriteFormats.pickle, _pypads_env, _args, _kwargs, **kwargs):
#         for i in range(len(args)):
#             arg = args[i]
#             name = os.path.join(_pypads_env.call.to_folder(),
#                                 "args",
#                                 str(i) + "_" + str(id(_pypads_env.callback)))
#             try_write_artifact(name, arg, _pypads_write_format)
#
#         for (k, v) in kwargs.items():
#             name = os.path.join(_pypads_env.call.to_folder(),
#                                 "kwargs",
#                                 str(k) + "_" + str(id(_pypads_env.callback)))
#             try_write_artifact(name, v, _pypads_write_format)
#
#     def __post__(self, ctx, *args, _pypads_env:LoggingEnv,
#                  _pypads_pre_return, _pypads_result, _args, _kwargs, **kwargs):
#         """
#
#         :param ctx:
#         :param args:
#         :param _pypads_env:
#         :param _pypads_pre_return:
#         :param _pypads_result:
#         :param _args:
#         :param _kwargs:
#         :param kwargs:
#         :return:
#         """
#
#         from pypads.app.pypads import get_current_pads
#         pads = get_current_pads()
#



