# Documentação do Projeto Clima Brasil

## Visão Geral

Este projeto é uma aplicação web criada com Flask que mostra previsões do tempo atuais, previsões para os próximos dias e análises climáticas. Ele utiliza a API gratuita do OpenWeatherMap para obter os dados meteorológicos. A aplicação foi desenvolvida como parte do trabalho da disciplina de Big Data.

## Estrutura do Projeto

O projeto está organizado da seguinte maneira:

```
.
├── app.py              # Arquivo principal que contém toda a lógica do programa
├── requirements.txt    # Lista de bibliotecas necessárias
├── static/             # Pasta com arquivos estáticos
│   └── style.css       # Estilos personalizados da aplicação
├── templates/          # Pasta com os arquivos HTML
│   ├── index.html      # Página inicial que mostra o clima atual e previsão
│   ├── insights.html   # Página que mostra análises e gráficos
│   └── error.html      # Página de erro
└── venv/               # Ambiente virtual Python (criado durante a instalação)
```

## Explicação do Código Principal (app.py)

Vou explicar as principais partes do arquivo `app.py`:

### 1. Importações e Configuração Inicial

```python
from flask import Flask, render_template, request, redirect, url_for, session
import requests
import datetime
import json
import os

app = Flask(__name__)
app.secret_key = 'clima_brasil_secret_key'
```

Nesta parte:
- Importamos as bibliotecas necessárias
- `Flask`: O framework web que estamos usando
- `requests`: Para fazer chamadas à API do OpenWeatherMap
- `datetime`: Para trabalhar com datas
- `json`: Para trabalhar com o formato JSON
- Criamos nossa aplicação Flask
- Definimos uma chave secreta para a sessão do usuário (para lembrar a última cidade pesquisada)

### 2. Função para obter dados do clima atual

```python
def get_weather_data(city=None, lat=None, lon=None):
    api_key = "96a82acf0b87dddd3bc26036f9125697"
    
    if city:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=pt_br"
    else:
        # Default para o Rio de Janeiro se não houver cidade ou coordenadas
        lat = lat if lat else -22.91
        lon = lon if lon else -43.17
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=pt_br"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        weather_data = {
            'cidade': data['name'],
            'pais': data.get('sys', {}).get('country', ''),
            'temperatura': round(data['main']['temp']),
            'sensacao': round(data['main']['feels_like']),
            'descricao': data['weather'][0]['description'],
            'icone': data['weather'][0]['icon'],
            'vento': data['wind']['speed'],
            'umidade': data['main']['humidity'],
            'pressao': data['main']['pressure'],
            'data_hora': datetime.datetime.now().strftime('%d/%m/%Y %H:%M'),
            'lat': data['coord']['lat'],
            'lon': data['coord']['lon']
        }
        return weather_data, None
    else:
        error_msg = "Cidade não encontrada. Tente novamente."
        if response.status_code == 404:
            error_msg = "Cidade não encontrada. Verifique o nome e tente novamente."
        elif response.status_code == 401:
            error_msg = "Erro de autenticação na API."
        return None, error_msg
```

Nesta função:
- Definimos o que acontece quando o usuário busca pelo clima de uma cidade
- Se o usuário digitar o nome de uma cidade, buscamos por esse nome
- Se não, usamos as coordenadas do Rio de Janeiro como padrão
- Fazemos uma requisição para a API do OpenWeatherMap usando a biblioteca requests
- Se a requisição for bem-sucedida, formatamos os dados de uma maneira que seja fácil usar no nosso site
- Se der erro, retornamos uma mensagem amigável explicando o problema

### 3. Função para obter previsão dos próximos dias

```python
def get_forecast_data(lat, lon):
    api_key = "96a82acf0b87dddd3bc26036f9125697"
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=pt_br"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        forecast_list = []
        
        # Filtrar uma previsão por dia (ao meio-dia)
        date_processed = set()
        
        for item in data['list']:
            dt = datetime.datetime.fromtimestamp(item['dt'])
            date_str = dt.strftime('%Y-%m-%d')
            
            # Pular se já tivermos essa data
            if date_str in date_processed:
                continue
                
            # Considerar apenas previsões para o meio-dia (em torno das 12:00)
            if 10 <= dt.hour <= 14:
                date_processed.add(date_str)
                
                forecast_list.append({
                    'data': dt.strftime('%d/%m'),
                    'dia_semana': dt.strftime('%a'),
                    'temperatura': round(item['main']['temp']),
                    'descricao': item['weather'][0]['description'],
                    'icone': item['weather'][0]['icon'],
                    'umidade': item['main']['humidity'],
                    'vento': item['wind']['speed']
                })
                
                # Limitar a 5 dias
                if len(forecast_list) >= 5:
                    break
        
        return forecast_list
    else:
        return []
```

