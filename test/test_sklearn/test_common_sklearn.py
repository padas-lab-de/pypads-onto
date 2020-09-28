import datetime

import mlflow

from test.base_test import TEST_FOLDER
from test.test_sklearn.base_sklearn_test import BaseSklearnTest, sklearn_simple_decision_tree_experiment, \
    sklearn_pipeline_experiment


class CommonSklearnTest(BaseSklearnTest):

    def test_default_tracking(self):
        """
        This example will track the experiment exection with the default configuration.
        :return:
        """
        # --------------------------- setup of the tracking ---------------------------
        # Activate tracking of pypads
        from pypads.app.base import PyPads
        tracker = PyPads(uri="http://mlflow.padre-lab.eu")
        tracker.activate_tracking()
        tracker.start_track()

        import timeit
        t = timeit.Timer(sklearn_simple_decision_tree_experiment)
        from pypads import logger
        logger.info(t.timeit(1))

        # --------------------------- asserts ---------------------------
        tracker.api.push_rdf(run_id=tracker.api.active_run().info.run_id)

        tracker.api.end_run()
        # !-------------------------- asserts ---------------------------
