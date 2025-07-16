from django.db import models
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models.manager import Manager

# Create your models here.

class PecaPrincipal(models.Model):
    codigo = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.codigo

    if TYPE_CHECKING:
        objects: 'Manager'

class SubPeca(models.Model):
    peca_principal = models.ForeignKey(PecaPrincipal, related_name='subpecas', on_delete=models.CASCADE)
    codigo = models.CharField(max_length=100)
    nome = models.TextField()
    material = models.CharField(max_length=200)
    espessura = models.CharField(max_length=50)
    perimetro_mm = models.FloatField()
    tempo_corte_segundos = models.FloatField()

    def __str__(self):
        return f"{self.codigo} - {self.nome}"

    if TYPE_CHECKING:
        objects: 'Manager'

def validar_dados_peca(dados):
    """
    Valida se todos os campos obrigatórios estão preenchidos.
    Retorna (True, None) se válido, (False, mensagem_erro) se inválido.
    """
    campos_obrigatorios = ["Nome", "Material", "Espessura", "PerimetroMm", "TempoCorteSegundos"]
    
    for campo in campos_obrigatorios:
        valor = dados.get(campo)
        if valor is None or (isinstance(valor, str) and not valor.strip()):
            return False, f"Campo obrigatório '{campo}' está vazio ou nulo"
    
    # Validar se PerimetroMm e TempoCorteSegundos são números válidos
    try:
        perimetro = float(dados.get("PerimetroMm", 0))
        tempo = float(dados.get("TempoCorteSegundos", 0))
        if perimetro < 0 or tempo < 0:
            return False, "PerimetroMm e TempoCorteSegundos devem ser valores positivos"
    except (ValueError, TypeError):
        return False, "PerimetroMm e TempoCorteSegundos devem ser números válidos"
    
    return True, None

def validar_e_salvar_pecas_e_subpecas_do_json(json_grupos):
    """
    Valida e salva o dicionário de grupos no banco de dados.
    Retorna (True, lista_sucessos, lista_erros) onde:
    - lista_sucessos: lista de códigos salvos com sucesso
    - lista_erros: lista de erros encontrados
    """
    sucessos = []
    erros = []
    
    for grupo, lista_pecas in json_grupos.items():
        for peca in lista_pecas:
            codigo_peca = peca.get("PecaPrincipal")
            if not codigo_peca:
                erros.append(f"PecaPrincipal não encontrada no grupo {grupo}")
                continue
            
            subpecas = peca.get("SubPecas", {})
            if not subpecas:
                erros.append(f"Nenhuma SubPeca encontrada para {codigo_peca}")
                continue
            
            # Validar cada subpeça
            subpecas_validas = {}
            for codigo_subpeca, dados in subpecas.items():
                if not codigo_subpeca:
                    erros.append(f"Código da subpeça vazio para {codigo_peca}")
                    continue
                
                valido, msg_erro = validar_dados_peca(dados)
                if not valido:
                    erros.append(f"Subpeça {codigo_subpeca}: {msg_erro}")
                    continue
                
                subpecas_validas[codigo_subpeca] = dados
            
            # Se todas as subpeças são válidas, salvar no banco
            if subpecas_validas:
                try:
                    peca_principal, _ = PecaPrincipal.objects.get_or_create(codigo=codigo_peca)
                    
                    for codigo_subpeca, dados in subpecas_validas.items():
                        SubPeca.objects.update_or_create(
                            peca_principal=peca_principal,
                            codigo=codigo_subpeca,
                            defaults={
                                "nome": dados.get("Nome", ""),
                                "material": dados.get("Material", ""),
                                "espessura": dados.get("Espessura", ""),
                                "perimetro_mm": float(dados.get("PerimetroMm", 0.0)),
                                "tempo_corte_segundos": float(dados.get("TempoCorteSegundos", 0.0)),
                            }
                        )
                    
                    sucessos.append(codigo_peca)
                    
                except Exception as e:
                    erros.append(f"Erro ao salvar {codigo_peca}: {str(e)}")
    
    return len(erros) == 0, sucessos, erros

# Função utilitária para converter o JSON em modelos do banco de dados (sem validação)
def salvar_pecas_e_subpecas_do_json(json_grupos):
    """
    Recebe o dicionário de grupos (como retornado pelo processamento) e salva no banco.
    """
    for grupo, lista_pecas in json_grupos.items():
        for peca in lista_pecas:
            codigo_peca = peca.get("PecaPrincipal")
            if not codigo_peca:
                continue
            peca_principal, _ = PecaPrincipal.objects.get_or_create(codigo=codigo_peca)
            subpecas = peca.get("SubPecas", {})
            for codigo_subpeca, dados in subpecas.items():
                SubPeca.objects.update_or_create(
                    peca_principal=peca_principal,
                    codigo=codigo_subpeca,
                    defaults={
                        "nome": dados.get("Nome", ""),
                        "material": dados.get("Material", ""),
                        "espessura": dados.get("Espessura", ""),
                        "perimetro_mm": dados.get("PerimetroMm", 0.0),
                        "tempo_corte_segundos": dados.get("TempoCorteSegundos", 0.0),
                    }
                )
