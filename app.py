from flask import Flask, render_template, request, redirect, url_for, session
import requests
import datetime
import json
import os
import unicodedata
from geopy.geocoders import Nominatim
from dotenv import load_dotenv

load_dotenv()  # Carregar variáveis de ambiente do arquivo .env

app = Flask(__name__)
app.secret_key = 'clima_brasil_secret_key'  # Chave para sessão
API_KEY = os.getenv('OPENWEATHERMAP_API_KEY') or "96a82acf0b87dddd3bc26036f9125697"  # Usar a chave padrão se não encontrar no .env

def remover_acentos(texto):
    """Remove acentos de um texto"""
    try:
        # Unicode normalize transforma um caracter em seu equivalente sem acento
        texto_sem_acentos = unicodedata.normalize('NFD', texto)
        texto_sem_acentos = ''.join(c for c in texto_sem_acentos if unicodedata.category(c) != 'Mn')
        return texto_sem_acentos
    except Exception as e:
        app.logger.error(f"Erro ao remover acentos: {str(e)}")
        return texto  # Retorna o texto original em caso de erro

def formatar_nome_cidade(cidade):
    """Formata o nome da cidade para exibição, aplicando regras básicas de formatação"""
    # Dicionário com traduções comuns
    traducoes = {
        'sao paulo': 'São Paulo',
        'rio de janeiro': 'Rio de Janeiro',
        'brasilia': 'Brasília',
        'belem': 'Belém',
        'curitiba': 'Curitiba',
        'recife': 'Recife',
        'porto alegre': 'Porto Alegre',
        'belo horizonte': 'Belo Horizonte',
        'fortaleza': 'Fortaleza',
        'salvador': 'Salvador',
        'manaus': 'Manaus',
        'joao pessoa': 'João Pessoa',
        'maceio': 'Maceió',
        'florianopolis': 'Florianópolis',
        'goiania': 'Goiânia',
        'sao luis': 'São Luís',
        'cuiaba': 'Cuiabá'
        # Adicione mais cidades brasileiras comuns conforme necessário
    }
    
    # Verificar se a cidade está no dicionário
    cidade_lower = cidade.lower()
    if cidade_lower in traducoes:
        return traducoes[cidade_lower]
    
    # Se não estiver no dicionário, aplica formatações básicas
    # Capitaliza cada palavra
    palavras = cidade.split()
    palavras_formatadas = []
    
    for palavra in palavras:
        # Preposições e artigos comuns permanecem em minúsculas
        if palavra.lower() in ['de', 'da', 'do', 'das', 'dos', 'e']:
            palavras_formatadas.append(palavra.lower())
        else:
            palavras_formatadas.append(palavra.capitalize())
    
    return ' '.join(palavras_formatadas)

def buscar_localizacao(nome_lugar):
    """Busca as coordenadas de um lugar usando o Nominatim"""
    # Lista de cidades da região metropolitana do RJ que podem ser ambíguas
    cidades_rj = [
        'Mesquita', 'Nova Iguaçu', 'Duque de Caxias', 'Belford Roxo', 'São João de Meriti',
        'Nilópolis', 'Magé', 'Itaguaí', 'Japeri', 'Queimados', 'Seropédica', 'Paracambi'
    ]
    
    # Verificar se o nome do lugar é uma das cidades que precisam de especificação
    nome_lugar_lower = nome_lugar.lower().strip()
    for cidade in cidades_rj:
        if cidade.lower() == nome_lugar_lower or f"{cidade.lower()}" == nome_lugar_lower:
            # Adicionar ", RJ" ao nome para melhorar a precisão
            nome_lugar = f"{nome_lugar}, Rio de Janeiro, Brasil"
            app.logger.info(f"Nome ajustado para: {nome_lugar}")
            break
    
    # Se o nome do lugar não contém Brasil ou RJ, verificar se é uma cidade brasileira
    if ", brasil" not in nome_lugar_lower and "brazil" not in nome_lugar_lower and ", rj" not in nome_lugar_lower and "rio de janeiro" not in nome_lugar_lower:
        # Verificar se é um nome de cidade ou estado brasileiro comum
        cidades_estados_br = [
            'São Paulo', 'Rio de Janeiro', 'Brasília', 'Salvador', 'Fortaleza', 
            'Belo Horizonte', 'Manaus', 'Curitiba', 'Recife', 'Goiânia', 'Porto Alegre',
            'Belém', 'Guarulhos', 'Campinas', 'São Luís', 'Maceió', 'Natal', 'Teresina',
            'Campo Grande', 'João Pessoa', 'Ribeirão Preto', 'Uberlândia', 'Contagem',
            'Sorocaba', 'Aracaju', 'Feira de Santana', 'Cuiabá', 'Joinville', 'Juiz de Fora',
            'Florianópolis', 'Paraná', 'Minas Gerais', 'Bahia', 'Santa Catarina', 'Acre',
            'Alagoas', 'Amapá', 'Amazonas', 'Ceará', 'Distrito Federal', 'Espírito Santo',
            'Goiás', 'Maranhão', 'Mato Grosso', 'Pará', 'Paraíba', 'Pernambuco',
            'Piauí', 'Rio Grande do Norte', 'Rio Grande do Sul', 'Rondônia',
            'Roraima', 'Sergipe', 'Tocantins'
        ]
        
        for cidade_estado in cidades_estados_br:
            if cidade_estado.lower() in nome_lugar_lower:
                # Adicionar Brasil ao nome para melhorar a precisão
                nome_lugar = f"{nome_lugar}, Brasil"
                app.logger.info(f"Adicionado Brasil ao nome: {nome_lugar}")
                break
    
    geolocator = Nominatim(user_agent="clima_brasil")
    
    try:
        # Primeiro tenta com o nome modificado para maior precisão
        location = geolocator.geocode(nome_lugar, exactly_one=True)
        
        if location:
            app.logger.info(f"Localização encontrada: {location.address}")
            return location.latitude, location.longitude, location.address
        
        # Se não encontrar, tenta novamente forçando a busca no Brasil
        if ", brasil" not in nome_lugar_lower and "brazil" not in nome_lugar_lower:
            location = geolocator.geocode(f"{nome_lugar}, Brasil", exactly_one=True)
            if location:
                app.logger.info(f"Localização encontrada com 'Brasil': {location.address}")
                return location.latitude, location.longitude, location.address
        
        # Última tentativa: especificar ainda mais para cidades ambíguas
        for cidade in cidades_rj:
            if cidade.lower() in nome_lugar_lower:
                location = geolocator.geocode(f"{cidade}, Baixada Fluminense, Rio de Janeiro, Brasil", exactly_one=True)
                if location:
                    app.logger.info(f"Localização encontrada com Baixada Fluminense: {location.address}")
                    return location.latitude, location.longitude, location.address
        
        app.logger.warning(f"Localização não encontrada para: {nome_lugar}")
        return None, None, None
    except Exception as e:
        app.logger.error(f"Erro ao buscar localização: {str(e)}")
        return None, None, None

