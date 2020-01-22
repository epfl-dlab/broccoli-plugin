# load fasttext embedding

import pickle

import dill
from gensim.models.keyedvectors import KeyedVectors
from tqdm import tqdm


def get_fasttext_neighbours(itos):

    # for every word in our vocabulary, the list of closest neighbours according to fasttext
    rerun = False

    if rerun:
        fasttext_model = KeyedVectors.load_word2vec_format("language_model/fasttext/wiki-news-300d-1M.vec",
                                                           binary=False)
        fasttext_neighbours = {}

        for word in tqdm(itos):
            if word in fasttext_model.vocab:
                neighbours = fasttext_model.most_similar(word, topn=30)
                fasttext_neighbours[word] = neighbours

        with open("./broccoli_api_neural/models//fasttext_neighbours.pkl", "wb") as file:
            pickle.dump(fasttext_neighbours, file)
    else:
        with open("./broccoli_api_neural/models//fasttext_neighbours.pkl", "rb") as file:
            fasttext_neighbours = pickle.load(file)

    return fasttext_neighbours
