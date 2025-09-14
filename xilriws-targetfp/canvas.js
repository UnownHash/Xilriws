import * as utils from "./utils.js"
import * as funcToString from "./funcToString.js"

const typeValues = {
    " monospace": 1, " sans-serif": 2, " serif": 3
}

const possibleFonts = ["ArialUnicodeMS", "Calibri", "Century", "Haettenschweiler", "Marlett", "Pristina", "Bauhaus93", "FuturaBkBT", "HelveticaNeue", "LucidaSans", "MYRIADPRO", "SegoeUILight"]

export function block() {
    utils.overwriteProp(CanvasRenderingContext2D.prototype, "isPointInPath", () => false)
    utils.overwriteProp(CanvasRenderingContext2D.prototype, "globalCompositeOperation", "screen")

    function zeroOrOne() {
        return utils.randomNumber(0, 2)
    }

    utils.overwriteProp(CanvasRenderingContext2D.prototype, "measureText", (s) => {
        const metrics = {}
        metrics.width = zeroOrOne()
        metrics.actualBoundingBoxAscent = zeroOrOne()
        metrics.actualBoundingBoxDescent = zeroOrOne()
        metrics.actualBoundingBoxLeft = zeroOrOne()
        metrics.actualBoundingBoxRight = zeroOrOne()
        return metrics
    })

    const goodFonts = utils.randomChooseMultiple(possibleFonts, utils.randomNumber(4, 7))
    console.log("good fonts are " + goodFonts.join(","))

    CanvasRenderingContext2D.prototype.measureText = function (text) {
        let value = -10
        for (const typeValue of Object.keys(typeValues)) {
            if (this.font.includes(typeValue)) {
                value = typeValues[typeValue]
            }
        }

        for (const goodFont of goodFonts) {
            if (this.font.includes(" " + goodFont + ",")) {
                value = -10
            }
        }

        const metrics = {}
        metrics.width = value
        metrics.actualBoundingBoxAscent = value
        metrics.actualBoundingBoxDescent = value
        metrics.actualBoundingBoxLeft = value
        metrics.actualBoundingBoxRight = value
        return metrics
    }
    funcToString.set(CanvasRenderingContext2D.prototype.measureText)

    const originalArc = CanvasRenderingContext2D.prototype.arc
    CanvasRenderingContext2D.prototype.arc = function (n1, n2, n3, zero, pi2, bool) {
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
}