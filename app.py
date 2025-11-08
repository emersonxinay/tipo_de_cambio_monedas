from flask import Flask, render_template, jsonify, request
import requests
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
# Carga las variables de entorno desde el archivo .env
load_dotenv()

# Obtén las variables de entorno
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")

app = Flask(__name__)
# Lista de monedas disponibles
monedas_disponibles = ["CLP", "PEN", "COP", "EUR", "USD", "UYU" ,"ARS", "MXN", "BRL", "BOB" ]  # Agrega más monedas según sea necesario

# solo moneda chilena y peruana 
# Ruta para obtener los precios del dólar a CLP y PEN
def obtener_precios_dolar():
    url = f"{BASE_URL}{API_KEY}/latest/USD"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        precio_dolar_clp = data['conversion_rates']['CLP']
        precio_dolar_pen = data['conversion_rates']['PEN']
        return {'precio_dolar_clp': precio_dolar_clp, 'precio_dolar_pen': precio_dolar_pen}
    else:
        return {'error': 'No se pudieron obtener los precios del dólar'}

# Decorador de contexto para ejecutar la función antes de manejar cualquier solicitud
@app.context_processor
def inject_precios_dolar():
    precios_dolar = obtener_precios_dolar()
    return dict(precio_dolar_clp=precios_dolar['precio_dolar_clp'], precio_dolar_pen=precios_dolar['precio_dolar_pen'])


# fin de solo moneda chilena y peruana

# Función para obtener precio histórico usando fawazahmed0 API (gratuita)
def obtener_precio_historico(fecha, moneda_origen='USD', moneda_destino='CLP'):
    """
    Obtiene el precio histórico usando fawazahmed0 Currency API
    fecha: objeto datetime
    moneda_origen: USD, EUR, etc.
    moneda_destino: CLP, PEN, etc.
    """
    fecha_str = fecha.strftime('%Y-%m-%d')
    moneda_origen_lower = moneda_origen.lower()
    moneda_destino_lower = moneda_destino.lower()

    # fawazahmed0 Currency API - completamente gratuita, sin límites
    url = f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@{fecha_str}/v1/currencies/{moneda_origen_lower}.json"

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if moneda_origen_lower in data and moneda_destino_lower in data[moneda_origen_lower]:
                return data[moneda_origen_lower][moneda_destino_lower]
        return None
    except Exception as e:
        print(f"Error al obtener precio histórico para {fecha_str}: {e}")
        return None

# Función para calcular comparaciones de precios
def calcular_comparaciones():
    """
    Calcula las comparaciones del precio actual vs fechas pasadas
    para CLP y PEN
    """
    # Fechas a comparar
    hoy = datetime.now()
    ayer = hoy - timedelta(days=1)
    hace_7_dias = hoy - timedelta(days=7)
    hace_30_dias = hoy - timedelta(days=30)

    # Obtener precio actual
    url = f"{BASE_URL}{API_KEY}/latest/USD"
    response = requests.get(url)

    comparaciones = {
        'CLP': {'actual': None, 'ayer': None, 'hace_7': None, 'hace_30': None},
        'PEN': {'actual': None, 'ayer': None, 'hace_7': None, 'hace_30': None}
    }

    if response.status_code == 200:
        data = response.json()
        comparaciones['CLP']['actual'] = data['conversion_rates']['CLP']
        comparaciones['PEN']['actual'] = data['conversion_rates']['PEN']

        # Obtener precios históricos para CLP
        comparaciones['CLP']['ayer'] = obtener_precio_historico(ayer, 'USD', 'CLP')
        comparaciones['CLP']['hace_7'] = obtener_precio_historico(hace_7_dias, 'USD', 'CLP')
        comparaciones['CLP']['hace_30'] = obtener_precio_historico(hace_30_dias, 'USD', 'CLP')

        # Obtener precios históricos para PEN
        comparaciones['PEN']['ayer'] = obtener_precio_historico(ayer, 'USD', 'PEN')
        comparaciones['PEN']['hace_7'] = obtener_precio_historico(hace_7_dias, 'USD', 'PEN')
        comparaciones['PEN']['hace_30'] = obtener_precio_historico(hace_30_dias, 'USD', 'PEN')

        # Calcular variaciones porcentuales para CLP
        if comparaciones['CLP']['ayer']:
            comparaciones['CLP']['var_ayer'] = ((comparaciones['CLP']['actual'] - comparaciones['CLP']['ayer']) / comparaciones['CLP']['ayer']) * 100
        if comparaciones['CLP']['hace_7']:
            comparaciones['CLP']['var_7'] = ((comparaciones['CLP']['actual'] - comparaciones['CLP']['hace_7']) / comparaciones['CLP']['hace_7']) * 100
        if comparaciones['CLP']['hace_30']:
            comparaciones['CLP']['var_30'] = ((comparaciones['CLP']['actual'] - comparaciones['CLP']['hace_30']) / comparaciones['CLP']['hace_30']) * 100

        # Calcular variaciones porcentuales para PEN
        if comparaciones['PEN']['ayer']:
            comparaciones['PEN']['var_ayer'] = ((comparaciones['PEN']['actual'] - comparaciones['PEN']['ayer']) / comparaciones['PEN']['ayer']) * 100
        if comparaciones['PEN']['hace_7']:
            comparaciones['PEN']['var_7'] = ((comparaciones['PEN']['actual'] - comparaciones['PEN']['hace_7']) / comparaciones['PEN']['hace_7']) * 100
        if comparaciones['PEN']['hace_30']:
            comparaciones['PEN']['var_30'] = ((comparaciones['PEN']['actual'] - comparaciones['PEN']['hace_30']) / comparaciones['PEN']['hace_30']) * 100

    return comparaciones

