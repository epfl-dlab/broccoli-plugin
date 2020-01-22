# coding utf-8

import pickle

import numpy as np
import torch
from fastai import untar_data, URLs
from fastai.text import get_language_model


# load the fastai awd-lstm
def get_model():
    # puzzling the pieces together
    # get weights and itos
    model_path = untar_data(URLs.WT103, data=False)
    fnames = [list(model_path.glob(f'*.{ext}'))[0] for ext in ['pth', 'pkl']]
    wgts_fname, itos_fname = fnames
    itos = pickle.load(open(itos_fname, 'rb'))
    wgts = torch.load(wgts_fname, map_location=lambda storage, loc: storage)

    # get parameters for language model
    default_dropout = {'language': np.array([0.25, 0.1, 0.2, 0.02, 0.15]),
                       'classifier': np.array([0.4, 0.5, 0.05, 0.3, 0.4])}
    drop_mult = 1.
    tie_weights = True
    bias = True
    qrnn = False
    dps = default_dropout['language'] * drop_mult
    bptt = 70
    vocab_size = len(itos)
    emb_sz = 400
    nh = 1150
    nl = 3
    pad_token = 1
    drop_mult = 1.

    model = get_language_model(vocab_size, emb_sz, nh, nl, pad_token, input_p=dps[0], output_p=dps[1],
                               weight_p=dps[2], embed_p=dps[3], hidden_p=dps[4], tie_weights=tie_weights, bias=bias,
                               qrnn=qrnn)

    # load weights into model
    model.load_state_dict(wgts)
    embedding_vectors = wgts['0.encoder.weight'].cpu().numpy()

    # move to gpu
    #model.cuda()

    return model, itos, embedding_vectors


with torch.no_grad():
    model, itos, embedding_vectors = get_model()
    t_embedding_vectors = torch.tensor(embedding_vectors)

    model.eval()
    model.reset()

    rnn_core = list(model.children())[0]
    enc = list(rnn_core.children())[0]
