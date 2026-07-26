#!/usr/bin/env python3
import http.server, json, mimetypes, os, shutil, io, zipfile, urllib.parse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
PORT = 8080
mimetypes.add_type('text/plain', '.atlas')

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path).path
        if p == '/api/skeletons':
            self.send_json(self.list_skeletons())
        elif p == '/api/clear':
            self.clear_uploads()
            self.send_json({'status': 'cleared'})
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == '/upload':
            ctype = self.headers.get('Content-Type', '')
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            if 'multipart/form-data' not in ctype:
                self.send_error(400); return
            boundary = ctype.split('boundary=')[1].strip().strip('"')
            _, data = self.parse_multipart(body, boundary.encode())
            if not data:
                self.send_error(400); return
            self.clear_uploads()
            self.extract_zip(data)
            self.send_json({'status': 'ok', 'skeletons': self.list_skeletons()})
        elif self.path == '/upload-file':
            ctype = self.headers.get('Content-Type', '')
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length)
            if 'multipart/form-data' not in ctype:
                self.send_error(400); return
            boundary = ctype.split('boundary=')[1].strip().strip('"')
            fields = self.parse_multipart_all(body, boundary.encode())
            file_data = fields.get('file')
            rel_path = fields.get('path', b'').decode('utf-8', errors='replace')
            if not file_data or not rel_path:
                self.send_error(400, 'Missing file or path'); return
            dest = os.path.join(UPLOAD_DIR, rel_path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, 'wb') as f: f.write(file_data)
            self.send_json({'status': 'ok', 'path': rel_path})
        else:
            self.send_error(404)

    def clear_uploads(self):
        if not os.path.isdir(UPLOAD_DIR): return
        for n in os.listdir(UPLOAD_DIR):
            p = os.path.join(UPLOAD_DIR, n)
            try: os.remove(p)
            except OSError: shutil.rmtree(p)

    def extract_zip(self, data):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            z.extractall(UPLOAD_DIR)

    def list_skeletons(self):
        skels = []
        for root, _, files in os.walk(UPLOAD_DIR):
            for f in files:
                if not f.endswith('.json'): continue
                full = os.path.join(root, f); d = os.path.dirname(full)
                atlas = next((x for x in os.listdir(d) if x.endswith('.atlas')), None)
                png = next((x for x in os.listdir(d) if x.endswith('.png')), None)
                rel = os.path.relpath(full, UPLOAD_DIR)
                skels.append({
                    'file': rel, 'name': os.path.splitext(f)[0],
                    'dir': os.path.dirname(rel) if os.path.dirname(rel) != '.' else '',
                    'atlas': os.path.relpath(os.path.join(d, atlas), UPLOAD_DIR) if atlas else None,
                    'png': os.path.relpath(os.path.join(d, png), UPLOAD_DIR) if png else None,
                })
        skels.sort(key=lambda x: (x['dir'], x['name']))
        return skels

    def parse_multipart_all(self, body, boundary):
        fields = {}
        for part in body.split(b'\r\n--' + boundary):
            if b'Content-Disposition' not in part: continue
            i = part.find(b'\r\n\r\n')
            if i == -1: continue
            headers = part[:i].decode('utf-8', errors='replace')
            content = part[i+4:]
            if content.endswith(b'\r\n'): content = content[:-2]
            if content.endswith(b'--'): content = content[:-2]
            if 'name="' in headers:
                name = headers.split('name="')[1].split('"')[0]
                fields[name] = content
        return fields

    def parse_multipart(self, body, boundary):
        for part in body.split(b'\r\n--' + boundary):
            if b'Content-Disposition' not in part: continue
            i = part.find(b'\r\n\r\n')
            if i == -1: continue
            c = part[i+4:]
            if c.endswith(b'\r\n'): c = c[:-2]
            if c.endswith(b'--'): c = c[:-2]
            h = part[:i].decode('utf-8', errors='replace')
            if 'filename="' in h:
                return h.split('filename="')[1].split('"')[0], c
        return None, None

    def send_json(self, d):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(d).encode())

    def translate_path(self, path):
        path = path.split('?')[0].split('#')[0]
        return os.path.join(BASE_DIR, path.lstrip('/'))

    def log_message(self, *a): pass

if __name__ == '__main__':
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    s = http.server.HTTPServer(('0.0.0.0', PORT), Handler)
    print(f'http://localhost:{PORT}')
    s.serve_forever()
