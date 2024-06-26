from io import BytesIO
import sys
import requests
from flask import Flask, request, send_file,jsonify, Response
import base64
import json




def obtener_direccion_ip():
    response = requests.get('https://httpbin.org/ip')
    data = response.json()
    return data['origin']


def registrar_con_servidor(host, port, capacidad, rack):
    server_url = 'http://44.218.148.6:80/register'
    data = {
        'host': host,
        'port': port,
        'capacidad': capacidad,
        'rack': rack
    }
    try:
        response = requests.post(server_url, json=data)
        if response.status_code == 200:
            print("DataNode registrado correctamente en el servidor.")
        else:
            print("Error al registrar DataNode en el servidor.")
    except requests.exceptions.RequestException as e:
        print("Error al conectar con el servidor:", e)

if __name__ == '__main__':
    host = obtener_direccion_ip()
    if host == "18.206.50.61" or host == "18.213.101.29":
        zona = "rack2"
    else:
        zona = "rack1"
    # Obtener el puerto de la línea de comandos
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 80

    # Definir el límite de peso en bytes (1000 KB en este caso)
    limite_peso_kilo_bytes = 500.0 # 500 KB 

    # Inicializar la lista de archivos
    archivos_guardados = {}

    # Inicializar la lista de nombre de archivos
    nombre_archivos = []
    partes_enviadas = []

    registrar_con_servidor(host, port, 500.0, zona)

    app = Flask(__name__)

    @app.route('/guardar', methods=['POST'])
    def guardar_archivo():
        datos_archivo = request.json.get('archivo')
        nombre_archivo = datos_archivo.get('nombre')
        contenido_archivo = datos_archivo.get('archivo')
        tamaño_archivo = datos_archivo.get('tamaño_archivo')

        global limite_peso_kilo_bytes  # Declarar como global para modificar la variable global

        capacidad_disponible = limite_peso_kilo_bytes - tamaño_archivo
        limite_peso_kilo_bytes = capacidad_disponible

        # Guardar el archivo en el diccionario con su nombre
        archivos_guardados[nombre_archivo] = contenido_archivo

        requests.post(f'http://44.218.148.6:80/actualizarCapacidadDataNode', json={'data': {'host': host, 'port': port, 'nuevaCapacidad': capacidad_disponible, 'rack': zona}})
        print("Nombres de archivos guardados:")
        for nombre_archivo in archivos_guardados:
            print(nombre_archivo)
        response = requests.post('http://44.218.148.6:80/opcionDatanode')
        lista_de_data_nodes = response.json()
        otro_data_node = None
        for data_node in lista_de_data_nodes:
            if data_node['rack'] != zona:
                otro_data_node = data_node
                break
        print(otro_data_node['rack'])
        if otro_data_node is not None:
            guardar_archivo = True
            if guardar_archivo:
                response = requests.post(f'http://{otro_data_node["host"]}:{otro_data_node["port"]}/recibir', json={'archivo': {'nombre': nombre_archivo, 'archivo': datos_archivo, 'tamaño_archivo': tamaño_archivo}})
                if response.status_code == 200:
                    print(response.text)
                    requests.post(f'http://44.218.148.6:80/guardar_ubicacion_archivo', json={'ubicacion': {'nombre': nombre_archivo, 'posicion': datos_archivo.get('posicion'), 'host': otro_data_node["host"], 'port': otro_data_node["port"]}})
                elif response.status_code == 400:
                    print(response.text)

        return f'Archivo guardado correctamente en el DataNode. Host: {host}, Puerto: {port}, Rack: {zona}', 200
    

    @app.route('/recuperar_archivo', methods=['GET'])
    def recuperar_archivo():
        data = request.json.get('data_archivo')
        nombre_archivo = data['nombre_archivo'] 


        contenido_archivo = archivos_guardados[nombre_archivo]
        return Response(contenido_archivo, mimetype='application/octet-stream')

    @app.route('/ping')
    def ping():
        return 'pong', 200

    @app.route('/recibir', methods=['POST'])
    def recibir_archivo():
        datos_archivo = request.json.get('archivo')
        nombre_archivo = datos_archivo.get('nombre')
        contenido_archivo = datos_archivo.get('archivo')
        tamaño_archivo = datos_archivo.get('tamaño_archivo')

        global limite_peso_kilo_bytes  # Declarar como global para modificar la variable global

        capacidad_disponible = limite_peso_kilo_bytes - tamaño_archivo
        limite_peso_kilo_bytes = capacidad_disponible

        # Guardar el archivo en el diccionario con su nombre
        archivos_guardados[nombre_archivo] = contenido_archivo

        requests.post(f'http://44.218.148.6:80/actualizarCapacidadDataNode', json={'data': {'host': host, 'port': port, 'nuevaCapacidad': capacidad_disponible, 'rack': zona}})
        print("Nombres de archivos guardados:")
        for nombre_archivo in archivos_guardados:
            print(nombre_archivo)
        return f'Archivo guardado correctamente en el DataNode. Host: {host}, Puerto: {port}, Rack: {zona}', 200
    # @app.route('/recuperar_archivo', methods=['GET'])
    # def recuperar_archivo():
    #     # Convertir la lista archivos a bytes
    #     contenido_archivo = bytes(archivos)

    #     # Devolver el contenido de la lista archivos como parte del cuerpo de la respuesta HTTP
    #     return Response(contenido_archivo, mimetype='application/octet-stream')


    app.run(debug=True, host='0.0.0.0', port=port)
