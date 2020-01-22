// see: https://stackoverflow.com/questions/54736468/using-fontawesome-in-firefox-webextension-contentscript/54738057#54738057

/* raf-ff-fix.js */
window.requestAnimationFrame = window.requestAnimationFrame.bind(window)