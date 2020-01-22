import $ from "jquery";
(<any>window).jQuery=$;

import browser from "webextension-polyfill";

let mark_filename=browser.extension.getURL("content/html_templates/mark.html");
let riddle_content_filename=browser.extension.getURL("content/html_templates/riddle_content.html");
let riddle_title_filename=browser.extension.getURL("content/html_templates/riddle_title.html");
let result_content_filename=browser.extension.getURL("content/html_templates/result_content.html");
let result_title_filename=browser.extension.getURL("content/html_templates/result_title.html");
let review_content_filename=browser.extension.getURL("content/html_templates/review_content.html");
let review_title_filename=browser.extension.getURL("content/html_templates/review_title.html");

export var mark_html:string;
export var riddle_content_html:string;
export var riddle_title_html:string;
export var result_content_html:string;
export var result_title_html:string;
export var review_content_html:string;
export var review_title_html:string;

export function loadAssets(){
    return $.when(
        $.get(mark_filename),
        $.get(riddle_content_filename),
        $.get(riddle_title_filename),
        $.get(result_content_filename),
        $.get(result_title_filename),
        $.get(review_content_filename),
        $.get(review_title_filename),

      ).done((v1, v2, v3, v4, v5, v6, v7)=>{
        
        mark_html = v1[0];
        riddle_content_html = v2[0];
        riddle_title_html = v3[0];
        result_content_html = v4[0];
        result_title_html = v5[0];
        review_content_html = v6[0];
        review_title_html = v7[0];
      
        return true;
    });
}