@app.route('/', methods=['GET', 'POST'])
def index():
    title = "Dashboard de Monedas"

    # Obtener datos actuales
    url = f"{BASE_URL}{API_KEY}/latest/USD"
    response = requests.get(url)
    data = response.json() if response.status_code == 200 else {}

    # Variables para el resultado de conversión
    resultado_conversion = None
    historico_conversion = []
    labels_grafica = []
    datos_grafica = []
    monto_convertido = None
    moneda_origen_sel = None
    moneda_destino_sel = None

    # Si es POST, procesar la conversión
    if request.method == 'POST':
        try:
            monto = float(request.form['monto'])
            moneda_origen = request.form['moneda_origen']
            moneda_destino = request.form['moneda_destino']

            moneda_origen_sel = moneda_origen
            moneda_destino_sel = moneda_destino
            monto_convertido = monto

            # Obtener tasa actual
            url_conversion = f"{BASE_URL}{API_KEY}/latest/{moneda_origen}"
            response_conversion = requests.get(url_conversion)

            if response_conversion.status_code == 200:
                data_conversion = response_conversion.json()
                tasa_actual = data_conversion['conversion_rates'][moneda_destino]
                resultado_conversion = monto * tasa_actual

                # Calcular conversiones históricas
                hoy = datetime.now()
                periodos = [
                    {'nombre': '1 día', 'fecha': hoy - timedelta(days=1)},
                    {'nombre': '7 días', 'fecha': hoy - timedelta(days=7)},
                    {'nombre': '30 días', 'fecha': hoy - timedelta(days=30)},
                    {'nombre': '90 días', 'fecha': hoy - timedelta(days=90)},
                    {'nombre': '180 días', 'fecha': hoy - timedelta(days=180)},
                    {'nombre': '1 año', 'fecha': hoy - timedelta(days=365)},
                ]

                for periodo in periodos:
                    fecha = periodo['fecha']
                    tasa_hist = obtener_precio_historico(fecha, moneda_origen, moneda_destino)

                    if tasa_hist:
                        resultado_hist = monto * tasa_hist
                        diferencia = resultado_conversion - resultado_hist
                        porcentaje = ((diferencia) / resultado_hist * 100) if resultado_hist != 0 else 0

                        historico_conversion.append({
                            'nombre': periodo['nombre'],
                            'fecha': fecha.strftime('%d/%m/%Y'),
                            'tasa': tasa_hist,
                            'resultado': resultado_hist,
                            'diferencia': diferencia,
                            'porcentaje': porcentaje,
                            'mejor_hoy': diferencia > 0
                        })

                # Preparar datos para gráfica
                for item in historico_conversion:
                    labels_grafica.append(item['nombre'])
                    datos_grafica.append(item['tasa'])
                labels_grafica.append('Hoy')
                datos_grafica.append(tasa_actual)

        except Exception as e:
            print(f"Error en conversión: {e}")

    # Obtener datos históricos para gráficas de tendencia (últimos 30 días)
    hoy = datetime.now()
    datos_historicos_clp = []
    datos_historicos_pen = []
    labels_tendencia = []

    for i in range(30, -1, -1):
        fecha = hoy - timedelta(days=i)
        precio_clp = obtener_precio_historico(fecha, 'USD', 'CLP')
        precio_pen = obtener_precio_historico(fecha, 'USD', 'PEN')

        if precio_clp and precio_pen:
            datos_historicos_clp.append(precio_clp)
            datos_historicos_pen.append(precio_pen)
            labels_tendencia.append(fecha.strftime('%d/%m'))

    # Comparaciones de precios
    comparaciones = calcular_comparaciones()

    return render_template('index.html',
                         title=title,
                         data=data,
                         currencies=monedas_disponibles,
                         resultado_conversion=resultado_conversion,
                         historico_conversion=historico_conversion,
                         monto=monto_convertido,
                         moneda_origen=moneda_origen_sel,
                         moneda_destino=moneda_destino_sel,
                         labels_grafica=labels_grafica,
                         datos_grafica=datos_grafica,
                         comparaciones=comparaciones,
                         datos_historicos_clp=datos_historicos_clp,
                         datos_historicos_pen=datos_historicos_pen,
                         labels_tendencia=labels_tendencia)

