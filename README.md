# Xilriws

## Installation

1. `mkdir xilriws && cd xilriws`
2. `wget https://raw.githubusercontent.com/UnownHash/Xilriws/refs/heads/main/docker-compose.yml.example -O docker-compose.yml`
3. `touch proxies.txt` file. Each line should have one proxy url. (i.e. `ip:port` or `http://user:pass@ip:port`)
4. `docker compose pull`, then `docker compose up -d`

in your Dragonite config, add: 

```toml
[general]
remote_auth_url = "http://xilriws:5090/api/v1/login-code"
```

this assumes you have everything in the same docker network. if you're hosting it externally, change the hostname to
something else accordingly.

To update: `docker compose pull && docker compose restart`

## License

Xilriws is licensed under the [GNU Affero General Public License v3.0 only](LICENSE) (`AGPL-3.0-only`).
