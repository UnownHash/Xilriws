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
    utils.setName(CanvasRenderingContext2D, "isPointInPath")
    funcToString.set(CanvasRenderingContext2D.prototype.isPointInPath)

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
    utils.setName(CanvasRenderingContext2D, "measureText")
    funcToString.set(CanvasRenderingContext2D.prototype.measureText)

    // const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData
    // CanvasRenderingContext2D.prototype.getImageData = function (sx, sy, sw, sh, settings) {
    //     // console.log(`getImageData ${sx} ${sy} ${sw} ${sh} ${settings.toString()}`)
    //
    //     return originalGetImageData.bind(this, sx, sy, sw, sh, settings)()
    // }
    // utils.setName(CanvasRenderingContext2D, "getImageData")
    // funcToString.set(CanvasRenderingContext2D.prototype.getImageData)

    // const originalToDataUrl = HTMLCanvasElement.prototype.toDataURL
    // const randomScale = utils.randomNumber(85, 99) * 0.01
    // HTMLCanvasElement.prototype.toDataURL = function (type, quality) {
    //     console.log(this.width)
    //     const result = originalToDataUrl.bind(this, type, quality)()
    //     console.log(result)
    //     return result
    //
    //     // blur
    //     // const ctx = this.getContext('2d');
    //     // ctx.filter = 'blur(1px)';
    //     // ctx.drawImage(this, 0, 0);
    //     // ctx.filter = 'none';
    //     // const blurResult = originalToDataUrl.bind(this, type, quality)()
    //     // console.log(blurResult)
    //     // return blurResult
    //
    //     // scale
    //     try {
    //         const ctx = this.getContext('2d');
    //         if (!ctx) return result
    //
    //         const tempCanvas = document.createElement('canvas');
    //         tempCanvas.width = this.width * randomScale;
    //         tempCanvas.height = this.height * randomScale;
    //         const tempCtx = tempCanvas.getContext('2d');
    //         console.log("made tempctx")
    //
    //         tempCtx.drawImage(this, 0, 0, tempCanvas.width, tempCanvas.height);
    //         console.log("drew image")
    //
    //         // tempCanvas.width = this.width
    //         // tempCanvas.height = this.height
    //         // const scaleResult = originalToDataUrl.bind(tempCanvas, type, quality)()
    //         // console.log(scaleResult)
    //         // return scaleResult
    //         //
    //         ctx.clearRect(0, 0, this.width, this.height);
    //         ctx.drawImage(tempCanvas, 0, 0, this.width, this.height);
    //         console.log("drew more image")
    //         const scaleResult = originalToDataUrl.bind(this, type, quality)()
    //         console.log(scaleResult)
    //         return scaleResult
    //     } catch(e) {
    //         console.error(e)
    //     }
    //
    //
    // }
    // utils.setName(HTMLCanvasElement, "toDataURL")
    // funcToString.set(HTMLCanvasElement.prototype.toDataURL)

    // HTMLCanvasElement.prototype.toDataURL = new Proxy(
    //     function toDataURL(type, quality) {
    //         console.log(this.width)
    //         const result = originalToDataUrl.bind(this, type, quality)()
    //         console.log(result)
    //         return result
    //
    //         // blur
    //         // const ctx = this.getContext('2d');
    //         // ctx.filter = 'blur(1px)';
    //         // ctx.drawImage(this, 0, 0);
    //         // ctx.filter = 'none';
    //         // const blurResult = originalToDataUrl.bind(this, type, quality)()
    //         // console.log(blurResult)
    //         // return blurResult
    //
    //         // scale
    //         try {
    //             const ctx = this.getContext('2d');
    //             if (!ctx) return result
    //
    //             const tempCanvas = document.createElement('canvas');
    //             tempCanvas.width = this.width * randomScale;
    //             tempCanvas.height = this.height * randomScale;
    //             const tempCtx = tempCanvas.getContext('2d');
    //             console.log("made tempctx")
    //
    //             tempCtx.drawImage(this, 0, 0, tempCanvas.width, tempCanvas.height);
    //             console.log("drew image")
    //
    //             // tempCanvas.width = this.width
    //             // tempCanvas.height = this.height
    //             // const scaleResult = originalToDataUrl.bind(tempCanvas, type, quality)()
    //             // console.log(scaleResult)
    //             // return scaleResult
    //             //
    //             ctx.clearRect(0, 0, this.width, this.height);
    //             ctx.drawImage(tempCanvas, 0, 0, this.width, this.height);
    //             console.log("drew more image")
    //             const scaleResult = originalToDataUrl.bind(this, type, quality)()
    //             console.log(scaleResult)
    //             return scaleResult
    //         } catch (e) {
    //             console.error(e)
    //             return result
    //         }
    //
    //
    //     },
    //     {
    //         get(target, prop) {
    //             if (prop === Symbol.toStringTag) {
    //                 return 'Function';
    //             }
    //             if (prop === 'toString' || prop === 'toLocaleString') {
    //                 return () => "test native code";
    //             }
    //             return target[prop];
    //         },
    //         apply(target, thisArg, args) {
    //             return target.apply(thisArg, args);
    //         }
    //     }
    // );
    // utils.setName(HTMLCanvasElement, "toDataURL")

    // the below 2 blocks seem to be detectable. but might be required

    // const originalFillText = CanvasRenderingContext2D.prototype.fillText
    // CanvasRenderingContext2D.prototype.fillText = function (text, x, y, maxWidth) {
    //     console.log(`fillText ${text} ${x} ${y} ${maxWidth} / ${this.font}`)
    //     this.font = this.font.replace("Arial", "serif")
    //     // this.fillStyle = "#069"
    //     // text = text.replaceAll("w", "m")
    //     // text = text.replaceAll("m", "w")
    //
    //     return originalFillText.bind(this, text, x, y, maxWidth)()
    // }
    // utils.setName(CanvasRenderingContext2D, "fillText")
    // funcToString.set(CanvasRenderingContext2D.prototype.fillText)
    //
    // const originalArc = CanvasRenderingContext2D.prototype.arc
    // const arcNumber1 = utils.randomNumber(-1, 2)
    // const arcNumber2 = utils.randomNumber(-1, 2)
    // const arcNumber3 = utils.randomNumber(-1, 2)
    // CanvasRenderingContext2D.prototype.arc = function (n1, n2, n3, zero, pi2, bool) {
    //     console.log("arc")
    //     n1 += arcNumber1
    //     // n2 += arcNumber2
    //     // n3 += arcNumber3
    //     return originalArc.bind(this, n1, n2, n3, zero, pi2, bool)()
    // }
    // utils.setName(CanvasRenderingContext2D, "arc")
    // funcToString.set(CanvasRenderingContext2D.prototype.arc)
    //
    // const originalPutImageData = CanvasRenderingContext2D.prototype.putImageData
    // CanvasRenderingContext2D.prototype.putImageData = function (img, x, y, ...args) {
    //     // this doesn't actually do anything. however, it doesn't appear this canvas differs between different chromiums
    //     x += utils.randomNumber(-1, 2)
    //     y += utils.randomNumber(-1, 2)
    //     return originalPutImageData.bind(this, img, x, y, ...args)()
    // }
    // utils.setName(CanvasRenderingContext2D, "putImageData")
    // funcToString.set(CanvasRenderingContext2D.prototype.putImageData)
}