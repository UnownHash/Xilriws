import * as utils from "./utils.js"
import * as funcToString from "./funcToString.js"

const baseLanguages = [
    "en-US",
    "fr",
    "de",
    "es"
]

const extraLanguages = [
    "en-GB",
    "pt-BR",
    "ru",
    "tr",
    "de",
    "fr",
    "es",
    "hr",
    "el",
    "hu",
    "no",
    "ro",
    "sr"
]

const englishes = [
    "en-US",
    "en-GB"
]

const timezones = [
    0, 1, 2, 3, 4, 5, 6, 8, 9, -4, -5, -6, -7
]

export function block() {
    utils.overwriteProp(navigator, "platform", "Win32")
    utils.overwriteProp(navigator, "doNotTrack", utils.randomChoose(["unknown", "unknown", "1"]))
    utils.overwriteProp(navigator, "maxTouchPoints", utils.randomChoose([0, 5, 10, 20]))
    utils.overwriteProp(navigator, "productSub", "20030107")
    utils.overwriteProp(navigator.connection, "rtt", utils.randomChoose([undefined, 0, 50, 100]))
    utils.overwriteProp(navigator, "hardwareConcurrency", utils.randomChoose([4, 8, 12, 16, 24, 32]))

    utils.overwriteProp(window.history, "length", utils.randomNumber(1, 5))

    const timezone = utils.randomChoose(timezones) * -60
    utils.overwriteProp(Date.prototype, "getTimezoneOffset", () => timezone)
    funcToString.set(Date.prototype.getTimezoneOffset)

    utils.overwriteProp(Navigator.prototype, "mimeTypes", {
        0: {
            suffixes: "pdf",
            type: "application/pdf",
            enabledPlugin: { filename: "internal-pdf-viewer" },
        },
        1: {
            suffixes: "pdf",
            type: "text/pdf",
            enabledPlugin: { filename: "internal-pdf-viewer" },
        },
        "application/pdf": {
            suffixes: "pdf",
            type: "application/pdf",
            enabledPlugin: { filename: "internal-pdf-viewer" },
        },
        "text/pdf": {
            suffixes: "pdf",
            type: "text/pdf",
            enabledPlugin: { filename: "internal-pdf-viewer" },
        },

    })

    // language
    const baseLanguage = utils.randomChoose(baseLanguages)
    const languages = [baseLanguage]

    const randomExtraLangs = utils.randomNumber(0, 10)
    if (randomExtraLangs > 3) {
        if (englishes.includes(baseLanguage)) {
            languages.push(utils.randomChoose(extraLanguages))
        } else {
            languages.push(utils.randomChoose(englishes))
        }
    }
    console.log("languages are " + languages.join(","))

    utils.overwriteProp(navigator, "language", baseLanguage)
    utils.overwriteProp(navigator, "languages", languages)
}