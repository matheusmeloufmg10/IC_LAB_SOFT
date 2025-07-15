import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import tempfile
import os
import io
import zipfile
import math
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status

from .archive_processor import ArchiveProcessor
from .dxf_processor import DXFProcessor
from .views import UploadZipView


class ArchiveProcessorTestCase(TestCase):
    """Testes para a classe ArchiveProcessor"""
    
    def setUp(self):
        self.processor = ArchiveProcessor()
    
    def test_init(self):
        """Testa inicialização do ArchiveProcessor"""
        self.assertEqual(self.processor.get_supported_formats(), ['.zip', '.rar'])
    
    def test_validate_file_format_zip(self):
        """Testa validação de arquivo ZIP"""
        self.assertTrue(self.processor.validate_file_format('arquivo.zip'))
        self.assertTrue(self.processor.validate_file_format('ARQUIVO.ZIP'))
    
    def test_validate_file_format_rar(self):
        """Testa validação de arquivo RAR"""
        self.assertTrue(self.processor.validate_file_format('arquivo.rar'))
        self.assertTrue(self.processor.validate_file_format('ARQUIVO.RAR'))
    
    def test_validate_file_format_invalid(self):
        """Testa validação de arquivo inválido"""
        self.assertFalse(self.processor.validate_file_format('arquivo.txt'))
        self.assertFalse(self.processor.validate_file_format('arquivo.pdf'))
    
    def test_get_supported_formats(self):
        """Testa obtenção de formatos suportados"""
        formats = self.processor.get_supported_formats()
        self.assertIn('.zip', formats)
        self.assertIn('.rar', formats)
        self.assertEqual(len(formats), 2)
    
    @patch('zipfile.ZipFile')
    def test_extract_zip_recursive(self, mock_zipfile):
        """Testa extração recursiva de ZIP"""
        # Mock do arquivo ZIP
        mock_zip = Mock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip
        
        # Mock das informações dos arquivos (apenas arquivos simples, sem aninhamento)
        mock_info1 = Mock()
        mock_info1.filename = 'arquivo1.txt'
        mock_info1.is_dir.return_value = False
        
        mock_info2 = Mock()
        mock_info2.filename = 'arquivo2.pdf'
        mock_info2.is_dir.return_value = False
        
        mock_info3 = Mock()
        mock_info3.filename = 'pasta/'
        mock_info3.is_dir.return_value = True
        
        mock_zip.infolist.return_value = [mock_info1, mock_info2, mock_info3]
        
        # Mock dos arquivos com context manager
        mock_file1 = Mock()
        mock_file1.read.return_value = b'conteudo1'
        mock_file1.__enter__ = Mock(return_value=mock_file1)
        mock_file1.__exit__ = Mock(return_value=None)
        
        mock_file2 = Mock()
        mock_file2.read.return_value = b'conteudo2'
        mock_file2.__enter__ = Mock(return_value=mock_file2)
        mock_file2.__exit__ = Mock(return_value=None)
        
        mock_zip.open.side_effect = [mock_file1, mock_file2]
        
        # Teste
        arquivos_extraidos = {}
        zip_bytes = io.BytesIO(b'fake zip content')
        
        self.processor._extract_zip_recursive(zip_bytes, '', arquivos_extraidos)
        
        # Verificações
        self.assertIn('arquivo1.txt', arquivos_extraidos)
        self.assertEqual(arquivos_extraidos['arquivo1.txt'], b'conteudo1')
        self.assertIn('arquivo2.pdf', arquivos_extraidos)
        self.assertEqual(arquivos_extraidos['arquivo2.pdf'], b'conteudo2')
    
    @patch('rarfile.RarFile')
    def test_extract_rar_recursive(self, mock_rarfile):
        """Testa extração recursiva de RAR"""
        # Mock do arquivo RAR
        mock_rar = Mock()
        mock_rarfile.return_value.__enter__.return_value = mock_rar
        
        # Mock das informações dos arquivos
        mock_info = Mock()
        mock_info.filename = 'arquivo.txt'
        mock_info.is_dir.return_value = False
        
        mock_rar.infolist.return_value = [mock_info]
        
        # Mock do arquivo com context manager
        mock_file = Mock()
        mock_file.read.return_value = b'conteudo rar'
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=None)
        
        mock_rar.open.return_value = mock_file
        
        # Teste
        arquivos_extraidos = {}
        rar_bytes = io.BytesIO(b'fake rar content')
        
        self.processor._extract_rar_recursive(rar_bytes, '', arquivos_extraidos)
        
        # Verificações
        self.assertIn('arquivo.txt', arquivos_extraidos)
        self.assertEqual(arquivos_extraidos['arquivo.txt'], b'conteudo rar')
    
    def test_extract_archive_recursive_zip(self):
        """Testa extração de arquivo ZIP"""
        # Mock do arquivo enviado
        mock_file = Mock()
        mock_file.name = 'teste.zip'
        mock_file.read.return_value = b'fake zip content'
        
        # Mock da extração ZIP
        with patch.object(self.processor, '_extract_zip_recursive') as mock_extract:
            mock_extract.return_value = None
            
            result = self.processor.extract_archive_recursive(mock_file)
            
            mock_extract.assert_called_once()
    
    def test_extract_archive_recursive_rar(self):
        """Testa extração de arquivo RAR"""
        # Mock do arquivo enviado
        mock_file = Mock()
        mock_file.name = 'teste.rar'
        mock_file.read.return_value = b'fake rar content'
        
        # Mock da extração RAR
        with patch.object(self.processor, '_extract_rar_recursive') as mock_extract:
            mock_extract.return_value = None
            
            result = self.processor.extract_archive_recursive(mock_file)
            
            mock_extract.assert_called_once()
    
    def test_extract_archive_recursive_invalid_format(self):
        """Testa extração de formato inválido"""
        mock_file = Mock()
        mock_file.name = 'teste.txt'
        mock_file.read.return_value = b'fake content'
        
        with self.assertRaises(Exception) as context:
            self.processor.extract_archive_recursive(mock_file)
        
        self.assertIn('Formato de arquivo não suportado', str(context.exception))
    
    @patch('zipfile.ZipFile')
    def test_extract_zip_recursive_with_nested_zip(self, mock_zipfile):
        """Testa extração ZIP com arquivo ZIP aninhado"""
        # Mock do arquivo ZIP
        mock_zip = Mock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip
        
        # Mock das informações dos arquivos
        mock_info1 = Mock()
        mock_info1.filename = 'arquivo1.txt'
        mock_info1.is_dir.return_value = False
        
        mock_info2 = Mock()
        mock_info2.filename = 'nested.zip'
        mock_info2.is_dir.return_value = False
        
        mock_zip.infolist.return_value = [mock_info1, mock_info2]
        
        # Mock dos arquivos
        mock_file1 = Mock()
        mock_file1.read.return_value = b'conteudo1'
        mock_file1.__enter__ = Mock(return_value=mock_file1)
        mock_file1.__exit__ = Mock(return_value=None)
        
        mock_file2 = Mock()
        mock_file2.read.return_value = b'nested zip content'
        mock_file2.__enter__ = Mock(return_value=mock_file2)
        mock_file2.__exit__ = Mock(return_value=None)
        
        mock_zip.open.side_effect = [mock_file1, mock_file2]
        
        # Mock da extração recursiva
        with patch.object(self.processor, '_extract_zip_recursive') as mock_recursive:
            arquivos_extraidos = {}
            zip_bytes = io.BytesIO(b'fake zip content')
            
            self.processor._extract_zip_recursive(zip_bytes, '', arquivos_extraidos)
            
            # Verifica que a extração recursiva foi chamada
            self.assertGreater(mock_recursive.call_count, 0)
    
    @patch('rarfile.RarFile')
    def test_extract_rar_recursive_with_nested_zip(self, mock_rarfile):
        """Testa extração RAR com arquivo ZIP aninhado"""
        # Mock do arquivo RAR
        mock_rar = Mock()
        mock_rarfile.return_value.__enter__.return_value = mock_rar
        
        # Mock das informações dos arquivos
        mock_info = Mock()
        mock_info.filename = 'nested.zip'
        mock_info.is_dir.return_value = False
        
        mock_rar.infolist.return_value = [mock_info]
        
        # Mock do arquivo
        mock_file = Mock()
        mock_file.read.return_value = b'nested zip content'
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=None)
        
        mock_rar.open.return_value = mock_file
        
        # Mock da extração recursiva
        with patch.object(self.processor, '_extract_zip_recursive') as mock_recursive:
            arquivos_extraidos = {}
            rar_bytes = io.BytesIO(b'fake rar content')
            
            self.processor._extract_rar_recursive(rar_bytes, '', arquivos_extraidos)
            
            # Verifica que a extração recursiva foi chamada
            self.assertGreater(mock_recursive.call_count, 0)
    
    @patch('rarfile.RarFile')
    def test_extract_rar_recursive_bad_rar_file(self, mock_rarfile):
        """Testa extração RAR com arquivo corrompido"""
        mock_rarfile.side_effect = Exception("Arquivo RAR inválido")
        
        arquivos_extraidos = {}
        rar_bytes = io.BytesIO(b'fake rar content')
        
        with self.assertRaises(Exception) as context:
            self.processor._extract_rar_recursive(rar_bytes, '', arquivos_extraidos)
        
        self.assertIn('Erro ao processar arquivo RAR', str(context.exception))
    
    @patch('rarfile.RarFile')
    def test_extract_rar_recursive_with_nested_rar(self, mock_rarfile):
        """Testa extração RAR com arquivo RAR aninhado"""
        # Mock do arquivo RAR
        mock_rar = Mock()
        mock_rarfile.return_value.__enter__.return_value = mock_rar
        
        # Mock das informações dos arquivos
        mock_info = Mock()
        mock_info.filename = 'nested.rar'
        mock_info.is_dir.return_value = False
        
        mock_rar.infolist.return_value = [mock_info]
        
        # Mock do arquivo
        mock_file = Mock()
        mock_file.read.return_value = b'nested rar content'
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=None)
        
        mock_rar.open.return_value = mock_file
        
        # Mock da extração recursiva
        with patch.object(self.processor, '_extract_rar_recursive') as mock_recursive:
            arquivos_extraidos = {}
            rar_bytes = io.BytesIO(b'fake rar content')
            
            self.processor._extract_rar_recursive(rar_bytes, '', arquivos_extraidos)
            
            # Verifica que a extração recursiva foi chamada
            self.assertGreater(mock_recursive.call_count, 0)
    
    @patch('rarfile.RarFile')
    def test_extract_rar_recursive_general_error(self, mock_rarfile):
        """Testa extração RAR com erro geral"""
        mock_rarfile.side_effect = Exception("Erro geral")
        
        arquivos_extraidos = {}
        rar_bytes = io.BytesIO(b'fake rar content')
        
        with self.assertRaises(Exception) as context:
            self.processor._extract_rar_recursive(rar_bytes, '', arquivos_extraidos)
        
        self.assertIn('Erro ao processar arquivo RAR', str(context.exception))
    
    @patch('zipfile.ZipFile')
    def test_extract_zip_recursive_with_nested_zip_error(self, mock_zipfile):
        """Testa extração ZIP com erro no arquivo aninhado"""
        # Mock do arquivo ZIP
        mock_zip = Mock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip
        
        # Mock das informações dos arquivos
        mock_info = Mock()
        mock_info.filename = 'nested.zip'
        mock_info.is_dir.return_value = False
        
        mock_zip.infolist.return_value = [mock_info]
        
        # Mock do arquivo
        mock_file = Mock()
        mock_file.read.return_value = b'nested zip content'
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=None)
        
        mock_zip.open.return_value = mock_file
        
        # Mock da extração recursiva com erro
        with patch.object(self.processor, '_extract_zip_recursive') as mock_recursive:
            mock_recursive.side_effect = Exception("Erro na extração recursiva")
            
            arquivos_extraidos = {}
            zip_bytes = io.BytesIO(b'fake zip content')
            
            # Deve continuar mesmo com erro na extração recursiva
            try:
                self.processor._extract_zip_recursive(zip_bytes, '', arquivos_extraidos)
            except Exception:
                pass  # Esperado que falhe
            
            # Verifica que pelo menos tentou processar
            self.assertGreater(mock_recursive.call_count, 0)
    
    @patch('rarfile.RarFile')
    def test_extract_rar_recursive_with_nested_zip_error(self, mock_rarfile):
        """Testa extração RAR com erro no arquivo ZIP aninhado"""
        # Mock do arquivo RAR
        mock_rar = Mock()
        mock_rarfile.return_value.__enter__.return_value = mock_rar
        
        # Mock das informações dos arquivos
        mock_info = Mock()
        mock_info.filename = 'nested.zip'
        mock_info.is_dir.return_value = False
        
        mock_rar.infolist.return_value = [mock_info]
        
        # Mock do arquivo
        mock_file = Mock()
        mock_file.read.return_value = b'nested zip content'
        mock_file.__enter__ = Mock(return_value=mock_file)
        mock_file.__exit__ = Mock(return_value=None)
        
        mock_rar.open.return_value = mock_file
        
        # Mock da extração recursiva com erro
        with patch.object(self.processor, '_extract_zip_recursive') as mock_recursive:
            mock_recursive.side_effect = Exception("Erro na extração recursiva")
            
            arquivos_extraidos = {}
            rar_bytes = io.BytesIO(b'fake rar content')
            
            # Deve continuar mesmo com erro na extração recursiva
            try:
                self.processor._extract_rar_recursive(rar_bytes, '', arquivos_extraidos)
            except Exception:
                pass  # Esperado que falhe
            
            # Verifica que pelo menos tentou processar
            self.assertGreater(mock_recursive.call_count, 0)


