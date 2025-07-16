# 🎨 IC Lab Soft - Frontend

Interface de upload minimalista em React para o sistema de processamento de arquivos técnicos.

## ✨ Características

- **Design Minimalista**: Interface limpa e moderna inspirada em TinyPNG, Squoosh e Vercel
- **Drag & Drop**: Upload intuitivo com arrastar e soltar
- **Responsivo**: Funciona perfeitamente em dispositivos móveis e desktop
- **Tailwind CSS**: Estilização moderna e consistente
- **Componentes Reutilizáveis**: Código limpo e bem estruturado

## 🚀 Tecnologias

- **React 18** - Framework principal
- **Vite** - Build tool e dev server
- **Tailwind CSS** - Framework de estilização
- **PostCSS** - Processamento de CSS

## 📦 Instalação

1. **Instalar dependências:**
```bash
cd frontend
npm install
```

2. **Executar em modo desenvolvimento:**
```bash
npm run dev
```

3. **Acessar a aplicação:**
```
http://localhost:3000
```

## 🛠️ Scripts Disponíveis

- `npm run dev` - Inicia o servidor de desenvolvimento
- `npm run build` - Gera build de produção
- `npm run preview` - Visualiza o build de produção
- `npm run lint` - Executa o linter

## 📁 Estrutura do Projeto

```
frontend/
├── src/
│   ├── components/
│   │   ├── Header.jsx          # Barra superior fixa
│   │   └── FileUpload.jsx      # Componente de upload reutilizável
│   ├── App.jsx                 # Componente principal
│   ├── main.jsx               # Ponto de entrada
│   └── index.css              # Estilos globais
├── public/                    # Arquivos estáticos
├── package.json              # Dependências e scripts
├── vite.config.js           # Configuração do Vite
├── tailwind.config.js       # Configuração do Tailwind
└── postcss.config.js        # Configuração do PostCSS
```

## 🎯 Funcionalidades

### Header
- Barra superior fixa com backdrop blur
- Logo e nome do sistema
- Menu de navegação (preparado para expansão)

### Upload de Arquivos
- **Drag & Drop**: Arraste arquivos diretamente na área
- **Seleção via Clique**: Clique para abrir o seletor de arquivos
- **Lista de Arquivos**: Visualização dos arquivos selecionados
- **Remoção Individual**: Remova arquivos específicos
- **Validação**: Aceita apenas arquivos ZIP e RAR
- **Limite**: Máximo de 5 arquivos por upload

### Design System
- **Cores**: Paleta minimalista com tons de cinza e azul
- **Tipografia**: Fonte Inter para melhor legibilidade
- **Animações**: Transições suaves e feedback visual
- **Responsividade**: Adaptação automática para diferentes telas

## 🔧 Configuração

### Tailwind CSS
O projeto usa uma paleta de cores personalizada:
- `primary-*`: Tons de cinza para elementos principais
- `accent-*`: Tons de azul para elementos de destaque

### Animações
- `fade-in`: Aparecimento suave de elementos
- `slide-up`: Deslizamento para cima
- `pulse-slow`: Pulsação lenta para loading

## 🔗 Integração com Backend

Para integrar com o backend Django, descomente e configure o código no `handleUpload`:

```javascript
const formData = new FormData();
selectedFiles.forEach(file => formData.append('file', file));
const response = await fetch('/api/upload/', { 
  method: 'POST', 
  body: formData 
});
```

## 📱 Responsividade

- **Mobile**: Layout otimizado para telas pequenas
- **Tablet**: Adaptação para telas médias
- **Desktop**: Layout completo com todas as funcionalidades

## 🎨 Personalização

### Cores
Edite `tailwind.config.js` para alterar a paleta de cores:

```javascript
colors: {
  primary: { /* tons de cinza */ },
  accent: { /* tons de azul */ }
}
```

### Componentes
Os componentes são modulares e podem ser facilmente customizados:
- `Header.jsx`: Barra superior
- `FileUpload.jsx`: Área de upload
- `App.jsx`: Layout principal

## 🚀 Deploy

1. **Build de produção:**
```bash
npm run build
```

2. **Os arquivos gerados estarão em `dist/`**

3. **Servir com qualquer servidor estático (nginx, Apache, etc.)**

## 📝 Próximos Passos

- [ ] Integração real com backend Django
- [ ] Preview de arquivos
- [ ] Validação de tipos de arquivo
- [ ] Barra de progresso de upload
- [ ] Histórico de uploads
- [ ] Configurações do usuário 