#!/usr/bin/env bash
set -euo pipefail

# Simple Mock OpenCode Server for Testing
# Uses Python's built-in HTTP server for better reliability

MOCK_PORT="${1:-4096}"
MOCK_DIR="/tmp/simple_mock_$$"
MOCK_PID_FILE="/tmp/simple_mock_$$.pid"

# Create temporary directory for server files
mkdir -p "$MOCK_DIR"

# Create Python HTTP server script
cat > "$MOCK_DIR/mock_server.py" << 'EOF'
#!/usr/bin/env python3
import http.server
import socketserver
import json
import urllib.parse
import time
import sys
from datetime import datetime

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 4096

# Global session storage
sessions = {}
messages = {}

class MockHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Log to stderr with timestamp
        sys.stderr.write(f"[{datetime.now().isoformat()}] {format % args}\n")

    def do_GET(self):
        path = urllib.parse.urlparse(self.path)

        if path.path == '/doc':
            self.send_json(200, {
                "openapi": "3.0.0",
                "info": {"title": "Mock OpenCode API", "version": "1.0.0"},
                "status": "healthy"
            })
        elif path.path == '/config/providers':
            self.send_json(200, {
                "providers": [{
                    "id": "mock",
                    "name": "Mock Provider",
                    "models": [{"id": "mock-model", "name": "Mock Model"}]
                }]
            })
        elif path.path.startswith('/session/') and path.path.endswith('/message'):
            # Get messages for session
            session_id = path.path.split('/')[2]
            if session_id in sessions:
                session_messages = messages.get(session_id, [])
                self.send_json(200, session_messages)
            else:
                self.send_json(404, {"error": "Session not found"})
        elif path.path.startswith('/session/'):
            # Validate session
            session_id = path.path.split('/')[2]
            if session_id in sessions:
                self.send_json(200, {"status": "ok"})
            else:
                self.send_json(404, {"error": "Session not found"})
        else:
            self.send_json(404, {"error": "Endpoint not found"})

    def do_POST(self):
        path = urllib.parse.urlparse(self.path)

        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'

        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            data = {}

        if path.path == '/session':
            # Create new session
            session_id = f"sess_mock_{int(time.time())}_{id(self)}"
            sessions[session_id] = {"created": datetime.now().isoformat()}
            messages[session_id] = []
            self.send_json(200, {"id": session_id})
        elif path.path.startswith('/session/') and path.path.endswith('/message'):
            # Send message to session
            session_id = path.path.split('/')[2]

            if session_id not in sessions:
                self.send_json(404, {"error": "Session not found"})
                return

            # Check for directory parameter
            query_params = urllib.parse.parse_qs(path.query)
            if 'directory' not in query_params:
                self.send_json(400, {"error": "Missing directory parameter"})
                return

            # Extract message text
            message_text = ""
            if 'parts' in data:
                for part in data['parts']:
                    if part.get('type') == 'text':
                        message_text = part.get('text', '')
                        break

            # Generate response
            response_text = "test successful"
            if "respond with just:" in message_text:
                # Extract requested response
                try:
                    response_text = message_text.split("respond with just:")[1].strip()
                except:
                    response_text = "test successful"

            # Store messages
            timestamp = datetime.now().isoformat()
            user_msg = {
                "id": f"msg_user_{int(time.time())}",
                "info": {"role": "user"},
                "parts": data.get('parts', []),
                "timestamp": timestamp
            }
            assistant_msg = {
                "id": f"msg_assistant_{int(time.time())}",
                "info": {"role": "assistant"},
                "parts": [{"type": "text", "text": response_text}],
                "timestamp": timestamp
            }

            if session_id not in messages:
                messages[session_id] = []
            messages[session_id].extend([user_msg, assistant_msg])

            # Return immediate response
            self.send_json(200, {"parts": [{"type": "text", "text": response_text}]})
        else:
            self.send_json(404, {"error": "Endpoint not found"})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def send_json(self, status_code, data):
        response = json.dumps(data, separators=(',', ':'))
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), MockHandler) as httpd:
        print(f"Mock server running on port {PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
            httpd.shutdown()
EOF

start_simple_mock() {
    local port="$1"

    echo "[simple-mock] Starting Python-based mock server on port $port"

    # Start server in background
    cd "$MOCK_DIR"
    nix-shell -p python3 --run "python3 mock_server.py $port" > "/tmp/simple_mock_$$.log" 2>&1 &
    local pid=$!
    echo "$pid" > "$MOCK_PID_FILE"

    # Wait for server to be ready
    echo "[simple-mock] Waiting for server to be ready..."
    local attempts=0
    while [[ $attempts -lt 20 ]]; do
        if curl -s --max-time 2 "http://127.0.0.1:$port/doc" >/dev/null 2>&1; then
            echo "[simple-mock] Server ready on port $port (PID: $pid)"
            return 0
        fi
        sleep 0.5
        ((attempts++))
    done

    echo "[simple-mock] ERROR: Server failed to start within timeout"
    stop_simple_mock
    return 1
}

stop_simple_mock() {
    if [[ -f "$MOCK_PID_FILE" ]]; then
        local pid=$(cat "$MOCK_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo "[simple-mock] Stopping server (PID: $pid)"
            kill "$pid" 2>/dev/null

            # Wait for process to stop
            local attempts=0
            while [[ $attempts -lt 10 ]] && kill -0 "$pid" 2>/dev/null; do
                sleep 0.5
                ((attempts++))
            done

            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid" 2>/dev/null
            fi
        fi
        rm -f "$MOCK_PID_FILE"
    fi

    # Cleanup
    rm -rf "$MOCK_DIR" 2>/dev/null || true
    echo "[simple-mock] Server stopped and cleaned up"
}

test_simple_mock() {
    local port="$1"
    local base_url="http://127.0.0.1:$port"

    echo "[simple-mock] Testing endpoints at $base_url"

    # Test /doc
    if curl -s --max-time 5 "$base_url/doc" | grep -q "healthy"; then
        echo "[simple-mock] ✅ /doc endpoint working"
    else
        echo "[simple-mock] ❌ /doc endpoint failed"
        return 1
    fi

    # Test /config/providers
    if curl -s --max-time 5 "$base_url/config/providers" | grep -q "providers"; then
        echo "[simple-mock] ✅ /config/providers endpoint working"
    else
        echo "[simple-mock] ❌ /config/providers endpoint failed"
        return 1
    fi

    # Test session creation and messaging
    local session_resp
    session_resp=$(curl -s --max-time 5 -X POST "$base_url/session" -H "Content-Type: application/json" -d '{}')
    local session_id
    session_id=$(echo "$session_resp" | grep -o '"id": *"[^"]*"' | sed 's/"id": *"\([^"]*\)"/\1/')

    if [[ -n "$session_id" ]]; then
        echo "[simple-mock] ✅ Session creation working (ID: $session_id)"

        # Test message sending
        local msg_resp
        msg_resp=$(curl -s --max-time 5 -X POST "$base_url/session/$session_id/message?directory=/tmp" \
            -H "Content-Type: application/json" \
            -d '{"parts": [{"type": "text", "text": "respond with just: test successful"}]}')

        if echo "$msg_resp" | grep -q "test successful"; then
            echo "[simple-mock] ✅ Message sending working"
        else
            echo "[simple-mock] ❌ Message sending failed"
            echo "[simple-mock] Response: $msg_resp"
            return 1
        fi
    else
        echo "[simple-mock] ❌ Session creation failed"
        echo "[simple-mock] Response: $session_resp"
        return 1
    fi

    echo "[simple-mock] All tests passed!"
    return 0
}

case "${1:-start}" in
    "start")
        start_simple_mock "${2:-$MOCK_PORT}"
        ;;
    "stop")
        stop_simple_mock
        ;;
    "test")
        test_simple_mock "${2:-$MOCK_PORT}"
        ;;
    *)
        start_simple_mock "$1"
        ;;
esac