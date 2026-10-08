"""Local preview exposing only the single landing and its public assets."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, unquote
import argparse

ROOT=Path(__file__).resolve().parent / "public"

class LandingHandler(SimpleHTTPRequestHandler):
    def public_request(self):
        path=unquote(urlsplit(self.path).path)
        if path not in ('/','/index.html') and not path.startswith('/assets/'):
            return False
        if path.startswith('/assets/'):
            target=(ROOT/path.lstrip('/')).resolve()
            if not target.is_relative_to(ROOT/'assets') or not target.is_file():
                return False
        return True

    def do_GET(self):
        if self.public_request():
            super().do_GET()
        else:
            self.send_error(404)

    def do_HEAD(self):
        if self.public_request():
            super().do_HEAD()
        else:
            self.send_error(404)

    def list_directory(self,path):
        self.send_error(404)
        return None

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8799)
    args=parser.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(LandingHandler,directory=str(ROOT)))
    print(f'Signal workshop: http://127.0.0.1:{args.port}',flush=True)
    server.serve_forever()
