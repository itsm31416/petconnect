import pika
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def conectar_rabbitmq():
    """Establece conexión con RabbitMQ con manejo de errores."""
    try:
        conexion = pika.BlockingConnection(
            pika.ConnectionParameters(
                host='localhost',
                heartbeat=600,
                blocked_connection_timeout=300
            )
        )
        canal = conexion.channel()
        logger.info("✅ Conexión establecida con RabbitMQ")
        return canal
    except Exception as e:
        logger.error(f"❌ Error conectando a RabbitMQ: {e}")
        raise

def declarar_colas(canal):
    """Declara todas las colas necesarias para el sistema."""
    colas = ['solicitudes_adopcion', 'notificaciones', 'resultados_adopcion']
    
    for cola in colas:
        canal.queue_declare(queue=cola, durable=True)
        logger.info(f"📦 Cola '{cola}' declarada correctamente")