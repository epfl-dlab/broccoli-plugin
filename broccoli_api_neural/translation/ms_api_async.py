#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import json
import uuid

import aiohttp
import requests
import ssl
from broccoli_api_neural.utils import EventLimiter
from broccoli_api_neural.config.azure_api_key import key


class MS_Translator_Async():
    def __init__(self, MAX_TRANSLATIONS_PER_SEC=10, MAX_CONCURRENT=10):

        self.limiter = EventLimiter(EVENTS_PER_SEC=MAX_TRANSLATIONS_PER_SEC, POLLS_PER_SEC=10, MAX_QUEUE=2)
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT)

        self.key = key

        """
        # try to load the api key
        key_path = "/home/lhk/data/azure_key.txt"
        try:
            with open(key_path) as file:
                key = file.read()
                self.key = key.strip()

        except:
            raise Exception("couldn't read API key")
        """

        self.ms_url = 'https://api.cognitive.microsofttranslator.com'
        self.default_params = '&includeAlignment=true'

        self.headers = {
            'Ocp-Apim-Subscription-Key': self.key,
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4()),
            #'Ocp-Apim-Subscription-Region': "westeurope"
        }

    async def __api_call(self, session: aiohttp.ClientSession, path, phrase, to_language, from_language: str):
        body = [{
            'text': phrase
        }]
        assert type(to_language) == str
        request_params = self.default_params + "&to=" + to_language

        if from_language is not None:
            assert type(from_language) == str
            request_params = request_params + "&from=" + from_language

        url = self.ms_url + path + request_params

        response = requests.post(url, json=body, headers=self.headers)
        return response.json()

        await self.limiter()

        # async with session.request("post", url, headers=self.headers, json=body) as resp:
        async with aiohttp.request("post", url, headers=self.headers, json=body) as resp:
            return await resp.json()

    async def translate_phrase(self, session: aiohttp.ClientSession, phrase: str, to_language: str,
                               from_language: str = None):

        path = '/translate?api-version=3.0'
        async with self.semaphore:
            response = await self.__api_call(session, path, phrase, to_language, from_language)

        try:
            translations = response[0]["translations"][0]
            translated_phrase = translations["text"]

            from_words = None
            if "alignment" in translations:
                alignment_proj = translations["alignment"]["proj"]
                from_words = self.__map_alignment(phrase, translated_phrase, alignment_proj)
            return translated_phrase, from_words
        except Exception as e:
            return False

    def __map_alignment(self, phrase, translated_phrase, alignment_proj):
        alignments = alignment_proj.split(" ")
        from_words = {}
        for alignment in alignments:
            from_seq, to_seq = alignment.split("-")

            from_start, from_end = from_seq.split(":")
            to_start, to_end = to_seq.split(":")

            from_start, from_end, to_start, to_end = map(int, [from_start, from_end, to_start, to_end])

            if from_end == len(phrase) - 1:
                from_end = -1
            else:
                from_end += 1

            if to_end == len(translated_phrase) - 1:
                to_end = -1
            else:
                to_end += 1

            from_word = phrase[from_start:from_end]
            to_word = translated_phrase[to_start:to_end]

            if from_word in from_words:
                from_words[from_word].append(to_word)
            else:
                from_words[from_word] = [to_word]

        return from_words

    async def translate_word(self, session, word: str, to_language: str, from_language: str = "en"):

        path = '/dictionary/lookup?api-version=3.0'
        async with self.semaphore:
            response = await self.__api_call(session, path, word, to_language, from_language)

        try:
            translations = []
            for translation in response[0]["translations"]:
                translations.append(translation["displayTarget"])

            return translations
        except Exception as e:
            return False


if __name__ == "__main__":
    ms_translator = MS_Translator_Async()


    async def main():
        async with aiohttp.ClientSession() as session:
            translated_phrase, from_words = await ms_translator.translate_phrase(session,
                                                                                 "The racial makeup of the village was 98.71 % White and 1.29 % Native American.",
                                                                                 to_language="it")
            print("translated to: " + translated_phrase)
            print("word mapping: ", from_words)

            response = await ms_translator.translate_word(session, "elephant", to_language="es")
            print(json.dumps(response, sort_keys=True, indent=4, separators=(',', ': ')))


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
