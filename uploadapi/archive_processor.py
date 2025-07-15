import zipfile
import rarfile
import io
from typing import Dict, List

class ArchiveProcessor:
    """
    Processador unificado para arquivos ZIP e RAR.
    Suporta descompactação recursiva de ambos os formatos.
    """
    
    def __init__(self):
        # Configurar rarfile para usar o unrar do sistema
        rarfile.UNRAR_TOOL = "unrar"
    
    def extract_archive_recursive(self, uploaded_file) -> Dict[str, bytes]:
        """
        Descompacta arquivo ZIP ou RAR recursivamente, incluindo arquivos aninhados.
        
        Args:
            uploaded_file: Arquivo enviado via upload
            
        Returns:
            Dicionário com caminho do arquivo como chave e bytes como valor
        """
        arquivos_extraidos = {}
        
        # Ler arquivo em memória
        in_memory = io.BytesIO(uploaded_file.read())
        nome_arquivo = uploaded_file.name.lower()
        
        try:
            if nome_arquivo.endswith('.zip'):
                self._extract_zip_recursive(in_memory, '', arquivos_extraidos)
            elif nome_arquivo.endswith('.rar'):
                self._extract_rar_recursive(in_memory, '', arquivos_extraidos)
            else:
                raise ValueError(f"Formato de arquivo não suportado: {nome_arquivo}")
                
        except Exception as e:
            raise Exception(f"Erro ao descompactar arquivo: {str(e)}")
        
        return arquivos_extraidos
    
    def _extract_zip_recursive(self, zip_bytes: io.BytesIO, parent_path: str, arquivos_extraidos: Dict[str, bytes]):
        """
        Descompacta arquivo ZIP recursivamente.
        
        Args:
            zip_bytes: Bytes do arquivo ZIP
            parent_path: Caminho pai para manter estrutura de pastas
            arquivos_extraidos: Dicionário para armazenar arquivos extraídos
        """
        with zipfile.ZipFile(zip_bytes) as zf:
            for info in zf.infolist():
                full_path = f"{parent_path}{info.filename}"
                
                if info.is_dir():
                    continue
                
                with zf.open(info) as file:
                    file_bytes = file.read()
                    
                    # Verificar se é um arquivo compactado aninhado
                    if info.filename.lower().endswith('.zip'):
                        nested_zip = io.BytesIO(file_bytes)
                        self._extract_zip_recursive(nested_zip, full_path.rsplit('/', 1)[0] + '/', arquivos_extraidos)
                    elif info.filename.lower().endswith('.rar'):
                        nested_rar = io.BytesIO(file_bytes)
                        self._extract_rar_recursive(nested_rar, full_path.rsplit('/', 1)[0] + '/', arquivos_extraidos)
                    else:
                        arquivos_extraidos[full_path] = file_bytes
    
    def _extract_rar_recursive(self, rar_bytes: io.BytesIO, parent_path: str, arquivos_extraidos: Dict[str, bytes]):
        """
        Descompacta arquivo RAR recursivamente.
        
        Args:
            rar_bytes: Bytes do arquivo RAR
            parent_path: Caminho pai para manter estrutura de pastas
            arquivos_extraidos: Dicionário para armazenar arquivos extraídos
        """
        try:
            with rarfile.RarFile(rar_bytes) as rf:
                for info in rf.infolist():
                    full_path = f"{parent_path}{info.filename}"
                    
                    if info.is_dir():
                        continue
                    
                    with rf.open(info) as file:
                        file_bytes = file.read()
                        
                        # Verificar se é um arquivo compactado aninhado
                        if info.filename.lower().endswith('.zip'):
                            nested_zip = io.BytesIO(file_bytes)
                            self._extract_zip_recursive(nested_zip, full_path.rsplit('/', 1)[0] + '/', arquivos_extraidos)
                        elif info.filename.lower().endswith('.rar'):
                            nested_rar = io.BytesIO(file_bytes)
                            self._extract_rar_recursive(nested_rar, full_path.rsplit('/', 1)[0] + '/', arquivos_extraidos)
                        else:
                            arquivos_extraidos[full_path] = file_bytes
                            
        except rarfile.BadRarFile:
            raise Exception("Arquivo RAR inválido ou corrompido")
        except Exception as e:
            raise Exception(f"Erro ao processar arquivo RAR: {str(e)}")
    
    def get_supported_formats(self) -> List[str]:
        """
        Retorna lista de formatos suportados.
        
        Returns:
            Lista de extensões suportadas
        """
        return ['.zip', '.rar']
    
    def validate_file_format(self, filename: str) -> bool:
        """
        Valida se o formato do arquivo é suportado.
        
        Args:
            filename: Nome do arquivo
            
        Returns:
            True se o formato é suportado, False caso contrário
        """
        return filename.lower().endswith(tuple(self.get_supported_formats())) 