Esta função:
- Busca a previsão do tempo para os próximos 5 dias
- A API retorna previsões para cada 3 horas, então precisamos filtrar
- Pegamos apenas uma previsão por dia, preferencialmente em torno do meio-dia
- Organizamos os dados para mostrar data, dia da semana, temperatura, descrição do clima, ícone, umidade e vento
- Se não conseguirmos obter os dados, retornamos uma lista vazia

### 4. Função para gerar dados históricos (simulados)

```python
def get_historical_data(lat, lon, city_name):
    # Esta função normalmente usaria a API de dados históricos
    # Como exemplo, estamos criando dados simulados para visualização
    
    # Ajustar dados de temperatura com base na latitude (simulado)
    temp_adjustment = 0
    if lat > 0:  # Hemisfério Norte
        temp_adjustment = min(lat * 0.2, 5)  # Ajuste de até 5 graus para norte
    else:  # Hemisfério Sul
        temp_adjustment = max(lat * 0.2, -5)  # Ajuste de até -5 graus para sul
    
    # Dados de temperatura média mensal (simulados com ajuste baseado na localização)
    monthly_temps = {
        'Jan': 30 + temp_adjustment, 
        'Fev': 29 + temp_adjustment, 
        'Mar': 28 + temp_adjustment, 
        'Abr': 26 + temp_adjustment,
        'Mai': 24 + temp_adjustment, 
        'Jun': 22 + temp_adjustment, 
        'Jul': 21 + temp_adjustment, 
        'Ago': 22 + temp_adjustment,
        'Set': 23 + temp_adjustment, 
        'Out': 25 + temp_adjustment, 
        'Nov': 27 + temp_adjustment, 
        'Dez': 29 + temp_adjustment
    }
    
    # ... (o resto da função que cria dados de precipitação, eventos extremos e impacto na agricultura)
    
    return {
        'monthly_temps': monthly_temps,
        'monthly_rainfall': monthly_rainfall,
        'extreme_events': local_events,
        'crop_impact': crop_impact
    }
```

Nesta função:
- Como não temos acesso gratuito aos dados históricos reais, criamos dados simulados
- Ajustamos as temperaturas baseadas na latitude (mais quente perto do equador, mais frio nos polos)
- Criamos dados diferentes para regiões tropicais, temperadas e polares
- Isso nos permite mostrar análises diferentes dependendo da localização da cidade pesquisada
- Em um ambiente real, esses dados viriam de uma API de dados históricos ou banco de dados

### 5. Rotas da Aplicação

```python
@app.route('/')
def index():
    # Verificar se há uma cidade armazenada na sessão
    city = session.get('last_city', None)
    
    if city:
        weather_data, error = get_weather_data(city=city)
    else:
        weather_data, error = get_weather_data()
    
    if error:
        return render_template('error.html', message=error)
    
    # Armazenar dados na sessão
    session['last_city'] = weather_data['cidade']
    session['last_lat'] = weather_data['lat']
    session['last_lon'] = weather_data['lon']
    
    forecast_data = get_forecast_data(weather_data['lat'], weather_data['lon'])
    return render_template('index.html', weather=weather_data, forecast=forecast_data)

@app.route('/buscar', methods=['POST'])
def buscar():
    city = request.form.get('cidade')
    if not city:
        return redirect(url_for('index'))
    
    weather_data, error = get_weather_data(city=city)
    if error:
        return render_template('error.html', message=error)
    
    # Armazenar dados na sessão
    session['last_city'] = weather_data['cidade']
    session['last_lat'] = weather_data['lat']
    session['last_lon'] = weather_data['lon']
    
    forecast_data = get_forecast_data(weather_data['lat'], weather_data['lon'])
    return render_template('index.html', weather=weather_data, forecast=forecast_data)

@app.route('/insights')
def insights():
    # Usar cidade da sessão ou default para Rio de Janeiro
    city = session.get('last_city', None)
    lat = session.get('last_lat', -22.91)
    lon = session.get('last_lon', -43.17)
    
    if city:
        weather_data, error = get_weather_data(city=city)
    else:
        weather_data, error = get_weather_data(lat=lat, lon=lon)
    
    if error:
        return render_template('error.html', message=error)
    
    historical_data = get_historical_data(weather_data['lat'], weather_data['lon'], weather_data['cidade'])
    
    # Converter dados para JSON para uso nos gráficos
    temp_data = json.dumps({
        'labels': list(historical_data['monthly_temps'].keys()),
        'values': list(historical_data['monthly_temps'].values())
    })
    
    rainfall_data = json.dumps({
        'labels': list(historical_data['monthly_rainfall'].keys()),
        'values': list(historical_data['monthly_rainfall'].values())
    })
    
    crop_impact_data = json.dumps(historical_data['crop_impact'])
    
    return render_template(
        'insights.html', 
        weather=weather_data,
        historical=historical_data,
        temp_data=temp_data,
        rainfall_data=rainfall_data,
        crop_impact_data=crop_impact_data
    )
```