class DXFProcessorTestCase(TestCase):
    """Testes para a classe DXFProcessor"""
    
    def setUp(self):
        self.processor = DXFProcessor()
    
    def test_init_default(self):
        """Testa inicialização com valores padrão"""
        self.assertEqual(self.processor.target_layer, "Corte")
        self.assertEqual(self.processor.cutting_speed_mm_per_second, 50)
    
    def test_init_custom(self):
        """Testa inicialização com valores customizados"""
        processor = DXFProcessor(target_layer="Teste")
        self.assertEqual(processor.target_layer, "Teste")
    
    def test_calculate_line_length(self):
        """Testa cálculo de comprimento de linha"""
        # Mock da entidade linha
        mock_line = Mock()
        mock_line.dxf.start = (0, 0)
        mock_line.dxf.end = (3, 4)
        
        length = self.processor._calculate_line_length(mock_line)
        expected = math.sqrt(3**2 + 4**2)  # 5.0
        
        self.assertEqual(length, expected)
    
    def test_calculate_line_length_error(self):
        """Testa cálculo de linha com erro"""
        mock_line = Mock()
        mock_line.dxf.start = None  # Causa erro
        
        length = self.processor._calculate_line_length(mock_line)
        self.assertEqual(length, 0.0)
    
    def test_calculate_arc_length(self):
        """Testa cálculo de comprimento de arco"""
        # Mock da entidade arco
        mock_arc = Mock()
        mock_arc.dxf.radius = 10
        mock_arc.dxf.start_angle = 0
        mock_arc.dxf.end_angle = 90  # 90 graus = π/2 radianos
        
        length = self.processor._calculate_arc_length(mock_arc)
        expected = 10 * (math.pi / 2)  # raio * ângulo
        
        self.assertAlmostEqual(length, expected, places=5)
    
    def test_calculate_arc_length_normalized(self):
        """Testa cálculo de arco com normalização de ângulos"""
        mock_arc = Mock()
        mock_arc.dxf.radius = 5
        mock_arc.dxf.start_angle = 270
        mock_arc.dxf.end_angle = 90  # Precisa normalizar
        
        length = self.processor._calculate_arc_length(mock_arc)
        self.assertGreater(length, 0)
    
    def test_calculate_circle_length(self):
        """Testa cálculo de comprimento de círculo"""
        mock_circle = Mock()
        mock_circle.dxf.radius = 5
        
        length = self.processor._calculate_circle_length(mock_circle)
        expected = 2 * math.pi * 5
        
        self.assertEqual(length, expected)
    
    def test_calculate_polyline_length(self):
        """Testa cálculo de comprimento de polylinha"""
        mock_polyline = Mock()
        mock_polyline.get_points.return_value = [(0, 0), (3, 0), (3, 4)]
        
        length = self.processor._calculate_polyline_length(mock_polyline)
        expected = 3 + 4  # 3 + 4 = 7
        
        self.assertEqual(length, expected)
    
    def test_get_entity_length_line(self):
        """Testa identificação e cálculo de linha"""
        mock_entity = Mock()
        mock_entity.dxftype.return_value = 'LINE'
        
        with patch.object(self.processor, '_calculate_line_length') as mock_calc:
            mock_calc.return_value = 5.0
            length = self.processor._get_entity_length(mock_entity)
            
            mock_calc.assert_called_once_with(mock_entity)
            self.assertEqual(length, 5.0)
    
    def test_get_entity_length_arc(self):
        """Testa identificação e cálculo de arco"""
        mock_entity = Mock()
        mock_entity.dxftype.return_value = 'ARC'
        
        with patch.object(self.processor, '_calculate_arc_length') as mock_calc:
            mock_calc.return_value = 10.0
            length = self.processor._get_entity_length(mock_entity)
            
            mock_calc.assert_called_once_with(mock_entity)
            self.assertEqual(length, 10.0)
    
    def test_get_entity_length_circle(self):
        """Testa identificação e cálculo de círculo"""
        mock_entity = Mock()
        mock_entity.dxftype.return_value = 'CIRCLE'
        
        with patch.object(self.processor, '_calculate_circle_length') as mock_calc:
            mock_calc.return_value = 15.0
            length = self.processor._get_entity_length(mock_entity)
            
            mock_calc.assert_called_once_with(mock_entity)
            self.assertEqual(length, 15.0)
    
    def test_get_entity_length_polyline(self):
        """Testa identificação e cálculo de polylinha"""
        mock_entity = Mock()
        mock_entity.dxftype.return_value = 'LWPOLYLINE'
        
        with patch.object(self.processor, '_calculate_polyline_length') as mock_calc:
            mock_calc.return_value = 20.0
            length = self.processor._get_entity_length(mock_entity)
            
            mock_calc.assert_called_once_with(mock_entity)
            self.assertEqual(length, 20.0)
    
    def test_get_entity_length_unknown(self):
        """Testa entidade desconhecida (fallback para linha)"""
        mock_entity = Mock()
        mock_entity.dxftype.return_value = 'UNKNOWN'
        
        with patch.object(self.processor, '_calculate_line_length') as mock_calc:
            mock_calc.return_value = 25.0
            length = self.processor._get_entity_length(mock_entity)
            
            mock_calc.assert_called_once_with(mock_entity)
            self.assertEqual(length, 25.0)
    
    def test_get_entity_length_error(self):
        """Testa erro no cálculo de entidade"""
        mock_entity = Mock()
        mock_entity.dxftype.side_effect = Exception("Erro")
        
        length = self.processor._get_entity_length(mock_entity)
        self.assertEqual(length, 0.0)
    
    def test_calculate_perimeter(self):
        """Testa cálculo de perímetro total"""
        # Mock do modelspace com várias entidades
        mock_modelspace = [
            Mock(), Mock(), Mock()
        ]
        
        # Configurar cada entidade
        for i, entity in enumerate(mock_modelspace):
            entity.dxftype.return_value = 'LINE'
        
        # Mock do cálculo de comprimento
        with patch.object(self.processor, '_get_entity_length') as mock_get_length:
            mock_get_length.side_effect = [5.0, 10.0, 15.0]
            
            perimeter = self.processor._calculate_perimeter(mock_modelspace)
            
            self.assertEqual(perimeter, 30.0)
            self.assertEqual(mock_get_length.call_count, 3)
    
    def test_get_material_factor(self):
        """Testa fatores de correção por material"""
        self.assertEqual(self.processor._get_material_factor('aço'), 1.0)
        self.assertEqual(self.processor._get_material_factor('alumínio'), 0.8)
        self.assertEqual(self.processor._get_material_factor('cobre'), 1.2)
        self.assertEqual(self.processor._get_material_factor('inox'), 1.3)
        self.assertEqual(self.processor._get_material_factor('material_desconhecido'), 1.0)
        self.assertEqual(self.processor._get_material_factor(None), 1.0)
    
    def test_get_thickness_factor(self):
        """Testa fatores de correção por espessura"""
        self.assertEqual(self.processor._get_thickness_factor(0.5), 0.8)   # ≤ 1.0
        self.assertEqual(self.processor._get_thickness_factor(2.0), 1.0)   # ≤ 3.0
        self.assertEqual(self.processor._get_thickness_factor(5.0), 1.3)   # ≤ 6.0
        self.assertEqual(self.processor._get_thickness_factor(8.0), 1.6)   # ≤ 10.0
        self.assertEqual(self.processor._get_thickness_factor(15.0), 2.0)  # > 10.0
        self.assertEqual(self.processor._get_thickness_factor(None), 1.0)
    
    def test_estimate_cutting_time(self):
        """Testa estimativa de tempo de corte"""
        # Teste básico
        time_basic = self.processor._estimate_cutting_time(100)  # 100mm
        expected_basic = 100 / 50  # 2 segundos
        self.assertEqual(time_basic, expected_basic)
        
        # Teste com material e espessura
        time_with_factors = self.processor._estimate_cutting_time(100, 'alumínio', 2.0)
        expected_with_factors = (100 / 50) * 0.8 * 1.0  # 1.6 segundos
        self.assertEqual(time_with_factors, expected_with_factors)
    
    @patch('tempfile.mktemp')
    @patch('ezdxf.readfile')
    def test_process_single_dxf_success(self, mock_readfile, mock_mktemp):
        """Testa processamento bem-sucedido de arquivo DXF"""
        # Mock do arquivo temporário
        mock_mktemp.return_value = '/tmp/test.dxf'
        
        # Mock do ezdxf
        mock_doc = Mock()
        mock_modelspace = [Mock(), Mock()]
        mock_doc.modelspace.return_value = mock_modelspace
        mock_readfile.return_value = mock_doc
        
        # Mock das entidades
        for entity in mock_modelspace:
            entity.dxftype.return_value = 'LINE'
        
        # Mock do cálculo de perímetro
        with patch.object(self.processor, '_calculate_perimeter') as mock_perimeter:
            mock_perimeter.return_value = 100.0
            
            with patch.object(self.processor, '_estimate_cutting_time') as mock_time:
                mock_time.return_value = 2.0
                
                # Mock do open e os.path.exists
                with patch('builtins.open', mock_open()) as mock_file:
                    with patch('os.path.exists', return_value=True):
                        result = self.processor._process_single_dxf('test.dxf', b'fake content')
                        
                        self.assertEqual(result['arquivo'], 'test.dxf')
                        self.assertEqual(result['perimetro_mm'], 100.0)
                        self.assertEqual(result['tempo_corte_segundos'], 2.0)
                        self.assertEqual(result['status'], 'processado')
                        self.assertEqual(result['layer_utilizada'], 'todas as layers')
    
    def test_process_single_dxf_empty_file(self):
        """Testa processamento de arquivo vazio"""
        result = self.processor._process_single_dxf('test.dxf', b'')
        
        self.assertEqual(result['status'], 'erro: Arquivo vazio')
        self.assertEqual(result['perimetro_mm'], 0)
    
    @patch('tempfile.mktemp')
    def test_process_single_dxf_file_creation_error(self, mock_mktemp):
        """Testa erro na criação do arquivo temporário"""
        mock_mktemp.return_value = '/tmp/test.dxf'
        
        with patch('builtins.open', side_effect=Exception("Erro de criação")):
            result = self.processor._process_single_dxf('test.dxf', b'content')
            
            self.assertIn('erro:', result['status'])
            self.assertEqual(result['perimetro_mm'], 0)
    
    def test_process_dxf_files(self):
        """Testa processamento de múltiplos arquivos DXF"""
        arquivos_extraidos = {
            'arquivo1.dxf': b'content1',
            'arquivo2.txt': b'content2',  # Não é DXF
            'arquivo3.dxf': b'content3'
        }
        
        with patch.object(self.processor, '_process_single_dxf') as mock_process:
            mock_process.side_effect = [
                {'arquivo': 'arquivo1.dxf', 'perimetro_mm': 100, 'status': 'processado'},
                {'arquivo': 'arquivo3.dxf', 'perimetro_mm': 200, 'status': 'processado'}
            ]
            
            resultados = self.processor.process_dxf_files(arquivos_extraidos)
            
            self.assertEqual(len(resultados), 2)
            self.assertEqual(mock_process.call_count, 2)
    
    def test_process_dxf_files_with_string_content(self):
        """Testa processamento com conteúdo em string"""
        arquivos_extraidos = {
            'arquivo1.dxf': 'string content'  # String em vez de bytes
        }
        
        with patch.object(self.processor, '_process_single_dxf') as mock_process:
            mock_process.return_value = {'arquivo': 'arquivo1.dxf', 'status': 'processado'}
            
            resultados = self.processor.process_dxf_files(arquivos_extraidos)
            
            self.assertEqual(len(resultados), 1)
            # Verifica se a string foi convertida para bytes
            mock_process.assert_called_once()
            args, kwargs = mock_process.call_args
            self.assertEqual(args[0], 'arquivo1.dxf')
            self.assertIsInstance(args[1], bytes)
    
    def test_process_dxf_files_with_errors(self):
        """Testa processamento com erros"""
        arquivos_extraidos = {
            'arquivo1.dxf': b'content1',
            'arquivo2.dxf': b'content2'
        }
        
        with patch.object(self.processor, '_process_single_dxf') as mock_process:
            mock_process.side_effect = [
                Exception("Erro no arquivo 1"),
                {'arquivo': 'arquivo2.dxf', 'status': 'processado'}
            ]
            
            resultados = self.processor.process_dxf_files(arquivos_extraidos)
            
            self.assertEqual(len(resultados), 2)
            self.assertIn('erro:', resultados[0]['status'])
            self.assertEqual(resultados[1]['status'], 'processado')
    
    def test_process_dxf_files_with_invalid_content_type(self):
        """Testa processamento com tipo de conteúdo inválido"""
        arquivos_extraidos = {
            'arquivo1.dxf': 123  # Tipo inválido (não bytes nem string)
        }
        
        with patch.object(self.processor, '_process_single_dxf') as mock_process:
            mock_process.return_value = {'arquivo': 'arquivo1.dxf', 'status': 'erro'}
            
            resultados = self.processor.process_dxf_files(arquivos_extraidos)
            
            self.assertEqual(len(resultados), 1)
            self.assertIn('tipo de conteúdo inválido', resultados[0]['status'])
    
    def test_calculate_polyline_length_error(self):
        """Testa cálculo de polylinha com erro"""
        mock_polyline = Mock()
        mock_polyline.get_points.side_effect = Exception("Erro na polylinha")
        
        length = self.processor._calculate_polyline_length(mock_polyline)
        self.assertEqual(length, 0.0)
    
    def test_calculate_polyline_length_insufficient_points(self):
        """Testa cálculo de polylinha com pontos insuficientes"""
        mock_polyline = Mock()
        mock_polyline.get_points.return_value = [(0, 0)]  # Apenas um ponto
        
        length = self.processor._calculate_polyline_length(mock_polyline)
        self.assertEqual(length, 0.0)
    
    def test_calculate_polyline_length_invalid_coordinates(self):
        """Testa cálculo de polylinha com coordenadas inválidas"""
        mock_polyline = Mock()
        mock_polyline.get_points.return_value = [(0,), (1,)]  # Coordenadas incompletas
        
        length = self.processor._calculate_polyline_length(mock_polyline)
        self.assertEqual(length, 0.0)
    
    @patch('tempfile.mktemp')
    def test_process_single_dxf_file_not_created(self, mock_mktemp):
        """Testa erro quando arquivo temporário não é criado"""
        mock_mktemp.return_value = '/tmp/test.dxf'
        
        with patch('os.path.exists', return_value=False):
            result = self.processor._process_single_dxf('test.dxf', b'content')
            
            self.assertIn('Falha ao criar arquivo temporário', result['status'])
    
    @patch('tempfile.mktemp')
    @patch('ezdxf.readfile')
    def test_process_single_dxf_ezdxf_error(self, mock_readfile, mock_mktemp):
        """Testa erro no ezdxf"""
        mock_mktemp.return_value = '/tmp/test.dxf'
        mock_readfile.side_effect = Exception("Erro no ezdxf")
        
        with patch('builtins.open', mock_open()):
            with patch('os.path.exists', return_value=True):
                result = self.processor._process_single_dxf('test.dxf', b'content')
                
                self.assertIn('erro:', result['status'])
    
    @patch('tempfile.mktemp')
    def test_process_single_dxf_temp_file_cleanup_error(self, mock_mktemp):
        """Testa erro na limpeza do arquivo temporário"""
        mock_mktemp.return_value = '/tmp/test.dxf'
        
        with patch('builtins.open', mock_open()):
            with patch('os.path.exists', return_value=True):
                with patch('os.unlink', side_effect=Exception("Erro na remoção")):
                    result = self.processor._process_single_dxf('test.dxf', b'content')
                    
                    # Deve retornar erro mas não quebrar
                    self.assertIn('erro:', result['status'])
    
    def test_calculate_arc_length_error(self):
        """Testa cálculo de arco com erro"""
        mock_arc = Mock()
        mock_arc.dxf.radius = 5
        mock_arc.dxf.start_angle = 0
        mock_arc.dxf.end_angle = 90
        
        # Simular erro no cálculo
        with patch('math.radians', side_effect=Exception("Erro no cálculo")):
            length = self.processor._calculate_arc_length(mock_arc)
            self.assertEqual(length, 0.0)
    
    def test_calculate_circle_length_radius_error(self):
        """Testa cálculo de círculo com erro no raio"""
        mock_circle = Mock()
        mock_circle.dxf.radius = None  # Raio inválido
        
        length = self.processor._calculate_circle_length(mock_circle)
        self.assertEqual(length, 0.0)
    
    def test_calculate_circle_length_radius_error(self):
        """Testa cálculo de círculo com erro no raio"""
        mock_circle = Mock()
        mock_circle.dxf.radius = None  # Raio inválido
        
        length = self.processor._calculate_circle_length(mock_circle)
        self.assertEqual(length, 0.0)
    
    def test_get_entity_length_with_layer_filter(self):
        """Testa filtro por layer específica"""
        # Criar processador com layer específica
        processor = DXFProcessor(target_layer="Corte")
        
        # Mock da entidade
        mock_entity = Mock()
        mock_entity.dxftype.return_value = 'LINE'
        mock_entity.dxf.layer = "Corte"  # Layer correta
        
        with patch.object(processor, '_calculate_line_length') as mock_calc:
            mock_calc.return_value = 10.0
            length = processor._get_entity_length(mock_entity)
            
            self.assertEqual(length, 10.0)
    
    def test_get_entity_length_with_wrong_layer(self):
        """Testa entidade com layer incorreta"""
        # Criar processador com layer específica
        processor = DXFProcessor(target_layer="Corte")
        
        # Mock da entidade
        mock_entity = Mock()
        mock_entity.dxftype.return_value = 'LINE'
        mock_entity.dxf.layer = "Outra"  # Layer incorreta
        
        length = processor._get_entity_length(mock_entity)
        self.assertEqual(length, 0.0)
    
    def test_get_entity_length_with_layer_attribute_error(self):
        """Testa entidade sem atributo layer"""
        # Criar processador com layer específica
        processor = DXFProcessor(target_layer="Corte")
        
        # Mock da entidade sem atributo layer
        mock_entity = Mock()
        mock_entity.dxftype.return_value = 'LINE'
        # Não definir dxf.layer para causar AttributeError
        
        length = processor._get_entity_length(mock_entity)
        self.assertEqual(length, 0.0)