def get_weather_data(city=None, lat=None, lon=None):
    api_key = API_KEY  # Usar a chave definida no topo do arquivo
    
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
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            # Extract relevant weather data
            weather_data = {
                'cidade': formatar_nome_cidade(data['name']),  # Formata o nome da cidade para exibição
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
            # Adicionar temperatura máxima e mínima se disponíveis
            if 'temp_max' in data['main']:
                weather_data['temp_max'] = round(data['main']['temp_max'])
            if 'temp_min' in data['main']:
                weather_data['temp_min'] = round(data['main']['temp_min'])
            
            return weather_data, None
        else:
            error_msg = "Cidade não encontrada. Tente novamente."
            if response.status_code == 404:
                error_msg = "Cidade não encontrada. Verifique o nome e tente novamente."
            elif response.status_code == 401:
                app.logger.error(f"Erro de autenticação na API. Verifique a chave API_KEY.")
                error_msg = "Erro de autenticação na API."
            
            app.logger.error(f"Erro na API do OpenWeatherMap: {response.status_code}")
            return None, error_msg
    except Exception as e:
        app.logger.error(f"Erro ao obter dados do clima: {e}")
        return None, "Erro ao conectar ao serviço meteorológico. Tente novamente mais tarde."

def get_forecast_data(lat, lon):
    """
    Obtém os dados de previsão do tempo para os próximos dias com base na latitude e longitude.
    """
    try:
        api_key = API_KEY  # Usar a chave definida no topo do arquivo
        
        # URL da API de previsão do OpenWeatherMap
        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&lang=pt_br&appid={api_key}"
        response = requests.get(url)
        
        if response.status_code != 200:
            app.logger.error(f"Erro na API de previsão: {response.status_code}")
            return None
            
        data = response.json()
        
        # Processar e organizar os dados de previsão
        forecast_list = []
        date_processed = set()
        
        for item in data['list']:
            # Converter timestamp para objeto datetime
            dt = datetime.datetime.fromtimestamp(item['dt'])
            date_str = dt.strftime('%Y-%m-%d')
            
            # Pegar apenas uma previsão por dia (ao meio-dia)
            if date_str in date_processed or dt.hour != 12:
                continue
                
            date_processed.add(date_str)
            
            # Tradução dos dias da semana
            dia_semana = dt.strftime('%A')
            traducoes_dia = {
                'Monday': 'Segunda-feira', 
                'Tuesday': 'Terça-feira', 
                'Wednesday': 'Quarta-feira',
                'Thursday': 'Quinta-feira', 
                'Friday': 'Sexta-feira', 
                'Saturday': 'Sábado', 
                'Sunday': 'Domingo'
            }
            dia_semana_pt = traducoes_dia.get(dia_semana, dia_semana)
            
            forecast_day = {
                'data': dt.strftime('%d/%m/%Y'),
                'dia_semana': dia_semana_pt,
                'temp_max': round(item['main']['temp_max']),
                'temp_min': round(item['main']['temp_min']),
                'descricao': item['weather'][0]['description'],
                'icone': item['weather'][0]['icon'],
                'umidade': item['main']['humidity'],
                'vento': round(item['wind']['speed'])
            }
            
            forecast_list.append(forecast_day)
            
            # Limitar a 5 dias
            if len(forecast_list) >= 5:
                break
                
        return forecast_list
    except Exception as e:
        app.logger.error(f"Erro ao obter dados de previsão: {e}")
        return None

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
    
    # Eventos históricos por cidade (simulados)
    eventos_historicos = {
        'Rio de Janeiro': [
            {'ano': 2011, 'evento': 'Enchentes e deslizamentos na região serrana', 'vitimas': '900+', 'impacto': 'Severo'},
            {'ano': 2019, 'evento': 'Chuvas de verão recordes', 'precipitacao': '400mm', 'impacto': 'Alto'},
            {'ano': 2010, 'evento': 'Fortes chuvas', 'danos': 'Desabamentos em favelas', 'impacto': 'Alto'},
        ],
        'São Paulo': [
            {'ano': 2021, 'evento': 'Crise hídrica', 'duracao': '8 meses', 'impacto': 'Alto'},
            {'ano': 2019, 'evento': 'Tempestade severa', 'danos': 'Quedas de árvores e alagamentos', 'impacto': 'Moderado'},
            {'ano': 2015, 'evento': 'Escassez de água', 'detalhe': 'Rodízio no abastecimento', 'impacto': 'Severo'},
        ],
        'Manaus': [
            {'ano': 2021, 'evento': 'Cheia histórica do Rio Negro', 'nivel': '30m acima do normal', 'impacto': 'Severo'},
            {'ano': 2012, 'evento': 'Inundação recorde', 'danos': 'Bairros submersos', 'impacto': 'Alto'},
            {'ano': 2009, 'evento': 'Seca extrema na Amazônia', 'duracao': '3 meses', 'impacto': 'Alto'},
        ],
        'Recife': [
            {'ano': 2022, 'evento': 'Enchentes e deslizamentos', 'vitimas': '120+', 'impacto': 'Severo'},
            {'ano': 2017, 'evento': 'Alagamentos', 'danos': 'Bairros inteiros afetados', 'impacto': 'Alto'},
            {'ano': 2010, 'evento': 'Erosão costeira', 'detalhe': 'Destruição de orla', 'impacto': 'Moderado'},
        ],
        'Porto Alegre': [
            {'ano': 2023, 'evento': 'Inundações históricas', 'nivel': 'Rio Guaíba 5m acima', 'impacto': 'Severo'},
            {'ano': 2015, 'evento': 'Enchentes', 'danos': 'Centro histórico afetado', 'impacto': 'Alto'},
            {'ano': 2005, 'evento': 'Fortes chuvas', 'precipitacao': '300mm em 48h', 'impacto': 'Alto'},
        ],
        'Brasília': [
            {'ano': 2023, 'evento': 'Seca prolongada', 'duracao': '5 meses', 'impacto': 'Alto'},
            {'ano': 2017, 'evento': 'Crise hídrica', 'detalhe': 'Racionamento de água', 'impacto': 'Severo'},
            {'ano': 2014, 'evento': 'Baixa umidade do ar', 'nivel': 'Abaixo de 12%', 'impacto': 'Moderado'},
        ],
    }
    
    # Obter eventos específicos para a cidade, ou usar genéricos baseados na latitude
    city_historical_events = eventos_historicos.get(city_name, [])
    # Se não houver eventos específicos, usar os eventos genéricos baseados na latitude
    if not city_historical_events:
        city_historical_events = local_events
    
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
        'city_historical_events': city_historical_events,
        'crop_impact': crop_impact
    }

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
    if request.method == 'POST':
        cidade = request.form.get('cidade', '')
        if not cidade:
            return render_template('index.html', error="Por favor, digite o nome da cidade.")
        
        try:
            # Obter dados do clima
            weather_data, error = get_weather_data(city=cidade)
            
            if error:
                # Se houver erro, volta para a página inicial com mensagem de erro
                return render_template('index.html', error=error)
            
            # Armazenar dados na sessão para uso em outras rotas
            session['weather_data'] = weather_data
            
            # Armazenar última cidade e coordenadas para uso futuro
            session['last_city'] = weather_data['cidade']
            session['last_lat'] = weather_data['lat']
            session['last_lon'] = weather_data['lon']
            
            # Obter previsão do tempo
            forecast_data = get_forecast_data(weather_data['lat'], weather_data['lon'])
            
            # Renderizar diretamente a página index com os dados obtidos
            return render_template('index.html', weather=weather_data, forecast=forecast_data)
        except Exception as e:
            # Tratar erros inesperados
            app.logger.error(f"Erro ao buscar dados do clima: {str(e)}")
            return render_template('index.html', error="Ocorreu um erro ao processar sua solicitação. Tente novamente.")

