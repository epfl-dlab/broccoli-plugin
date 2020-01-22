import asyncio

import aiohttp

from broccoli_api_neural.translation.ms_api_async import MS_Translator_Async

ms_translator = MS_Translator_Async()


async def sentence_translation_coroutine(session: aiohttp.ClientSession, sentences, TARGET_LANGUAGE):
    sentence_translations = []

    # set up coroutines for translations
    for sentence in sentences:
        sentence_translations.append(
            ms_translator.translate_phrase(session, sentence, TARGET_LANGUAGE))

    # group all translations into a single coroutine
    return await asyncio.gather(*sentence_translations)


async def word_translation_coroutine(session: aiohttp.ClientSession, tokens, TARGET_LANGUAGE):
    word_translations = []
    # set up coroutines for translations
    for token in tokens:
        word_translations.append(ms_translator.translate_word(session, token, TARGET_LANGUAGE))

    # group all translations into a single coroutine
    return await asyncio.gather(*word_translations)


def translate_tokens(target_token_infos, TARGET_LANGUAGE):
    # all the target_token_infos have to be augmented with their translations
    # this is done asynchronously
    # all HTTP requests are dispatched immediately one after the other
    async def main():
        sentences = [t["sentence"] for t in target_token_infos]
        tokens = [t["token"] for t in target_token_infos]

        async with aiohttp.ClientSession() as session:
            all_requests = asyncio.wait_for(asyncio.gather(
                sentence_translation_coroutine(session, sentences, TARGET_LANGUAGE),
                word_translation_coroutine(session, tokens, TARGET_LANGUAGE)), timeout=100000)

            sentence_translations, word_translations = await all_requests
        return sentence_translations, word_translations

    loop = asyncio.new_event_loop()
    sentence_translations, word_translations = loop.run_until_complete(main())

    # step 3
    # process translations
    processed_target_tokens = []
    for target_token_info, sentence_translation, word_translation in zip(target_token_infos,
                                                                         sentence_translations,
                                                                         word_translations):

        # if the API call failed, our coroutines return False
        # in that case we simply continue, the target token_info is not added to the list of processed tokens
        if not sentence_translation or not word_translation:
            continue

        translated_phrase, from_words = sentence_translation
        target_token = target_token_info["token"]

        translation = None
        if from_words and target_token in from_words:
            translation = from_words[target_token][0]
        elif from_words and target_token[:-1] in from_words:
            translation = from_words[target_token[:-1]][0]

        if translation is None or target_token.strip().lower() == translation.strip().lower():
            if type(word_translation) == list:

                word_translation_ = [option for option in word_translation if
                                     not ((option.strip().lower() in target_token.strip().lower()) or (
                                                 target_token.strip().lower() in option.strip().lower()))]
                if not word_translation_:
                    translation = word_translation[0]
                else:
                    translation = word_translation_[0]
            else:
                translation = word_translation

        target_token_info["translation"] = translation

        target_token_info["translated_phrase"] = translated_phrase

        processed_target_tokens.append(target_token_info)
    return processed_target_tokens
