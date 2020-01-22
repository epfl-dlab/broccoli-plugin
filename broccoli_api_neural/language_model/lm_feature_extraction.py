import numpy as np
import torch
import torch.nn.functional as F


def get_lm_features(tokens, model, enc, itos, fasttext_neighbours):
    with torch.no_grad():
        numerals = [itos.index(v) if v in itos else 0 for v in tokens]

        # from the fasttext model, we derive additional information on neigh
        neighbours = [[(token, similarity) for (token, similarity) in fasttext_neighbours[v] if
                       token in itos] if v in fasttext_neighbours else [] for v in tokens]
        neighbour_numerals = [[itos.index(t) for (t, s) in n] for n in neighbours]
        neighbour_similarities = [np.array([s for (t, s) in n]) for n in neighbours]

        # set up torch tensor
        # and add a batch dimension
        #t = torch.tensor(numerals).unsqueeze(1).cuda()
        t = torch.tensor(numerals).unsqueeze(1)
        input_embedding = enc(t)

        # give this to the model
        res, *_ = model(t)
        softmaxed = F.softmax(res, 1)

        # get the probability of the tokens in our sequence
        token_probas = softmaxed[np.arange(softmaxed.shape[0] - 1), numerals[1:]]

        # get the rank of each token, if our token was the n-likeliest, the rank is n
        token_ranks = np.zeros((len(tokens) - 1,))
        for idx in range(len(tokens) - 1):
            token_proba = token_probas[idx]
            token_ranks[idx] = (softmaxed[idx] > token_proba).sum()

        # get the entropy of the top predictions
        n_best = 50
        max_vals, max_indices = torch.topk(softmaxed, n_best, 1)
        entropy50 = - (max_vals * torch.log(max_vals)).sum(dim=1)[:-1]
        n_best = 10
        max_vals, max_indices = torch.topk(max_vals, n_best, 1)
        entropy10 = - (max_vals * torch.log(max_vals)).sum(dim=1)[:-1]

        # get the top n next words, this is only for debugging
        n_best = 5
        max_vals, max_indices = torch.topk(softmaxed, n_best, 1)
        words = [[itos[idx] for idx in pred] for pred in max_indices]
        hits = [int(t in w) for t, w in zip(tokens[1:], words[:-1])]

        # compare the probability of our target token with the max probability
        max_probas = max_vals[:-1, 0]
        ratios = token_probas / max_probas
        ratios = ratios.detach().cpu().numpy()

        # get a sum of probabilities, based on the fasttext similarities
        fasttext_sum = np.zeros((len(tokens) - 1,))
        for idx in range(len(tokens) - 1):
            neighbour_nums = neighbour_numerals[idx + 1]
            neighbour_sims = neighbour_similarities[idx + 1]

            fasttext_sum[idx] += token_probas[idx]
            fasttext_sum[idx] += (neighbour_sims * softmaxed[idx, neighbour_nums].cpu().detach().numpy()).sum()

        # convert everything (that is not already converted) to numpy
        token_probas = token_probas.cpu().numpy()
        entropy50 = entropy50.cpu().numpy()
        entropy10 = entropy10.cpu().numpy()
        return token_probas, token_ranks, entropy50, entropy10, ratios, fasttext_sum


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
