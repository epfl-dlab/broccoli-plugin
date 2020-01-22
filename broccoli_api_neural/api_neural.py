#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re

import bleach
import numpy as np
import spacy
from bs4 import BeautifulSoup as soup
from flask import Flask, session
from flask import request, make_response, jsonify
from flask_cors import CORS
from flask_session import Session
from spacy.tokenizer import Tokenizer

import broccoli_api_neural.language_model.analysis as analysis
from broccoli_api_neural.translation.coroutines import translate_tokens
from broccoli_api_neural.tutor_algorithm.decision_algorithm.greedyproposer import GreedyProposer
from broccoli_api_neural.utils import get_html_tags

Proposer = GreedyProposer

app = Flask(__name__)
SESSION_TYPE = 'filesystem'
app.config.from_object(__name__)
Session(app)
cors = CORS(app, resources={r"/predict/*": {"origins": "*"}})

# please note: this code has lots of non-threadsafe parts
# the model needs to be fed with data in the order that it occurs on-site
# wordnet, spacy, etc are not threadsafe
# ...
multi_threaded = False  # if you want to change this, all the non-threadsafe APIs have to be allocated thread-locally
infix_re = re.compile(r'''[".,]''')


def custom_tokenizer(nlp):
    return Tokenizer(nlp.vocab, infix_finditer=infix_re.finditer)


spacy_en = spacy.load('en')
#spacy_en.tokenizer = custom_tokenizer(spacy_en)


@app.route("/clear_session", methods=["GET"])
def clear_session():
    session.clear()
    return make_response("session cleared", 200)


@app.route("/reset_api", methods=["GET"])
def reset_api():
    session.clear()

    if "proposer" not in session:
        proposer = Proposer()
        session["proposer"] = proposer

    return make_response("session reset", 200)


@app.route("/register", methods=["POST"])
def register():
    # get parameters from query
    data = json.loads(request.data)

    if "proposer" not in session:
        proposer = Proposer()
        session["proposer"] = proposer
    else:
        proposer = session["proposer"]

    exposures = []
    feedbacks = []
    for item in data:
        lemma = item["targetTokenInfo"]["lemma"]
        timestamp = item["timestamp"]

        if "exposure" in item:
            exposures.append((lemma, timestamp))
        elif "feedback" in item:
            correct = item["correct"]
            feedbacks.append((lemma, timestamp, correct))

    proposer.register_user_data(exposures, feedbacks)

    return make_response("feedback recorded", 200)


@app.route('/get_target_tokens', methods=['POST'])
def get_target_tokens():
    # get parameters from query
    data = json.loads(request.data)

    paragraph = data['paragraph']  # a copy of the paragraph object stored in firebase
    paragraph_key = data['paragraph_key']  # the corresponding key, used to identify the paragraph on the page
    settings = data['settings']  # settings regarding model choice, etc
    current_time = data['time']

    html = paragraph['innerHTML']

    # sanitize html
    #html = bleach.clean(html, tags=['*'], attributes={'*': ['*']})
    #html = html.replace("&lt;", "<")
    #html = html.replace("&gt;", ">")

    # extract all tags
    html_tags = list(get_html_tags(html))

    # remove html tags, effectively converting this to text
    text = html

    for html_tag in html_tags:\
        text = text.replace(html_tag, " ")

    # remove double spaces
    text = re.sub("\s+", " ", text)

    # tokenize
    doc = spacy_en(text, disable=['tagger', 'ner'])
    tokens = [tok.text.lower() for tok in doc]
    tokens = [token for token in tokens if token != ' '] #remove spaces from tokens

    lemmas = [tok.lemma_ for tok in doc if tok.text.lower() != ' ']

    if "proposer" not in session:
        proposer = Proposer()
        session["proposer"] = proposer
    else:
        proposer = session["proposer"]

    # lemmas are for look-up in the vocabulary

    ratios = []
    hits = []
    proba_sum = []
    target_token_infos = []
    new_text = ""

    # nothing to do here, the text is empty
    if not lemmas:
        return make_response(jsonify({
            "hits": hits,
            "proba_sum": proba_sum,
            "ratios": ratios,
            "target_token_infos": target_token_infos,
            "new_text": new_text
        }), 200)

    tokens, lemmas, probas = analysis.process(tokens, lemmas, text, settings)

    probas = np.concatenate([[0], probas])

    proposer.register_language_model_data(lemmas, probas)
    chosen_indices = proposer.propose(lemmas, probas, current_time, settings)
    chosen_tokens = [tokens[idx] for idx in chosen_indices]
    chosen_probas = [probas[idx] for idx in chosen_indices]

    # sort by occurence, the expression doesn't work for empty lists
    if chosen_indices:
        chosen_indices, chosen_tokens, chosen_probas = zip(
            *sorted(list(zip(chosen_indices, chosen_tokens, chosen_probas)), key=lambda x: x[0]))

    # create target token infos
    target_token_infos = []
    for token_idx, (chosen_idx, chosen_token, chosen_proba) in enumerate(
            zip(chosen_indices, chosen_tokens, chosen_probas)):
        token_id = paragraph_key + '_' + str(token_idx)
        mark_id = 'mark_' + token_id
        target_token_info = {
            "token": chosen_token,
            "chosen_idx": chosen_idx,
            "lemma": lemmas[chosen_idx],
            "sentence": doc[chosen_idx:chosen_idx + 1].sent.text,
            "synonyms": [chosen_token, lemmas[chosen_idx]],
            "proba": chosen_proba,
            'paragraph_key': paragraph_key,
            'token_id': token_id,
            'mark_id': mark_id,
            'mark': "<mark orig_token=\"" + chosen_token + "\"id=\"" + mark_id + "\"></mark>"
        }

        target_token_infos.append(target_token_info)

    target_token_infos = translate_tokens(target_token_infos, settings['language_id'])
    chosen_indices = [int(target_token_info['chosen_idx']) for target_token_info in target_token_infos]
    for target_token_info in target_token_infos:
        del target_token_info['chosen_idx']

    offset = 0
    stopgap_item = "STOPGAPAFTERLAST"
    token_gen = iter(tokens + [stopgap_item])
    target_token_gen = iter(target_token_infos + [stopgap_item])
    html_tag_gen = iter(html_tags + [stopgap_item])

    current_token = next(token_gen)
    current_target_token = next(target_token_gen)
    current_html_tag = next(html_tag_gen)
    tokens_processed = 0
    while True:
        html_offset = html.lower().find(current_html_tag.lower(), offset)
        token_offset = html.lower().find(current_token.lower(), offset)

        if max(html_offset, token_offset) < 0:
            break

        if (html_offset >= 0 and (html_offset <= token_offset)) or token_offset <0:
            offset = html_offset + len(current_html_tag)
            current_html_tag = next(html_tag_gen)
        else:
            if tokens_processed in chosen_indices:
                html = html[:token_offset] + current_target_token["mark"] + html[token_offset + len(current_token):]
                offset = token_offset + len(current_target_token["mark"])
                current_target_token = next(target_token_gen)
            else:
                offset = token_offset + len(current_token)

            current_token = next(token_gen)
            tokens_processed += 1

    if current_token != stopgap_item or \
        current_html_tag != stopgap_item or \
        current_target_token != stopgap_item:
        raise AssertionError()

    return make_response(jsonify({
        "hits": hits,
        "proba_sum": proba_sum,
        "ratios": ratios,
        "target_token_infos": target_token_infos,
        "new_text": html
    }), 200)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=multi_threaded)
