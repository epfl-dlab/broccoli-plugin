import copy
from collections import defaultdict

import numpy as np

from broccoli_api_neural.tutor_algorithm.memory_model.statefulmemory import StatefulMemory
from broccoli_api_neural.utils import ConstantProvider


class SupermemoMemory(StatefulMemory):
    def __init__(self):
        super().__init__()

        self.state = {}
        self.reset()

    def reset(self):
        # supermemo configuration
        self.state['a'] = 76
        self.state['b'] = 0.023
        self.state['c'] = -3.1
        self.state['d'] = -2

        # overwriting parts of the supermemo configuration
        # with a more conservative estimate
        self.state['b'] = 0.075  # S^-b => higher stabilities increase slower

        # the effect of S_inc is decreased if you are only passively exposed to the word
        self.state['exposure_bonus'] = 0.01
        self.state['feedback_bonus'] = 1
        self.state['stability_base'] = 2
        self.state['stability_start_exponent'] = -1

        # current stability and last exposures for each word
        self.state['stability_exponent'] = defaultdict(ConstantProvider(self.state['stability_start_exponent']))
        self.state['last_exposure'] = defaultdict(int)

        # for calculating the loss
        self.state['horizon'] = 1  # delay until next expected exposure

    def reset_progress(self, lemma):
        del self.state['last_exposure'][lemma]
        del self.state['stability_exponent'][lemma]

    @staticmethod
    def __s_inc(state, S, R):
        a = state['a']
        b = state['b']
        c = state['c']
        d = state['d']

        return a * S ** -b * np.exp(c * R) + d

    @staticmethod
    def process_observation(state, lemma, observation):
        timepoint = observation[0]

        # calculate stability increase, according to SuperMemo formula
        S = state['stability_base'] ** state['stability_exponent'][lemma]
        S = max(S, state['stability_base'] ** state['stability_start_exponent'])
        R = SupermemoMemory.predict_recall(state, lemma, timepoint)
        s_inc = SupermemoMemory.__s_inc(state, S, R)
        s_inc = np.log2(s_inc)

        # apply increase in stability
        # the increase is scaled up/down, depending on whether the observation was exposure or feedback
        if len(observation) == 1:
            s_inc_multiplier = state['exposure_bonus']
        else:
            s_inc_multiplier = state['feedback_bonus']

        s_inc *= s_inc_multiplier

        if len(observation) == 1 or observation[1]:
            state['stability_exponent'][lemma] += s_inc
        else:
            state['stability_exponent'][lemma] = state['stability_start_exponent']

        state['last_exposure'][lemma] = timepoint

        return state

    @staticmethod
    def update(state, new_observations):
        new_state = copy.deepcopy(state)

        for lemma, observations in new_observations.items():
            for observation in observations:
                new_state = SupermemoMemory.process_observation(new_state, lemma, observation)

        return new_state

    def save(self, exposures: [(str, int)], feedbacks: [(str, int, bool)]):
        """
        stores new exposure and feedback data in the model and updates the state
        :param exposures:
        :param feedbacks:
        :return:
        """
        # saving this data works in three steps
        # 1. register the data, this means storing the exposures and feedbacks in our list of observations
        # this provides us with a number of new observations for each lemma
        # 2. parse the number of observations, if it's a zero, the data has arrived out of order and we have to
        # recompute the memory trace, we reset it and choose all observations as new observation data
        # 3. use the new observations to update our state

        # 1. use the base register method to store this data
        num_new_observations = super().register(exposures, feedbacks)

        # 2. parse number of new observations, reset state if necessary
        new_observations = {}  # maps lemmata to new observations

        for lemma, num_new in num_new_observations.items():
            if num_new == -1:
                self.reset_progress(lemma)
                observations = self.observations[lemma]
            else:
                observations = self.observations[lemma][-num_new:]

            new_observations[lemma] = observations

        new_state = self.update(self.state, new_observations)
        self.state = new_state

    @staticmethod
    def utility(x):
        """ utility curve"""
        return x

    @staticmethod
    def learning_progress(state, current_time):
        sum_utility = 0
        for lemma, stability_exponent in state['stability_exponent'].items():
            stability = state['stability_base'] ** stability_exponent
            utility = SupermemoMemory.utility(stability)
            sum_utility += utility

        return sum_utility

    def learning_progress_after(self, current_time, exposure):

        lemma, timepoint = exposure
        new_observations = {lemma: [(timepoint,)]}

        new_state = self.update(self.state, new_observations)
        lp_after = self.learning_progress(new_state, current_time)

        return lp_after

    @staticmethod
    def predict_recall(state, lemma, current_time):
        if lemma in state['last_exposure'].keys():
            if state['last_exposure'][lemma] > 0:
                last_exposure = state['last_exposure'][lemma]
                assert current_time >= last_exposure

                timedelta = current_time - state['last_exposure'][lemma]
            else:
                timedelta = 0
        else:
            timedelta = 0

        # convert to seconds
        timedelta = timedelta/1000

        # convert to hours
        timedelta = timedelta/3600

        # convert to days
        timedelta = timedelta/24

        S = state['stability_base'] ** state['stability_exponent'][lemma]
        S = max(S, state['stability_base'] ** state['stability_start_exponent'])
        R = np.exp(-timedelta / S)

        return R

    def fit(self, exposures, feedbacks):
        raise NotImplementedError
