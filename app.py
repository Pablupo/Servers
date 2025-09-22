from flask import Flask, render_template, request, redirect, url_for
import json
from datetime import datetime
import threading
import os

app = Flask(__name__)

# Lock para asegurar que solo una petición modifique el JSON al mismo tiempo
lock = threading.Lock()

# Ruta al archivo JSON de estado
ARCHIVO = 'servidores_status.json'

def leer_servidores():
    # Leer el JSON completo
    if not os.path.exists(ARCHIVO):
        # Si no existe, devolver lista vacía o generar error
        return []
    with open(ARCHIVO, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            # Si hay problema de formato, manejarlo
            data = []
    return data

def escribir_servidores(data):
    # Escribir el JSON con indentación, para legibilidad
    with open(ARCHIVO, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@app.route('/')
def index():
    servidores = leer_servidores()
    return render_template('index.html', servidores=servidores)

@app.route('/reservar/<nombre>', methods=['POST'])
def reservar(nombre):
    usuario = request.form.get('usuario', '').strip()
    if usuario == '':
        # Si no envían nombre de usuario, redirigir con un mensaje o ignorar
        return redirect(url_for('index'))
    with lock:
        servidores = leer_servidores()
        encontrado = False
        for s in servidores:
            if s['nombre'] == nombre:
                encontrado = True
                if s['estado'] == 'libre':
                    s['estado'] = 'ocupado'
                    s['usuario'] = usuario
                    s['hora'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                # Si ya está ocupado, no hacer nada o informar
                break
        if not encontrado:
            # Podrías retornar error o mensaje que no existe ese servidor
            pass
        escribir_servidores(servidores)
    return redirect(url_for('index'))

@app.route('/liberar/<nombre>', methods=['POST'])
def liberar(nombre):
    usuario = request.form.get('usuario', '').strip()
    if usuario == '':
        return redirect(url_for('index'))
    with lock:
        servidores = leer_servidores()
        for s in servidores:
            if s['nombre'] == nombre:
                # Solo liberar si el usuario coincide
                if s['estado'] == 'ocupado' and s['usuario'] == usuario:
                    s['estado'] = 'libre'
                    s['usuario'] = ""
                    s['hora'] = ""
                break
        escribir_servidores(servidores)
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Puedes cambiar el host si quieres que sea accesible desde otros equipos
    app.run(debug=True, host='0.0.0.0', port=5000)
