const ws = new WebSocket('ws://127.0.0.1:9091');

let currentProxyCreds = {
    "username": null,
    "password": null
}

const blockedAccessScripts = [
    "login-util.js",
    "screen-name-script.js",
    "set-state-script.js",
]
const blockedJoinScripts = [
    "main.*.js.map",
    "*.chunk.js",
]
const blockedFiles = ["woff", "ttf", "css", "png", "jpg", "jpeg", "svg", "ico", "json"]


const BLOCK_URLS = [
    "*://gstatic.com/*",
    "*://fonts.googleapis.com/*",
    "*://optimizationguide-pa.googleapis.com/*",
    "*://*.launchdarkly.com/*",
    "*://*.browser-intake-datadoghq.com/*",
    "*://join.pokemon.com/manifest.json",
]

blockedAccessScripts.forEach(name => BLOCK_URLS.push("*://access.pokemon.com/scripts/" + name))
blockedJoinScripts.forEach(name => BLOCK_URLS.push("*://join.pokemon.com/static/js/" + name))
blockedFiles.forEach(name => BLOCK_URLS.push("*://*/*." + name + "*"))

chrome.webRequest.onBeforeRequest.addListener(
    () => { return {cancel: true} },
    {urls: BLOCK_URLS},
    ["blocking"]
)

ws.onmessage = (event) => {
    console.log('Message from server: ', event.data);
    const message = JSON.parse(event.data)
    const action = message.action
    const data = message.data

    if (action === 'setProxy') {
        currentProxyCreds = {
            username: data.username,
            password: data.password
        }
        startProxy(data.host, data.port, data.scheme)
    }
}

function sendWs(action, detail = null) {
    ws.send(JSON.stringify({action: action, detail: detail}))
}

function startProxy(host, port, scheme) {
    const proxyConfig = {
        mode: 'fixed_servers',
        rules: {
            singleProxy: {
                scheme: scheme,
                host: host,
                port: port,
            },
            bypassList: [],
        },
    };
    chrome.proxy.settings.set(
        {value: proxyConfig},
        () => {
            sendWs('finish:setProxy', host + ':' + port)
        },
    )
}

chrome.webRequest.onAuthRequired.addListener(
    () => {
        return {
            authCredentials: currentProxyCreds
        }
    },
    {urls: ["<all_urls>"]},
    ["blocking"],
)

chrome.tabs.onUpdated.addListener((tabId, details) => {
    if (!details.url) {
        return
    }

    chrome.tabs.executeScript(
        tabId,
        {code: 'localStorage.clear()', runAt: 'document_start'},
        (result) => {
            console.log('Cleared local storage')
        }
    )
})

chrome.tabs.onRemoved.addListener(
    (tabId) => {
        chrome.cookies.getAll({}, cookies => {
                console.log('Deleting ' + cookies.length + ' cookies')
                let goal = cookies.length

                function deleteCallback(details) {
                    console.log(details)
                    goal -= 1

                    if (goal <= 0) {
                        console.log('Deleted all cookies')
                        sendWs('finish:cookiePurge', null)
                    }
                }

                cookies.forEach(cookie => {
                    let domain = cookie.domain
                    if (domain.startsWith('.')) {
                        domain = domain.substring(1, domain.length)
                    }
                    const protocol = cookie.secure ? 'https' : 'http'
                    console.log(`${protocol}://${domain}${cookie.path}`)

                    chrome.cookies.remove({
                        name: cookie.name,
                        url: `${protocol}://${domain}${cookie.path}`,
                        storeId: cookie.storeId
                    }, deleteCallback)
                })
            }
        )
    }
)
