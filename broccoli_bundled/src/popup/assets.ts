import $ from "jquery";
(<any>window).jQuery=$;

import browser from "webextension-polyfill";

let firebase_ui_container_filename=browser.extension.getURL("popup/html_templates/firebase_ui_container.html");

export var firebase_ui_container_html:string;

export function loadAssets(){
    return Promise.all([$.get(firebase_ui_container_filename)]).then((res)=>{
        firebase_ui_container_html = res[0];
        return true;
    })
}