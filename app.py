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

# Función para obtener precio histórico de una fecha específica
def obtener_precio_historico(fecha, moneda_destino='CLP'):
    """
    Obtiene el precio del dólar en una fecha específica
    fecha: objeto datetime
    moneda_destino: CLP o PEN
    """
    year = fecha.year
    month = fecha.month
    day = fecha.day

    url = f"{BASE_URL}{API_KEY}/history/USD/{year}/{month}/{day}"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if 'conversion_rates' in data and moneda_destino in data['conversion_rates']:
                return data['conversion_rates'][moneda_destino]
        return None
    except Exception as e:
        print(f"Error al obtener precio histórico: {e}")
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
        comparaciones['CLP']['ayer'] = obtener_precio_historico(ayer, 'CLP')
        comparaciones['CLP']['hace_7'] = obtener_precio_historico(hace_7_dias, 'CLP')
        comparaciones['CLP']['hace_30'] = obtener_precio_historico(hace_30_dias, 'CLP')

        # Obtener precios históricos para PEN
        comparaciones['PEN']['ayer'] = obtener_precio_historico(ayer, 'PEN')
        comparaciones['PEN']['hace_7'] = obtener_precio_historico(hace_7_dias, 'PEN')
        comparaciones['PEN']['hace_30'] = obtener_precio_historico(hace_30_dias, 'PEN')

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

@app.route('/', methods=['GET'])
def mostrar_formulario():
    title = "Conversor Moneda"
    url = f"{BASE_URL}{API_KEY}/latest/USD"
    response = requests.get(url)
    data =response.json()
    return render_template('conversor.html',  title=title, currencies=monedas_disponibles, data=data)

@app.route('/convertir', methods=['POST', 'GET'])
def convertir_moneda():
    title = "Covirtiendo"
    monto = float(request.form['monto'])
    moneda_origen = request.form['moneda_origen']
    moneda_destino = request.form['moneda_destino']

    url = f"{BASE_URL}{API_KEY}/latest/{moneda_origen}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        conversion_rate = data['conversion_rates'][moneda_destino]
        resultado = monto * conversion_rate
        return render_template('conversor.html', title=title, data=data, currencies=monedas_disponibles, resultado=f"{monto:,.3f} {moneda_origen}  ", resultado2 = f"{resultado:,.3f}  {moneda_destino}")
    else:
        return render_template('conversor.html', title=title, data=data, currencies=monedas_disponibles, resultado="Error al realizar la conversión")



# Ruta para comparación de precios históricos
@app.route('/comparacion', methods=['GET'])
def comparacion_historica():
    title = "Comparación Histórica USD"
    comparaciones = calcular_comparaciones()

    # Obtener fechas formateadas
    hoy = datetime.now()
    fecha_ayer = (hoy - timedelta(days=1)).strftime('%d/%m/%Y')
    fecha_7 = (hoy - timedelta(days=7)).strftime('%d/%m/%Y')
    fecha_30 = (hoy - timedelta(days=30)).strftime('%d/%m/%Y')
    fecha_actual = hoy.strftime('%d/%m/%Y')

    return render_template('comparacion.html',
                         title=title,
                         comparaciones=comparaciones,
                         fecha_actual=fecha_actual,
                         fecha_ayer=fecha_ayer,
                         fecha_7=fecha_7,
                         fecha_30=fecha_30)

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
