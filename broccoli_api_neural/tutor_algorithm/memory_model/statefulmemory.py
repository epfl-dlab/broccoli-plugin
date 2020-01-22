"""
This is an abstract base class for memory models.

The memory model is split in two parts:
a learning model that maps from exposures and feedback to a memory state,
a recall model that maps from a memory state to recall predictions

The border between those two models depends on the implementation and might not be well-defined.
For example, there could be a parameter for word difficulty which affects both recall and exposure effectiveness.

The state of the model is a representation of the users memory.
We can use it to derive a learning progress, which quantifies how well the user is learning.
The state of the model changes over time, so the learning progress is also time dependent.

The memory state changes with each exposure and each user feedback.
Data on user feedback (and exposures) can be used as ground truth in an optimization process.
We pass the data forward through the learning model and the resulting state forward through the recall model.
Then we can compare the predicted recall chance with the given feedback and fit both learning and recall model.
This process could be very expensive and is only possible with data on user feedback.
Therefore we expose three different functions:
 - register, store a list of exposures and feedbacks, this is a forward pass through the learning model
 - predict_recall, a forward pass through the recall model
 - fit, (re-)fits the model to the registered data, and updates the state

The fitting process will also need to take into consideration a trade-off between data on this individual user,
and data that we have collected on all users.
To begin with we should use an estimate fitted to all available data and then slowly adapt to this specific user.
"""

from collections import defaultdict


class StatefulMemory:
    def __init__(self, max_memory_items=10000):
        self.state = {}

        self.max_memory_items = max_memory_items

        # maps lemmata to a list of exposures and feedbacks
        # we keep both exposures and feedbacks in the same list
        # and this list is sorted by time
        self.observations = defaultdict(list)

    def save(self, exposures: [(str, int)], feedbacks: [(str, int, bool)]):
        raise NotImplementedError()

    def register(self, exposures, feedbacks):
        """
        updates the internal list of observations.
        For each lemma, the new observations are returned.
        It is important to process observations in order, the sequence of observations has a huge influence on
        memory stability as computed by supermemo.
        Therefore, if an observation is younger than what we have stored in the dict of observations, we have to
        recompute the entire memory trace.
        :param exposures:
        :param feedbacks:
        :return: dictionary which maps lemmata to number of new observations, a -1 means that the trace has to be recomputed
        """

        joint_exposures_feedbacks = exposures + feedbacks

        for exposure in exposures:
            lemma, timestamp = exposure
            assert type(lemma) == str
            assert type(timestamp) == int

        for feedback in feedbacks:
            lemma, timestamp, correct = feedback
            assert type(lemma) == str
            assert type(timestamp) == int
            assert type(correct) == bool

        # sort by time
        joint_exposures_feedbacks = sorted(joint_exposures_feedbacks, key=lambda x: x[1])

        out_of_order_lemmata = set()
        num_new_observations = defaultdict(int)

        for observation in joint_exposures_feedbacks:
            lemma, timestamp = observation[:2]

            if self.observations[lemma] and self.observations[lemma][-1][0] > timestamp:
                out_of_order_lemmata.add(lemma)

            self.observations[lemma].append(observation[1:])
            num_new_observations[lemma] += 1

        for lemma in out_of_order_lemmata:
            self.observations[lemma] = sorted(self.observations[lemma], key=lambda x: x[0])
            num_new_observations[lemma] = -1

        return num_new_observations

    def predict_recall(self, lemma, current_time):
        raise NotImplementedError

    def fit(self):
        raise NotImplementedError

    def learning_progress(self, current_time):
        raise NotImplementedError

    def learning_progress_after(self, current_time, exposure):
        raise NotImplementedError
