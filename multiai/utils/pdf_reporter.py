# multiai/utils/pdf_reporter.py
import json
import hashlib
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, List

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import qrcode

from ..core.ledger_sign import ledger_signer

class PDFReporter:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(name='Title2', parent=self.styles['Heading1'], fontSize=16, spaceAfter=30, textColor=colors.darkblue))
        self.styles.add(ParagraphStyle(name='Header2', parent=self.styles['Heading2'], fontSize=12, spaceAfter=12, textColor=colors.darkblue))

    def _events_table(self, events: List[Dict[str, Any]]):
        headers = ['Timestamp', 'Event Type', 'Action', 'User', 'Status']
        data = [headers]
        for e in events[:10]:
            data.append([str(e.get('timestamp',''))[:19], e.get('event_type',''), e.get('action',''), e.get('user_id','System'), e.get('status','')])
        if len(events) > 10:
            data.append(['...', f"+{len(events)-10} more", '', '', ''])
        t = Table(data, colWidths=[90, 100, 120, 80, 60])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('FONTSIZE', (0,0), (-1,-1), 8)
        ]))
        return t

    def generate(self, export_id: str, audit_data: Dict[str, Any]) -> BytesIO:
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4)
        story = []
        story.append(Paragraph(f"AUDIT REPORT - {export_id}", self.styles['Title2']))
        story.append(Spacer(1, 10))

        meta = [
            ['Report ID', export_id],
            ['Generated', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Event Count', str(audit_data.get('event_count', 0))]
        ]
        meta_tbl = Table(meta, colWidths=[200, 300])
        meta_tbl.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.black)]))
        story.append(meta_tbl)
        story.append(Spacer(1, 16))

        story.append(Paragraph("Events Summary", self.styles['Header2']))
        if audit_data.get('events'):
            story.append(self._events_table(audit_data['events']))
            story.append(Spacer(1, 16))

        # QR + signer
        qr_data = f"MULTIAI Audit Report\nID: {export_id}\nDate: {datetime.now().isoformat()}"
        qr_img = qrcode.make(qr_data)
        qr_buf = BytesIO()
        qr_img.save(qr_buf, format='PNG'); qr_buf.seek(0)
        story.append(Image(qr_buf, width=80, height=80))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"Key Fingerprint: {ledger_signer.get_public_key_fingerprint()}", self.styles['Normal']))

        doc.build(story)

        # Create detached signature info
        buf.seek(0)
        pdf = buf.getvalue()
        sig_payload = json.dumps({
            "export_id": export_id,
            "timestamp": datetime.now().isoformat(),
            "content_hash": hashlib.sha256(pdf).hexdigest()
        }, sort_keys=True)
        signature = ledger_signer.sign_data(sig_payload)
        sig_info = {
            "pdf_hash": hashlib.sha256(pdf).hexdigest(),
            "signature": signature,
            "public_key_fingerprint": ledger_signer.get_public_key_fingerprint()
        }
        with open(f"exports/{export_id}_signature.json", "w", encoding="utf-8") as f:
            json.dump(sig_info, f, indent=2)
        buf.seek(0)
        return buf

pdf_reporter = PDFReporter()