@app.route('/convertir', methods=['POST', 'GET'])
def convertir_moneda():
    title = "Convirtiendo"
    monto = float(request.form['monto'])
    moneda_origen = request.form['moneda_origen']
    moneda_destino = request.form['moneda_destino']

    url = f"{BASE_URL}{API_KEY}/latest/{moneda_origen}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        conversion_rate = data['conversion_rates'][moneda_destino]
        resultado = monto * conversion_rate

        # Calcular conversiones históricas
        hoy = datetime.now()
        periodos_historicos = [
            {'nombre': '1 día atrás', 'key': '1_dia', 'fecha': hoy - timedelta(days=1)},
            {'nombre': '1 semana atrás', 'key': '1_semana', 'fecha': hoy - timedelta(days=7)},
            {'nombre': '1 mes atrás', 'key': '1_mes', 'fecha': hoy - timedelta(days=30)},
            {'nombre': '6 meses atrás', 'key': '6_meses', 'fecha': hoy - timedelta(days=180)},
            {'nombre': '1 año atrás', 'key': '1_anio', 'fecha': hoy - timedelta(days=365)},
            {'nombre': '5 años atrás', 'key': '5_anios', 'fecha': hoy - timedelta(days=365*5)}
        ]

        historico_resultados = []

        for periodo in periodos_historicos:
            try:
                fecha = periodo['fecha']

                # Usar Frankfurter API para datos históricos (gratuita)
                tasa_historica = obtener_precio_historico(fecha, moneda_origen, moneda_destino)

                if tasa_historica:
                    resultado_historico = monto * tasa_historica
                    diferencia = resultado - resultado_historico
                    porcentaje = ((resultado - resultado_historico) / resultado_historico * 100) if resultado_historico != 0 else 0

                    historico_resultados.append({
                        'nombre': periodo['nombre'],
                        'fecha': fecha.strftime('%d/%m/%Y'),
                        'tasa': tasa_historica,
                        'resultado': resultado_historico,
                        'diferencia': diferencia,
                        'porcentaje': porcentaje,
                        'ganancia': diferencia > 0
                    })
            except Exception as e:
                print(f"Error al obtener datos históricos para {periodo['nombre']}: {e}")

        # Preparar datos para gráficas
        labels_grafica = []
        datos_grafica = []

        for item in historico_resultados:
            labels_grafica.append(item['nombre'].replace(' atrás', ''))
            datos_grafica.append(item['tasa'])

        # Agregar punto actual
        labels_grafica.append('HOY')
        datos_grafica.append(conversion_rate)

        return render_template('conversor.html',
                             title=title,
                             data=data,
                             currencies=monedas_disponibles,
                             resultado=f"{monto:,.3f} {moneda_origen}  ",
                             resultado2=f"{resultado:,.3f}  {moneda_destino}",
                             monto=monto,
                             moneda_origen=moneda_origen,
                             moneda_destino=moneda_destino,
                             resultado_actual=resultado,
                             historico=historico_resultados,
                             labels_grafica=labels_grafica,
                             datos_grafica=datos_grafica)
    else:
        return render_template('conversor.html', title=title, data=data, currencies=monedas_disponibles, resultado="Error al realizar la conversión")



