from flask import Flask, render_template, request, redirect, url_for, session
import requests
import datetime
import json
import os
from geopy.geocoders import Nominatim
from dotenv import load_dotenv

load_dotenv()  # Carregar variáveis de ambiente do arquivo .env

app = Flask(__name__)
app.secret_key = 'clima_brasil_secret_key'  # Chave para sessão
API_KEY = os.getenv('OPENWEATHERMAP_API_KEY')

def buscar_localizacao(nome_lugar):
    geolocator = Nominatim(user_agent="clima_brasil")
    location = geolocator.geocode(nome_lugar)
    if location:
        return location.latitude, location.longitude, location.address
    return None, None, None

def get_weather_data(city=None, lat=None, lon=None):
    api_key = "96a82acf0b87dddd3bc26036f9125697"
    
    if city:
        # Tenta buscar coordenadas primeiro para melhorar a precisão
        lat_loc, lon_loc, address = buscar_localizacao(city)
        if lat_loc and lon_loc:
            lat = lat_loc
            lon = lon_loc
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=pt_br"
        else:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=pt_br"
    else:
        # Default to Rio de Janeiro if no city or coordinates provided
        lat = lat if lat else -22.91
        lon = lon if lon else -43.17
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=pt_br"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        # Extract relevant weather data
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

def get_forecast_data(lat, lon):
    api_key = "96a82acf0b87dddd3bc26036f9125697"
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=pt_br"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        forecast_list = []
        
        # Filter one forecast per day (at noon)
        date_processed = set()
        
        for item in data['list']:
            dt = datetime.datetime.fromtimestamp(item['dt'])
            date_str = dt.strftime('%Y-%m-%d')
            
            # Skip if we already have this date
            if date_str in date_processed:
                continue
                
            # Only consider forecasts for noon (around 12:00)
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
                
                # Limit to 5 days
                if len(forecast_list) >= 5:
                    break
        
        return forecast_list
    else:
        return []

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
    
    # Ajustar dados de precipitação com base na latitude (simulado)
    rain_multiplier = 1.0
    if abs(lat) < 10:  # Região equatorial - mais chuva
        rain_multiplier = 1.3
    elif abs(lat) > 40:  # Regiões mais ao norte/sul - menos chuva
        rain_multiplier = 0.7
    
    # Dados de precipitação média mensal (mm) (simulados)
    monthly_rainfall = {
        'Jan': int(137 * rain_multiplier), 
        'Fev': int(130 * rain_multiplier), 
        'Mar': int(136 * rain_multiplier), 
        'Abr': int(95 * rain_multiplier),
        'Mai': int(70 * rain_multiplier), 
        'Jun': int(56 * rain_multiplier), 
        'Jul': int(52 * rain_multiplier), 
        'Ago': int(50 * rain_multiplier),
        'Set': int(65 * rain_multiplier), 
        'Out': int(88 * rain_multiplier), 
        'Nov': int(106 * rain_multiplier), 
        'Dez': int(134 * rain_multiplier)
    }
    
    # Eventos extremos simulados nos últimos anos
    # Ajuste baseado na localização
    local_events = []
    
    if abs(lat) < 15:  # Região tropical
        local_events = [
            {'ano': 2023, 'evento': 'Onda de calor', 'temperatura': 42, 'impacto': 'Alto'},
            {'ano': 2022, 'evento': 'Chuvas intensas', 'precipitacao': 325, 'impacto': 'Severo'},
            {'ano': 2021, 'evento': 'Seca prolongada', 'duracao': '3 meses', 'impacto': 'Moderado'},
            {'ano': 2020, 'evento': 'Tempestades', 'precipitacao': 280, 'impacto': 'Alto'},
            {'ano': 2019, 'evento': 'Inundações', 'nivel_agua': '2.5m acima do normal', 'impacto': 'Severo'}
        ]
    elif 15 <= abs(lat) <= 35:  # Região subtropical/temperada
        local_events = [
            {'ano': 2023, 'evento': 'Tempestade severa', 'precipitacao': 180, 'impacto': 'Alto'},
            {'ano': 2022, 'evento': 'Ondas de calor', 'temperatura': 39, 'impacto': 'Moderado'},
            {'ano': 2021, 'evento': 'Granizo', 'precipitacao': 40, 'impacto': 'Alto'},
            {'ano': 2020, 'evento': 'Seca', 'duracao': '2 meses', 'impacto': 'Moderado'},
            {'ano': 2019, 'evento': 'Enchentes', 'nivel_agua': '1.8m acima do normal', 'impacto': 'Alto'}
        ]
    else:  # Região temperada/polar
        local_events = [
            {'ano': 2023, 'evento': 'Nevascas', 'precipitacao': 120, 'impacto': 'Alto'},
            {'ano': 2022, 'evento': 'Ondas de frio', 'temperatura': -25, 'impacto': 'Severo'},
            {'ano': 2021, 'evento': 'Tempestades de gelo', 'precipitacao': 40, 'impacto': 'Severo'},
            {'ano': 2020, 'evento': 'Verão atípico', 'temperatura': 32, 'impacto': 'Moderado'},
            {'ano': 2019, 'evento': 'Chuvas fora de época', 'precipitacao': 150, 'impacto': 'Moderado'}
        ]
    
    # Culturas típicas e impactos baseados na região
    if abs(lat) < 15:  # Região tropical
        crop_impact = {
            'Café': {'temp_alta': -20, 'seca': -30, 'chuva_intensa': -15},
            'Cana-de-açúcar': {'temp_alta': -5, 'seca': -25, 'chuva_intensa': -10},
            'Banana': {'temp_alta': -10, 'seca': -35, 'chuva_intensa': -25},
            'Arroz': {'temp_alta': -15, 'seca': -40, 'chuva_intensa': -5},
            'Manga': {'temp_alta': -8, 'seca': -20, 'chuva_intensa': -30}
        }
    elif 15 <= abs(lat) <= 35:  # Região subtropical/temperada
        crop_impact = {
            'Soja': {'temp_alta': -15, 'seca': -35, 'chuva_intensa': -20},
            'Milho': {'temp_alta': -25, 'seca': -40, 'chuva_intensa': -10},
            'Trigo': {'temp_alta': -30, 'seca': -25, 'chuva_intensa': -35},
            'Laranja': {'temp_alta': -10, 'seca': -20, 'chuva_intensa': -15},
            'Uva': {'temp_alta': -20, 'seca': -15, 'chuva_intensa': -30}
        }
    else:  # Região temperada/polar
        crop_impact = {
            'Trigo': {'temp_alta': -5, 'seca': -25, 'chuva_intensa': -35},
            'Cevada': {'temp_alta': -10, 'seca': -30, 'chuva_intensa': -40},
            'Batata': {'temp_alta': -20, 'seca': -35, 'chuva_intensa': -25},
            'Centeio': {'temp_alta': -15, 'seca': -30, 'chuva_intensa': -20},
            'Beterraba': {'temp_alta': -25, 'seca': -15, 'chuva_intensa': -30}
        }
    
    return {
        'monthly_temps': monthly_temps,
        'monthly_rainfall': monthly_rainfall,
        'extreme_events': local_events,
        'crop_impact': crop_impact
    }

