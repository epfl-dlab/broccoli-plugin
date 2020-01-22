import numpy as np

from sklearn.externals import joblib

cvec = joblib.load("./broccoli_api_neural/models/cvec.pkl")
transformer = joblib.load("./broccoli_api_neural/models/transformer.pkl")


def tf_idf(token, text):
    try:
        token_idx = cvec.vocabulary_[token.lower()]
    except KeyError:
        return 0
    transformed_weights = transformer.transform(cvec.transform([text]))
    return transformed_weights[0, token_idx]
