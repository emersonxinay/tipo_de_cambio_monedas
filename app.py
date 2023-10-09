from flask import Flask, render_template, jsonify, request
import requests
from dotenv import load_dotenv
import os
import datetime
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
