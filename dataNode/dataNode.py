from io import BytesIO
import sys
import requests
from flask import Flask, request, send_file,jsonify, Response
import base64
import boto3

def obtener_direccion_ip():
    response = requests.get('https://httpbin.org/ip')
    data = response.json()
    return data['origin']

# Obtener el nombre de la instancia de EC2 actual
def get_instance_id():
    response = requests.get("http://169.254.169.254/latest/meta-data/instance-id")
    return response.text

# Obtener la zona de disponibilidad de la instancia de EC2
def get_instance_availability_zone(instance_id, region_name):
    ec2_client = boto3.client('ec2', region_name=region_name)
    response = ec2_client.describe_instances(InstanceIds=[instance_id])
    availability_zone = response['Reservations'][0]['Instances'][0]['Placement']['AvailabilityZone']
    return availability_zone

def obtener_zona_disponibilidad():
    instance_id = get_instance_id()
    region_name = 'us-east-1'  # Reemplaza con la región en la que se encuentra tu instancia
    availability_zone = get_instance_availability_zone(instance_id, region_name)
    return availability_zone

def registrar_con_servidor(host, port, capacidad):
    server_url = 'http://44.218.148.6:80/register'
    data = {
        'host': host,
        'port': port,
        'capacidad': capacidad
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
    zona = obtener_zona_disponibilidad()
    print(zona)
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


    registrar_con_servidor(host, port, 500.0)

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
        
        requests.post(f'http://44.218.148.6:80/actualizarCapacidadDataNode', json={'data': {'host': host, 'port': port, 'nuevaCapacidad': capacidad_disponible}})
             
        return f'Archivo guardado correctamente en el DataNode. Host: {host}, Puerto: {port}', 200
    

    @app.route('/recuperar_archivo', methods=['GET'])
    def recuperar_archivo():
        data = request.json.get('data_archivo')
        nombre_archivo = data['nombre_archivo'] 


        contenido_archivo = archivos_guardados[nombre_archivo]
        return Response(contenido_archivo, mimetype='application/octet-stream')



    # @app.route('/recuperar_archivo', methods=['GET'])
    # def recuperar_archivo():
    #     # Convertir la lista archivos a bytes
    #     contenido_archivo = bytes(archivos)

    #     # Devolver el contenido de la lista archivos como parte del cuerpo de la respuesta HTTP
    #     return Response(contenido_archivo, mimetype='application/octet-stream')


    app.run(debug=True, host='0.0.0.0', port=port)
