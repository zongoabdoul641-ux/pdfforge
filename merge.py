api/merge.py — Fusionner plusieurs PDFs en un seul.
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
            length = int(self.headers.get("Content-Length", 0))
            body   = json.loads(self.rfile.read(length))
            files  = body.get("files", [])

            if len(files) < 2:
                self._error(400, "Minimum 2 fichiers requis pour fusionner.")
                return

            writer = PdfWriter()
            for f in files:
                file_bytes = base64.b64decode(f["data"])
                reader     = PdfReader(io.BytesIO(file_bytes))
                for page in reader.pages:
                    writer.add_page(page)

            out = io.BytesIO()
            writer.write(out)
            pdf_bytes = out.getvalue()

            result = {
                "success":  True,
                "filename": "fusionné.pdf",
                "size":     len(pdf_bytes),
                "data":     base64.b64encode(pdf_bytes).decode(),
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
