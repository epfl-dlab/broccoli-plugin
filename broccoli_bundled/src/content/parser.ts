
export function findParagraphs() {
    let paragraphs: HTMLParagraphElement[] = [];
    let main_div = document.querySelector(".mw-parser-output");

    for (let element of main_div.children) {

        // we are only interested in paragraphs
        if (element.tagName.toLowerCase() != "p")
            continue

        // skip elements in a table
        if (element.parentElement.tagName.toLowerCase() == "td")
            continue;

        // skip elements with layout
        if (element.hasAttribute("style"))
            continue;

        let paragraph = <HTMLParagraphElement>element;
        paragraphs.push(paragraph);
        element.setAttribute("class", "to-fill");
    }
    return paragraphs;
}