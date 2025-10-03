from conexion import conectar_rabbitmq, declarar_colas
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConsumidorResultados:
    def __init__(self):
        self.canal = conectar_rabbitmq()
        declarar_colas(self.canal)
    
    def manejar_resultado(self, ch, method, properties, body):
        """Maneja los resultados de las solicitudes procesadas."""
        try:
            resultado = json.loads(body.decode())
            solicitud = resultado['solicitud_original']
            datos_resultado = resultado['resultado']
            
            estado = "APROBADO" if datos_resultado['aprobado'] else "RECHAZADO"
            logger.info(f"[Consumidor] Resultado recibido:")
            logger.info(f"   Mascota: {solicitud['mascota_id']}")
            logger.info(f"   Usuario: {solicitud['usuario_id']}")
            logger.info(f"   Estado: {estado}")
            logger.info(f"   Mensaje: {datos_resultado['mensaje']}")
            
            # Mostrar criterios evaluados
            if 'criterios_evaluados' in datos_resultado:
                logger.info("   Criterios evaluados:")
                for criterio, valor in datos_resultado['criterios_evaluados'].items():
                    estado_criterio = "CUMPLE" if valor else "NO CUMPLE"
                    logger.info(f"     {estado_criterio} {criterio}")
            
            logger.info("=" * 50)
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"[Consumidor] Error procesando resultado: {e}")
    
    def manejar_notificacion(self, ch, method, properties, body):
        """Maneja las notificaciones del sistema."""
        try:
            notificacion = json.loads(body.decode())
            
            tipo_texto = {
                'success': 'EXITO',
                'warning': 'ADVERTENCIA',
                'info': 'INFORMACION',
                'error': 'ERROR'
            }
            
            tipo = tipo_texto.get(notificacion['tipo_notificacion'], 'NOTIFICACION')
            logger.info(f"[{tipo}] Para {notificacion['usuario_id']}: {notificacion['mensaje']}")
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"[Consumidor] Error procesando notificación: {e}")
    
    def iniciar_consumo(self):
        """Inicia el consumo de resultados y notificaciones."""
        print("[Consumidor] Iniciando consumidor de resultados...")
        
        # Consumir resultados de adopción
        self.canal.basic_consume(
            queue='resultados_adopcion',
            on_message_callback=self.manejar_resultado
        )
        
        # Consumir notificaciones
        self.canal.basic_consume(
            queue='notificaciones',
            on_message_callback=self.manejar_notificacion
        )
        
        try:
            print("[Consumidor] Escuchando resultados y notificaciones...")
            self.canal.start_consuming()
        except KeyboardInterrupt:
            print("[Consumidor] Deteniendo consumidor...")
        except Exception as e:
            print(f"[Consumidor] Error: {e}")

if __name__ == "__main__":
    consumidor = ConsumidorResultados()
    consumidor.iniciar_consumo()