# coding utf-8

import numpy as np
from sklearn.externals import joblib

from broccoli_api_neural.language_model.embedding import get_fasttext_neighbours
from broccoli_api_neural.language_model.lm_feature_extraction import tf_idf, get_lm_features
from broccoli_api_neural.language_model.neural_model import model, enc, itos

regression_model = joblib.load("./broccoli_api_neural/models/final_model.pkl")
ss = joblib.load("./broccoli_api_neural/models/scaler.pkl")

fasttext_neighbours = get_fasttext_neighbours(itos)


def reset_model():
    model.eval()
    model.reset()


def process(tokens, lemmas, text, settings):

    token_probas, token_ranks, entropy10, entropy50, ratios, fasttext_sums = get_lm_features(tokens, model, enc, itos,
                                                                                             fasttext_neighbours)
    if settings['only_neural']:
        return tokens, lemmas, fasttext_sums
    else:
        is_in_context = [lemma in (lemmas[:idx] if idx > 0 else []) + (lemmas[idx + 1:]) for idx, lemma in
                         enumerate(lemmas)]
        tf_idfs = [tf_idf(token, text) for token in tokens]

        top5 = token_ranks < 5
        top10 = token_ranks < 10
        top50 = token_ranks < 50

        # this must be the same order as in training, compare with list of selected features
        features = np.stack([entropy10,
                             entropy50,
                             fasttext_sums,
                             ratios,
                             token_ranks,
                             token_probas,
                             tf_idfs[1:],
                             is_in_context[1:],
                             top5, top10, top50], axis=1)

        features = ss.transform(features)

        probas = regression_model.predict(features)
        return tokens, lemmas, probas
