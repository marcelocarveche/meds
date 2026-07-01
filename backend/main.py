from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from database import db
from drive_sync import drive_sync
from googleapiclient.errors import HttpError
import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Medicine(BaseModel):
    id: str
    name: str
    substance: Optional[str] = None
    dosage: str
    quantity: int
    periods: List[str]
    type: str = "Comprimido"
    price: Optional[float] = 0.0
    requires_prescription: Optional[bool] = False
    source: Optional[str] = "Comprado" # "Comprado" or "SUS"

def sync_up():
    """Background task to sync to Drive"""
    try:
        drive_sync.upload_file()
    except (HttpError, OSError, ValueError, RuntimeError) as e:
        print(f"Sync failed: {e}")

@app.on_event("startup")
async def startup_event():
    print("Startup: Attempting to sync from Drive...")
    try:
        drive_sync.download_file()
        db.load()
    except (HttpError, OSError, ValueError, RuntimeError) as e:
        print(f"Failed to sync from Drive on startup: {e}")

@app.get("/")
def read_root():
    return {"message": "Medicamentos API running", "docs": "/docs"}

@app.get("/medicines", response_model=List[Medicine])
def get_medicines():
    return db.data.get("medicines", [])

@app.post("/medicines")
def add_medicine(medicine: Medicine, background_tasks: BackgroundTasks):
    db.data["medicines"].append(medicine.dict())
    db.save()
    background_tasks.add_task(sync_up)
    return medicine

@app.post("/consume/{period}")
def consume_period(period: str, background_tasks: BackgroundTasks):
    medicines = db.data.get("medicines", [])
    consumed = []
    
    for med in medicines:
        if period in med["periods"]:
            if med["quantity"] > 0:
                med["quantity"] -= 1
                consumed.append(med["name"])
            else:
                print(f"Warning: {med['name']} is out of stock!")

    # Log entry
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "period": period,
        "consumed": consumed
    }
    db.data.setdefault("history", []).append(log_entry)
    
    db.save()
    background_tasks.add_task(sync_up)
    
    return {"status": "success", "consumed": consumed, "remaining_stock": {m["name"]: m["quantity"] for m in medicines if period in m["periods"]}}

@app.put("/medicines/{medicine_id}")
def update_medicine(medicine_id: str, medicine: Medicine, background_tasks: BackgroundTasks):
    for i, med in enumerate(db.data["medicines"]):
        if med["id"] == medicine_id:
            db.data["medicines"][i] = medicine.dict()
            db.save()
            background_tasks.add_task(sync_up)
            return medicine
    raise HTTPException(status_code=404, detail="Medicine not found")

@app.delete("/medicines/{medicine_id}")
def delete_medicine(medicine_id: str, background_tasks: BackgroundTasks):
    initial_len = len(db.data["medicines"])
    db.data["medicines"] = [m for m in db.data["medicines"] if m["id"] != medicine_id]
    
    if len(db.data["medicines"]) < initial_len:
        db.save()
        background_tasks.add_task(sync_up)
        return {"status": "success"}
    
    raise HTTPException(status_code=404, detail="Medicine not found")

@app.get("/sync")
def trigger_sync(background_tasks: BackgroundTasks):
    background_tasks.add_task(sync_up)
    return {"status": "Sync started"}


from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from fastapi.responses import StreamingResponse, HTMLResponse
import io



from reportlab.graphics.shapes import Drawing, Rect, Line

_REPORT_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: 'Inter', sans-serif;
  background: #f0f4f8;
  color: #0f172a;
  padding: 32px;
}

