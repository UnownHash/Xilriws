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

export function set(func) {
    fakeSources.set(window.alert, `function ${func.name}() { [native code] }`);
}
