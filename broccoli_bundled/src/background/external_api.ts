import axios from "axios"
import browser from "webextension-polyfill";


// sends data to python backend
export function register(messages: {}[]) {

  let url = "http://localhost:5000/register";
  let headers = {
    "Content-Type": "application/json; charset=utf-8"
  }
  return axios({
    url: url,
    method: "post",
    headers: headers,
    data: messages
  }).catch((error)=>{
    browser.storage.local.set({
      api_connected : false
    })
  })
}

// resets the backend
export function reset() {

  let url = "http://localhost:5000/reset_api";
  let headers = {
    "Content-Type": "application/json; charset=utf-8"
  }
  return axios({
    url: url,
    method: "get",
    headers: headers
  })
}


// using api to get target_token_infos
export function getTargetTokens(message) {

  let url = "http://localhost:5000/get_target_tokens";
  let headers = {
    "Content-Type": "application/json; charset=utf-8"
  }

  return axios({
    url: url,
    method: "post",
    headers: headers,
    data: message
  }).then(response => {

      let payload = response.data;
      return payload;
  }).catch((error)=>{
    browser.storage.local.set({
      api_connected : false
    })
  })
}