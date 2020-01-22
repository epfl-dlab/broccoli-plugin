import pickle
from collections import defaultdict

import numpy as np
from nltk.corpus import words

from broccoli_api_neural.tutor_algorithm.decision_algorithm.proposer import Proposer


class LeitnerProposer(Proposer):
    """
    implements a Leitner Queue Model
    """

    def __init__(self, min_dist=10, min_threshold=0.3, number_queues=7, exposures_per_queue=3, min_active_words=250,
                 max_num_exposures=100, max_num_feedbacks=10, max_num_lm_scores=20):

        # words that we are interested in
        self.english_words = words.words(fileids=["en"])
        self.basic_words = words.words(fileids=["en-basic"])

        # route params from our constructor back to the parent class
        super().__init__(max_num_exposures=max_num_exposures, max_num_feedbacks=max_num_feedbacks,
                         max_num_lm_scores=max_num_lm_scores, track_only_selection=True,
                         tracked_words=self.english_words)

        # config of the Leitner Queue Model
        self.min_dist = min_dist
        self.min_threshold = min_threshold
        self.number_queues = number_queues
        self.exposures_per_queue = exposures_per_queue
        self.min_active_words = min_active_words

        self.exposure_counter = defaultdict(0)
        self.current_queue = defaultdict(0)
        self.learned_words = set()

    def register_exposure(self, lemma, timestamp):
        super().register_feedback(lemma, timestamp)

        num_exposures = self.exposure_counter[lemma] + 1
        current_queue = self.current_queue[lemma]

        if lemma not in self.learned_words and num_exposures > self.exposures_per_queue:
            self.exposure_counter[lemma] = 0

            # word has been learned
            if current_queue == self.number_queues:
                self.learned_words.add(lemma)
                del self.current_queue[lemma]
            else:
                self.current_queue[lemma] = current_queue + 1

        self.refill_queue()

    def register_feedback(self, lemma, timestamp, feedback):
        super().register_feedback(lemma, timestamp, feedback)

        current_queue = self.current_queue[lemma]

        # move word up or down the queue, based on feedback
        if feedback == 1:

            # word has been learned
            if current_queue == self.number_queues:
                self.learned_words.add(lemma)
                del self.current_queue[lemma]
            else:
                self.current_queue[lemma] = current_queue + 1
        else:
            if lemma in self.learned_words:
                self.learned_words.remove(lemma)

            if current_queue != 0:
                self.current_queue[lemma] = current_queue - 1

        self.refill_queue()

    def refill_queue(self):
        # refill queue 0 until we have desired total number of words
        while len(self.current_queue.keys()) < self.min_active_words:
            # choose a new word to learn
            summed_scores = [(lemma, sum(scores)) for lemma, scores in self.lm_scores.items() if
                             lemma not in self.current_queue.keys() and lemma not in self.learned_words]
            summed_scores = sorted(summed_scores, key=lambda x: x[1], reverse=True)

            if summed_scores:
                best_lemma = summed_scores[0][0]
                self.current_queue[best_lemma] = 0
            if not summed_scores:
                break

    def propose(self, lemmas, scores):

        mask = np.zeros_like(scores)
        for i, lemma in enumerate(lemmas):
            mask[i] = 1 if lemma in self.current_queue.keys() else 0

        adjusted_scores = scores * mask

        chosen_indices, chosen_probas = [], []
        while adjusted_scores.max() > self.threshold:
            max_idx = adjusted_scores.argmax()
            chosen_indices.append(max_idx)
            chosen_probas.append(scores[max_idx])

            adjusted_scores[max(0, max_idx - self.min_dist): max_idx + self.min_dist] = 0

        return chosen_indices, chosen_probas


if __name__ == "__main__":
    prop = LeitnerProposer()
    pickled = pickle.dumps(prop)
    print(len(pickled))
