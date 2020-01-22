import browser from "webextension-polyfill";

export interface ITargetTokenInfo {
  token: string,
  lemma: string,
  translation: string,
  sentence: string,
  synonyms: string[],
  proba: number
}
export function getTargetTokens(innerText: string, innerHTML: string) {
  let message = {
    'paragraph': {
      'innerText': innerText,
      'innerHTML': innerHTML
    }
  }

  return browser.runtime.sendMessage(message)
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
export function registerExposure(targetTokenInfo: ITargetTokenInfo, timestamp: number) {
  let message = {
    "exposure": true,
    "targetTokenInfo": targetTokenInfo,
    "timestamp": timestamp
  };

  browser.runtime.sendMessage(message)
}