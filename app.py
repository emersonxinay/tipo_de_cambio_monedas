from flask import Flask, render_template, jsonify, request
import requests
from dotenv import load_dotenv
import os
# Carga las variables de entorno desde el archivo .env
load_dotenv()

# Obtén las variables de entorno
API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")

app = Flask(__name__)
# Lista de monedas disponibles
monedas_disponibles = ["CLP", "PEN", "COP", "EUR", "USD", "UYU" ,"ARS", "MXN", "BRL", "BOB" ]  # Agrega más monedas según sea necesario

@app.route('/', methods=['GET'])
def mostrar_formulario():
    return render_template('conversor.html', currencies=monedas_disponibles)

@app.route('/convertir', methods=['POST'])
def convertir_moneda():
    monto = float(request.form['monto'])
    moneda_origen = request.form['moneda_origen']
    moneda_destino = request.form['moneda_destino']

    url = f"{BASE_URL}{API_KEY}/latest/{moneda_origen}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        conversion_rate = data['conversion_rates'][moneda_destino]
        resultado = monto * conversion_rate
        return render_template('conversor.html', currencies=monedas_disponibles, resultado=f"{monto} {moneda_origen} equivale a {resultado:.3f} {moneda_destino}")
    else:
        return render_template('conversor.html', currencies=monedas_disponibles, resultado="Error al realizar la conversión")

# Ruta para obtener datos de ExchangeRate-API
@app.route('/datos-exchange', methods=['GET'])
def obtener_datos_exchange():
    # URL de la API de ExchangeRate-API para el dólar como moneda base
    url = f"{BASE_URL}{API_KEY}/latest/USD"

    # Realiza la solicitud a la API de ExchangeRate-API
    response = requests.get(url)
    
    # Verifica si la solicitud fue exitosa
    if response.status_code == 200:
        # Convierte la respuesta a formato JSON
        data = response.json()
        # Renderiza la plantilla HTML con los datos
        return render_template('datos_exchange.html', data=data)
    else:
        # Si la solicitud falla, devuelve un mensaje de error
        return jsonify({'error': 'No se pudieron obtener los datos de ExchangeRate-API'}), 500

if __name__ == '__main__':
    app.run(debug=True)
