import ezdxf
import io
import math
import tempfile
import os
from typing import Dict, List, Tuple

class DXFProcessor:
    def __init__(self, target_layer: str = "Corte"):
        self.target_layer = target_layer
        self.cutting_speed_mm_per_second = 50  # Velocidade de corte em mm/s (configurável)
    
    def process_dxf_files(self, arquivos_extraidos: Dict[str, bytes]) -> List[Dict]:
        """
        Processa todos os arquivos DXF encontrados nos arquivos extraídos.
        
        Args:
            arquivos_extraidos: Dicionário com caminho do arquivo como chave e bytes como valor
            
        Returns:
            Lista de dicionários com informações de cada arquivo DXF processado
        """
        resultados = []
        arquivos_dxf_encontrados = []
        
        # Primeiro, identificar todos os arquivos DXF
        for caminho_arquivo in arquivos_extraidos.keys():
            if caminho_arquivo.lower().endswith('.dxf'):
                arquivos_dxf_encontrados.append(caminho_arquivo)
        
        # Processar cada arquivo DXF encontrado
        for caminho_arquivo in arquivos_dxf_encontrados:
            conteudo_bytes = arquivos_extraidos[caminho_arquivo]
            
            # Verificar se o conteúdo é bytes
            if not isinstance(conteudo_bytes, bytes):
                if isinstance(conteudo_bytes, str):
                    conteudo_bytes = conteudo_bytes.encode('utf-8')
                else:
                    resultado_erro = {
                        "arquivo": caminho_arquivo,
                        "perimetro_mm": 0,
                        "tempo_corte_segundos": 0,
                        "layer_utilizada": self.target_layer,
                        "status": f"erro: tipo de conteúdo inválido: {type(conteudo_bytes)}"
                    }
                    resultados.append(resultado_erro)
                    continue
            
            try:
                resultado = self._process_single_dxf(caminho_arquivo, conteudo_bytes)
                if resultado:
                    resultados.append(resultado)
            except Exception as e:
                resultado_erro = {
                    "arquivo": caminho_arquivo,
                    "perimetro_mm": 0,
                    "tempo_corte_segundos": 0,
                    "layer_utilizada": "todas as layers",
                    "status": f"erro: {str(e)}"
                }
                resultados.append(resultado_erro)
                continue
        
        return resultados
    
    def _process_single_dxf(self, caminho_arquivo: str, conteudo_bytes: bytes) -> Dict:
        """
        Processa um único arquivo DXF.
        
        Args:
            caminho_arquivo: Caminho do arquivo DXF
            conteudo_bytes: Conteúdo do arquivo em bytes
            
        Returns:
            Dicionário com informações do arquivo processado
        """
        temp_file_path = None
        try:
            # Verificar se o conteúdo não está vazio
            if len(conteudo_bytes) == 0:
                raise Exception("Arquivo vazio")
            
            # Criar arquivo temporário para o ezdxf
            temp_file_path = tempfile.mktemp(suffix='.dxf')
            with open(temp_file_path, 'wb') as temp_file:
                temp_file.write(conteudo_bytes)
            
            # Verificar se o arquivo foi criado corretamente
            if not os.path.exists(temp_file_path):
                raise Exception("Falha ao criar arquivo temporário")
            
            # Carregar o arquivo DXF usando ezdxf
            doc = ezdxf.readfile(temp_file_path)
            msp = doc.modelspace()
            
            # Calcular perímetro
            perimetro_mm = self._calculate_perimeter(msp)
            
            # Estimar tempo de corte (sem dados de material/espessura por enquanto)
            tempo_corte_segundos = self._estimate_cutting_time(perimetro_mm)
            
            resultado = {
                "arquivo": caminho_arquivo,
                "perimetro_mm": round(perimetro_mm, 2),
                "tempo_corte_segundos": round(tempo_corte_segundos, 2),
                "layer_utilizada": "todas as layers",
                "status": "processado"
            }
            
            return resultado
            
        except Exception as e:
            resultado_erro = {
                "arquivo": caminho_arquivo,
                "perimetro_mm": 0,
                "tempo_corte_segundos": 0,
                "layer_utilizada": "todas as layers",
                "status": f"erro: {str(e)}"
            }
            return resultado_erro
        finally:
            # Limpar arquivo temporário
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass
    
    def _calculate_perimeter(self, modelspace) -> float:
        """
        Calcula o perímetro total de todas as entidades (todas as layers).
        
        Args:
            modelspace: Espaço do modelo do DXF
            
        Returns:
            Perímetro total em milímetros
        """
        perimetro_total = 0.0
        
        # Processar diferentes tipos de entidades
        for entity in modelspace:
            # Calcular comprimento baseado no tipo de entidade (todas as layers)
            comprimento = self._get_entity_length(entity)
            perimetro_total += comprimento
        
        return perimetro_total
    
    def _get_entity_length(self, entity) -> float:
        """
        Calcula o comprimento de uma entidade específica.
        
        Args:
            entity: Entidade do DXF
            
        Returns:
            Comprimento em milímetros
        """
        try:
            entity_type = entity.dxftype()
            
            if entity_type == 'LINE':
                return self._calculate_line_length(entity)
            elif entity_type == 'ARC':
                return self._calculate_arc_length(entity)
            elif entity_type == 'CIRCLE':
                return self._calculate_circle_length(entity)
            elif entity_type == 'LWPOLYLINE':
                return self._calculate_polyline_length(entity)
            elif entity_type == 'POLYLINE':
                return self._calculate_polyline_length(entity)
            else:
                # Para outros tipos de entidade, tentar calcular como linha
                return self._calculate_line_length(entity)
                
        except Exception as e:
            return 0.0
    
    def _calculate_line_length(self, line) -> float:
        """Calcula o comprimento de uma linha."""
        try:
            start_point = line.dxf.start
            end_point = line.dxf.end
            return math.sqrt((end_point[0] - start_point[0])**2 + 
                           (end_point[1] - start_point[1])**2)
        except:
            return 0.0
    
    def _calculate_arc_length(self, arc) -> float:
        """Calcula o comprimento de um arco."""
        try:
            radius = arc.dxf.radius
            start_angle = math.radians(arc.dxf.start_angle)
            end_angle = math.radians(arc.dxf.end_angle)
            
            # Normalizar ângulos
            if end_angle < start_angle:
                end_angle += 2 * math.pi
            
            angle_diff = end_angle - start_angle
            return radius * angle_diff
        except:
            return 0.0
    
    def _calculate_circle_length(self, circle) -> float:
        """Calcula o comprimento de um círculo."""
        try:
            radius = circle.dxf.radius
            return 2 * math.pi * radius
        except:
            return 0.0
    
    def _calculate_polyline_length(self, polyline) -> float:
        """Calcula o comprimento de uma polylinha."""
        try:
            total_length = 0.0
            points = list(polyline.get_points())
            
            for i in range(len(points) - 1):
                p1 = points[i]
                p2 = points[i + 1]
                
                # Extrair coordenadas (pode variar dependendo do tipo de polyline)
                if len(p1) >= 2 and len(p2) >= 2:
                    x1, y1 = p1[0], p1[1]
                    x2, y2 = p2[0], p2[1]
                    
                    segment_length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                    total_length += segment_length
            
            return total_length
        except:
            return 0.0
    
    def _estimate_cutting_time(self, perimetro_mm: float, material: str = None, espessura_mm: float = None) -> float:
        """
        Estima o tempo de corte baseado no perímetro e propriedades do material.
        
        Args:
            perimetro_mm: Perímetro em milímetros
            material: Tipo de material (opcional)
            espessura_mm: Espessura em milímetros (opcional)
            
        Returns:
            Tempo estimado em segundos
        """
        # Fator de correção baseado no material (se fornecido)
        material_factor = self._get_material_factor(material)
        
        # Fator de correção baseado na espessura (se fornecida)
        thickness_factor = self._get_thickness_factor(espessura_mm)
        
        # Cálculo básico: tempo = distância / velocidade
        tempo_base = perimetro_mm / self.cutting_speed_mm_per_second
        
        # Aplicar fatores de correção
        tempo_final = tempo_base * material_factor * thickness_factor
        
        return tempo_final
    
    def _get_material_factor(self, material: str) -> float:
        """Retorna fator de correção baseado no material."""
        if not material:
            return 1.0
        
        material_factors = {
            'aço': 1.0,
            'alumínio': 0.8,
            'cobre': 1.2,
            'latão': 1.1,
            'inox': 1.3,
            'ferro': 1.0
        }
        
        material_lower = material.lower()
        return material_factors.get(material_lower, 1.0)
    
    def _get_thickness_factor(self, espessura_mm: float) -> float:
        """Retorna fator de correção baseado na espessura."""
        if not espessura_mm:
            return 1.0
        
        # Fator baseado na espessura (mais espesso = mais tempo)
        if espessura_mm <= 1.0:
            return 0.8
        elif espessura_mm <= 3.0:
            return 1.0
        elif espessura_mm <= 6.0:
            return 1.3
        elif espessura_mm <= 10.0:
            return 1.6
        else:
            return 2.0 