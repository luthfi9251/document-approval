import base64
import mimetypes
from odoo import http
from odoo.http import request
import os

class FileDownloadController(http.Controller):

    @http.route('/download/file', type='http', auth='public')
    def download_file(self, **kwargs):
        # Path file yang akan dikirimkan kepada pengguna
        record_id = kwargs.get('id')
        # file_path = '/etc/file-storage/documents/mahasiswa_0b256e03-e568-4d87-84e5-a327429906c5 (1).pdf.pdf'  # Ganti dengan path file yang sesuai

        record = http.request.env['xf.doc.approval.document'].sudo().browse(int(record_id))
        if record:
            file_path = record.file_path
        else:
            file_path = '/null'

        if os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                file_data = file.read()
            file_name = os.path.basename(file_path)

            file_content = file_data
            
            # Menyiapkan response HTTP
            http_headers = [('Content-Type', 'application/octet-stream'), ('Content-Disposition', f'attachment; filename="{file_name}"')]
            
            return request.make_response(file_content, headers=http_headers)
        else:
            return "File not found"