@app.route('/insights')
def insights():
    try:
        # Verificar se temos uma nova busca sendo feita através de um parâmetro de URL
        cidade_pesquisada = request.args.get('cidade', None)
        
        if cidade_pesquisada:
            # Se temos uma nova pesquisa, verificar se é uma cidade do RJ que precisa de especificação
            cidades_rj = [
                'Mesquita', 'Nova Iguaçu', 'Duque de Caxias', 'Belford Roxo', 'São João de Meriti',
                'Nilópolis', 'Magé', 'Itaguaí', 'Japeri', 'Queimados', 'Seropédica', 'Paracambi'
            ]
            
            cidade_lower = cidade_pesquisada.lower().strip()
            cidade_especificada = cidade_pesquisada
            
            for cidade_rj in cidades_rj:
                if cidade_rj.lower() == cidade_lower:
                    cidade_especificada = f"{cidade_pesquisada}, Rio de Janeiro"
                    app.logger.info(f"Especificando cidade do RJ para insights: {cidade_especificada}")
                    break
            
            # Buscar os dados desta cidade com a especificação adequada
            app.logger.info(f"Nova pesquisa de insights para: {cidade_especificada}")
            weather_data, error = get_weather_data(city=cidade_especificada)
            if not error:
                # Armazenar na sessão apenas se não houver erro
                session['last_city'] = weather_data['cidade']
                session['last_lat'] = weather_data['lat']
                session['last_lon'] = weather_data['lon']
        else:
            # Usar cidade da sessão ou default para Rio de Janeiro
            cidade_pesquisada = session.get('last_city', 'Rio de Janeiro')
            lat = session.get('last_lat', -22.91)
            lon = session.get('last_lon', -43.17)
            
            if cidade_pesquisada:
                weather_data, error = get_weather_data(city=cidade_pesquisada)
            else:
                weather_data, error = get_weather_data(lat=lat, lon=lon)
        
        if error:
            app.logger.warning(f"Erro ao obter dados para insights: {error}. Usando cidade padrão.")
            # Em caso de erro, usar dados padrão para Rio de Janeiro
            weather_data = {
                'cidade': cidade_pesquisada or 'Rio de Janeiro',
                'pais': 'BR',
                'temperatura': 28,
                'sensacao': 30,
                'descricao': 'céu limpo',
                'icone': '01d',
                'vento': 3.5,
                'umidade': 70,
                'pressao': 1012,
                'data_hora': datetime.datetime.now().strftime('%d/%m/%Y %H:%M'),
                'lat': -22.91,
                'lon': -43.17
            }
        
        # Obter dados históricos específicos da região
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
        
        # Obter dados do mapa (uso da mesma função da rota do mapa)
        try:
            map_data = get_map_data(weather_data['cidade'], weather_data['lat'], weather_data['lon'])
        except Exception as e:
            app.logger.error(f"Erro ao obter dados do mapa: {e}")
            map_data = {
                'lat': weather_data['lat'],
                'lon': weather_data['lon'],
                'temperatura': weather_data['temperatura'],
                'descricao': weather_data['descricao'],
                'icone': weather_data['icone']
            }
        
        # Obter desastres naturais ESPECIFICAMENTE para a região pesquisada
        desastres = obter_desastres_por_regiao(weather_data['cidade'])
        
        return render_template(
            'insights.html', 
            weather=weather_data,
            historical=historical_data,
            temp_data=temp_data,
            rainfall_data=rainfall_data,
            crop_impact_data=crop_impact_data,
            map_data=map_data,
            desastres=desastres,
            cidade_pesquisada=weather_data['cidade']  # Garantir que temos a cidade pesquisada
        )
    except Exception as e:
        app.logger.error(f"Erro não tratado na rota insights: {e}")
        # Em caso de erro, mostrar uma mensagem de erro
        return render_template('error.html', message="Ocorreu um erro ao carregar os insights climáticos. Por favor, tente novamente mais tarde.")

