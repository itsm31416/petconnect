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
        """Envía mensaje a RabbitMQ SIN notificaciones automáticas"""
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
            
            # Solo log en consola para debugging
            print(f"📤 Mensaje enviado a cola '{queue_name}': {message['mascota_id']}")
            
            return True
            
        except Exception as e:
            print(f"❌ ERROR RabbitMQ: No se pudo conectar: {str(e)}")
            return False
    
    def process_adoption(self, mascota_id, usuario_nombre):
        """Procesa una solicitud de adopción paso a paso CON notificaciones de proceso"""
        print(f"🔹 Iniciando proceso para {mascota_id} - Usuario: {usuario_nombre}")
        
        # Notificación de INICIO
        self.add_notification(
            "📤 SOLICITUD ENVIADA", 
            f"Solicitud enviada para {mascota_id} - Usuario: {usuario_nombre}",
            "envio"
        )
        
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
        time.sleep(1)
        
        # Notificación de PROCESAMIENTO
        self.add_notification(
            "⚙️ PROCESANDO SOLICITUD", 
            f"Validando solicitud de {usuario_nombre} para {mascota_id}",
            "procesamiento"
        )
        
        time.sleep(1)
        
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
            # Notificación de RESULTADO
            tipo_notificacion = "respuesta" if aprobado else "error"
            self.add_notification(
                "📥 RESULTADO FINAL", 
                f"{mascota_id} → {resultado} | Motivo: {motivo}",
                tipo_notificacion
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
        rabbit_mq.add_notification("❌ ERROR", f"Error procesando solicitud: {str(e)}", "error")
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
        
        # Notificación de reset
        rabbit_mq.add_notification("🔄 SISTEMA REINICIADO", "Colas de RabbitMQ reseteadas correctamente", "info")
        
        return jsonify({
            'estado': 'success', 
            'mensaje': 'Colas de RabbitMQ reseteadas correctamente'
        })
        
    except Exception as e:
        rabbit_mq.add_notification("❌ ERROR RESET", f"Error reseteando RabbitMQ: {str(e)}", "error")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Iniciando PetConnect con RabbitMQ...")
    print("📊 Las notificaciones aparecerán durante el proceso de adopción")
    app.run(debug=True, port=5000)