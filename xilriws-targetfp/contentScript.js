(async () => {
    const tabId = await chrome.runtime.sendMessage("getTabId")
    const div = document.createElement("div")
    div.setAttribute("data-xil-tab-id", tabId)

    while (!document.body) {
        console.log("body is null, waiting 0.1s")
        await new Promise(resolve => setTimeout(resolve, 100))
    }
    document.body.appendChild(div)
})()