def get_map_data(cidade, lat, lon):
    """Função auxiliar para obter dados formatados para o mapa"""
    try:
        # Tentar buscar dados atualizados
        weather_data, error = get_weather_data(city=cidade)
        
        if error:
            # Se houver erro, usar os dados de latitude e longitude fornecidos
            return {
                'cidade': cidade,
                'lat': lat,
                'lon': lon,
                'temperatura': 25,  # Valor padrão
                'descricao': 'céu limpo',
                'icone': '01d'
            }
        
        return {
            'cidade': weather_data['cidade'],
            'lat': weather_data['lat'],
            'lon': weather_data['lon'],
            'temperatura': weather_data['temperatura'],
            'descricao': weather_data['descricao'],
            'icone': weather_data['icone'],
            'umidade': weather_data['umidade'],
            'vento': weather_data['vento'],
            'pais': weather_data.get('pais', 'BR')
        }
    except Exception as e:
        app.logger.error(f"Erro ao obter dados para mapa: {e}")
        return {
            'cidade': cidade,
            'lat': lat,
            'lon': lon,
            'temperatura': 25,
            'descricao': 'céu limpo',
            'icone': '01d'
        }

def obter_desastres_por_regiao(cidade):
    """Obtém desastres naturais específicos para a região pesquisada"""
    app.logger.info(f"Buscando desastres para cidade: {cidade}")
    
    # Primeira tentativa: buscar desastres específicos para a cidade
    desastres_por_cidade = {
        "Belford Roxo": [
            {
                'tipo': 'Inundação',
                'local': 'Belford Roxo, RJ',
                'data': 'Jan/2023',
                'pessoas_afetadas': '15.000+',
                'badge_class': 'primary',
                'detalhes': 'Fortes chuvas causaram alagamentos em diversos bairros de Belford Roxo, afetando principalmente áreas próximas ao Rio Botas.'
            },
            {
                'tipo': 'Inundação',
                'local': 'Belford Roxo, RJ',
                'data': 'Dez/2020',
                'pessoas_afetadas': '8.000+',
                'badge_class': 'primary',
                'detalhes': 'Transbordamento do Rio Botas após chuvas intensas, afetando principalmente os bairros de São Bernardo e Lote XV.'
            },
            {
                'tipo': 'Deslizamento',
                'local': 'Morro do Murundu, Belford Roxo',
                'data': 'Jan/2022',
                'pessoas_afetadas': '200+',
                'badge_class': 'danger',
                'detalhes': 'Deslizamento de terra em área de encosta, resultando em desalojamento de diversas famílias.'
            }
        ],
        "Nova Iguaçu": [
            {
                'tipo': 'Inundação',
                'local': 'Nova Iguaçu, RJ',
                'data': 'Jan/2023',
                'pessoas_afetadas': '20.000+',
                'badge_class': 'primary',
                'detalhes': 'Enchentes em diversos bairros de Nova Iguaçu após fortes chuvas, com o transbordamento do Rio Botas e Rio Iguaçu.'
            },
            {
                'tipo': 'Deslizamento',
                'local': 'Morro da Boa Esperança, Nova Iguaçu',
                'data': 'Fev/2022',
                'pessoas_afetadas': '150+',
                'badge_class': 'danger',
                'detalhes': 'Deslizamento de terra em área residencial após período de chuvas intensas.'
            }
        ],
        "Rio de Janeiro": [
            {
                'tipo': 'Deslizamento',
                'local': 'Rocinha, Rio de Janeiro',
                'data': 'Abr/2023',
                'pessoas_afetadas': '500+',
                'badge_class': 'danger',
                'detalhes': 'Deslizamentos de terra na comunidade da Rocinha após chuvas torrenciais, afetando centenas de famílias.'
            },
            {
                'tipo': 'Inundação',
                'local': 'Zona Norte, Rio de Janeiro',
                'data': 'Jan/2023',
                'pessoas_afetadas': '30.000+',
                'badge_class': 'primary',
                'detalhes': 'Alagamentos severos em bairros da Zona Norte como Madureira, Irajá e Pavuna após fortes chuvas.'
            },
            {
                'tipo': 'Deslizamento',
                'local': 'Morro do Borel, Rio de Janeiro',
                'data': 'Fev/2022',
                'pessoas_afetadas': '300+',
                'badge_class': 'danger',
                'detalhes': 'Deslizamento que atingiu várias casas na comunidade do Borel, na Tijuca.'
            }
        ],
        "Maricá": [
            {
                'tipo': 'Inundação',
                'local': 'Maricá, RJ',
                'data': 'Jan/2023',
                'pessoas_afetadas': '5.000+',
                'badge_class': 'primary',
                'detalhes': 'Fortes chuvas causaram alagamentos em diversos bairros de Maricá, afetando principalmente áreas próximas à lagoa.'
            },
            {
                'tipo': 'Erosão Costeira',
                'local': 'Praias de Maricá, RJ',
                'data': '2020-2023',
                'pessoas_afetadas': 'Indeterminado',
                'badge_class': 'warning',
                'detalhes': 'Processo contínuo de erosão nas praias de Maricá, afetando moradores e comércio local.'
            }
        ],
        "Mesquita": [
            {
                'tipo': 'Inundação',
                'local': 'Mesquita, RJ',
                'data': 'Jan/2023',
                'pessoas_afetadas': '8.000+',
                'badge_class': 'primary',
                'detalhes': 'Enchentes em diversos bairros de Mesquita após fortes chuvas, afetando principalmente áreas próximas ao Rio Sarapuí.'
            },
            {
                'tipo': 'Inundação',
                'local': 'Chatuba, Mesquita',
                'data': 'Fev/2020',
                'pessoas_afetadas': '3.500+',
                'badge_class': 'primary',
                'detalhes': 'Alagamentos no bairro da Chatuba após período de chuvas intensas.'
            }
        ],
        "São Paulo": [
            {
                'tipo': 'Inundação',
                'local': 'Marginal Tietê, São Paulo',
                'data': 'Fev/2023',
                'pessoas_afetadas': '100.000+',
                'badge_class': 'primary',
                'detalhes': 'Fortes chuvas causaram o transbordamento do Rio Tietê, paralisando a principal via da cidade.'
            },
            {
                'tipo': 'Deslizamento',
                'local': 'Franco da Rocha, SP',
                'data': 'Fev/2022',
                'pessoas_afetadas': '2.500+',
                'badge_class': 'danger',
                'detalhes': 'Deslizamentos fatais na região metropolitana de São Paulo após chuvas intensas.'
            }
        ],
        "Porto Alegre": [
            {
                'tipo': 'Inundação',
                'local': 'Porto Alegre, RS',
                'data': 'Mai/2023',
                'pessoas_afetadas': '150.000+',
                'badge_class': 'primary',
                'detalhes': 'Histórica enchente do Rio Guaíba que atingiu níveis recordes, alagando o centro histórico e diversos bairros da capital gaúcha.'
            },
            {
                'tipo': 'Inundação',
                'local': 'Região Central, Porto Alegre',
                'data': 'Jun/2023',
                'pessoas_afetadas': '80.000+',
                'badge_class': 'primary',
                'detalhes': 'Segunda onda de cheias do Rio Guaíba que manteve diversos bairros alagados por mais de um mês.'
            }
        ],
        "Recife": [
            {
                'tipo': 'Deslizamento',
                'local': 'Jaboatão dos Guararapes, PE',
                'data': 'Mai/2022',
                'pessoas_afetadas': '30.000+',
                'badge_class': 'danger',
                'detalhes': 'Deslizamentos de terra em diversos morros da região metropolitana do Recife, causando mais de 100 mortes.'
            },
            {
                'tipo': 'Inundação',
                'local': 'Centro do Recife, PE',
                'data': 'Mai/2022',
                'pessoas_afetadas': '20.000+',
                'badge_class': 'primary',
                'detalhes': 'Alagamentos severos no centro da cidade e em bairros históricos após chuvas torrenciais.'
            }
        ]
    }
    
    # Lista de cidades conhecidas do estado do Rio de Janeiro
    cidades_rj = [
        'Angra dos Reis', 'Araruama', 'Armação dos Búzios', 'Arraial do Cabo', 
        'Barra do Piraí', 'Barra Mansa', 'Belford Roxo', 'Bom Jardim', 
        'Cabo Frio', 'Cachoeiras de Macacu', 'Campos dos Goytacazes', 'Cantagalo', 
        'Carmo', 'Casimiro de Abreu', 'Duque de Caxias', 'Guapimirim', 
        'Iguaba Grande', 'Itaboraí', 'Itaguaí', 'Italva', 'Itaperuna', 
        'Japeri', 'Macaé', 'Magé', 'Mangaratiba', 'Maricá', 'Mesquita', 
        'Miguel Pereira', 'Miracema', 'Natividade', 'Nilópolis', 'Niterói', 
        'Nova Friburgo', 'Nova Iguaçu', 'Paracambi', 'Paraíba do Sul', 
        'Paraty', 'Paty do Alferes', 'Petrópolis', 'Pinheiral', 'Piraí', 
        'Porciúncula', 'Porto Real', 'Quatis', 'Queimados', 'Resende', 
        'Rio Bonito', 'Rio Claro', 'Rio das Ostras', 'Rio de Janeiro', 
        'Santa Maria Madalena', 'Santo Antônio de Pádua', 'São Fidélis', 
        'São Francisco de Itabapoana', 'São Gonçalo', 'São João de Meriti', 
        'São João de Meriti', 'São José de Ubá', 'São José do Vale do Rio Preto', 
        'São Pedro da Aldeia', 'São Sebastião do Alto', 'Saquarema', 'Seropédica', 
        'Silva Jardim', 'Tanguá', 'Teresópolis', 'Três Rios', 'Valença', 
        'Varre-Sai', 'Vassouras', 'Volta Redonda'
    ]
    
    # Lista de termos que indicam Rio de Janeiro
    termos_rj = ['rj', 'rio de janeiro', 'fluminense', 'carioca', 'baixada', 'baixada fluminense']
    
    # Verificar se a cidade solicitada é explicitamente do Rio de Janeiro
    cidade_lower = cidade.lower()
    
    # Primeira verificação: a cidade contém "Rio de Janeiro" ou ", RJ"
    for termo in ['rio de janeiro', ', rj']:
        if termo in cidade_lower:
            app.logger.info(f"Cidade {cidade} contém termo explícito do Rio de Janeiro: {termo}")
            
            # Extrair o nome da cidade antes de "Rio de Janeiro" ou ", RJ"
            if ',' in cidade_lower:
                nome_cidade = cidade_lower.split(',')[0].strip()
            else:
                partes = cidade_lower.split(' rio de janeiro')
                nome_cidade = partes[0].strip()
            
            # Verificar se temos esse nome específico no dicionário
            for nome_conhecido, desastres in desastres_por_cidade.items():
                if nome_conhecido.lower() == nome_cidade:
                    app.logger.info(f"Encontrado desastre específico para {nome_conhecido}")
                    return desastres
            
            # Se não encontrou, usar os desastres do Rio de Janeiro
            app.logger.info(f"Usando desastres gerais do Rio de Janeiro para {cidade}")
            return desastres_por_cidade.get("Rio de Janeiro", [])
    
    # Segunda verificação: nome da cidade exato
    for nome_cidade, desastres in desastres_por_cidade.items():
        if nome_cidade.lower() == cidade_lower:
            app.logger.info(f"Encontrados desastres específicos para {nome_cidade}")
            return desastres
    
    # Terceira verificação: verificar se o nome da cidade está na lista de cidades do RJ
    for cidade_rj in cidades_rj:
        if cidade_rj.lower() == cidade_lower:
            app.logger.info(f"Cidade {cidade} identificada como cidade do Rio de Janeiro")
            # Se for cidade do RJ mas não temos dados específicos, usar dados do Rio de Janeiro
            return desastres_por_cidade.get("Rio de Janeiro", [])
    
    # Quarta verificação: verificar substring no nome da cidade
    for cidade_rj in cidades_rj:
        if cidade_rj.lower() in cidade_lower:
            app.logger.info(f"Cidade {cidade} identificada como contendo nome de cidade do Rio de Janeiro: {cidade_rj}")
            # Verificar se temos dados específicos para esta cidade
            if cidade_rj in desastres_por_cidade:
                return desastres_por_cidade[cidade_rj]
            # Se não temos dados específicos, usar dados do Rio de Janeiro
            return desastres_por_cidade.get("Rio de Janeiro", [])
    
    # Quinta verificação: verificar se contém termos relacionados ao Rio de Janeiro
    for termo in termos_rj:
        if termo in cidade_lower:
            app.logger.info(f"Cidade {cidade} contém termo relacionado ao Rio de Janeiro: {termo}")
            return desastres_por_cidade.get("Rio de Janeiro", [])
    
    # Se não encontramos nada até aqui, seguir com a lógica anterior
    # Mapeamento de cidades para suas regiões/estados
    mapeamento_regioes = {
        'Rio de Janeiro': 'Rio de Janeiro',
        'São Paulo': 'São Paulo',
        'Belo Horizonte': 'Minas Gerais',
        'Porto Alegre': 'Rio Grande do Sul',
        'Florianópolis': 'Santa Catarina',
        'Curitiba': 'Paraná',
        'Salvador': 'Bahia',
        'Recife': 'Pernambuco',
        'Fortaleza': 'Ceará',
        'Natal': 'Rio Grande do Norte',
        'Manaus': 'Amazonas',
        'Belém': 'Pará',
        'Brasília': 'Distrito Federal',
        'Goiânia': 'Goiás',
        'Vitória': 'Espírito Santo',
        'Cuiabá': 'Mato Grosso',
        'Campo Grande': 'Mato Grosso do Sul',
        'Teresina': 'Piauí',
        'João Pessoa': 'Paraíba',
        'Maceió': 'Alagoas',
        'Aracaju': 'Sergipe',
        'São Luís': 'Maranhão',
        'Porto Velho': 'Rondônia',
        'Boa Vista': 'Roraima',
        'Macapá': 'Amapá',
        'Palmas': 'Tocantins',
        'Rio Branco': 'Acre'
    }
    
    # Adicionar todas as cidades do RJ ao mapeamento
    for cidade_rj in cidades_rj:
        mapeamento_regioes[cidade_rj] = 'Rio de Janeiro'
    
    # Se a cidade não estiver no mapeamento, tenta verificar se contém Rio de Janeiro
    if cidade not in mapeamento_regioes:
        if "rio" in cidade_lower or "rj" in cidade_lower:
            mapeamento_regioes[cidade] = 'Rio de Janeiro'
    
    # Se ainda não estiver no mapeamento, tenta identificar a região pelo nome
    if cidade not in mapeamento_regioes:
        for estado, uf in [
            ('Acre', 'AC'), ('Alagoas', 'AL'), ('Amapá', 'AP'), ('Amazonas', 'AM'),
            ('Bahia', 'BA'), ('Ceará', 'CE'), ('Distrito Federal', 'DF'), ('Espírito Santo', 'ES'),
            ('Goiás', 'GO'), ('Maranhão', 'MA'), ('Mato Grosso', 'MT'), ('Mato Grosso do Sul', 'MS'),
            ('Minas Gerais', 'MG'), ('Pará', 'PA'), ('Paraíba', 'PB'), ('Paraná', 'PR'),
            ('Pernambuco', 'PE'), ('Piauí', 'PI'), ('Rio de Janeiro', 'RJ'), ('Rio Grande do Norte', 'RN'),
            ('Rio Grande do Sul', 'RS'), ('Rondônia', 'RO'), ('Roraima', 'RR'), ('Santa Catarina', 'SC'),
            ('São Paulo', 'SP'), ('Sergipe', 'SE'), ('Tocantins', 'TO')
        ]:
            if estado.lower() in cidade_lower or uf.lower() in cidade_lower:
                mapeamento_regioes[cidade] = estado
                break
    
    # Região/estado da cidade pesquisada
    regiao = mapeamento_regioes.get(cidade, "Região não identificada")
    app.logger.info(f"Região identificada para {cidade}: {regiao}")
    
    # Desastres específicos do Rio de Janeiro (para cidades do RJ não listadas explicitamente)
    desastres_rio_de_janeiro = [
        {
            'tipo': 'Deslizamento',
            'local': 'Região Serrana, RJ',
            'data': 'Jan/2011',
            'pessoas_afetadas': '30.000+',
            'badge_class': 'danger',
            'detalhes': 'Um dos piores desastres naturais da história do Brasil, com mais de 900 mortes por deslizamentos de terra após chuvas intensas.'
        },
        {
            'tipo': 'Inundação',
            'local': 'Baixada Fluminense, RJ',
            'data': 'Jan/2023',
            'pessoas_afetadas': '50.000+',
            'badge_class': 'primary',
            'detalhes': 'Fortes chuvas causaram inundações em várias cidades da região metropolitana do Rio de Janeiro.'
        },
        {
            'tipo': 'Deslizamento',
            'local': 'Niterói, RJ',
            'data': 'Abr/2010',
            'pessoas_afetadas': '5.000+',
            'badge_class': 'danger',
            'detalhes': 'Deslizamento no Morro do Bumba que soterrou dezenas de casas e deixou muitas vítimas.'
        }
    ]
    
    # Base de dados simulada de desastres naturais para cada região
    desastres_por_regiao = {
        'Rio Grande do Sul': [
            {
                'tipo': 'Inundação',
                'local': 'Rio Grande do Sul',
                'data': 'Mai/2023',
                'pessoas_afetadas': '400.000+',
                'badge_class': 'primary',
                'detalhes': 'Grande inundação que afetou mais de 400 mil pessoas no RS em 2023, resultando em dezenas de mortes e danos significativos à infraestrutura.'
            },
            {
                'tipo': 'Inundação',
                'local': 'Vale do Taquari, RS',
                'data': 'Set/2023',
                'pessoas_afetadas': '150.000+',
                'badge_class': 'primary',
                'detalhes': 'Inundações severas no Vale do Taquari que destruíram várias comunidades e causaram perdas humanas significativas.'
            },
            {
                'tipo': 'Seca',
                'local': 'Metade Sul, RS',
                'data': '2022',
                'pessoas_afetadas': '500.000+',
                'badge_class': 'warning',
                'detalhes': 'Seca intensa que afetou a produção agrícola do estado, com perdas de bilhões na safra de soja e milho.'
            }
        ],
        'Rio de Janeiro': desastres_rio_de_janeiro,
        'São Paulo': [
            {
                'tipo': 'Inundação',
                'local': 'Litoral Norte, SP',
                'data': 'Fev/2023',
                'pessoas_afetadas': '4.000+',
                'badge_class': 'primary',
                'detalhes': 'Chuvas intensas provocaram inundações e deslizamentos no Litoral Norte de São Paulo, causando diversas mortes e isolando comunidades.'
            },
            {
                'tipo': 'Seca',
                'local': 'Região Metropolitana, SP',
                'data': '2014-2015',
                'pessoas_afetadas': '10.000.000+',
                'badge_class': 'warning',
                'detalhes': 'Crise hídrica severa que afetou o abastecimento de água na Grande São Paulo, com o sistema Cantareira atingindo níveis críticos.'
            },
            {
                'tipo': 'Inundação',
                'local': 'São Paulo (capital)',
                'data': 'Anual',
                'pessoas_afetadas': 'Variável',
                'badge_class': 'primary',
                'detalhes': 'Alagamentos recorrentes durante o período de chuvas, afetando diversas regiões da cidade e o trânsito.'
            }
        ]
    }
    
    # Verificar primeiramente se a região é Rio de Janeiro (pois já adicionamos muitas cidades do RJ)
    if regiao == "Rio de Janeiro":
        app.logger.info(f"Cidade {cidade} identificada como do estado do Rio de Janeiro")
        return desastres_rio_de_janeiro
    
    # Desastres para outras regiões do Nordeste
    desastres_nordeste = [
        {
            'tipo': 'Seca',
            'local': 'Semiárido Nordestino',
            'data': '2012-2017',
            'pessoas_afetadas': '10.000.000+',
            'badge_class': 'warning',
            'detalhes': 'Pior seca dos últimos 50 anos no Nordeste, afetando milhões de pessoas e a economia regional.'
        },
        {
            'tipo': 'Inundação',
            'local': 'Pernambuco',
            'data': 'Mai/2022',
            'pessoas_afetadas': '100.000+',
            'badge_class': 'primary',
            'detalhes': 'Chuvas intensas causaram inundações e deslizamentos em Recife e região metropolitana, resultando em mais de 100 mortes.'
        }
    ]
    
    # Desastres para outras regiões do Norte
    desastres_norte = [
        {
            'tipo': 'Inundação',
            'local': 'Acre',
            'data': 'Fev/2021',
            'pessoas_afetadas': '130.000+',
            'badge_class': 'primary',
            'detalhes': 'Cheia dos rios acreanos que afetou mais de 10 cidades e isolou comunidades ribeirinhas.'
        },
        {
            'tipo': 'Queimadas',
            'local': 'Amazônia Legal',
            'data': '2019',
            'pessoas_afetadas': 'Indeterminado',
            'badge_class': 'danger',
            'detalhes': 'Aumento significativo das queimadas na Amazônia, gerando preocupação internacional sobre o desmatamento.'
        }
    ]
    
    # Desastres para outras regiões do Centro-Oeste
    desastres_centro_oeste = [
        {
            'tipo': 'Seca',
            'local': 'Centro-Oeste',
            'data': '2020-2021',
            'pessoas_afetadas': 'Agricultura',
            'badge_class': 'warning',
            'detalhes': 'Seca que afetou a produção agrícola regional e o abastecimento de água.'
        },
        {
            'tipo': 'Incêndio',
            'local': 'Cerrado',
            'data': 'Ago-Set/2021',
            'pessoas_afetadas': 'Indeterminado',
            'badge_class': 'danger',
            'detalhes': 'Incêndios no Cerrado que destruíram vegetação nativa e afetaram a biodiversidade.'
        }
    ]
    
    # Desastres gerais para quando não temos informações específicas da região
    desastres_gerais = [
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
            'data': '2012-2017',
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
    
    # Estados por região (para classificar quando não temos dados específicos)
    nordeste = ['Alagoas', 'Bahia', 'Ceará', 'Maranhão', 'Paraíba', 'Pernambuco', 'Piauí', 'Rio Grande do Norte', 'Sergipe']
    norte = ['Acre', 'Amapá', 'Amazonas', 'Pará', 'Rondônia', 'Roraima', 'Tocantins']
    centro_oeste = ['Distrito Federal', 'Goiás', 'Mato Grosso', 'Mato Grosso do Sul']
    
    # Verificar se temos dados específicos para a região pesquisada
    if regiao in desastres_por_regiao:
        app.logger.info(f"Encontrados desastres para a região: {regiao}")
        return desastres_por_regiao[regiao]
    elif regiao in nordeste:
        return desastres_nordeste
    elif regiao in norte:
        return desastres_norte
    elif regiao in centro_oeste:
        return desastres_centro_oeste
    else:
        # Se não temos dados específicos, retornar os desastres gerais
        return desastres_gerais

@app.route('/mapa')
def mapa():
    try:
        cidade = request.args.get('cidade', 'Brasília')  # Cidade padrão: Brasília
        
        # Adicionar verificação para cidades do RJ que precisam de especificação
        cidades_rj = [
            'Mesquita', 'Nova Iguaçu', 'Duque de Caxias', 'Belford Roxo', 'São João de Meriti',
            'Nilópolis', 'Magé', 'Itaguaí', 'Japeri', 'Queimados', 'Seropédica', 'Paracambi'
        ]
        
        cidade_lower = cidade.lower().strip()
        cidade_especificada = cidade
        
        for cidade_rj in cidades_rj:
            if cidade_rj.lower() == cidade_lower:
                cidade_especificada = f"{cidade}, Rio de Janeiro"
                app.logger.info(f"Especificando cidade do RJ: {cidade_especificada}")
                break
        
        # Tentar buscar dados direto via get_weather_data para reusar o tratamento de erros
        weather_data, error = get_weather_data(city=cidade_especificada)
        
        if error:
            # Se houver erro, mostrar uma mensagem e criar dados padrão
            app.logger.warning(f"Erro ao obter dados para mapa: {error}. Usando dados padrão.")
            weather = {
                'cidade': cidade,
                'pais': 'BR',
                'temperatura': 25,
                'sensacao': 26,
                'minima': 22,
                'maxima': 28,
                'pressao': 1013,
                'umidade': 65,
                'vento': 2.1,
                'descricao': 'parcialmente nublado',
                'icone': '03d',
                'lat': -15.78, # Coordenadas padrão para Brasília
                'lon': -47.93
            }
        else:
            # Se não houver erro, preparar os dados para o template
            weather = {
                'cidade': weather_data['cidade'],
                'pais': weather_data.get('pais', 'BR'),
                'temperatura': weather_data['temperatura'],
                'sensacao': weather_data.get('sensacao', weather_data['temperatura']),
                'minima': weather_data.get('temp_min', round(weather_data['temperatura'] - 2)),
                'maxima': weather_data.get('temp_max', round(weather_data['temperatura'] + 2)),
                'pressao': weather_data.get('pressao', 1013),
                'umidade': weather_data['umidade'],
                'vento': weather_data['vento'],
                'descricao': weather_data['descricao'],
                'icone': weather_data['icone'],
                'lat': weather_data['lat'],
                'lon': weather_data['lon']
            }
        
        return render_template('mapa.html', weather=weather)
    
    except Exception as e:
        # Em caso de erro inesperado, registrar e mostrar uma página com dados padrão
        app.logger.error(f"Erro não tratado na rota do mapa: {e}")
        
        # Dados padrão para Brasília
        weather = {
            'cidade': 'Brasília',
            'pais': 'BR',
            'temperatura': 25,
            'sensacao': 26,
            'minima': 22,
            'maxima': 28,
            'pressao': 1013,
            'umidade': 65,
            'vento': 2.1,
            'descricao': 'parcialmente nublado',
            'icone': '03d',
            'lat': -15.78,
            'lon': -47.93
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
        "Espírito Santo", "Goiás", "Maranhão", "Paraíba", "Pernambuco", "Piauí", "Rio Grande do Norte", "Sergipe"
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

@app.route('/turma')
def turma():
    """Rota para página com informações sobre a turma de desenvolvimento"""
    # Dados dos alunos
    alunos = [
        {
            'nome': 'Yuri Fernandes de Oliveira',
            'matricula': '202208614744',
            'papel': 'Desenvolvedor Principal',
            'github': 'https://github.com/yuri',
            'linkedin': 'https://linkedin.com/in/yuri',
            'projetos': [
                {'nome': 'Sistema de Monitoramento Climático', 'url': '#', 'descricao': 'Sistema de análise de dados meteorológicos'},
                {'nome': 'Dashboard de Análise', 'url': '#', 'descricao': 'Visualização de dados climáticos em tempo real'},
                {'nome': 'API de Integração', 'url': '#', 'descricao': 'Serviço para integração com fontes de dados externas'}
            ],
            'contribuicoes': [
                'Arquitetura do sistema e planejamento do projeto',
                'Implementação das APIs de clima e previsão do tempo',
                'Desenvolvimento do módulo de mapeamento de dados'
            ]
        },
        {
            'nome': 'Rodrigo Ortega G F Camacho',
            'matricula': '202402303902',
            'papel': 'Desenvolvedor Backend',
            'github': 'https://github.com/rodrigo',
            'linkedin': 'https://linkedin.com/in/rodrigo',
            'projetos': [
                {'nome': 'Serviço de Processamento de Dados', 'url': '#', 'descricao': 'Processamento de dados climáticos em larga escala'},
                {'nome': 'Microserviços para Análise', 'url': '#', 'descricao': 'Arquitetura de microserviços para análise de dados'},
                {'nome': 'Sistema de Cache Distribuído', 'url': '#', 'descricao': 'Implementação de cache para otimização de performance'}
            ],
            'contribuicoes': [
                'Desenvolvimento do backend e infraestrutura',
                'Implementação do banco de dados e camada de persistência',
                'Otimização de performance e escalabilidade'
            ]
        },
        {
            'nome': 'Peterson Costa da Silva',
            'matricula': '201603434535',
            'papel': 'Desenvolvedor Frontend',
            'github': 'https://github.com/peterson',
            'linkedin': 'https://linkedin.com/in/peterson',
            'projetos': [
                {'nome': 'Interface Responsiva', 'url': '#', 'descricao': 'Design responsivo para aplicações web'},
                {'nome': 'Visualização de Dados', 'url': '#', 'descricao': 'Componentes de visualização interativa'},
                {'nome': 'Dashboard Analítico', 'url': '#', 'descricao': 'Painel de controle para monitoramento de métricas'}
            ],
            'contribuicoes': [
                'Design e implementação da interface do usuário',
                'Desenvolvimento de componentes reutilizáveis',
                'Integração frontend-backend e consumo de APIs'
            ]
        },
        {
            'nome': 'Pedro Carvalho Bocos',
            'matricula': '202308251457',
            'papel': 'Analista de Dados',
            'github': 'https://github.com/pedro',
            'linkedin': 'https://linkedin.com/in/pedro',
            'projetos': [
                {'nome': 'Modelos Preditivos', 'url': '#', 'descricao': 'Algoritmos de previsão do tempo baseados em ML'},
                {'nome': 'Análise Estatística', 'url': '#', 'descricao': 'Ferramentas para análise estatística avançada'},
                {'nome': 'Visualização de Séries Temporais', 'url': '#', 'descricao': 'Gráficos dinâmicos para análise de tendências'}
            ],
            'contribuicoes': [
                'Análise e processamento de dados meteorológicos',
                'Implementação de algoritmos de machine learning',
                'Desenvolvimento de modelos preditivos para eventos climáticos'
            ]
        }
    ]
    
    return render_template('turma.html', alunos=alunos)

if __name__ == '__main__':
    app.run(debug=True) 