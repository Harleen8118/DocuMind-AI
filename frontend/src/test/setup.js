import '@testing-library/jest-dom';

// Polyfill scrollIntoView for jsdom
Element.prototype.scrollIntoView = function () {};

// Polyfill HTMLMediaElement for jsdom
window.HTMLMediaElement.prototype.play = function () {
  return Promise.resolve();
};
window.HTMLMediaElement.prototype.pause = function () {};
window.HTMLMediaElement.prototype.load = function () {};
