import axios from "axios"
import browser from "webextension-polyfill";

export interface ITargetTokenInfo {
  token: string,
  lemma: string,
  translation: string,
  sentence: string,
  synonyms: string[],
  proba: number,
  token_id: string,
  mark_id: string
}

// use this on every new page
export function resetAPI() {
  let url = "http://localhost:5000/reset_api";
  return axios.get(url);
}

// using api to get target_token_infos
export function getTargetTokens(innerText: string, innerHTML:string, threshold: any, targetLanguage: any, translationFilter: any, onePerSentence: any, modelSelected: any) {

  let url = "http://localhost:5000/get_target_tokens";
  let headers = {
    "Content-Type": "application/json; charset=utf-8"
  }
  let dataObject = {
    'innerText': innerText,
    'innerHTML': innerHTML,
    'threshold': threshold,
    'targetLanguage': targetLanguage,
    'translationFilter': translationFilter,
    'onePerSentence': onePerSentence,
    'modelSelected': modelSelected
  };

  return axios({
    url: url,
    method: "post",
    headers: headers,
    data: dataObject
  })
    .then(response => {

      let payload = response.data;
      return payload;
    });
}

// sending user feedback on token to API
export function registerFeedback(targetTokenInfo: ITargetTokenInfo, correct: boolean, timestamp: number) {

  let message = {
    "feedback": true,
    'targetTokenInfo': targetTokenInfo,
    'correct': correct,
    "timestamp": timestamp
  };

  browser.runtime.sendMessage(message)
}

// sending info on user exposure to token to API
export function registerExposure(targetTokenInfo: ITargetTokenInfo, timestamp: number){
  let message = {
    "exposure": true,
    "targetTokenInfo": targetTokenInfo,
    "timestamp": timestamp
  };

  browser.runtime.sendMessage(message)
}