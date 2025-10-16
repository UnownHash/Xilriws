import * as utils from "./utils.js"
import {randomChoose} from "./utils.js"
import * as funcToString from "./funcToString.js"

const typeValues = {
    " monospace": 1, " sans-serif": 2, " serif": 3
}

const MONOSPACE = "monospace"
const SANS_SERIF = "sans-serif"
const SERIF = "serif"
const BASE_FONTS = [MONOSPACE, SANS_SERIF, SERIF]

const possibleFonts = ["ArialUnicodeMS", "Calibri", "Century", "Haettenschweiler", "Marlett", "Pristina", "Bauhaus93", "FuturaBkBT", "HelveticaNeue", "LucidaSans", "MYRIADPRO", "SegoeUILight"]

export function block() {
    utils.overwriteProp(CanvasRenderingContext2D.prototype, "isPointInPath", () => false)
    funcToString.set(CanvasRenderingContext2D.prototype.isPointInPath)
    utils.overwriteProp(CanvasRenderingContext2D.prototype, "globalCompositeOperation", "screen")

    const goodFonts = utils.randomChooseMultiple(possibleFonts, utils.randomNumber(4, 7))
    console.log("good fonts are " + goodFonts.join(","))

    const baseMeasures = new Map();
    const goodFontMeasures = new Map();
    const originalMeasure = CanvasRenderingContext2D.prototype.measureText
    CanvasRenderingContext2D.prototype.measureText = function (text) {
        function getBaseMeasure(thisThis, thisBaseFont) {
            let baseMeasure = baseMeasures.get(thisBaseFont)
            if (!baseMeasure) {
                baseMeasure = originalMeasure.bind(thisThis, text)()
                baseMeasures.set(thisBaseFont, baseMeasure)
            }
            return baseMeasure
        }

        let baseFont = SANS_SERIF
        for (const possibleBase of BASE_FONTS) {
            if (this.font.includes(possibleBase)) {
                baseFont = possibleBase
                break
            }
        }
        const baseMeasure = getBaseMeasure(this, baseFont)

        let goodFont = ''
        for (const possibleGoodFont of goodFonts) {
            if (this.font.includes(" " + possibleGoodFont + ",")) {
                goodFont = possibleGoodFont
                break
            }
        }

        if (!goodFont) return baseMeasure

        let goodFontMeasure = goodFontMeasures.get(goodFont)
        if (goodFontMeasure) return goodFontMeasure

        const goodFontBase = randomChoose(BASE_FONTS)
        let goodBaseMeasure = JSON.parse(JSON.stringify(getBaseMeasure(this, goodFontBase)))

        const widthDifference = utils.randomNumber(-10, 10)
        goodBaseMeasure.width += widthDifference
        goodBaseMeasure.actualBoundingBoxRight += widthDifference
        goodFontMeasures.set(goodFont, goodBaseMeasure)
        return goodBaseMeasure
    }
    funcToString.set(CanvasRenderingContext2D.prototype.measureText)

    const originalArc = CanvasRenderingContext2D.prototype.arc
    CanvasRenderingContext2D.prototype.arc = function (n1, n2, n3, zero, pi2, bool) {
        console.log("arc")
        n1 += utils.randomNumber(-1, 2)
        n2 += utils.randomNumber(-1, 2)
        n3 += utils.randomNumber(-1, 2)
        return originalArc.bind(this, n1, n2, n3, zero, pi2, bool)()
    }
    funcToString.set(CanvasRenderingContext2D.prototype.arc)

    const originalPutImageData = CanvasRenderingContext2D.prototype.putImageData
    CanvasRenderingContext2D.prototype.putImageData = function (img, x, y, ...args) {
        // this doesn't actually do anything. however, it doesn't appear this canvas differs between different chromiums
        x += utils.randomNumber(-1, 2)
        y += utils.randomNumber(-1, 2)
        return originalPutImageData.bind(this, img, x, y, ...args)()
    }
    funcToString.set(CanvasRenderingContext2D.prototype.putImageData)

    // const originalGetContext = HTMLCanvasElement.prototype.getContext;
    //
    // Override getContext to intercept 2d contexts
    // HTMLCanvasElement.prototype.getContext = function (...args) {
    //     const context = originalGetContext.apply(this, args);
    //
    //     // Only wrap 2d contexts
    //     if (args[0] === '2d' && context) {
    //         return wrapContext(context, this);
    //     }
    //
    //     return context;
    // };
    //
    // function wrapContext(ctx, canvas) {
    //     // Create a proxy to intercept all method calls and property access
    //     return new Proxy(ctx, {
    //         get(target, prop) {
    //             const value = target[prop];
    //
    //             // If it's a function, wrap it with logging
    //             if (typeof value === 'function') {
    //                 return function (...args) {
    //                     // Format arguments for cleaner logging
    //                     const formattedArgs = args.map(arg => {
    //                         if (typeof arg === 'object' && arg !== null) {
    //                             return JSON.stringify(arg);
    //                         }
    //                         return arg;
    //                     });
    //
    //                     // Log the function call with timestamp
    //                     console.log(`%c[Canvas] ${prop}`, 'color: #4CAF50; font-weight: bold',
    //                         formattedArgs.length > 0 ? formattedArgs : '');
    //
    //                     // Call the original function
    //                     return value.apply(target, args);
    //                 };
    //             }
    //
    //             // For properties (getters/setters), log access if desired
    //             // Uncomment below to log property reads
    //             // console.log(`[Canvas] GET ${prop}`);
    //             return value;
    //         },
    //
    //         set(target, prop, value) {
    //             // Log property changes
    //             console.log(`%c[Canvas] ${prop} =`, 'color: #2196F3; font-weight: bold', value);
    //             target[prop] = value;
    //             return true;
    //         }
    //     });
    // }
}