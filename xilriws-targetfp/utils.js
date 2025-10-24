const ws = new WebSocket('ws://127.0.0.1:9091');

let random = null

export function sendWs(action, detail = null) {
    try {
        ws.send(JSON.stringify({action: action, detail: detail}))
    } catch (e) {
    }
}

export function setSeed(newSeed) {
    random = seededRandom(newSeed)
}

function seededRandom(seed) {
    let m = 0x80000000; // 2^31
    let a = 1103515245;
    let c = 12345;
    let state = seed ? seed : Math.floor(Math.random() * (m - 1));

    return function () {
        state = (a * state + c) % m;
        return state / (m - 1);
    };
}

/**
 * @param {Object} object
 * @param {string} propName
 * @param {any} propValue
 */
export function overwriteProp(object, propName, propValue) {
    Object.defineProperty(object, propName, {
        get: () => propValue,
        set: () => {
        },
        configurable: true
    });
}

/**
 * @param {Object} object
 * @param {string} name
 */
export function setName(object, name) {
    Object.defineProperty(object.prototype[name], "name", {
        value: name,
        writable: false,
        configurable: true
    })
}

/**
 * @template T
 * @param {T[]} array
 * @returns {T}
 */
export function randomChoose(array) {
    return array[Math.floor(random() * array.length)]
}

/**
 * Generates a random integer number within the given bounds.
 * @param {number} min - The lower bound (inclusive).
 * @param {number} max - The upper bound (exclusive).
 * @returns {number} A random number between min (inclusive) and max (exclusive).
 */
export function randomNumber(min, max) {
    return Math.floor(random() * (max - min)) + min;
}

/**
 * @template T
 * @param {T[]} arr
 * @param {number} amount
 * @returns {T[]}
 */
export function randomChooseMultiple(arr, amount) {
    const shuffledArray = arr.sort(() => 0.5 - random());
    return shuffledArray.slice(0, amount);
}