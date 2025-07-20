# Ollama CORS Proxy Server

A lightweight HTTP proxy server that enables browser-based applications and extensions to communicate with Ollama by solving CORS (Cross-Origin Resource Sharing) issues.

## Why is this needed?

Browser applications and extensions are subject to strict security policies that prevent them from making direct requests to local services like Ollama. This proxy server adds the necessary CORS headers to allow web applications to communicate with your local Ollama instance.

## Quick Start

### Option 1: Direct Python (Recommended for development)

1. **Prerequisites**: Python 3.6+ (no additional packages required)

2. **Clone and run**:
   ```bash
   git clone https://github.com/vinesh178/ollama-proxy-server.git
   cd ollama-proxy-server
   python3 simple_ollama_proxy.py
   ```

3. **Access**: Proxy runs on `http://localhost:8000` and forwards to Ollama at `http://localhost:11434`

### Option 2: Docker (Recommended for production)

1. **Using Docker Compose**:
   ```bash
   git clone https://github.com/vinesh178/ollama-proxy-server.git
   cd ollama-proxy-server
   docker-compose up -d
   ```

2. **Using Docker directly**:
   ```bash
   docker build -t ollama-proxy .
   docker run -p 8000:8000 ollama-proxy
   ```

## Configuration

The proxy can be configured using environment variables:

- `PROXY_PORT`: Port for the proxy server (default: `8000`)
- `OLLAMA_URL`: URL of your Ollama instance (default: `http://localhost:11434`)

### Examples:

**Custom port**:
```bash
PROXY_PORT=9000 python3 simple_ollama_proxy.py
```

**Remote Ollama instance**:
```bash
OLLAMA_URL=http://192.168.1.100:11434 python3 simple_ollama_proxy.py
```

**Docker with custom configuration**:
```bash
docker run -p 9000:9000 -e PROXY_PORT=9000 -e OLLAMA_URL=http://host.docker.internal:11434 ollama-proxy
```

**Docker Compose**: Edit the `docker-compose.yml` file to customize ports and environment variables as needed.

## Usage

Once running, your web applications can make requests to the proxy instead of directly to Ollama:

**Instead of**: `http://localhost:11434/api/generate`  
**Use**: `http://localhost:8000/api/generate`

The proxy supports all Ollama API endpoints and maintains the same request/response format.

## Verification

Test that everything is working:

1. **Check Ollama is running**:
   ```bash
   ollama list
   ```

2. **Test proxy connectivity**:
   Visit `http://localhost:8000/api/tags` in your browser

3. **Test from JavaScript**:
   ```javascript
   fetch('http://localhost:8000/api/generate', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({
       model: 'llama2',
       prompt: 'Hello, world!'
     })
   }).then(response => response.json())
     .then(data => console.log(data));
   ```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Failed to connect to Ollama" | Ensure Ollama is running: `ollama list` |
| Proxy won't start | Check if port 8000 is already in use |
| CORS errors persist | Verify you're using the proxy URL (`localhost:8000`) not Ollama directly (`localhost:11434`) |
| Docker connectivity issues | For Docker Desktop: Use `host.docker.internal` in `OLLAMA_URL` |

## Security Considerations

- This proxy opens your Ollama instance to browser-based access
- Only run this on trusted networks
- Consider firewall rules if running in production
- The proxy adds permissive CORS headers (`Access-Control-Allow-Origin: *`)

## How it works

```
Browser App → Proxy Server (localhost:8000) → Ollama (localhost:11434)
           ←                                 ←
           + CORS headers added
```

The proxy:
1. Receives requests from browser applications
2. Forwards them to your Ollama instance
3. Adds CORS headers to the response
4. Returns the response to the browser

For streaming endpoints like `/api/generate`, the proxy collects the full response before returning it to ensure compatibility with browser applications that may not handle streaming responses well.

## Contributing

Issues and pull requests welcome! This is a simple tool designed to solve a specific problem - keeping it lightweight and dependency-free is a priority. 