# Função para traduzir cidade para inglês (versão simplificada)
def traduzir_para_ingles(texto):
    # Dicionário de traduções comuns para cidades brasileiras
    traducoes = {
        'são paulo': 'sao paulo',
        'rio de janeiro': 'rio de janeiro',
        'brasília': 'brasilia',
        'salvador': 'salvador',
        'fortaleza': 'fortaleza',
        'belo horizonte': 'belo horizonte',
        'manaus': 'manaus',
        'curitiba': 'curitiba',
        'recife': 'recife',
        'porto alegre': 'porto alegre',
        'belém': 'belem',
        'goiânia': 'goiania',
        'florianópolis': 'florianopolis',
        'cuiabá': 'cuiaba',
        'joão pessoa': 'joao pessoa',
        'são luís': 'sao luis',
        'maceió': 'maceio',
        'campo grande': 'campo grande',
        'teresina': 'teresina',
        'natal': 'natal'
    }
    
    # Verificar se a cidade está no dicionário
    texto_lower = texto.lower()
    if texto_lower in traducoes:
        return traducoes[texto_lower]
    
    # Se não estiver no dicionário, retorna o texto original
    # sem acentos para melhor compatibilidade com APIs
    import unicodedata
    texto_sem_acentos = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    return texto_sem_acentos

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

@app.route('/mapa')
def mapa():
    cidade = request.args.get('cidade', 'Brasília')  # Cidade padrão: Brasília
    
    # Traduzir a cidade para inglês para melhor precisão na API
    cidade_en = traduzir_para_ingles(cidade)
    
    url = f'https://api.openweathermap.org/data/2.5/weather?q={cidade_en}&units=metric&lang=pt_br&appid={API_KEY}'
    
    response = requests.get(url)
    data = response.json()
    
    # Verificar se a API retornou dados válidos
    if response.status_code != 200:
        return render_template('error.html', message='Cidade não encontrada. Tente novamente.')
    
    # Extrair dados do clima
    weather = {
        'cidade': data['name'],
        'pais': data.get('sys', {}).get('country', ''),
        'temperatura': round(data['main']['temp']),
        'sensacao': round(data['main']['feels_like']),
        'minima': round(data['main']['temp_min']),
        'maxima': round(data['main']['temp_max']),
        'pressao': data['main']['pressure'],
        'umidade': data['main']['humidity'],
        'vento': data['wind']['speed'],
        'descricao': data['weather'][0]['description'],
        'icone': data['weather'][0]['icon'],
        'lat': data['coord']['lat'],
        'lon': data['coord']['lon']
    }
    
    return render_template('mapa.html', weather=weather)

