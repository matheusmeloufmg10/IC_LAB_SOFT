from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Count, Avg, Max, Min
from django.utils import timezone
from datetime import timedelta
import io
from .dxf_processor import DXFProcessor
from .archive_processor import ArchiveProcessor
from .integrated_processor import processar_lote_pdfs_dxfs
from .models import validar_e_salvar_pecas_e_subpecas_do_json, PecaPrincipal, SubPeca
from django.core.exceptions import ObjectDoesNotExist

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
            
            # Processamento consolidado PDF + DXF
            pecas = processar_lote_pdfs_dxfs(arquivos_extraidos)
            
            # Validar e salvar no banco de dados
            sucesso_validacao, sucessos, erros = validar_e_salvar_pecas_e_subpecas_do_json(pecas)
            
            response_data = {
                'status': 'upload concluído com sucesso',
                'formato_arquivo': uploaded_file.name.split('.')[-1].upper(),
                'total_arquivos': len(arquivos_extraidos),
                'grupos': pecas,
                'validacao': {
                    'sucesso': sucesso_validacao,
                    'pecas_salvas': sucessos,
                    'erros_validacao': erros
                }
            }
            
            # Se houve erros de validação, retornar status 400 mas com os dados processados
            if not sucesso_validacao:
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': f'Erro ao processar o arquivo: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


class DashboardStatsView(APIView):
    """View para retornar estatísticas gerais do dashboard"""
    
    def get(self, request, format=None):
        print("DEBUG: DashboardStatsView foi chamada!")  # Debug
        try:
            # Estatísticas gerais
            total_pecas_principais = PecaPrincipal.objects.count()
            total_subpecas = SubPeca.objects.count()
            
            # Últimas peças cadastradas (últimos 7 dias)
            data_limite = timezone.now() - timedelta(days=7)
            pecas_recentes = PecaPrincipal.objects.filter(
                created_at__gte=data_limite
            ).count()
            
            # Estatísticas por material
            materiais_stats = SubPeca.objects.values('material').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            # Estatísticas por espessura
            espessuras_stats = SubPeca.objects.values('espessura').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            # Médias de perímetro e tempo de corte
            medias = SubPeca.objects.aggregate(
                perimetro_medio=Avg('perimetro_mm'),
                tempo_corte_medio=Avg('tempo_corte_segundos')
            )
            
            # Últimas peças cadastradas (detalhadas)
            ultimas_pecas = PecaPrincipal.objects.select_related().prefetch_related('subpecas').order_by(
                '-created_at'
            )[:5]
            
            ultimas_pecas_detalhadas = []
            for peca in ultimas_pecas:
                ultimas_pecas_detalhadas.append({
                    'codigo': peca.codigo,
                    'created_at': peca.created_at,
                    'total_subpecas': peca.subpecas.count(),
                    'materiais_unicos': peca.subpecas.values('material').distinct().count(),
                    'espessuras_unicas': peca.subpecas.values('espessura').distinct().count()
                })
            
            response_data = {
                'estatisticas_gerais': {
                    'total_pecas_principais': total_pecas_principais,
                    'total_subpecas': total_subpecas,
                    'pecas_recentes_7dias': pecas_recentes,
                    'perimetro_medio_mm': round(medias['perimetro_medio'] or 0, 2),
                    'tempo_corte_medio_segundos': round(medias['tempo_corte_medio'] or 0, 2)
                },
                'materiais': [
                    {'material': item['material'], 'quantidade': item['count']}
                    for item in materiais_stats
                ],
                'espessuras': [
                    {'espessura': item['espessura'], 'quantidade': item['count']}
                    for item in espessuras_stats
                ],
                'ultimas_pecas': ultimas_pecas_detalhadas
            }
            
            print(f"DEBUG: Retornando dados: {response_data}")  # Debug
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"DEBUG: Erro na DashboardStatsView: {str(e)}")  # Debug
            return Response(
                {'error': f'Erro ao buscar estatísticas: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DashboardPecasView(APIView):
    """View para retornar lista detalhada de peças com paginação"""
    
    def get(self, request, format=None):
        try:
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            search = request.GET.get('search', '')
            
            # Calcular offset
            offset = (page - 1) * page_size
            
            # Query base
            pecas_query = PecaPrincipal.objects.select_related().prefetch_related('subpecas')
            
            # Aplicar filtro de busca se fornecido
            if search:
                pecas_query = pecas_query.filter(codigo__icontains=search)
            
            # Contar total para paginação
            total_pecas = pecas_query.count()
            
            # Buscar peças com paginação
            pecas = pecas_query.order_by('-created_at')[offset:offset + page_size]
            
            # Preparar dados de resposta
            pecas_detalhadas = []
            for peca in pecas:
                subpecas = peca.subpecas.all()
                materiais_unicos = subpecas.values('material').distinct().count()
                espessuras_unicas = subpecas.values('espessura').distinct().count()
                
                pecas_detalhadas.append({
                    'codigo': peca.codigo,
                    'created_at': peca.created_at,
                    'updated_at': peca.updated_at,
                    'total_subpecas': subpecas.count(),
                    'materiais_unicos': materiais_unicos,
                    'espessuras_unicas': espessuras_unicas,
                    'perimetro_total': sum(sp.perimetro_mm for sp in subpecas),
                    'tempo_corte_total': sum(sp.tempo_corte_segundos for sp in subpecas)
                })
            
            response_data = {
                'pecas': pecas_detalhadas,
                'paginacao': {
                    'pagina_atual': page,
                    'tamanho_pagina': page_size,
                    'total_pecas': total_pecas,
                    'total_paginas': (total_pecas + page_size - 1) // page_size
                }
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Erro ao buscar peças: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DashboardDetalhesPecaView(APIView):
    """View para retornar detalhes de uma peça específica"""
    
    def get(self, request, codigo_peca, format=None):
        try:
            peca = PecaPrincipal.objects.select_related().prefetch_related('subpecas').get(codigo=codigo_peca)
            
            subpecas = peca.subpecas.all()
            
            # Estatísticas da peça
            stats = {
                'total_subpecas': subpecas.count(),
                'materiais_unicos': subpecas.values('material').distinct().count(),
                'espessuras_unicas': subpecas.values('espessura').distinct().count(),
                'perimetro_total': sum(sp.perimetro_mm for sp in subpecas),
                'tempo_corte_total': sum(sp.tempo_corte_segundos for sp in subpecas),
                'perimetro_medio': sum(sp.perimetro_mm for sp in subpecas) / subpecas.count() if subpecas.count() > 0 else 0,
                'tempo_corte_medio': sum(sp.tempo_corte_segundos for sp in subpecas) / subpecas.count() if subpecas.count() > 0 else 0
            }
            
            # Lista de subpeças
            subpecas_list = []
            for subpeca in subpecas:
                subpecas_list.append({
                    'codigo': subpeca.codigo,
                    'nome': subpeca.nome,
                    'material': subpeca.material,
                    'espessura': subpeca.espessura,
                    'perimetro_mm': subpeca.perimetro_mm,
                    'tempo_corte_segundos': subpeca.tempo_corte_segundos
                })
            
            response_data = {
                'peca': {
                    'codigo': peca.codigo,
                    'created_at': peca.created_at,
                    'updated_at': peca.updated_at
                },
                'estatisticas': stats,
                'subpecas': subpecas_list
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except ObjectDoesNotExist:
            return Response(
                {'error': f'Peça com código {codigo_peca} não encontrada'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Erro ao buscar detalhes da peça: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
