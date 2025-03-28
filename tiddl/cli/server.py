from functools import cached_property
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import click
import json
import logging
from tiddl.utils import TidalResource
from tiddl.cli.auth import refresh
from tiddl.cli.ctx import Context, passContext
from tiddl.cli.download import DownloadCommand
from concurrent.futures import ThreadPoolExecutor


@click.command()
@passContext
@click.option('--port', default=48150, help='Port to listen, default to 48150', type=int)
@click.option('--address', default='0.0.0.0', help='Address to listen, default to 0.0.0.0')
def serve(ctx: Context, address: str, port: int):
    def download_resources(resources: list[TidalResource]):
        ctx.obj.resources = resources

        # refresh the token for long live running server to avoid error with expired token
        ctx.invoke(refresh)
        ctx.obj.initApi()
        ctx.invoke(DownloadCommand)

    download_thread_pool = ThreadPoolExecutor(max_workers=1)

    class HttpHandler(BaseHTTPRequestHandler):

        @cached_property
        def url(self):
            return urlparse(self.path)

        @cached_property
        def query_data(self):
            return dict(parse_qs(self.url.query))

        def do_GET(self) -> None:
            url = self.url
            if url.path == '/fetch':
                errors = []
                data = self.query_data
                resources_to_fetch = []
                if 'url' in data:
                    for url in data['url']:
                        try:
                            parsed = TidalResource.fromString(url)
                            resources_to_fetch.append(parsed)
                        except ValueError as e:
                            errors.append(e)
                    if resources_to_fetch:
                        print(resources_to_fetch)
                        download_thread_pool.submit(download_resources, resources_to_fetch)

                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps(errors).encode('utf-8'))
            else:
                self.send_response(404)
                self.end_headers()

    logging.info(f"start server at http://{address}:{port}")
    http_server = HTTPServer((address, port), HttpHandler)
    http_server.serve_forever()

    download_thread_pool.shutdown(wait=True, cancel_futures=True)

