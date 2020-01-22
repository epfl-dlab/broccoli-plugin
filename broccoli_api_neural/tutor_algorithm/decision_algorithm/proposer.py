from collections import defaultdict

import numpy as np

import broccoli_api_neural.tutor_algorithm.decision_algorithm.filters as filters
from broccoli_api_neural.tutor_algorithm.memory_model.statefulmemory import StatefulMemory
from broccoli_api_neural.utils import DequeProvider


class Proposer:
    """
    abstract base class for a Proposer Algorithm
    contains functionality to keep track of exposures, feebbacks and word statistics.

    please note:
    instead of 'word' or 'vocab', I'm using 'lemma'
    This is meant to emphasize that we are using the lemmatized versions of each word.
    'state' and 'states' should correspond to the same entry in our vocabulary.

    TODO: this hides grammatical complexity.
    """

    def __init__(self, memory_model: StatefulMemory, max_num_lm_scores=10, track_only_selection=True,
                 tracked_words=None):

        self.memory_model = memory_model

        # keeping track of a word is costly
        # we record data about its language model scores and occurences
        # it is possible to limit this to a subset of vocabulary
        self.track_only_selection = track_only_selection
        self.tracked_words = tracked_words

        # maps word to list of tuples (timestamp, language model score)
        self.lm_scores = defaultdict(DequeProvider(max_num_lm_scores))

    def register_language_model_data(self, lemmas, scores):
        """
        this is statistical data about the language, it is stored in the proposer
        :param lemmas:
        :param scores:
        :return:
        """
        assert type(scores) == np.ndarray
        assert type(lemmas) == list

        for lemma, score in zip(lemmas, scores):
            if self.track_only_selection and lemma not in self.tracked_words:
                continue
            if filters.is_markup(lemma):
                continue

            self.lm_scores[lemma].append(score)

    def register_user_data(self, exposures, feedbacks):
        """
        this data is routed to the memory model
        :param exposures:
        :param feedbacks:
        :return:
        """
        self.memory_model.save(exposures, feedbacks)

    def propose(self, lemmas, scores, settings):
        raise NotImplementedError("don't use this abstract base class")
