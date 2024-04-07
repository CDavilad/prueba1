from flask import Flask, request, jsonify
import json


app = Flask(__name__)

data_nodes = []
direccion_archivos_guardados = []

@app.route('/register', methods=['POST'])
def register_data_node():
    data = request.json
    host = data.get('host')
    port = data.get('port')
    capacidad = data.get('capacidad')

    # Verificar si el DataNode ya esta registrado
    for node in data_nodes:
        if node['host'] == host and node['port'] == port:
            return jsonify({'message': 'DataNode ya registrado'}), 200

    # Si el DataNode no está registrado, agregarlo a la lista
    data_nodes.append({'host': host, 'port': port, 'capacidadActual': capacidad})

    print("Lista de DataNodes registrados:")
    for node in data_nodes:
        print(node)

    return jsonify({'message': 'DataNode registrado correctamente'}), 200

if __name__ == '__main__':
    # Especifica el HOST y PORT deseado
    host = '54.196.53.17'  # Por ejemplo
    port = 5000  # Por ejemplo

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

    

    # Ejecuta la aplicación Flask con el HOST y PORT especificado
    app.run(debug=True, host='54.196.53.17', port=port)
