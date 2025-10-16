import re

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
)


IMPERVA_ERROR_CODES = {
    "3": "There was an error in processing the request",
    "4": "The request could not be fully read",
    "5": "There was an error in processing the server response",
    "8": "The proxy failed to connect to the web server, due to TCP connection rejection (TCP Reset)",
    "9": "Error code 9",
    "12": "Captcha",
    "14": "This request was blocked by our security service",
    "15": "General bot protection",
    "16": "IP is permanently blocked",
    "17": "IP is rate-limited",
    "18": "Requests to the web site you are trying to access cannot be served (The site was probably removed from the service because it is in violation of our terms of service or if it is under a DDoS attack and site service plan does not cover DDoS mitigation)",
    "20": "The proxy failed to connect to the web server, due to TCP connection timeout",
    "22": "The proxy failed to resolve site from host name, if this site was recently added please allow a few minutes before trying again",
    "23": "The proxy failed to resolve site from host name - duplicate sites with same host name exist. To resolve this issue, complete the DNS changes as instructed",
    "24": "The proxy failed to resolve site from host name - CNAME is invalid. To resolve this issue, complete the DNS changes as instructed",
    "26": "The proxy failed to connect to the web server, SSL connection failed",
    "29": "SSL is not supported",
    "30": "The proxy failed to connect to the web server, no web server IP is defined",
    "31": "Port not supported",
    "32": "The proxy failed to connect to the web server",
    "33": "Timeout reading request POST/PUT body",
    "35": "The certificate on the web server is not valid.",
    "36": "This site does not have an IPV6 address, please use IPV4 instead",
    "37": "The site is using an origin server which is reserved for another account.",
    "38": "The domain was blacklisted as it violates Imperva terms of use.",
    "39": "The domain is pointing to the wrong DNS records.",
    "40": "The SSL certificate on the origin server was issued to a different domain.",
    "41": "The site is not currently configured to support non-SNI connections.",
    "42": "The client did not provide a client certificate, and the site requires one in all connections.",
    "43": "Too many connections are open simultaneously between the Imperva proxy and the origin server.",
    "44": "The proxy failed to connect to the web server. Detected loop in CDN."
}


def get_imperva_error_code(text: str) -> tuple[str, str]:
    code_match = re.search(r"edet=(\d*)&", text)
    if code_match and code_match.group(1):
        code = code_match.group(1)
        error = IMPERVA_ERROR_CODES.get(code, "Unknown reason")
    else:
        code = "?"
        error = "unknown reason"

    return code, error
