from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
import io
from .dxf_processor import DXFProcessor
from .archive_processor import ArchiveProcessor

# Create your views here.

class UploadZipView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    MAX_UPLOAD_SIZE = 200 * 1024 * 1024  # 200MB

    def post(self, request, format=None):
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({'error': 'Nenhum arquivo enviado.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validar formato do arquivo
        archive_processor = ArchiveProcessor()
        if not archive_processor.validate_file_format(uploaded_file.name):
            return Response({
                'error': f'Formato de arquivo não suportado. Formatos aceitos: {", ".join(archive_processor.get_supported_formats())}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if uploaded_file.size > self.MAX_UPLOAD_SIZE:
            return Response({'error': 'Arquivo excede o limite de 200MB.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Descompactar arquivo em memória (ZIP ou RAR)
            arquivos_extraidos = archive_processor.extract_archive_recursive(uploaded_file)
            
            # Contar arquivos DXF encontrados
            arquivos_dxf_count = sum(1 for arquivo in arquivos_extraidos.keys() if arquivo.lower().endswith('.dxf'))
            
            # Processar arquivos DXF
            dxf_processor = DXFProcessor()  # Processa todas as layers
            resultados_dxf = dxf_processor.process_dxf_files(arquivos_extraidos)
            
            # Preparar resposta
            response_data = {
                'status': 'upload concluído com sucesso',
                'formato_arquivo': uploaded_file.name.split('.')[-1].upper(),
                'total_arquivos': len(arquivos_extraidos),
                'arquivos_dxf_encontrados': arquivos_dxf_count,
                'arquivos_dxf_processados': len(resultados_dxf),
                'resultados_dxf': resultados_dxf
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': f'Erro ao processar o arquivo: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
