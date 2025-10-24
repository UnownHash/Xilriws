import * as utils from "./utils.js"

const realToString = Function.prototype.toString;
const realToLocaleString = Function.prototype.toLocaleString;
const fakeSources = new WeakMap();

Function.prototype.toString = function () {
    if (fakeSources.has(this)) {
        return fakeSources.get(this);
    }
    return realToString.call(this);
};

Function.prototype.toLocaleString = function () {
    if (fakeSources.has(this)) {
        return fakeSources.get(this);
    }
    return realToLocaleString.call(this);
};

function getFunctionString(name) {
    return `function ${name}() { [native code] }`
}

export function set(func) {
    fakeSources.set(func, getFunctionString(func.name));
}

utils.setName(Function, "toString")
set(Function.prototype.toString)

utils.setName(Function, "toLocaleString")
set(Function.prototype.toLocaleString)