@app.route('/abrir_mapa')
def abrir_mapa():
    # Obter a cidade selecionada da query string (se existir)
    cidade = request.args.get('cidade', 'Brasília')
    
    # Buscar informações da cidade para obter coordenadas
    url = f'https://api.openweathermap.org/data/2.5/weather?q={cidade}&units=metric&lang=pt_br&appid={API_KEY}'
    response = requests.get(url)
    
    if response.status_code != 200:
        return redirect(url_for('mapa', cidade=cidade))
    
    data = response.json()
    lat = data['coord']['lat']
    lon = data['coord']['lon']
    
    # Criar URL para o Google Maps
    url = f'https://www.google.com/maps/search/?api=1&query={lat},{lon}'
    
    # Redirecionar para o Google Maps
    return redirect(url)

@app.route('/mapa_externo')
def mapa_externo():
    """Abre o Google Maps diretamente com a localização atual"""
    # Obter coordenadas da sessão ou usar valores padrão
    lat = request.args.get('lat') or session.get('last_lat', -22.91)
    lon = request.args.get('lon') or session.get('last_lon', -43.17)
    
    # Construir a URL para o Google Maps
    url = f"https://www.google.com/maps/@{lat},{lon},15z"
    
    # Redirecionar para a URL externa
    return redirect(url)

@app.route('/desastres_naturais')
def desastres_naturais():
    # Implementação para buscar dados reais do IBGE
    # Como exemplo, estamos usando dados simulados
    
    # IBGE não possui API específica para desastres naturais, então usamos dados simulados
    # Em um projeto real, você poderia fazer scraping das páginas do IBGE ou usar outras fontes
    desastres = [
        {
            'tipo': 'Inundação',
            'local': 'Rio Grande do Sul',
            'data': 'Mai/2023',
            'pessoas_afetadas': '400.000+',
            'badge_class': 'primary',
            'detalhes': 'Grande inundação que afetou mais de 400 mil pessoas no RS em 2023.'
        },
        {
            'tipo': 'Deslizamento',
            'local': 'Petrópolis, RJ',
            'data': 'Fev/2022',
            'pessoas_afetadas': '25.000+',
            'badge_class': 'danger',
            'detalhes': 'Deslizamentos de terra em Petrópolis/RJ devido às chuvas intensas.'
        },
        {
            'tipo': 'Seca',
            'local': 'Nordeste',
            'data': '2022-2023',
            'pessoas_afetadas': '10.000.000+',
            'badge_class': 'warning',
            'detalhes': 'Seca prolongada afetando a região Nordeste, impactando a agricultura e o abastecimento de água.'
        },
        {
            'tipo': 'Incêndio',
            'local': 'Pantanal',
            'data': 'Jul-Out/2020',
            'pessoas_afetadas': '3.400.000+ ha',
            'badge_class': 'danger',
            'detalhes': 'Grandes incêndios no Pantanal destruíram mais de 3,4 milhões de hectares.'
        },
        {
            'tipo': 'Inundação',
            'local': 'Bahia',
            'data': 'Dez/2021',
            'pessoas_afetadas': '500.000+',
            'badge_class': 'primary',
            'detalhes': 'Fortes chuvas causaram inundações em diversas cidades da Bahia.'
        }
    ]
    
    # Lista de estados brasileiros para o filtro
    estados = [
        "Acre", "Alagoas", "Amapá", "Amazonas", "Bahia", "Ceará", "Distrito Federal",
        "Espírito Santo", "Goiás", "Maranhão", "Mato Grosso", "Mato Grosso do Sul",
        "Minas Gerais", "Pará", "Paraíba", "Paraná", "Pernambuco", "Piauí",
        "Rio de Janeiro", "Rio Grande do Norte", "Rio Grande do Sul", "Rondônia",
        "Roraima", "Santa Catarina", "São Paulo", "Sergipe", "Tocantins"
    ]
    
    # Lista de tipos de desastres para o filtro
    tipos_desastres = [
        "Todos", "Inundações", "Deslizamentos", "Secas", "Incêndios"
    ]
    
    # Em um projeto real, aqui você buscaria dados da API do IBGE ou de uma fonte apropriada
    
    return render_template('desastres_naturais.html', 
                           desastres=desastres, 
                           estados=estados,
                           tipos_desastres=tipos_desastres)

@app.route('/sobre')
def sobre():
    # Rota para página de informações sobre a equipe
    return render_template('sobre.html')

if __name__ == '__main__':
    app.run(debug=True) 