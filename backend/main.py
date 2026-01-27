from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from database import db
from drive_sync import drive_sync
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
    except Exception as e:
        print(f"Sync failed: {e}")

@app.on_event("startup")
async def startup_event():
    print("Startup: Attempting to sync from Drive...")
    try:
        drive_sync.download_file()
        db.data = db._load() # Reload DB from downloaded file
    except Exception as e:
        print(f"Failed to sync from Drive on startup: {e}")

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
from fastapi.responses import StreamingResponse
import io



from reportlab.graphics.shapes import Drawing, Rect, Line
from reportlab.graphics import renderPDF

@app.get("/report")
def generate_report():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=50, bottomMargin=50)
    elements = []
    
    # Modern Color Palette
    primary_color = colors.HexColor("#25282c") # Dark elegant gray
    header_bg = colors.HexColor("#f8f9fa") # Very light gray
    border_color = colors.HexColor("#e9ecef") # Subtle border
    text_muted = colors.HexColor("#6c757d")
    
    # Status Colors
    success_color = colors.HexColor("#198754")
    warning_color = colors.HexColor("#fd7e14") # Orange
    danger_color = colors.HexColor("#dc3545") # Red

    # Background Colors
    warning_bg = colors.HexColor("#fff3cd") # Light Orange
    danger_bg = colors.HexColor("#f8d7da")  # Light Red
    zebra_bg = colors.HexColor("#f8f9fa")   # Light Gray

    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    title_style.alignment = 1 # Center
    title_style.fontName = 'Helvetica-Bold'
    title_style.fontSize = 24
    title_style.textColor = primary_color
    title_style.spaceAfter = 10
    
    subtitle_style = styles['Normal']
    subtitle_style.alignment = 1
    subtitle_style.textColor = text_muted
    subtitle_style.fontSize = 10

    elements.append(Paragraph("Medicamentos para Fevereiro/2026", title_style))
    elements.append(Paragraph(f"Gerado em: {datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')}", subtitle_style))
    elements.append(Spacer(1, 0.4 * inch))
    
    # Clean Rx Icon
    def get_rx_icon():
        d = Drawing(12, 14)
        # Simplify icon: Just a subtle document shape
        d.add(Rect(0, 0, 10, 12, fillColor=colors.whitesmoke, strokeColor=text_muted, strokeWidth=0.5, rx=1, ry=1))
        # "Rx" text simulation lines
        d.add(Line(2, 9, 8, 9, strokeColor=text_muted, strokeWidth=0.5))
        d.add(Line(2, 7, 6, 7, strokeColor=text_muted, strokeWidth=0.5))
        d.add(Line(2, 5, 8, 5, strokeColor=text_muted, strokeWidth=0.5))
        return d

    # Table Data
    headers = ['MEDICAMENTO', 'DOSAGEM', 'ESTOQUE', 'USO DIÁRIO', 'STATUS']
    data = [headers]
    row_bg_cmds = [] # Store background commands
    
    medicines = db.data.get("medicines", [])
    medicines.sort(key=lambda x: x['name'])
    
    for i, med in enumerate(medicines, start=1):
        daily_usage = len(med.get('periods', []))
        quantity = med['quantity']
        
        days_left = quantity // daily_usage if daily_usage > 0 else 999
        
        status_text = "OK"
        status_col = success_color
        current_bg = None
        
        if quantity == 0:
            status_text = "ESGOTADO"
            status_col = danger_color
            current_bg = danger_bg
        elif days_left < 28:
            status_text = "INSUFICIENTE"
            status_col = warning_color
            current_bg = warning_bg
        else:
            # Alternating gray/white only for OK rows
            if i % 2 == 0:
                current_bg = zebra_bg
                
        if current_bg:
            row_bg_cmds.append(('BACKGROUND', (0, i), (-1, i), current_bg))

        # Medicine Name Construction
        # Main Name Bold, Substance lighter and below
        name_str = f"<b>{med['name']}</b>"
        substance = med.get('substance')
        
        if substance and substance.lower() != med['name'].lower():
            name_str += f"<br/><font color='#6c757d' size='8'>{substance}</font>"
            
        name_cell = Paragraph(name_str, styles['Normal'])
        
        if med.get('requires_prescription'):
            icon = get_rx_icon()
            # Nested table for Icon | Text
            # colWidths adjusted to ensure text has space (Increased to 180)
            sub_table = Table([[icon, name_cell]], colWidths=[15, 180])
            sub_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), # Vertically center icon and text
                ('ALIGN', (0,0), (0,0), 'CENTER'),    # Center icon horizontally in its cell
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0),
            ]))
            med_name_content = sub_table
        else:
            med_name_content = name_cell
            
        # Status Badge
        status_cell = Paragraph(f'<font color="{status_col.hexval()}"><b>{status_text}</b></font>', styles['Normal'])

        data.append([
            med_name_content,
            med['dosage'],
            str(quantity),
            str(daily_usage),
            status_cell
        ])
        
    # Minimalist Table Style
    # Increased first column to 3.0*inch (approx 10% increase)
    col_widths = [3.0*inch, 0.9*inch, 0.8*inch, 0.9*inch, 1.6*inch]
    table = Table(data, colWidths=col_widths)
    
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), header_bg),
        ('TEXTCOLOR', (0, 0), (-1, 0), text_muted),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),             # Default Center
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),                # Left align Meds Column Content ONLY (Row 1 to End)
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TEXTCOLOR', (0, 1), (-1, -1), primary_color),
        
        ('LINEBELOW', (0, 0), (-1, 0), 1, border_color),
        ('TOPPADDING', (0, 1), (-1, -1), 6), # Add breathing room for rows
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]
    
    # Add calculated background colors
    style_cmds.extend(row_bg_cmds)
    
    table.setStyle(TableStyle(style_cmds))
    elements.append(table)
    
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=relatorio_medicamentos.pdf"})
