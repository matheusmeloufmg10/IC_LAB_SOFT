import fitz
from typing import Dict, Optional

# Estrutura de layouts de PDF e coordenadas dos campos
PDF_LAYOUTS = {
    "A1_SECURITY": {
        "nome": fitz.Rect(2027.24, 1523, 2179, 1540),
        "codigo": fitz.Rect(2193, 1607, 2230, 1621),
        "material": fitz.Rect(2026.68, 1639, 2160, 1652),
        "espessura": fitz.Rect(2198, 1638, 2228, 1655),
    },
    "A2_SECURITY": {
        "nome": fitz.Rect(1334, 1038, 1530, 1055),
        "codigo": fitz.Rect(1500, 1123, 1540, 1140),
        "material": fitz.Rect(1335, 1154, 1470, 1170),
        "espessura": fitz.Rect(1500, 1155, 1540, 1170),
    },
    "A3_SECURITY": {
        "nome": fitz.Rect(841, 690, 1045, 708),
        "codigo": fitz.Rect(1005, 774, 1048, 792),
        "material": fitz.Rect(840, 805, 1000, 820),
        "espessura": fitz.Rect(1005, 805, 1048, 820),
    },
    "A4_SECURITY": {
        "nome": fitz.Rect(471, 540, 615, 550),
        "codigo": fitz.Rect(760, 560, 795, 570),
        "material": fitz.Rect(620, 540, 720, 550),
        "espessura": fitz.Rect(725, 540, 760, 550),
    },
    # Adicione outros layouts conforme necessário
}

class PDFProcessor:
    def __init__(self, pdf_path: str, pdf_name: str, margin: float = 5.0):
        self.pdf_path = pdf_path
        self.pdf_name = pdf_name
        self.margin = margin
        self.layout = None
        self.page = None
        self.doc = None

    def detect_layout(self) -> Optional[str]:
        """Detecta o layout do PDF com base nas dimensões e textos-chave."""
        self.doc = fitz.open(self.pdf_path)
        self.page = self.doc.load_page(0)
        text = self.page.get_text('text')
        width = self.page.rect.width
        # Lógica simplificada baseada no código original
        if 'S   E   C   U   R   I   T   Y' in text:
            if width > 2000:
                return 'A1_SECURITY'
            elif 1300 < width < 2000:
                return 'A2_SECURITY'
            elif 870 < width < 1200:
                return 'A3_SECURITY'
            elif width < 840:
                return 'A4_SECURITY'
        # Adicione outras regras conforme necessário
        return None

    def extract_field(self, field: str) -> str:
        """Extrai o campo do PDF usando o layout detectado e margem de tolerância."""
        if not self.layout or self.layout not in PDF_LAYOUTS:
            return ''
        rect = PDF_LAYOUTS[self.layout].get(field)
        if not rect:
            return ''
        expanded_rect = fitz.Rect(
            rect.x0 - self.margin, rect.y0 - self.margin,
            rect.x1 + self.margin, rect.y1 + self.margin
        )
        text = self.page.get_text("text", clip=expanded_rect)
        return text.replace('\n', ' ').strip()

    def process(self) -> Dict[str, str]:
        """Processa o PDF e retorna os campos extraídos."""
        self.layout = self.detect_layout()
        if not self.layout:
            return {"erro": "Layout não reconhecido"}
        result = {
            "codigo": self.extract_field("codigo"),
            "nome": self.extract_field("nome"),
            "material": self.extract_field("material"),
            "espessura": self.extract_field("espessura"),
        }
        if self.doc:
            self.doc.close()
        return result 