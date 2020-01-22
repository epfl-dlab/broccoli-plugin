from collections import defaultdict

import numpy as np
from nltk.corpus import words

from broccoli_api_neural.tutor_algorithm.decision_algorithm.proposer import Proposer
from broccoli_api_neural.tutor_algorithm.memory_model.supermemo import SupermemoMemory as MemoryModel
import broccoli_api_neural.tutor_algorithm.decision_algorithm.filters as filters


class GreedyProposer(Proposer):
    """
    implements a Leitner Queue Model
    """

    def __init__(self, min_active_words=250, S_threshold=50, start_with_basic_words = False, forbidden_words = []):

        # words that we are interested in
        english_words = words.words(fileids=["en"])
        basic_words = words.words(fileids=["en-basic"])

        tracked_words = [w for w in english_words if len(w) >= 3]

        if start_with_basic_words:
            starting_words = [w for w in basic_words if len(w) >= 3]
        else:
            starting_words = tracked_words

        self.forbidden_words = forbidden_words

        super().__init__(MemoryModel(), track_only_selection=True, tracked_words=tracked_words)

        self.active_words = starting_words

        # additional config
        self.min_active_words = min_active_words
        self.S_threshold = S_threshold  # when stability reaches this level, we move a word to the set of learned words

        # TODO: the idea of Supermemo is to steadily increase the pool of words that you know
        # as their stability increases, they have to be reviewed less and less frequently
        # this makes place for new words
        # as a first implementation I'm keeping an explicit list of words that we consider learned
        self.learned_words = set()

    def refill_active_words(self):
        # refill queue 0 until we have desired total number of words
        while len(self.active_words) < self.min_active_words:
            # choose a new word to learn
            summed_scores = [(lemma, sum(scores)) for lemma, scores in self.lm_scores.items() if
                             lemma not in self.active_words and lemma not in self.learned_words and lemma not in self.forbidden_words]
            summed_scores = sorted(summed_scores, key=lambda x: x[1], reverse=True)

            if summed_scores:
                best_lemma = summed_scores[0][0]
                self.active_words.append(best_lemma)
            if not summed_scores:
                break

    def register_user_data(self, exposures, feedbacks):
        super().register_user_data(exposures, feedbacks)

        for lemma, stability in self.memory_model.state['stability_exponent'].items():
            if stability > self.S_threshold:
                self.learned_words.add(lemma)
                self.active_words.remove(lemma)

        self.refill_active_words()

    def propose(self, lemmas, scores, current_time, settings):

        learning_progress_value = defaultdict(int)
        recall_probas = defaultdict(int)
        for lemma in set(lemmas):
            if lemma not in self.active_words:
                continue

            if lemma in self.forbidden_words:
                continue

            if settings['filter_stopwords']:
                if filters.is_stop_word(lemma):
                    continue

            learning_progress_value[lemma] = self.memory_model.learning_progress_after(current_time,
                                                                                       (lemma, current_time))
            recall_probas[lemma] = self.memory_model.predict_recall(self.memory_model.state, lemma, current_time)

        mask = np.zeros_like(scores)
        for i, lemma in enumerate(lemmas):
            mask[i] = learning_progress_value[lemma]

        adjusted_probas = np.zeros_like(scores)
        for i, (lemma, score) in enumerate(zip(lemmas, scores)):
            adjusted_probas[i] = score + (1 - score) * recall_probas[lemma]

        adjusted_scores = adjusted_probas * mask

        chosen_indices, chosen_probas = [], []
        while adjusted_scores.max() > settings['threshold']:
            max_idx = adjusted_scores.argmax()
            chosen_indices.append(max_idx)
            chosen_probas.append(scores[max_idx])

            adjusted_scores[max(0, max_idx - settings['min_dist']): max_idx + settings['min_dist']] = 0

        return chosen_indices


if __name__=="__main__":
    proposer = GreedyProposer()

    lemmas = ['I', 'see', 'a', 'dog']
    probas = np.array([0.1, 0.2, 0.5, 0.4])

    proposals = proposer.propose(lemmas, probas, 0, {'min_dist':5, 'filter_stopwords':True, 'threshold':0})
    proposer.register_language_model_data(lemmas, probas)
    proposer.active_words = []
    proposer.refill_active_words()

    print("finished")