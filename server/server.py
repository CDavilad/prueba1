import time
import threading
from flask import Flask, request, jsonify
import json
import requests

app = Flask(__name__)

data_nodes = []
direccion_archivos_guardados = []

def ping_data_nodes():
    while True:
        for node in data_nodes:
            try:
                response = requests.get(f'http://{node["host"]}:{node["port"]}/ping')
                if response.status_code != 200:
                    print(f'DataNode {node["host"]}:{node["port"]} no responde. Eliminándolo de la lista.')
                    eliminar_data_node(node["host"], node["port"])
            except requests.RequestException:
                print(f'Error al comunicarse con DataNode {node["host"]}:{node["port"]}. Eliminándolo de la lista.')
                eliminar_data_node(node["host"], node["port"])
        time.sleep(10)  # Espera 10 segundos antes de volver a verificar

def eliminar_data_node(host, port):
    global data_nodes
    data_nodes = [node for node in data_nodes if node['host'] != host or node['port'] != port]
    redistribuir_archivos(host, port)

def redistribuir_archivos(host_desconectado, port_desconectado):
    archivos_a_redistribuir = []
    
    # Obtener los archivos almacenados en el DataNode desconectado
    for direccion_archivo in direccion_archivos_guardados:
        if direccion_archivo['host'] == host_desconectado and direccion_archivo['port'] == port_desconectado:
            archivos_a_redistribuir.append(direccion_archivo)
    
    # Eliminar las entradas de archivos del DataNode desconectado
    direccion_archivos_guardados[:] = [archivo for archivo in direccion_archivos_guardados if archivo not in archivos_a_redistribuir]

    # Enviar los archivos a otros DataNodes disponibles
    for archivo in archivos_a_redistribuir:
        redistribuir_archivo(archivo)

def redistribuir_archivo(archivo):
    # Obtener lista de DataNodes disponibles ordenados por capacidad
    response = requests.post('http://44.218.148.6:80/opcionesDataNodes')
    if response.status_code == 200:
        data_nodes_disponibles = response.json()
        
        # Seleccionar DataNode con mayor capacidad disponible
        data_node_destino = max(data_nodes_disponibles, key=lambda x: x['capacidadActual'])
        
        # Enviar archivo al DataNode seleccionado
        response = requests.post(f'http://{data_node_destino["host"]}:{data_node_destino["port"]}/guardar', json={'archivo': archivo})
        # Actualizar la lista de ubicación de archivos en el servidor
        requests.post(f'http://44.218.148.6:80/guardar_ubicacion_archivo', json={'ubicacion': archivo})
    else:
        print('Error al obtener lista de DataNodes disponibles.')


@app.route('/register', methods=['POST'])
def register_data_node():
    data = request.json
    host = data.get('host')
    port = data.get('port')
    capacidad = data.get('capacidad')
    if host == "18.206.50.61" or host == "18.213.101.29":
        zona = "rack2"
    else:
        zona = "rack1"
    # Verificar si el DataNode ya esta registrado
    for node in data_nodes:
        if node['host'] == host and node['port'] == port:
            return jsonify({'message': 'DataNode ya registrado'}), 200

    # Si el DataNode no está registrado, agregarlo a la lista
    data_nodes.append({'host': host, 'port': port, 'capacidadActual': capacidad, 'rack': zona})

    print("Lista de DataNodes registrados:")
    for node in data_nodes:
        print(node)

    return jsonify({'message': 'DataNode registrado correctamente'}), 200

@app.route('/opcionDatanode', methods=['POST'])
def buscar_dataNode():
    # Ordenar la lista de DataNodes por 'capacidadActual' en orden descendente
    data_nodes_ordenados = sorted(data_nodes, key=lambda x: x['capacidadActual'], reverse=True)
    
    return jsonify(data_nodes_ordenados)

@app.route('/opcionesDataNodes', methods=['POST'])
def buscar_dataNodes_disponibles():
    # Ordenar la lista de DataNodes por 'capacidadActual' en orden descendente
    data_nodes_ordenados = sorted(data_nodes, key=lambda x: x['capacidadActual'], reverse=True)
    
    # Seleccionar los dos primeros DataNodes con la mayor capacidad
    data_nodes_top = data_nodes_ordenados[:2]
    
    # Devolver los dos DataNodes seleccionados como respuesta
    return jsonify(data_nodes_top)

@app.route('/actualizarCapacidadDataNode', methods=['POST'])
def actualizar_capacidad_data_node():
    data_actualizacion = request.json.get('data')
    nuevo_host = data_actualizacion['host']
    nuevo_port = data_actualizacion['port']
    nueva_capacidad = data_actualizacion['nuevaCapacidad']
    
    for data_node in data_nodes:
        if data_node['host'] == nuevo_host and data_node['port'] == nuevo_port:
            data_node['capacidadActual'] = nueva_capacidad
            print("Lista de DataNodes ahora:")
            for node in data_nodes:
                print(node)
            return 'Capacidad actualizada correctamente.', 200

    return 'No se encontró el DataNode especificado.', 404

@app.route('/guardar_ubicacion_archivo', methods=['POST'])
def guardar_ubicacion_archivo():
    ubicacion_archivo = request.json.get('ubicacion')
    nombre = ubicacion_archivo['nombre'] 
    posicion = ubicacion_archivo['posicion'] 
    host = ubicacion_archivo['host'] 
    port = ubicacion_archivo['port'] 

    direccion_archivos_guardados.append({"nombre": nombre, "posicion": posicion, "host": host, "port": port})

    return jsonify({'message': 'Ubicación del archivo guardada correctamente'}), 200

@app.route('/recuperar_ubicacion_archivos', methods=['GET'])
def devolver_ubicacion_archivos():
    # Convertir la lista a formato JSON
    ubicacion_json = json.dumps(direccion_archivos_guardados)
    
    # Devolver la lista como parte de la respuesta HTTP
    return ubicacion_json, 200

if __name__ == '__main__':
    host = '44.218.148.6'
    port = 80

    # Iniciar hilo para la detección de desconexión de DataNodes
    threading.Thread(target=ping_data_nodes, daemon=True).start()

    # Ejecutar la aplicación Flask con el HOST y PORT especificado
    app.run(debug=True, host='0.0.0.0', port=port)
