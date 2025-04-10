# Aplicação de Previsão do Tempo - Clima Brasil

Esta é uma aplicação web Flask que exibe dados meteorológicos atuais, previsão para os próximos 5 dias, e análises de insights climáticos utilizando a API OpenWeatherMap. A aplicação permite buscar informações climáticas para qualquer cidade do mundo.

## Características

- Exibe temperatura atual, sensação térmica, descrição do clima, umidade, pressão e velocidade do vento
- Mostra previsão do tempo para os próximos 5 dias
- Busca de cidades via formulário
- **Insights climáticos com visualizações:**
  - Padrões sazonais de temperatura e precipitação
  - Histórico de eventos climáticos extremos
  - Análise de impacto na agricultura
  - Recomendações para mitigação de riscos
- Interface responsiva e moderna usando Bootstrap 5
- Ícones climáticos dinâmicos
- Design adaptativo para dispositivos móveis e desktop
- Visualizações de dados com Chart.js
- Tradução para português dos dados meteorológicos

## APIs e Bibliotecas Utilizadas

- **OpenWeatherMap Current Weather**: Para obter dados meteorológicos atuais
- **OpenWeatherMap 5 Day / 3 Hour Forecast**: Para obter previsão dos próximos dias
- **Chart.js**: Para visualizações de dados na página de insights
- **Bootstrap 5**: Para interface responsiva
- **Font Awesome**: Para ícones

## Pré-requisitos

- Python 3.7 ou superior
- pip (gerenciador de pacotes Python)

## Instalação

### 1. Clone o repositório (ou baixe os arquivos)

```
git clone <url-do-repositorio>
cd <nome-da-pasta>
```

### 2. Criar e ativar ambiente virtual

No Windows:
```
python -m venv venv
venv\Scripts\activate
```

No macOS/Linux:
```
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependências

```
pip install -r requirements.txt
```

## Executando a aplicação

Para iniciar o servidor Flask:

```
flask run
```

Acesse a aplicação em seu navegador através do endereço: [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Como usar

1. Ao acessar a aplicação, você verá o clima atual do Rio de Janeiro por padrão
2. Use o formulário de busca no topo para buscar qualquer cidade do mundo
3. Digite o nome da cidade e clique no botão de busca
4. A aplicação exibirá os dados meteorológicos atuais e previsão para os próximos 5 dias para a cidade pesquisada
5. Clique em "Insights Climáticos" no menu ou no botão "Ver Insights" para acessar as análises e visualizações de dados

## Funcionalidades de Insights

### Padrões Sazonais
Visualize tendências mensais de temperatura e precipitação ao longo do ano, permitindo identificar padrões sazonais.

### Eventos Climáticos Extremos
Analise histórico de eventos climáticos extremos, como ondas de calor, secas e inundações, incluindo detalhes sobre impacto e severidade.

### Impacto na Agricultura
Visualize como diferentes eventos climáticos (temperaturas elevadas, secas, chuvas intensas) afetam a produtividade de diversas culturas.

## Estrutura do projeto

```
.
├── app.py              # Aplicação principal Flask
├── requirements.txt    # Dependências do projeto
├── static/             # Arquivos estáticos
│   └── style.css       # Estilos personalizados
├── templates/          # Templates HTML
│   ├── index.html      # Página principal
│   ├── insights.html   # Página de insights climáticos 
│   └── error.html      # Página de erro
└── venv/               # Ambiente virtual Python (gerado na instalação)
```

## Tecnologias utilizadas

- Flask - Framework web Python
- OpenWeatherMap API - Fornecimento de dados meteorológicos
- Bootstrap 5 - Framework CSS para interface responsiva
- Chart.js - Biblioteca para visualização de dados
- Font Awesome - Ícones
- Google Fonts (Poppins) - Tipografia 