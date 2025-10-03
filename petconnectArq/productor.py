from conexion import conectar_rabbitmq, declarar_colas
import json
import time
import random
import pika

class ProductorAdopciones:
    def __init__(self):
        self.canal = conectar_rabbitmq()
        declarar_colas(self.canal)
    
    def publicar_solicitud_adopcion(self, mascota_id, usuario_id, datos_adicionales=None):
        """Publica una solicitud de adopción en la cola."""
        mensaje = {
            'tipo': 'solicitud_adopcion',
            'mascota_id': mascota_id,
            'usuario_id': usuario_id,
            'datos_adicionales': datos_adicionales or {},
            'timestamp': time.time(),
            'estado': 'pendiente'
        }
        
        self.canal.basic_publish(
            exchange='',
            routing_key='solicitudes_adopcion',
            body=json.dumps(mensaje),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Hacer el mensaje persistente
            )
        )
        
        print(f"🐾 [Productor] Solicitud de adopción publicada: Mascota {mascota_id}, Usuario {usuario_id}")
    
    def publicar_notificacion(self, usuario_id, mensaje, tipo='info'):
        """Publica una notificación para el usuario."""
        notificacion = {
            'tipo': 'notificacion',
            'usuario_id': usuario_id,
            'mensaje': mensaje,
            'tipo_notificacion': tipo,
            'timestamp': time.time()
        }
        
        self.canal.basic_publish(
            exchange='',
            routing_key='notificaciones',
            body=json.dumps(notificacion)
        )
        
        print(f"[Productor] Notificación enviada: {mensaje}")

def simular_solicitudes():
    """Simula múltiples solicitudes de adopción para testing."""
    productor = ProductorAdopciones()
    
    mascotas = ['Budy_001', 'Luna_002', 'Max_003', 'Molly_004', 'Simba_005']
    usuarios = ['user_123', 'user_456', 'user_789', 'user_101', 'user_112']
    
    for i in range(5):
        mascota = random.choice(mascotas)
        usuario = random.choice(usuarios)
        
        datos_adicionales = {
            'experiencia_previa': random.choice([True, False]),
            'tipo_vivienda': random.choice(['casa', 'apartamento']),
            'otros_animales': random.choice([True, False])
        }
        
        productor.publicar_solicitud_adopcion(mascota, usuario, datos_adicionales)
        time.sleep(2)

if __name__ == "__main__":
    simular_solicitudes()