/* ── Toolbar ── */
.toolbar {
  max-width: 1100px;
  margin: 0 auto 20px;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn-action {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border-radius: 12px;
  font-family: 'Inter', sans-serif;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: opacity 0.15s;
}
.btn-action:hover { opacity: 0.85; }
.btn-save  { background: #0f172a; color: #fff; }
.btn-print { background: #fff; color: #0f172a; border: 1px solid #e2e8f0; }

/* ── Report container ── */
.report-container {
  max-width: 1100px;
  margin: 0 auto;
  background: #ffffff;
  border-radius: 28px;
  padding: 40px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 24px rgba(15,23,42,0.06), 0 1px 2px rgba(15,23,42,0.04);
}

/* ── Header ── */
.report-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  gap: 24px;
}

.header-left { display: flex; align-items: center; gap: 20px; }

.avatar {
  width: 68px; height: 68px; border-radius: 22px;
  background: #eef4ff;
  display: flex; align-items: center; justify-content: center;
  font-size: 30px;
}

.header-title h1 { font-size: 1.8rem; font-weight: 700; margin-bottom: 4px; }
.header-title p  { color: #64748b; font-size: 0.9rem; }

.meta-grid {
  margin-left: auto;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px 48px;
  justify-items: end;
  width: max-content;
}
.meta-item { display: flex; flex-direction: column; gap: 4px; text-align: right; }
.meta-item span   { font-size: 0.8rem; color: #94a3b8; font-weight: 500; white-space: nowrap; }
.meta-item strong { font-size: 1rem; font-weight: 600; white-space: nowrap; }

/* ── Summary ── */
.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 28px;
}

.summary-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.summary-card.card-danger { background: #fff5f5; border-color: #fecaca; }
.summary-card.card-ok     { background: #f0fdf4; border-color: #bbf7d0; }

.summary-icon {
  width: 52px; height: 52px; border-radius: 16px;
  background: #edf3ff;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; flex-shrink: 0;
}
.summary-card.card-danger .summary-icon { background: #fee2e2; }
.summary-card.card-ok     .summary-icon { background: #dcfce7; }

.summary-content strong {
  display: block; font-size: 1.9rem; line-height: 1; margin-bottom: 4px;
}
.summary-content span { color: #64748b; font-size: 0.85rem; }
.summary-card.card-danger .summary-content strong { color: #dc2626; }
.summary-card.card-ok     .summary-content strong { color: #16a34a; }

/* ── Table ── */
.table-wrapper {
  overflow: hidden;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
}

table { width: 100%; border-collapse: collapse; }

thead { background: #0f172a; }
thead th {
  text-align: center;
  padding: 16px 20px;
  font-size: 0.78rem;
  color: #94a3b8;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
thead th:first-child { text-align: left; }

tbody tr { transition: background 0.15s; }
tbody tr:hover { background: #fafcff; }
tbody tr.row-danger { background: #fff5f5; }
tbody tr.row-danger:hover { background: #fee2e2; }

tbody td {
  padding: 18px 20px; vertical-align: middle; font-size: 0.95rem;
  border-top: 1px solid #e2e8f0;
  text-align: center;
}
tbody td:first-child { text-align: left; }
tbody tr.row-danger td { border-top-color: #fecaca; }

.medication-text strong { display: block; margin-bottom: 3px; }
.medication-text span   { color: #64748b; font-size: 0.85rem; }

.rx-icon {
  display: inline-block;
  width: 28px; height: 28px;
  vertical-align: middle;
}
.no-rx { color: #cbd5e1; font-size: 0.9rem; }

.danger-value { color: #dc2626; font-weight: 700; font-size: 1rem; }
.muted-value  { color: #94a3b8; }

.status {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 100px; padding: 8px 14px;
  border-radius: 999px; font-size: 0.82rem; font-weight: 700;
  letter-spacing: 0.03em;
}
.status-buy { background: #fef2f2; color: #dc2626; }
.status-ok  { background: #ecfdf5; color: #16a34a; }

@media print {
  body { background: white; padding: 0; }
  .toolbar { display: none; }
  .report-container { box-shadow: none; border: none; border-radius: 0; }
}
"""

@app.get("/report/html", response_class=HTMLResponse)
def generate_html_report():
    medicines_data = db.data.get("medicines", [])
    patient_name = "Joamir Alves"
    patient_cpf = "008.738.531-72"
    birth_date = datetime.date(1931, 12, 8)

    def med_sort_key(med):
        daily_usage = len(med.get('periods', []))
        quantity = med['quantity']
        days_left = quantity // daily_usage if daily_usage > 0 else 999
        return (0 if (quantity == 0 or days_left < 28) else 1, med['name'].lower())

    medicines_data = sorted(medicines_data, key=med_sort_key)

    total_meds = len(medicines_data)
    total_daily = sum(len(m.get('periods', [])) for m in medicines_data)
    buy_count = 0
    ok_count = 0
    rows_html = ""

    for med in medicines_data:
        daily_usage = len(med.get('periods', []))
        quantity = med['quantity']
        days_left = quantity // daily_usage if daily_usage > 0 else 999
        needs_buy = quantity == 0 or days_left < 28
        to_buy = daily_usage * 30

        if needs_buy:
            buy_count += 1
            to_buy_cell = f'<span class="danger-value">{to_buy}</span>'
            status_cell = '<span class="status status-buy">COMPRAR</span>'
            row_class = ' class="row-danger"'
        else:
            ok_count += 1
            to_buy_cell = f'<span class="muted-value">{to_buy}</span>'
            status_cell = '<span class="status status-ok">SUFICIENTE</span>'
            row_class = ''

        substance = med.get('substance') or ''
        substance_html = f'<span>{substance}</span>' if substance and substance.lower() != med['name'].lower() else ''

        if med.get('requires_prescription'):
            rx_cell = '''<svg class="rx-icon" viewBox="0 0 28 28" fill="none" xmlns="http://www.w3.org/2000/svg" title="Receita obrigatória">
              <rect x="3" y="1" width="22" height="26" rx="3.5" fill="#dbeafe" stroke="#3b82f6" stroke-width="1.5"/>
              <rect x="7" y="5" width="14" height="1.5" rx="0.75" fill="#3b82f6"/>
              <rect x="7" y="9" width="14" height="1.5" rx="0.75" fill="#3b82f6"/>
              <rect x="7" y="13" width="9" height="1.5" rx="0.75" fill="#3b82f6"/>
              <path d="M7 18h4.5a3 3 0 0 0 0-6H7v6Z" fill="#3b82f6" opacity="0.25"/>
              <path d="M7 18h4.5a3 3 0 0 0 0-6H7v6Z" stroke="#1d4ed8" stroke-width="1.3" stroke-linejoin="round"/>
              <line x1="7" y1="21" x2="11" y2="18" stroke="#1d4ed8" stroke-width="1.3" stroke-linecap="round"/>
              <line x1="9" y1="18" x2="13" y2="23" stroke="#1d4ed8" stroke-width="1.3" stroke-linecap="round"/>
            </svg>'''
        else:
            rx_cell = '<span class="no-rx">—</span>'

        rows_html += f"""
        <tr{row_class}>
          <td>
            <div class="medication-text">
              <strong>{med['name']}</strong>
              {substance_html}
            </div>
          </td>
          <td>{rx_cell}</td>
          <td>{med['dosage']}</td>
          <td>{daily_usage}x</td>
          <td>{to_buy_cell}</td>
          <td>{status_cell}</td>
        </tr>"""

    today_dt = datetime.datetime.now()
    today = today_dt.strftime('%d/%m/%Y')
    age = today_dt.year - birth_date.year - ((today_dt.month, today_dt.day) < (birth_date.month, birth_date.day))

    content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Relatório de Medicamentos</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"/>
  <style>{_REPORT_CSS}</style>
</head>
<body>

  <div class="toolbar">
    <button class="btn-action btn-print" onclick="window.print()">🖨️ Imprimir</button>
    <button class="btn-action btn-save" onclick="saveAsImage()">💾 Salvar como imagem</button>
  </div>

  <main class="report-container" id="report">

    <header class="report-header">
      <div class="header-left">
        <div class="avatar">💊</div>
        <div class="header-title">
          <h1>Relatório de Medicamentos</h1>
        </div>
      </div>
      <div class="meta-grid">
        <div class="meta-item">
          <span>Paciente</span>
          <strong>{patient_name}</strong>
        </div>
        <div class="meta-item">
          <span>Nascimento</span>
          <strong>08/12/1931 ({age} anos)</strong>
        </div>
        <div class="meta-item">
          <span>CPF</span>
          <strong>{patient_cpf}</strong>
        </div>
        <div class="meta-item">
          <span>Data</span>
          <strong>{today}</strong>
        </div>
      </div>
    </header>

    <section class="summary-grid">
      <article class="summary-card">
        <div class="summary-icon">💊</div>
        <div class="summary-content">
          <strong>{total_meds}</strong>
          <span>Medicamentos</span>
        </div>
      </article>
      <article class="summary-card">
        <div class="summary-icon">📅</div>
        <div class="summary-content">
          <strong>{total_daily}</strong>
          <span>Uso diário total</span>
        </div>
      </article>
      <article class="summary-card card-danger">
        <div class="summary-icon">🛒</div>
        <div class="summary-content">
          <strong>{buy_count}</strong>
          <span>A comprar</span>
        </div>
      </article>
      <article class="summary-card card-ok">
        <div class="summary-icon">✅</div>
        <div class="summary-content">
          <strong>{ok_count}</strong>
          <span>OK</span>
        </div>
      </article>
    </section>

    <section class="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>Medicamento</th>
            <th>Receita</th>
            <th>Dosagem</th>
            <th>Uso diário</th>
            <th>A comprar</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>{rows_html}</tbody>
      </table>
    </section>

  </main>

  <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
  <script>
    async function saveAsImage() {{
      const btn = document.querySelector('.btn-save');
      btn.textContent = '⏳ Gerando...';
      btn.disabled = true;
      try {{
        const el = document.getElementById('report');
        const canvas = await html2canvas(el, {{ scale: 2, useCORS: true, backgroundColor: '#ffffff' }});
        const a = document.createElement('a');
        a.download = 'relatorio_medicamentos.png';
        a.href = canvas.toDataURL('image/png');
        a.click();
      }} finally {{
        btn.textContent = '💾 Salvar como imagem';
        btn.disabled = false;
      }}
    }}
  </script>

</body>
</html>"""

    return HTMLResponse(content=content)


@app.get("/report")
def generate_report():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=48, bottomMargin=48, leftMargin=48, rightMargin=48)
    elements = []

    # Color Palette
    primary_color   = colors.HexColor("#1a1d21")
    header_bg       = colors.HexColor("#1a1d21")
    header_text     = colors.HexColor("#ffffff")
    border_color    = colors.HexColor("#e2e8f0")
    text_muted      = colors.HexColor("#64748b")
    accent_color    = colors.HexColor("#dc2626")  # Red accent

    success_color   = colors.HexColor("#16a34a")
    danger_color    = colors.HexColor("#dc2626")

    danger_bg       = colors.HexColor("#fef2f2")
    zebra_bg        = colors.HexColor("#f8fafc")

    styles = getSampleStyleSheet()

    # Title
    title_style = styles['Heading1']
    title_style.alignment = 0
    title_style.fontName = 'Helvetica-Bold'
    title_style.fontSize = 22
    title_style.textColor = primary_color
    title_style.spaceAfter = 4
    title_style.spaceBefore = 0

    elements.append(Paragraph("Estoque de Medicamentos", title_style))

    # Red accent bar below title
    bar = Drawing(500, 3)
    bar.add(Rect(0, 0, 60, 3, fillColor=accent_color, strokeColor=None))
    elements.append(bar)
    elements.append(Spacer(1, 0.3 * inch))

    # Rx icon for prescription medicines
    def get_rx_icon():
        d = Drawing(12, 14)
        d.add(Rect(0, 0, 10, 12, fillColor=colors.whitesmoke, strokeColor=text_muted, strokeWidth=0.5, rx=1, ry=1))
        d.add(Line(2, 9, 8, 9, strokeColor=text_muted, strokeWidth=0.5))
        d.add(Line(2, 7, 6, 7, strokeColor=text_muted, strokeWidth=0.5))
        d.add(Line(2, 5, 8, 5, strokeColor=text_muted, strokeWidth=0.5))
        return d

    medicines = db.data.get("medicines", [])

    # Pre-compute status and sort: COMPRAR first, then OK — both groups alphabetical
    def med_sort_key(med):
        daily_usage = len(med.get('periods', []))
        quantity = med['quantity']
        days_left = quantity // daily_usage if daily_usage > 0 else 999
        needs_buy = quantity == 0 or days_left < 28
        return (0 if needs_buy else 1, med['name'].lower())

    medicines = sorted(medicines, key=med_sort_key)

    headers = ['MEDICAMENTO', 'DOSAGEM', 'USO DIÁRIO', 'A COMPRAR', 'STATUS']
    data = [headers]
    row_bg_cmds = []

    ok_row_index = 0  # Counter for zebra striping within OK rows

    for i, med in enumerate(medicines, start=1):
        daily_usage = len(med.get('periods', []))
        quantity = med['quantity']
        days_left = quantity // daily_usage if daily_usage > 0 else 999
        to_buy = daily_usage * 30

        needs_buy = quantity == 0 or days_left < 28

        if needs_buy:
            status_text = "COMPRAR"
            status_col  = danger_color
            current_bg  = danger_bg
        else:
            status_text = "SUFICIENTE"
            status_col  = success_color
            ok_row_index += 1
            current_bg  = zebra_bg if ok_row_index % 2 == 0 else None

        if current_bg:
            row_bg_cmds.append(('BACKGROUND', (0, i), (-1, i), current_bg))

        # Medicine name cell
        name_str = f"<b>{med['name']}</b>"
        substance = med.get('substance')
        if substance and substance.lower() != med['name'].lower():
            name_str += f"<br/><font color='#64748b' size='8'>{substance}</font>"
        name_cell = Paragraph(name_str, styles['Normal'])

        if med.get('requires_prescription'):
            icon = get_rx_icon()
            sub_table = Table([[icon, name_cell]], colWidths=[15, 195])
            sub_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('ALIGN', (0,0), (0,0), 'CENTER'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0),
            ]))
            med_name_content = sub_table
        else:
            med_name_content = name_cell

        # Status badge
        status_cell = Paragraph(
            f'<font color="{status_col.hexval()}"><b>{status_text}</b></font>',
            styles['Normal']
        )

        # "A comprar" value: bold red when > 0
        if to_buy > 0:
            buy_cell = Paragraph(f'<font color="{danger_color.hexval()}"><b>{to_buy}</b></font>', styles['Normal'])
        else:
            buy_cell = Paragraph(f'<font color="{text_muted.hexval()}">—</font>', styles['Normal'])

        data.append([
            med_name_content,
            med['dosage'],
            str(daily_usage),
            buy_cell,
            status_cell,
        ])

    # Column widths — total ~6.9 inch to fit A4 with 48pt margins each side
    col_widths = [3.0*inch, 1.0*inch, 0.85*inch, 0.9*inch, 1.15*inch]
    table = Table(data, colWidths=col_widths)

    style_cmds = [
        # Header row
        ('BACKGROUND', (0, 0), (-1, 0), header_bg),
        ('TEXTCOLOR', (0, 0), (-1, 0), header_text),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('LEFTPADDING', (0, 0), (-1, 0), 8),
        ('RIGHTPADDING', (0, 0), (-1, 0), 8),

        # Alignment
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),       # Header: left for medicine col
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),       # Rows: left for medicine col
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

        # Body rows
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TEXTCOLOR', (0, 1), (-1, -1), primary_color),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('LEFTPADDING', (0, 1), (-1, -1), 8),
        ('RIGHTPADDING', (0, 1), (-1, -1), 8),

        # Row dividers
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, border_color),
    ]

    style_cmds.extend(row_bg_cmds)
    table.setStyle(TableStyle(style_cmds))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": "inline; filename=relatorio_medicamentos.pdf"})
