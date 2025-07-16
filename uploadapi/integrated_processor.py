import os
from typing import Dict, List
from .pdf_processor import PDFProcessor
from .dxf_processor import DXFProcessor
from collections import defaultdict

def extrair_grupo_do_caminho(caminho: str) -> str:
    # Remove o nome do arquivo e pega a última subpasta
    partes = caminho.replace('\\', '/').split('/')
    if len(partes) > 1:
        return partes[-2]
    return 'raiz'

def processar_lote_pdfs_dxfs(arquivos_extraidos: Dict[str, bytes], margem: float = 5.0) -> Dict[str, List[Dict]]:
    """
    Processa todos os arquivos PDF e DXF extraídos, agrupando por grupo (última subpasta),
    e retorna um dicionário no formato solicitado pelo usuário.
    """
    grupos = defaultdict(list)
    pdfs = [f for f in arquivos_extraidos if f.lower().endswith('.pdf')]
    dxfs = [f for f in arquivos_extraidos if f.lower().endswith('.dxf')]
    dxf_processor = DXFProcessor()

    # Indexar PDFs por nome base e grupo
    pdfs_info = []
    for pdf in pdfs:
        nome_base = os.path.splitext(os.path.basename(pdf))[0]
        grupo = extrair_grupo_do_caminho(pdf)
        pdfs_info.append({"caminho": pdf, "nome_base": nome_base, "grupo": grupo})

    # Indexar DXFs por grupo
    dxfs_por_grupo = defaultdict(list)
    for dxf in dxfs:
        grupo = extrair_grupo_do_caminho(dxf)
        dxfs_por_grupo[grupo].append(dxf)

    # Para cada grupo, montar a estrutura
    for grupo in set([p["grupo"] for p in pdfs_info] + list(dxfs_por_grupo.keys())):
        # PDFs desse grupo
        pdfs_do_grupo = [p for p in pdfs_info if p["grupo"] == grupo]
        dxfs_do_grupo = dxfs_por_grupo.get(grupo, [])

        # Mapear PDFs por nome_base
        pdfs_por_nome_base = {p["nome_base"]: p for p in pdfs_do_grupo}
        # Mapear DXFs por nome_base do PDF correspondente
        sub_pecas = {}
        usados_pdf = set()
        for dxf in dxfs_do_grupo:
            dxf_nome = os.path.splitext(os.path.basename(dxf))[0]
            pdf_correspondente = None
            for nome_base, pdf_info in pdfs_por_nome_base.items():
                if nome_base in dxf_nome:
                    pdf_correspondente = pdf_info
                    break
            if not pdf_correspondente:
                continue  # Só processa DXFs com PDF correspondente
            usados_pdf.add(pdf_correspondente["nome_base"])
            # Processar PDF
            pdf_path = None
            try:
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
                    temp_pdf.write(arquivos_extraidos[pdf_correspondente["caminho"]])
                    pdf_path = temp_pdf.name
                pdf_proc = PDFProcessor(pdf_path, pdf_correspondente["caminho"], margin=margem)
                dados_pdf = pdf_proc.process()
            finally:
                if pdf_path and os.path.exists(pdf_path):
                    try:
                        os.unlink(pdf_path)
                    except Exception:
                        pass
            # Processar DXF
            dxf_bytes = arquivos_extraidos[dxf]
            dxf_result = dxf_processor.process_single_dxf_completo(
                dxf_nome,
                dxf_bytes,
                material=dados_pdf.get('material', ''),
                espessura=dados_pdf.get('espessura', '')
            )
            # Montar resultado consolidado
            resultado = {
                "nome": dados_pdf.get('nome', ''),
                "material": dados_pdf.get('material', ''),
                "espessura": dados_pdf.get('espessura', ''),
                "perimetro_mm": dxf_result.get('perimetro_mm'),
                "tempo_corte_segundos": dxf_result.get('tempo_corte_segundos')
            }
            sub_pecas[pdf_correspondente["nome_base"]] = resultado

        # PDFs sem DXF correspondente
        pdfs_sem_dxf = [p for p in pdfs_do_grupo if p["nome_base"] not in usados_pdf]
        if sub_pecas or pdfs_sem_dxf:
            obj = {}
            # Trocar para PascalCase e nome correto
            obj["PecaPrincipal"] = grupo
            # SubPecas em PascalCase
            subPecas = {}
            for codigo, dados in sub_pecas.items():
                subPecas[codigo] = {
                    "Nome": dados.get("nome", ""),
                    "Material": dados.get("material", ""),
                    "Espessura": dados.get("espessura", ""),
                    "PerimetroMm": dados.get("perimetro_mm"),
                    "TempoCorteSegundos": dados.get("tempo_corte_segundos")
                }
            obj["SubPecas"] = subPecas
            grupos[grupo].append(obj)

    return grupos 