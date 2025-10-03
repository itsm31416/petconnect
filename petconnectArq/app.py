from flask import Flask, render_template, request, jsonify
import pika
import json
import time
import threading
from datetime import datetime

app = Flask(__name__)

class RabbitMQManager:
    def __init__(self):
        self.notifications = []
    
    def send_to_rabbitmq(self, queue_name, message):
        """Envía mensaje a RabbitMQ y muestra en notificaciones"""
        try:
            # Conexión real a RabbitMQ
            connection = pika.BlockingConnection(
                pika.ConnectionParameters('localhost')
            )
            channel = connection.channel()
            
            # Declarar cola SIN durable para evitar conflictos
            channel.queue_declare(queue=queue_name)
            
            # Publicar mensaje
            channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message)
            )
            
            connection.close()
            
            # Agregar notificación de ENVÍO
            self.add_notification(
                "📤 PRODUCTOR RabbitMQ", 
                f"Enviado a cola '{queue_name}': Solicitud para {message['mascota_id']}",
                "envio"
            )
            
            return True
            
        except Exception as e:
            self.add_notification("❌ ERROR RabbitMQ", f"No se pudo conectar: {str(e)}", "error")
            return False
    
    def process_adoption(self, mascota_id, usuario_nombre):
        """Procesa una solicitud de adopción paso a paso"""
        print(f"🔹 Iniciando proceso para {mascota_id} - Usuario: {usuario_nombre}")
        
        # PASO 1: Enviar solicitud a RabbitMQ
        solicitud = {
            'mascota_id': mascota_id,
            'usuario': usuario_nombre,
            'timestamp': time.time(),
            'tipo': 'solicitud_adopcion',
            'accion': 'inicio_proceso'
        }
        
        if not self.send_to_rabbitmq('solicitudes_adopcion', solicitud):
            return {'error': 'No se pudo enviar a RabbitMQ'}
        
        # PASO 2: Simular procesamiento (2 segundos)
        time.sleep(2)
        
        # Agregar notificación de PROCESAMIENTO
        self.add_notification(
            "⚙️ PROCESADOR RabbitMQ", 
            f"Procesando: {usuario_nombre} → {mascota_id}",
            "procesamiento"
        )
        
        # Simular validación (reglas simples)
        aprobado = len(usuario_nombre) > 3  # Nombre debe tener más de 3 letras
        resultado = "APROBADA 🎉" if aprobado else "RECHAZADA ❌"
        motivo = "¡Cumples con los requisitos!" if aprobado else "Nombre muy corto para validación"
        
        # PASO 3: Enviar RESULTADO a RabbitMQ
        respuesta = {
            'mascota_id': mascota_id,
            'usuario': usuario_nombre,
            'resultado': resultado,
            'aprobado': aprobado,
            'motivo': motivo,
            'timestamp': time.time(),
            'tipo': 'respuesta_adopcion',
            'accion': 'resultado_final'
        }
        
        if self.send_to_rabbitmq('respuestas_adopcion', respuesta):
            # Notificación final del CONSUMIDOR
            self.add_notification(
                "📥 CONSUMIDOR RabbitMQ", 
                f"RESULTADO: {mascota_id} → {resultado} | Motivo: {motivo}",
                "respuesta" if aprobado else "error"
            )
        
        return {
            'aprobado': aprobado,
            'resultado': resultado,
            'mascota_id': mascota_id,
            'motivo': motivo
        }
    
    def add_notification(self, titulo, mensaje, tipo):
        """Agrega una notificación al sistema"""
        notification = {
            'id': len(self.notifications) + 1,
            'titulo': titulo,
            'mensaje': mensaje,
            'tipo': tipo,
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.notifications.insert(0, notification)  # Agregar al inicio
        print(f"🔔 Notificación: {titulo} - {mensaje}")
        
        # Mantener máximo 15 notificaciones
        if len(self.notifications) > 15:
            self.notifications.pop()
    
    def get_notifications(self):
        """Obtiene todas las notificaciones"""
        return self.notifications
    
    def clear_notifications(self):
        """Limpia todas las notificaciones"""
        self.notifications.clear()

# Instancia global
rabbit_mq = RabbitMQManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/solicitar_adopcion', methods=['POST'])
def solicitar_adopcion():
    datos = request.json
    mascota_id = datos.get('mascota_id')
    usuario_nombre = datos.get('usuario_nombre', 'Usuario Anónimo')
    
    if not mascota_id:
        return jsonify({'error': 'No se especificó mascota'}), 400
    
    try:
        print(f"🎯 Nueva solicitud: {mascota_id} por {usuario_nombre}")
        
        resultado = rabbit_mq.process_adoption(mascota_id, usuario_nombre)
        
        return jsonify({
            'estado': 'success',
            'resultado': resultado
        })
        
    except Exception as e:
        print(f"❌ Error en solicitud: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/notificaciones')
def get_notificaciones():
    """Endpoint para obtener notificaciones actualizadas"""
    return jsonify(rabbit_mq.get_notifications())

@app.route('/limpiar_notificaciones', methods=['POST'])
def limpiar_notificaciones():
    """Limpia todas las notificaciones"""
    rabbit_mq.clear_notifications()
    return jsonify({'estado': 'success', 'mensaje': 'Notificaciones limpiadas'})

@app.route('/reset_rabbitmq', methods=['POST'])
def reset_rabbitmq():
    """Elimina y recrea las colas para resetear"""
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        
        # Eliminar colas existentes
        channel.queue_delete(queue='solicitudes_adopcion')
        channel.queue_delete(queue='respuestas_adopcion')
        
        # Crear nuevas colas
        channel.queue_declare(queue='solicitudes_adopcion')
        channel.queue_declare(queue='respuestas_adopcion')
        
        connection.close()
        
        rabbit_mq.clear_notifications()
        
        return jsonify({
            'estado': 'success', 
            'mensaje': 'Colas de RabbitMQ reseteadas correctamente'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Iniciando PetConnect con RabbitMQ...")
    print("📊 Las notificaciones SOLO aparecerán cuando hagas clic en los botones")
    app.run(debug=True, port=5000)