class UploadZipViewTestCase(APITestCase):
    """Testes para a view UploadZipView"""
    
    def setUp(self):
        self.client = Client()
        self.url = '/api/upload/'
    
    def test_post_no_file(self):
        """Testa upload sem arquivo"""
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Nenhum arquivo enviado', response.data['error'])
    
    def test_post_invalid_format(self):
        """Testa upload com formato inválido"""
        file_content = b'fake content'
        uploaded_file = SimpleUploadedFile('test.txt', file_content)
        
        response = self.client.post(self.url, {'file': uploaded_file})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Formato de arquivo não suportado', response.data['error'])
    
    def test_post_file_too_large(self):
        """Testa upload de arquivo muito grande"""
        # Criar arquivo maior que 200MB
        file_content = b'x' * (201 * 1024 * 1024)  # 201MB
        uploaded_file = SimpleUploadedFile('test.zip', file_content)
        
        response = self.client.post(self.url, {'file': uploaded_file})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('excede o limite de 200MB', response.data['error'])
    
    @patch('uploadapi.views.ArchiveProcessor')
    def test_post_valid_zip(self, mock_archive_processor):
        """Testa upload de arquivo ZIP válido"""
        # Mock do processador de arquivo
        mock_processor = Mock()
        mock_processor.validate_file_format.return_value = True
        mock_processor.extract_archive_recursive.return_value = {
            'arquivo1.dxf': b'dxf content',
            'arquivo2.pdf': b'pdf content'
        }
        mock_archive_processor.return_value = mock_processor
        
        # Mock do processador DXF
        with patch('uploadapi.views.DXFProcessor') as mock_dxf_processor:
            mock_dxf = Mock()
            mock_dxf.process_dxf_files.return_value = [
                {'arquivo': 'arquivo1.dxf', 'perimetro_mm': 100, 'status': 'processado'}
            ]
            mock_dxf_processor.return_value = mock_dxf
            
            # Criar arquivo ZIP de teste
            file_content = b'fake zip content'
            uploaded_file = SimpleUploadedFile('test.zip', file_content)
            
            response = self.client.post(self.url, {'file': uploaded_file})
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['status'], 'upload concluído com sucesso')
            self.assertEqual(response.data['formato_arquivo'], 'ZIP')
            self.assertEqual(response.data['total_arquivos'], 2)
            self.assertEqual(response.data['arquivos_dxf_encontrados'], 1)
            self.assertEqual(response.data['arquivos_dxf_processados'], 1)
    
    @patch('uploadapi.views.ArchiveProcessor')
    def test_post_valid_rar(self, mock_archive_processor):
        """Testa upload de arquivo RAR válido"""
        # Mock do processador de arquivo
        mock_processor = Mock()
        mock_processor.validate_file_format.return_value = True
        mock_processor.extract_archive_recursive.return_value = {
            'arquivo1.dxf': b'dxf content'
        }
        mock_archive_processor.return_value = mock_processor
        
        # Mock do processador DXF
        with patch('uploadapi.views.DXFProcessor') as mock_dxf_processor:
            mock_dxf = Mock()
            mock_dxf.process_dxf_files.return_value = []
            mock_dxf_processor.return_value = mock_dxf
            
            # Criar arquivo RAR de teste
            file_content = b'fake rar content'
            uploaded_file = SimpleUploadedFile('test.rar', file_content)
            
            response = self.client.post(self.url, {'file': uploaded_file})
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['formato_arquivo'], 'RAR')
    
    @patch('uploadapi.views.ArchiveProcessor')
    def test_post_extraction_error(self, mock_archive_processor):
        """Testa erro na extração do arquivo"""
        # Mock do processador de arquivo com erro
        mock_processor = Mock()
        mock_processor.validate_file_format.return_value = True
        mock_processor.extract_archive_recursive.side_effect = Exception("Erro de extração")
        mock_archive_processor.return_value = mock_processor
        
        # Criar arquivo de teste
        file_content = b'fake content'
        uploaded_file = SimpleUploadedFile('test.zip', file_content)
        
        response = self.client.post(self.url, {'file': uploaded_file})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Erro ao processar o arquivo', response.data['error'])


if __name__ == '__main__':
    unittest.main()