Aqui definimos as diferentes páginas da nossa aplicação:

- **Rota '/'**: 
  - É a página inicial que mostra o clima atual 
  - Lembra a última cidade pesquisada usando sessão
  - Busca dados do clima atual e previsão para 5 dias
  - Renderiza o template index.html com esses dados

- **Rota '/buscar'**: 
  - Recebe o nome da cidade do formulário
  - Busca dados do clima para essa cidade
  - Salva a cidade na sessão para lembrar mais tarde
  - Mostra a página inicial com os dados da cidade pesquisada

- **Rota '/insights'**: 
  - Mostra a página de análises climáticas
  - Usa a cidade salva na sessão (ou Rio de Janeiro como padrão)
  - Gera dados históricos simulados adaptados à localização
  - Prepara os dados para os gráficos usando JSON
  - Renderiza o template insights.html com todas essas informações

## Templates HTML

### 1. index.html

Este é o arquivo HTML da página inicial. Ele tem:
- Um menu de navegação
- Um formulário para buscar cidades
- Um card que mostra o clima atual (temperatura, sensação térmica, vento, etc.)
- Cards para a previsão dos próximos 5 dias
- Um banner com link para a página de insights

Usamos o Jinja2 (um sistema de templates) para preencher os dados dinâmicos. Por exemplo, `{{ weather.temperatura }}` mostra a temperatura recebida da API.

### 2. insights.html

Este é o arquivo HTML da página de análises. Ele tem:
- Menu de navegação
- Gráficos de temperatura e precipitação usando Chart.js
- Uma tabela de eventos climáticos extremos
- Um gráfico de impacto do clima na agricultura
- Seção de "Atualizações em Breve"

Novamente, usamos Jinja2 para dados dinâmicos e JavaScript para criar os gráficos com os dados recebidos do backend.

## CSS (style.css)

O arquivo CSS contém todos os estilos personalizados para deixar nossa aplicação bonita:
- Cores de fundo e gradientes
- Formatação dos cards
- Estilos para os gráficos
- Efeitos de hover (quando o mouse passa por cima)
- Responsividade (para funcionar bem em celulares e computadores)

## Como Tudo Funciona Junto

1. O usuário abre a aplicação e vê o clima do Rio de Janeiro (padrão)
2. Ele pode pesquisar uma cidade no formulário
3. O Flask pega esse nome e envia para a API do OpenWeatherMap
4. A API retorna dados do clima atual e previsão
5. O Flask processa esses dados e os envia para o template HTML
6. O HTML mostra os dados de forma bonita e organizada
7. Se o usuário clicar em "Insights", o sistema usa a última cidade pesquisada
8. Na página de insights, os gráficos são gerados usando Chart.js e dados simulados

## Conceitos de Big Data Aplicados

Embora este seja um projeto de demonstração, ele ilustra vários conceitos de Big Data:

1. **Coleta de dados**: Obtemos dados de uma API externa (OpenWeatherMap)
2. **Processamento de dados**: Filtramos e transformamos os dados antes de exibi-los
3. **Análise de dados**: Criamos visualizações e insights a partir dos dados climáticos
4. **Visualização de dados**: Usamos gráficos interativos para mostrar tendências
5. **Tomada de decisão baseada em dados**: Mostramos como os dados climáticos afetam diferentes setores (ex: agricultura)

Em um ambiente real de Big Data, poderíamos:
- Armazenar dados históricos em um banco de dados NoSQL (como MongoDB ou Cassandra)
- Usar Apache Spark para processar grandes volumes de dados climáticos
- Implementar modelos de Machine Learning para previsões mais precisas
- Integrar com outras fontes de dados (satélites, estações meteorológicas, etc.)

## Melhorias Futuras

Este projeto poderia ser expandido com:
1. Integração com dados climáticos históricos reais
2. Sistema de alertas para eventos extremos
3. Análises mais detalhadas por região
4. Modelos de Machine Learning para previsões personalizadas
5. Mais visualizações interativas e comparativas 