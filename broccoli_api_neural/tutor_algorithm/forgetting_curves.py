import numpy as np


def exponential_decay(t, H):
    return np.exp(-t / H)
