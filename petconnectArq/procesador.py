from conexion import conectar_rabbitmq, declarar_colas
import json
import time
import random
import pika
class ProcesadorAdopciones:
    def __init__(self):
        self.canal = conectar_rabbitmq()
        declarar_colas(self.canal)
        self.mascotas_info = {
            'Budy_001': {'nombre': 'Budy', 'tipo': 'perro', 'dificultad': 'baja'},
            'Luna_002': {'nombre': 'Luna', 'tipo': 'gato', 'dificultad': 'baja'},
            'Max_003': {'nombre': 'Max', 'tipo': 'perro', 'dificultad': 'media'},
            'Molly_004': {'nombre': 'Molly', 'tipo': 'perro', 'dificultad': 'alta'},
            'Simba_005': {'nombre': 'Simba', 'tipo': 'gato', 'dificultad': 'media'}
        }
    
    def procesar_solicitud(self, ch, method, properties, body):
        """Procesa una solicitud de adopción recibida."""
        try:
            solicitud = json.loads(body.decode())
            mascota_id = solicitud['mascota_id']
            usuario_id = solicitud['usuario_id']
            
            print(f"🐕 [Procesador] Procesando solicitud: {mascota_id} para {usuario_id}")
            
            # Simular tiempo de procesamiento realista
            tiempo_procesamiento = random.uniform(1, 3)
            time.sleep(tiempo_procesamiento)
            
            # Validar la adopción con criterios más realistas
            resultado = self.validar_adopcion_completa(solicitud)
            
            # Publicar resultado
            self.publicar_resultado(solicitud, resultado)
            
            print(f"✅ [Procesador] Solicitud procesada: {mascota_id} - {'APROBADA' if resultado['aprobado'] else 'RECHAZADA'}")
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            print(f"❌ [Procesador] Error procesando solicitud: {e}")
    
    def validar_adopcion_completa(self, solicitud):
        """Valida la adopción con criterios detallados."""
        datos = solicitud.get('datos_adicionales', {})
        mascota_id = solicitud['mascota_id']
        info_mascota = self.mascotas_info.get(mascota_id, {})
        
        # Criterios de validación
        criterios = {
            'experiencia_suficiente': self.validar_experiencia(datos, info_mascota),
            'vivienda_adecuada': self.validar_vivienda(datos, info_mascota),
            'compatibilidad_animales': self.validar_compatibilidad(datos, info_mascota),
            'tiempo_suficiente': self.validar_tiempo(datos),
            'estabilidad_economica': random.random() > 0.2  # 80% de aprobación
        }
        
        # Calcular puntaje
        puntaje_total = sum(1 for criterio in criterios.values() if criterio)
        aprobado = puntaje_total >= 3  # Necesita al menos 3 de 5 criterios
        
        # Generar mensaje personalizado
        mensaje = self.generar_mensaje_resultado(aprobado, criterios, info_mascota)
        
        return {
            'aprobado': aprobado,
            'puntaje': puntaje_total,
            'criterios_evaluados': criterios,
            'mensaje': mensaje,
            'fecha_procesamiento': time.time(),
            'tiempo_procesamiento_segundos': round(time.time() - solicitud['timestamp'], 2)
        }
    
    def validar_experiencia(self, datos, info_mascota):
        """Valida experiencia previa con mascotas."""
        tiene_experiencia = datos.get('experiencia_previa', False)
        dificultad = info_mascota.get('dificultad', 'baja')
        
        if dificultad == 'alta':
            return tiene_experiencia
        elif dificultad == 'media':
            return tiene_experiencia or random.random() > 0.3
        else:
            return True  # Baja dificultad, no necesita experiencia
    
    def validar_vivienda(self, datos, info_mascota):
        """Valida que la vivienda sea adecuada."""
        tipo_vivienda = datos.get('tipo_vivienda', 'desconocido')
        tipo_mascota = info_mascota.get('tipo', 'perro')
        
        if tipo_mascota == 'perro':
            return tipo_vivienda in ['casa', 'apartamento']
        else:  # gato
            return tipo_vivienda in ['casa', 'apartamento', 'duplex']
    
    def validar_compatibilidad(self, datos, info_mascota):
        """Valida compatibilidad con otros animales."""
        tiene_otros_animales = datos.get('otros_animales', False)
        
        if not tiene_otros_animales:
            return True
        
        # Si tiene otros animales, validar compatibilidad
        return random.random() > 0.4  # 60% de compatibilidad
    
    def validar_tiempo(self, datos):
        """Valida que tenga tiempo suficiente."""
        return random.random() > 0.3  # 70% de aprobación
    
    def generar_mensaje_resultado(self, aprobado, criterios, info_mascota):
        """Genera mensaje personalizado según el resultado."""
        nombre_mascota = info_mascota.get('nombre', 'la mascota')
        
        if aprobado:
            mensajes = [
                f"¡Felicidades! 🎉 Has sido aprobado para adoptar a {nombre_mascota}.",
                f"¡Buenas noticias! 🤗 {nombre_mascota} pronto será parte de tu familia.",
                f"¡Adopción aprobada! 🐾 {nombre_mascota} te está esperando.",
                f"¡Completaste el proceso! ✅ Prepárate para recibir a {nombre_mascota}."
            ]
        else:
            mensajes = [
                f"Lo sentimos 😔, no cumples con los requisitos para adoptar a {nombre_mascota}.",
                f"Por esta vez no fue posible 😟. {nombre_mascota} necesita otro tipo de hogar.",
                f"Tu solicitud no pudo ser aprobada 📝. Te invitamos a ver otras mascotas.",
                f"Los requisitos no coinciden 🔍. Pero tenemos muchos amigos esperando por ti."
            ]
        
        return random.choice(mensajes)
    
    def publicar_resultado(self, solicitud, resultado):
        """Publica el resultado del procesamiento."""
        mensaje_resultado = {
            'solicitud_original': solicitud,
            'resultado': resultado,
            'procesado_por': 'sistema_adopciones_v2',
            'timestamp': time.time()
        }
        
        self.canal.basic_publish(
            exchange='',
            routing_key='resultados_adopcion',
            body=json.dumps(mensaje_resultado),
            properties=pika.BasicProperties(delivery_mode=2)
        )
    
    def iniciar_procesamiento(self):
        """Inicia el consumo de solicitudes de adopción."""
        print("🚀 [Procesador v2] Iniciando procesador inteligente...")
        print("📊 Sistema de validación con 5 criterios activado")
        
        self.canal.basic_qos(prefetch_count=1)
        self.canal.basic_consume(
            queue='solicitudes_adopcion',
            on_message_callback=self.procesar_solicitud
        )
        
        try:
            self.canal.start_consuming()
        except KeyboardInterrupt:
            print("⏹️ [Procesador] Deteniendo procesador...")
        except Exception as e:
            print(f"💥 [Procesador] Error: {e}")

if __name__ == "__main__":
    procesador = ProcesadorAdopciones()
    procesador.iniciar_procesamiento()