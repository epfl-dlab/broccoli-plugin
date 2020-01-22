import $ from "jquery";
(<any>window).jQuery = $;

import "popper.js"
import "bootstrap";
import Mustache from 'mustache';

import * as assets from "./assets"
import * as colors from "./colors"
import * as api from "./internal_api"
import * as config from "./config"

import browser from "webextension-polyfill";

import { default_settings, settingsInterface } from '../defaults/settings'

export class Popover {
    target_token_info: api.ITargetTokenInfo;
    popover_element: HTMLElement;
    visible: boolean;
    time: number;
    settings: settingsInterface

    constructor(target_token_info: api.ITargetTokenInfo, popover_element: HTMLElement, settings:settingsInterface) {
        this.target_token_info = target_token_info
        this.popover_element = popover_element
        this.visible = false
        this.settings = settings
        console.log('popup received params', settings)

        browser.storage.onChanged.addListener((changes, areaName)=>{
            console.log('changes', changes)
            console.log('before update', this.settings)
            if ('settings' in changes) {
                console.log('changes[settings]', changes['settings'])
                this.settings = {
                    ...this.settings,
                    ...changes['settings'].newValue
                }
            }
            console.log('after update', this.settings)
        })


        $(this.popover_element).popover().on("shown.bs.popover", () => {
            if (this.settings.show_riddle) {
                this.setup_riddle()
            }
            else {
                this.setup_review()
            }
        })

        $(popover_element).not(".processed").addClass("processed")

        let timerInterval = window.setInterval(() => {
            let rect = this.popover_element.getBoundingClientRect();
            let viewHeight = Math.max(document.documentElement.clientHeight, window.innerHeight);
            let visible = !(rect.bottom < 0 || rect.top - viewHeight >= 0);

            if (this.visible != visible) {
                // change in visibility, reset timer
                this.time = (new Date()).getTime();
                this.visible = visible;
            }
            else if (visible) {
                let total_time = (new Date()).getTime() - this.time
                // $(this.popover_element).text(total_time)
                if (total_time > config.min_token_exposure) {
                    api.registerExposure(target_token_info, (new Date().getTime()))
                    window.clearInterval(timerInterval)
                }
            }
        }, 500);
    }

    setup_riddle() {

        let riddle_content_html = Mustache.render(assets.riddle_content_html, this.target_token_info)
        let riddle_title_html = Mustache.render(assets.riddle_title_html, this.target_token_info)
        $("#popover-content").html(riddle_content_html);
        $("#popover-title").html(riddle_title_html);

        var num_hints = 0;

        $("#hint_button").click(() => {
            num_hints += 1;
            let hint_text = this.target_token_info["token"].substr(0, num_hints);
            $("#riddle_input_text").val(hint_text)
        });

        $("#guess_button").click(() => {
            let guess = $("#riddle_input_text").val().toString().toLowerCase();
            let token = this.target_token_info["token"].toLowerCase();
            let synonyms: string[] = this.target_token_info["synonyms"].map((s) => s.toLowerCase());

            if (guess == token || synonyms.includes(guess)) {

                api.registerFeedback(this.target_token_info, true, (new Date()).getTime())
                this.setup_result(true);
            } else {
                api.registerFeedback(this.target_token_info, false, (new Date()).getTime())
                this.setup_result(false);
            }
        });

        $("#skip_button").click(() => {
            this.setup_review();
        });
    }

    setup_review() {
        let token_index = $("#popover-content").attr("token_index");
        let token = this.target_token_info["token"].toLowerCase();

        let review_content_html = Mustache.render(assets.review_content_html, this.target_token_info)
        let review_title_html = Mustache.render(assets.review_title_html, this.target_token_info)
        $("#popover-content").html(review_content_html);
        $("#popover-title").html(review_title_html);

        $("#wrong_button").click(() => {
            api.registerFeedback(this.target_token_info, false, (new Date()).getTime())
            $("#wrong_button").prop("disabled", true)
            $("#correct_button").prop("disabled", true)
        });

        $("#correct_button").click(() => {
            api.registerFeedback(this.target_token_info, true, (new Date()).getTime())
            $("#wrong_button").prop("disabled", true)
            $("#correct_button").prop("disabled", true)
        })
    }

    setup_result(correct_answer: boolean) {
        let token_index = $("#popover-content").attr("token_index");
        this.target_token_info["synonyms"] = this.target_token_info["synonyms"].slice(0, 5)

        let result_content_html = Mustache.render(assets.result_content_html, this.target_token_info)
        let result_title_html = Mustache.render(assets.result_title_html, this.target_token_info)
        $("#popover-content").html(result_content_html);
        $("#popover-title").html(result_title_html);

        if (correct_answer) {
            $("#wrong_icon").attr("hidden", "true")
        } else {
            $("#correct_icon").attr("hidden", "true")
        }

        $("#wrong_button").click(() => {
            api.registerFeedback(this.target_token_info, false, (new Date()).getTime())
            $("#wrong_button").prop("disabled", true)
            $("#correct_button").prop("disabled", true)
        });

        $("#correct_button").click(() => {
            api.registerFeedback(this.target_token_info, true, (new Date()).getTime())
            $("#wrong_button").prop("disabled", true)
            $("#correct_button").prop("disabled", true)
        })
    }
}