(async () => {
    "use strict"

    const utils = await import("./utils.js")
    const screen = await import("./screen.js")
    const general = await import("./general.js")
    const canvas = await import("./canvas.js")
    const webgl = await import("./webgl.js")

    let div = null
    while (!div) {
        div = document.querySelector("[data-xil-tab-id]")
        if (!div) {
            console.log("didn't find seed element, waiting 0.3s")
            await new Promise(resolve => setTimeout(resolve, 300))
        }
    }
    const seed = div.getAttribute("data-xil-tab-id")
    document.body.removeChild(div)
    utils.setSeed(seed)

    utils.sendWs("debug:seed", seed)

    screen.block()
    general.block()
    canvas.block()
    webgl.block()

    document.fpLoaded = true
})()

HTMLIFrameElement.prototype.addEventListener = async function (eventType, callback) {
    if (eventType !== "load") {
        return
    }

    let fpLoaded = false
    while (!fpLoaded) {
        console.log("waiting for plugin load")
        await new Promise(resolve => setTimeout(resolve, 200))
        if (this.contentDocument) {
            fpLoaded = this.contentDocument.fpLoaded
        }
    }
    callback()
}