# Ruta para comparación de precios históricos
@app.route('/comparacion', methods=['GET', 'POST'])
def comparacion_historica():
    title = "Comparación Histórica"

    # Obtener datos de la API para el navbar
    url = f"{BASE_URL}{API_KEY}/latest/USD"
    response = requests.get(url)
    data = response.json() if response.status_code == 200 else {}

    # Variables para el conversor
    resultado_conversion = None
    historico_conversion = []
    monto_convertido = None
    moneda_origen_sel = None
    moneda_destino_sel = None

    # Si es POST, procesar la conversión
    if request.method == 'POST':
        try:
            monto = float(request.form['monto'])
            moneda_origen = request.form['moneda_origen']
            moneda_destino = request.form['moneda_destino']

            moneda_origen_sel = moneda_origen
            moneda_destino_sel = moneda_destino
            monto_convertido = monto

            # Obtener tasa actual
            url_actual = f"{BASE_URL}{API_KEY}/latest/{moneda_origen}"
            response_actual = requests.get(url_actual)

            if response_actual.status_code == 200:
                data_actual = response_actual.json()
                tasa_actual = data_actual['conversion_rates'][moneda_destino]
                resultado_conversion = monto * tasa_actual

                # Calcular conversiones históricas
                hoy = datetime.now()
                periodos = [
                    {'nombre': '1 día atrás', 'fecha': hoy - timedelta(days=1)},
                    {'nombre': '1 semana atrás', 'fecha': hoy - timedelta(days=7)},
                    {'nombre': '1 mes atrás', 'fecha': hoy - timedelta(days=30)},
                    {'nombre': '6 meses atrás', 'fecha': hoy - timedelta(days=180)},
                    {'nombre': '1 año atrás', 'fecha': hoy - timedelta(days=365)},
                ]

                for periodo in periodos:
                    fecha = periodo['fecha']

                    # Usar Frankfurter API para datos históricos
                    tasa_hist = obtener_precio_historico(fecha, moneda_origen, moneda_destino)

                    if tasa_hist:
                        resultado_hist = monto * tasa_hist
                        diferencia = resultado_conversion - resultado_hist
                        porcentaje = ((diferencia) / resultado_hist * 100) if resultado_hist != 0 else 0

                        historico_conversion.append({
                            'nombre': periodo['nombre'],
                            'fecha': fecha.strftime('%d/%m/%Y'),
                            'tasa': tasa_hist,
                            'resultado': resultado_hist,
                            'diferencia': diferencia,
                            'porcentaje': porcentaje,
                            'mejor_hoy': diferencia > 0
                        })

        except Exception as e:
            print(f"Error en conversión: {e}")

    # Comparaciones de USD predeterminadas
    comparaciones = calcular_comparaciones()
    hoy = datetime.now()
    fecha_ayer = (hoy - timedelta(days=1)).strftime('%d/%m/%Y')
    fecha_7 = (hoy - timedelta(days=7)).strftime('%d/%m/%Y')
    fecha_30 = (hoy - timedelta(days=30)).strftime('%d/%m/%Y')
    fecha_actual = hoy.strftime('%d/%m/%Y')

    return render_template('comparacion.html',
                         title=title,
                         data=data,
                         currencies=monedas_disponibles,
                         comparaciones=comparaciones,
                         fecha_actual=fecha_actual,
                         fecha_ayer=fecha_ayer,
                         fecha_7=fecha_7,
                         fecha_30=fecha_30,
                         resultado_conversion=resultado_conversion,
                         historico_conversion=historico_conversion,
                         monto=monto_convertido,
                         moneda_origen=moneda_origen_sel,
                         moneda_destino=moneda_destino_sel)

# Ruta para obtener todos los datos de ExchangeRate-API
@app.route('/datos-exchange', methods=['GET'])
def obtener_datos_exchange():
    title = "Todas las Monedas"
    # URL de la API de ExchangeRate-API para el dólar como moneda base
    url = f"{BASE_URL}{API_KEY}/latest/USD"

    # Realiza la solicitud a la API de ExchangeRate-API
    response = requests.get(url)
    
    # Verifica si la solicitud fue exitosa
    if response.status_code == 200:
        # Convierte la respuesta a formato JSON
        data = response.json()
        # Renderiza la plantilla HTML con los datos
        return render_template('datos_exchange.html', title=title, data=data)
    else:
        # Si la solicitud falla, devuelve un mensaje de error
        return jsonify({'error': 'No se pudieron obtener los datos de ExchangeRate-API'}), 500

if __name__ == '__main__':
    app.run(debug=True)
