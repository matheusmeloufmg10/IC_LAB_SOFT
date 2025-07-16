# 🏭 IC_LAB_SOFT - Processador de Arquivos DXF

Sistema web em Django para upload e processamento de arquivos técnicos (PDF, DXF, DWG) contidos em arquivos compactados (ZIP/RAR), com cálculo automático de perímetros e estimativa de tempo de corte.

## 🎯 Funcionalidades

- **Upload de arquivos ZIP/RAR** com validação de tamanho (até 200MB)
- **Descompactação recursiva** de arquivos aninhados em memória
- **Processamento de arquivos DXF** com cálculo de perímetros
- **Estimativa de tempo de corte** baseada em material e espessura
- **API REST** para integração com outros sistemas
- **Testes unitários** com 98% de cobertura
- **Dashboard dinâmico de peças** (NOVO)
  - Visualização de estatísticas agregadas (total de peças, subpeças, perímetro médio, etc)
  - Gráficos de peças por material e por espessura
  - Tabela paginada e buscável de peças principais
  - Detalhamento de peça principal com subpeças e estatísticas
  - Atualização automática dos dados (polling)
  - Interface moderna e responsiva em React + Tailwind CSS

## 🆕 Funcionalidades implementadas recentemente

### Dashboard Dinâmico de Peças
- **Aba "Dashboard"** no frontend React, acessível pelo menu de navegação
- **Gráficos interativos** (Recharts) mostrando distribuição de peças por material e espessura
- **Cards informativos** com totais e médias
- **Tabela paginada** com busca de peças principais, integração com backend
- **Detalhamento de peça**: clique em uma linha da tabela para abrir modal com estatísticas e subpeças
- **Atualização automática**: polling a cada 10 segundos para dados sempre atualizados
- **Responsividade**: layout adaptado para desktop e mobile

### API REST para Dashboard
- **Endpoint `/api/dashboard/stats/`**: estatísticas agregadas (totais, médias, últimas peças)
- **Endpoint `/api/dashboard/pecas/`**: lista paginada e buscável de peças principais
- **Endpoint `/api/dashboard/pecas/<codigo_peca>/`**: detalhes completos de uma peça principal e suas subpeças

### Integração Frontend/Backend
- **Proxy Vite** configurado para `/api` → backend Django
- **CORS** habilitado no Django para permitir requisições do frontend React
- **Componentes React** reutilizáveis para cards, gráficos, tabela e modal de detalhes

---

## 🛠️ Tecnologias Utilizadas

- **Backend**: Django 5.2.4 + Django REST Framework
- **Processamento DXF**: ezdxf
- **Arquivos compactados**: zipfile, rarfile
- **Testes**: unittest + coverage
- **Frontend**: React + Vite + Tailwind CSS + Recharts
- **Python**: 3.10+

## 📋 Pré-requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)
- Git

## 🚀 Instalação

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/IC_LAB_SOFT.git
cd IC_LAB_SOFT
```

### 2. Crie um ambiente virtual
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Execute as migrações
```bash
python3 manage.py migrate
```

### 5. Inicie o servidor
```bash
python3 manage.py runserver
```

O sistema estará disponível em: http://localhost:8000

## 📖 Como Usar

### Upload de Arquivos

**Endpoint**: `POST /api/upload/`

**Exemplo com curl:**
```bash
curl -X POST \
  http://localhost:8000/api/upload/ \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@seu_arquivo.zip'
```

**Exemplo com Python:**
```python
import requests

url = 'http://localhost:8000/api/upload/'
files = {'file': open('arquivo.zip', 'rb')}
response = requests.post(url, files=files)
print(response.json())
```

### Resposta da API

```json
{
  "status": "upload concluído com sucesso",
  "formato_arquivo": "ZIP",
  "total_arquivos": 24,
  "arquivos_dxf_encontrados": 6,
  "arquivos_dxf_processados": 6,
  "resultados_dxf": [
    {
      "arquivo": "arquivo1.dxf",
      "perimetro_mm": 150.5,
      "tempo_corte_segundos": 3.01,
      "status": "processado",
      "layer_utilizada": "todas as layers"
    }
  ]
}
```

## 🔧 Configuração

### Formatos Suportados
- **Arquivos de entrada**: `.zip`, `.rar`
- **Arquivos processados**: `.dxf`, `.dwg`, `.pdf`

### Parâmetros Configuráveis
- **Tamanho máximo**: 200MB
- **Velocidade de corte**: 50mm/s (padrão)
- **Layer padrão**: "Corte" (configurável)
- **Fatores de correção por material**:
  - Aço: 1.0
  - Alumínio: 0.8
  - Cobre: 1.2
  - Inox: 1.3

## 🧪 Testes

### Executar todos os testes
```bash
python3 manage.py test uploadapi.tests
```

### Executar com cobertura
```bash
coverage run --source='uploadapi' manage.py test uploadapi.tests
coverage report --show-missing
```

### Cobertura de Testes
- **Total**: 98%
- **ArchiveProcessor**: 86%
- **DXFProcessor**: 99%
- **Views**: 100%

## 📁 Estrutura do Projeto

```
IC_LAB_SOFT/
├── docmanager/           # Configurações do Django
├── uploadapi/           # App principal
│   ├── archive_processor.py  # Processamento de ZIP/RAR
│   ├── dxf_processor.py      # Processamento de DXF
│   ├── views.py             # API endpoints
│   └── tests.py             # Testes unitários
├── manage.py
├── requirements.txt
└── README.md
```

## 🔍 Processamento de Arquivos DXF

### Entidades Suportadas
- **Linhas (LINE)**: Cálculo por distância euclidiana
- **Arcos (ARC)**: Cálculo por raio × ângulo
- **Círculos (CIRCLE)**: Cálculo por 2π × raio
- **Polylines (LWPOLYLINE)**: Soma dos segmentos

### Fatores de Correção

#### Por Material
- Aço: 1.0
- Alumínio: 0.8
- Cobre: 1.2
- Inox: 1.3

#### Por Espessura
- ≤ 1.0mm: 0.8
- ≤ 3.0mm: 1.0
- ≤ 6.0mm: 1.3
- ≤ 10.0mm: 1.6
- > 10.0mm: 2.0

## 🐛 Solução de Problemas

### Erro: "Arquivo muito grande"
- Verifique se o arquivo não excede 200MB
- Comprima arquivos grandes antes do upload

### Erro: "Formato não suportado"
- Use apenas arquivos .zip ou .rar
- Verifique se o arquivo não está corrompido

### Erro: "Falha no processamento DXF"
- Verifique se o arquivo DXF é válido
- Certifique-se de que o arquivo não está corrompido

## 📝 Histórico de Desenvolvimento

### User Stories Implementadas

1. **US1**: Upload e descompactação de arquivos ZIP aninhados
2. **US2**: Leitura de arquivos DXF e cálculo de perímetro
3. **Suporte a arquivos RAR**: Processamento de arquivos .rar
4. **Ajustes finais**: Correções e melhorias
5. **Testes unitários**: Cobertura de 98%

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👨‍💻 Autor

**Matheus Melo**
- Email: matheusmelos@ufmg.br
- GitHub: [@matheusmeloufmg10](https://github.com/matheusmeloufmg10)

## 🙏 Agradecimentos

- Django Framework
- ezdxf para processamento de arquivos DXF
- Comunidade Python 