
from kazhttp import HTTP_OK, HTTP_NOT_FOUND, run
import json

get_handlers = {}

def get(path):
    def decorator(f):
        get_handlers[path] = f
        return f
    return decorator

@get('/')
def index():
    with open('output/devices.json', 'r') as f:
        content = f.read()


    data = json.loads(content)

    qrcode = "<script src='/static/qrcode.min.js'></script><script>qrcode('data').makeCode(JSON.stringify(data))</script>"
    return """<style>
    .tri-container {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
    }
    </style><div class="tri-container"><textarea id="data" style="width: 30%; height: 100%;">"""+ content + f"""</textarea>
    <form>
    
    </form>
    <div>
    python vpn_setup.py \\
		--subnet {data['subnet']} \\
		--server-ip {data['server-ip']} \\
		--ssh-remote {data['remote']} \\
		--server server \\
		--local bigmac \\
		--clients phone
    
    {qrcode}
    </div>
    </div>
    """

@get('/static/qrcode.min.js')
def handle_request(request):
    method = request['method']
    path = request['path']
    headers = request['headers']
    body = request['body']

    if method == 'GET':
        if path in get_handlers:
            content = get_handlers[path]()
            return HTTP_OK(content.encode(), mimetype=b"text/html")
        
    return HTTP_NOT_FOUND(b"path not found", mimetype=b"text/plain")

def main():
    run(host='', port=9123, handle_request=handle_request)

if __name__ == '__main__':
    main()