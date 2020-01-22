// importing jQuery and bootstrap
// if JQuery is used with this module syntax, it doesn't add itself to window
// but bootstrap expects window.jQuery, so we add it manually
import $ from "jquery";
(<any>window).jQuery = $;
import Popper from 'popper.js';
import "bootstrap";

// in Firefox the Webextension functionality is offered by "browser"
// in Chrome it's called "chrome"
// we use browser and add a polyfill to be cross-platform compatible
import browser from "webextension-polyfill";
import "@babel/polyfill";

// templating
import Mustache from 'mustache';
import * as assets from "./content/assets"

// processing the website
import { PopupManager } from "./content/popup_management"
import { findParagraphs } from "./content/parser"

// sending messages to the python backend
import * as internal_api from "./content/internal_api"

import {default_settings} from "./defaults/settings"
var settings = default_settings


// params
var active = true
var api_connected = false
var paragraph_progress = 0

// main function, the website is processed in here
// the function has to be async to that we can use the await command inside
async function process() {

  // tell the API that we are visiting a new page
  // await external_api.resetAPI();

  // extract text that will be given to our language model
  let paragraphs = findParagraphs();
  paragraphs = paragraphs.slice(paragraph_progress)

  for (let paragraph of paragraphs) {
    if (document.visibilityState == 'hidden') {
      return
    }
    if (!active) {
      return
    }
    if(!api_connected){
      return
    }

    //let paragraph = paragraphs[6]
    let innerText = paragraph.innerText
    let innerHTML = paragraph.innerHTML

    // use python backend to get target tokens, this is done in an async way
    let promise = internal_api.getTargetTokens(innerText, innerHTML)
      .then((payload) => {
        paragraph.innerHTML = payload["new_text"]

        // look for token marks and fill in proper html
        var target_token_infos = payload['target_token_infos'];
        for (let i = 0; i < target_token_infos.length; i++) {
          let target_token_info = target_token_infos[i];
          let mark_html = Mustache.render(assets.mark_html, target_token_info);

          let mark_id = target_token_info["mark_id"]
          $("#" + mark_id).not(".processed").replaceWith(mark_html)
        }

        // set up popup logic for each mark
        let popupManager = new PopupManager(target_token_infos, settings)

        // alternatively, calculate the predictability based on neural prediction
        let tokens: string[] = payload["tokens"];
        let ratios: number[] = payload["ratios"];
        let hits: number[] = payload["hits"];
        let proba_sums: number[] = payload["proba_sum"];

      })
      .catch(error => {
      });

    await promise;
    paragraph_progress++
  }
}

$(async function () {

  // taken from https://stackoverflow.com/questions/11703093/how-to-dismiss-a-twitter-bootstrap-popover-by-clicking-outside
  /*$("html").on("mouseup", function (e) {
    var l = $(e.target);
    if (l[0].className.indexOf("popover") == -1) {
      $(".popover").each(function () {
        $(this).popover("hide");
      });
    }
  });
  /*
  $('body').on('click', function (e) {
    //only buttons
    if ($(e.target).data('toggle') !== 'popover'
      && $(e.target).parents('.popover.in').length === 0) {
      $('[data-toggle="popover"]').popover('hide');
    }
  });*/

  /*$("html").on("mouseup", function (e) {
    if ($(e.target).parents('.popover.in').length === 0) {
      $(".popover").each(function () {
        $(this).popover("hide");
      });
    }
  });*/

  $('body').on('mouseup', function (e) {
    $('[data-toggle=popover]').each(function () {
      // hide any open popovers when the anywhere else in the body is clicked
      if (!$(this).is(e.target) && $(this).has(e.target).length === 0 && $('.popover').has(e.target).length === 0) {
        $(this).popover('hide');
      }
    });
  });

  // query whether broccoli is active
  await browser.storage.local.get("active")
    .then((result) => {
      if (result) {
        active = result.active
      }
    }, (error) => { console.log(error) });
  // listen to updates for active
  browser.storage.onChanged.addListener(function (changes, areaName) {
    if ('active' in changes) {
      active = changes['active'].newValue
      process()
    }
  })

  // query whether broccoli is connected to the python api
  await browser.storage.local.get("api_connected")
    .then((result) => {
      if (result) {
        api_connected = result.api_connected
      }
    }, (error) => { console.log(error) });
  // listen to updates for API connectivity
  browser.storage.onChanged.addListener(function (changes, areaName) {
    if ('api_connected' in changes) {
      api_connected = changes['api_connected'].newValue
      process()
    }
  })

  await browser.storage.local.get("settings")
  .then((result) => {
    console.log('contentscript got settings', result)
    if (result.settings) {
      result = result.settings
      settings = {
        ...settings,
        ...result
      }
      console.log('contentscript working with', settings)
    }
    console.log('after update', settings)
  }, (error) => { console.log(error) });

browser.storage.onChanged.addListener(function (changes, areaName) {
  if ('settings' in changes) {
    settings = {
      ...settings,
      ...changes['settings']
    }
  }
})

  

  // wait for assets loading
  assets.loadAssets().then(function () {
    process();
  }).fail((err) => {
    console.log(err);
  });

  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState == 'visible') {
      process()
    }
  }, false);
});
