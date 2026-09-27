"""Render the editable manuscript Markdown into a review PDF with ReportLab."""
from pathlib import Path
import argparse
import re
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, KeepTogether, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,default=ROOT/'output/pdf/egg-journal-working-draft.pdf')
args=parser.parse_args()
font=Path('/Users/nadan/Documents/ChatGPT/egg/.research-venv/lib/python3.12/site-packages/matplotlib/mpl-data/fonts/ttf')
if font.is_dir():
    for name,file in [('Paper','DejaVuSerif.ttf'),('PaperBold','DejaVuSerif-Bold.ttf'),('PaperItalic','DejaVuSerif-Italic.ttf')]:
        pdfmetrics.registerFont(TTFont(name,str(font/file)))
    pdfmetrics.registerFontFamily('Paper',normal='Paper',bold='PaperBold',italic='PaperItalic',boldItalic='PaperBold')
    body,bold,italic='Paper','PaperBold','PaperItalic'
else:
    body,bold,italic='Times-Roman','Times-Bold','Times-Italic'
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='PaperBody',fontName=body,fontSize=10,leading=14.4,spaceAfter=7,alignment=TA_LEFT,allowWidows=0,allowOrphans=0))
styles.add(ParagraphStyle(name='PaperTitle',fontName=bold,fontSize=19,leading=24,spaceAfter=11))
styles.add(ParagraphStyle(name='PaperSubtitle',fontName=body,fontSize=13,leading=17,spaceAfter=9))
styles.add(ParagraphStyle(name='PaperHeading',fontName=bold,fontSize=12,leading=16,spaceBefore=12,spaceAfter=7,keepWithNext=True))
styles.add(ParagraphStyle(name='PaperCaption',fontName=body,fontSize=8.4,leading=11.4,spaceAfter=10))
styles.add(ParagraphStyle(name='PaperCell',fontName=body,fontSize=8,leading=10.5))
styles.add(ParagraphStyle(name='PaperRef',fontName=body,fontSize=8.4,leading=11.8,spaceAfter=6,wordWrap='CJK'))
styles.add(ParagraphStyle(name='PaperMeta',fontName=italic,fontSize=8.8,leading=12,spaceAfter=12,textColor=colors.HexColor('#53606b')))

def markup(s):
    s=escape(s.replace('>=','≥').replace('<=','≤').replace('Delta','Δ').replace('lambda','λ'))
    for token, replacement in [('F_n','F<sub>n</sub>'),('CH_n','CH<sub>n</sub>'),('r_n','r<sub>n</sub>'),('E^2','E<super>2</super>'),('L^2','L<super>2</super>'),('p_s','p<sub>s</sub>'),('L_D','L<sub>D</sub>'),('U_D','U<sub>D</sub>'),('L_CH','L<sub>CH</sub>'),('U_CH','U<sub>CH</sub>'),('F*','F<super>*</super>'),('x^2','x<super>2</super>'),('e^2','e<super>2</super>'),('l^2','l<super>2</super>'),(')^2',')<super>2</super>')]:
        s=s.replace(token,replacement)
    s=re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',s)
    s=re.sub(r'(https?://[^\s<]+)',r'<link href="\1" color="#156082">\1</link>',s)
    return s

class PageCanvas(canvas.Canvas):
    def __init__(self,*a,**k):
        super().__init__(*a,**k); self.saved=[]
    def showPage(self):
        self.saved.append(dict(self.__dict__)); self._startPage()
    def save(self):
        total=len(self.saved)
        for state in self.saved:
            self.__dict__.update(state)
            self.setStrokeColor(colors.HexColor('#CED4DA')); self.line(48,36,564,36)
            self.setFont('Helvetica',8); self.setFillColor(colors.HexColor('#53606b'))
            self.drawString(48,23,'EGG | Working manuscript | 27 September 2026')
            self.drawRightString(564,23,f'{self._pageNumber} / {total}')
            super().showPage()
        super().save()

lines=(ROOT/'paper/manuscript.md').read_text().splitlines()
story=[]; i=0; references=False; equation_number=0
while i<len(lines):
    s=lines[i].strip()
    if not s: i+=1; continue
    if s.startswith('$$'):
        equation_number+=1
        p=ROOT/'paper/figures'/f'equation_{equation_number:02}.png'
        w,h=ImageReader(str(p)).getSize(); width=min(490,w*72/300); height=width*h/w
        story.extend([Spacer(1,5),Image(str(p),width=width,height=height),Spacer(1,8)])
        i+=1;continue
    if s.startswith('!['):
        path=re.search(r'\]\(([^)]+)\)',s).group(1)
        p=ROOT/'paper'/path; w,h=ImageReader(str(p)).getSize(); width=500; height=width*h/w
        parts=[Image(str(p),width=width,height=height),Spacer(1,5)]
        j=i+1
        while j<len(lines) and not lines[j].strip(): j+=1
        if j<len(lines) and lines[j].startswith('Figure '):
            parts.append(Paragraph(markup(lines[j]),styles['PaperCaption']));i=j
        story.append(KeepTogether(parts));i+=1;continue
    if s.startswith('|'):
        rows=[]
        while i<len(lines) and lines[i].strip().startswith('|'):
            parts=[x.strip() for x in lines[i].strip().strip('|').split('|')]
            if not all(re.fullmatch(r'[:\- ]+',x) for x in parts):
                rows.append([Paragraph(markup(x),styles['PaperCell']) for x in parts])
            i+=1
        widths=[138,138,111,113] if len(rows[0])==4 else [500/len(rows[0])]*len(rows[0])
        t=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EAF0F3')),
            ('LINEABOVE',(0,0),(-1,0),.8,colors.HexColor('#667783')),
            ('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#667783')),
            ('LINEBELOW',(0,-1),(-1,-1),.8,colors.HexColor('#667783')),
            ('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),7),
            ('BOTTOMPADDING',(0,0),(-1,-1),7)]))
        parts=[t,Spacer(1,7)]
        j=i
        while j<len(lines) and not lines[j].strip(): j+=1
        if j<len(lines) and lines[j].startswith('Table '):
            parts.append(Paragraph(markup(lines[j]),styles['PaperCaption']));i=j+1
        story.append(KeepTogether(parts));continue
    if s.startswith('### '):
        title=s[4:]
        if title=='References':
            story.append(PageBreak())
        references=title=='References';style='PaperHeading';s=title
    elif s.startswith('## '):style='PaperSubtitle';s=s[3:]
    elif s.startswith('# '):style='PaperTitle';s=s[2:]
    elif s.startswith('Research draft '):style='PaperMeta'
    elif s.startswith('Figure ') or s.startswith('Table '):style='PaperCaption'
    elif references:style='PaperRef'
    else:style='PaperBody'
    story.append(Paragraph(markup(s),styles[style]));i+=1
out=args.output.resolve()
out.parent.mkdir(parents=True,exist_ok=True)
doc=SimpleDocTemplate(str(out),pagesize=(612,792),rightMargin=56,leftMargin=56,topMargin=45,bottomMargin=51,
 title='When marginal electricity prices cannot coordinate electric-bus schedules',author='EGG Research',
 subject='Working research manuscript; analytical core verified, operational study in preparation')
doc.build(story,canvasmaker=PageCanvas)
print(out)
