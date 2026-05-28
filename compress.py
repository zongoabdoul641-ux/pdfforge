api/compress.py — Compresser un PDF.
"""

import json
import base64
import io
from http.server import BaseHTTPRequestHandler

from pypdf import PdfReader, PdfWriter


# ─── Vercel handler ──────────────────────────────────────────────────────────

class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        try:
            length   = int(self.headers.get("Content-Length", 0))
            body     = json.loads(self.rfile.read(length))
            file_b64 = body.get("file")
            quality  = body.get("quality", "standard")

            if not file_b64:
                self._error(400, "Aucun fichier reçu.")
                return

            file_bytes = base64.b64decode(file_b64)
            reader     = PdfReader(io.BytesIO(file_bytes))
            writer     = PdfWriter()

            for page in reader.pages:
                if quality == "rapide":
                    page.compress_content_streams()
                writer.add_page(page)

            writer.compress_identical_objects(
                remove_identicals=True,
                remove_orphans=True,
            )

            out = io.BytesIO()
            writer.write(out)
            pdf_bytes = out.getvalue()

            original_size   = len(file_bytes)
            compressed_size = len(pdf_bytes)
            reduction       = (
                round((1 - compressed_size / original_size) * 100, 1)
                if original_size > 0 else 0
            )

            result = {
                "success":          True,
                "filename":         "compressé.pdf",
                "original_size":    original_size,
                "size":             compressed_size,
                "reduction_percent": reduction,
                "data":             base64.b64encode(pdf_bytes).decode(),
            }

            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self._error(500, str(e))

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _error(self, code: int, msg: str):
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"success": False, "error": msg}).encode())

    def log_message(self, *args):
        pass  # Silence logs in Vercel
