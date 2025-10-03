// Estado de la aplicación
let estadoApp = {
    solicitudesPendientes: new Map(),
    notificacionesCargadas: false
};

// Función para solicitar adopción
async function solicitarAdopcion(mascotaId) {
    const boton = document.querySelector(`[data-mascota-id="${mascotaId}"] .btn-adoptar`);
    const nombreMascota = mascotaId.split('_')[0];
    
    // Verificar si ya hay una solicitud pendiente
    if (estadoApp.solicitudesPendientes.has(mascotaId)) {
        mostrarNotificacionLocal({
            tipo: 'warning',
            mensaje: `Ya estás procesando adopción para ${nombreMascota}`,
            timestamp: new Date()
        });
        return;
    }
    
    // Pedir nombre del usuario
    const usuarioNombre = prompt(`Hola! ¿Cuál es tu nombre para adoptar a ${nombreMascota}?`);
    
    if (!usuarioNombre) {
        mostrarNotificacionLocal({
            tipo: 'info',
            mensaje: 'Solicitud cancelada',
            timestamp: new Date()
        });
        return;
    }

    // Pedir salario del usuario
    const usuarioSalario = prompt(`¿Cuál es tu salario mensual? (Solo números, sin puntos)\n`);
    
    if (!usuarioSalario) {
        mostrarNotificacionLocal({
            tipo: 'info',
            mensaje: 'Solicitud cancelada - Salario no proporcionado',
            timestamp: new Date()
        });
        return;
    }

    // Validar que el salario sea un número
    const salarioNumero = parseInt(usuarioSalario.replace(/[^0-9]/g, ''));
    if (isNaN(salarioNumero)) {
        mostrarNotificacionLocal({
            tipo: 'error',
            mensaje: 'El salario debe ser un número válido',
            timestamp: new Date()
        });
        return;
    }

    try {
        // Actualizar UI inmediatamente
        boton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';
        boton.disabled = true;
        boton.classList.add('procesando');
        
        // Marcar como pendiente
        estadoApp.solicitudesPendientes.set(mascotaId, true);
        
        console.log(`Enviando solicitud para ${mascotaId} - Usuario: ${usuarioNombre} - Salario: $${salarioNumero.toLocaleString()}`);
        
        // Enviar solicitud al servidor
        const response = await fetch('/solicitar_adopcion', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                mascota_id: mascotaId,
                usuario_nombre: usuarioNombre,
                usuario_salario: salarioNumero
            })
        });

        const resultado = await response.json();
        
        if (resultado.estado === 'success') {
            // Actualizar el botón según el resultado
            actualizarBotonMascota(mascotaId, resultado.resultado.aprobado);
            
            // SOLO UNA recarga de notificaciones después de la acción
            await cargarNotificaciones();
            
        } else {
            throw new Error(resultado.error);
        }

    } catch (error) {
        console.error('Error:', error);
        
        mostrarNotificacionLocal({
            tipo: 'error',
            mensaje: 'Error al conectar con el servidor. Verifica que RabbitMQ esté ejecutándose.',
            timestamp: new Date()
        });
        
        // Restaurar botón en caso de error
        restaurarBoton(boton);
        
    } finally {
        // Remover de pendientes después de un tiempo
        setTimeout(() => {
            estadoApp.solicitudesPendientes.delete(mascotaId);
        }, 3000);
    }
}

// Función para restaurar botón
function restaurarBoton(boton) {
    boton.innerHTML = '<i class="fas fa-heart"></i> Solicitar Adopción';
    boton.disabled = false;
    boton.classList.remove('procesando', 'aprobado', 'rechazado');
    boton.style.background = '';
}

// Función para actualizar el estado del botón
function actualizarBotonMascota(mascotaId, aprobado) {
    const boton = document.querySelector(`[data-mascota-id="${mascotaId}"] .btn-adoptar`);
    if (!boton) return;
    
    if (aprobado) {
        boton.innerHTML = '<i class="fas fa-check"></i> Aprobado!';
        boton.disabled = true;
        boton.classList.remove('procesando');
        boton.classList.add('aprobado');
        boton.style.background = 'linear-gradient(135deg, #06D6A0, #00B894)';
    } else {
        boton.innerHTML = '<i class="fas fa-times"></i> No aprobado';
        boton.disabled = false;
        boton.classList.remove('procesando');
        boton.classList.add('rechazado');
        boton.style.background = 'linear-gradient(135deg, #EF476F, #E84393)';
        
        // Restaurar después de 3 segundos SIN recargar notificaciones
        setTimeout(() => {
            if (!boton.disabled) { // Solo si no fue aprobado después
                boton.innerHTML = '<i class="fas fa-heart"></i> Intentar nuevamente';
                boton.classList.remove('rechazado');
                boton.style.background = 'linear-gradient(135deg, var(--primary), var(--secondary))';
            }
        }, 3000);
    }
}

// Función para mostrar notificaciones locales (solo para errores)
function mostrarNotificacionLocal(notificacion) {
    const container = document.getElementById('notificaciones-container');
    const placeholder = container.querySelector('.notificacion-placeholder');
    
    if (placeholder) {
        placeholder.style.display = 'none';
    }
    
    const notificacionElement = document.createElement('div');
    notificacionElement.className = `notificacion ${notificacion.tipo}`;
    
    const tiempo = new Date(notificacion.timestamp).toLocaleTimeString();
    
    notificacionElement.innerHTML = `
        <div class="notificacion-header">
            <span class="notificacion-tipo">${notificacion.tipo.toUpperCase()}</span>
            <span class="notificacion-tiempo">${tiempo}</span>
        </div>
        <div class="notificacion-mensaje">${notificacion.mensaje}</div>
    `;
    
    container.insertBefore(notificacionElement, container.firstChild);
    
    // Efecto de entrada
    notificacionElement.style.animation = 'slideIn 0.5s ease';
    
    // Auto-eliminar después de 6 segundos
    setTimeout(() => {
        if (notificacionElement.parentNode) {
            notificacionElement.style.animation = 'slideOut 0.5s ease';
            setTimeout(() => {
                if (notificacionElement.parentNode) {
                    notificacionElement.remove();
                }
                // Mostrar placeholder si no hay notificaciones
                if (container.querySelectorAll('.notificacion').length === 0) {
                    placeholder.style.display = 'block';
                }
            }, 500);
        }
    }, 6000);
    
    // Limitar a 8 notificaciones
    const notificaciones = container.querySelectorAll('.notificacion');
    if (notificaciones.length > 8) {
        notificaciones[notificaciones.length - 1].remove();
    }
}

// Función para cargar notificaciones del servidor
async function cargarNotificaciones() {
    try {
        const response = await fetch('/notificaciones');
        const notificaciones = await response.json();
        
        const container = document.getElementById('notificaciones-container');
        const placeholder = container.querySelector('.notificacion-placeholder');
        
        if (notificaciones.length > 0) {
            placeholder.style.display = 'none';
            
            // Limpiar contenedor (excepto placeholder)
            const notificacionesExistentes = container.querySelectorAll('.notificacion');
            notificacionesExistentes.forEach(n => n.remove());
            
            // Agregar nuevas notificaciones
            notificaciones.forEach(notif => {
                const notificacionElement = document.createElement('div');
                notificacionElement.className = `notificacion ${notif.tipo}`;
                
                notificacionElement.innerHTML = `
                    <div class="notificacion-header">
                        <span class="notificacion-tipo">${notif.titulo}</span>
                        <span class="notificacion-tiempo">${notif.timestamp}</span>
                    </div>
                    <div class="notificacion-mensaje">${notif.mensaje}</div>
                `;
                
                container.appendChild(notificacionElement);
            });
        } else {
            // Mostrar placeholder si no hay notificaciones
            placeholder.style.display = 'block';
        }
        
        estadoApp.notificacionesCargadas = true;
        
    } catch (error) {
        console.error('Error cargando notificaciones:', error);
    }
}

// Función para limpiar notificaciones
async function limpiarNotificaciones() {
    try {
        await fetch('/limpiar_notificaciones', { method: 'POST' });
        // Recargar notificaciones SOLO UNA VEZ después de limpiar
        await cargarNotificaciones();
    } catch (error) {
        console.error('Error limpiando notificaciones:', error);
    }
}

// Inicializar aplicación
document.addEventListener('DOMContentLoaded', function() {
    console.log('PetConnect con RabbitMQ - VALIDACIÓN DE SALARIO ACTIVADA');
    console.log('Mínimo requerido: $1,600,000');
    console.log('GETs exactos: 1 al cargar, 1 por adopción, 1 por limpiar');
    
    // Cargar notificaciones iniciales SOLO UNA VEZ
    cargarNotificaciones();
    
    // Efectos de scroll suave
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Agregar botón para limpiar notificaciones
    const notificacionesSection = document.querySelector('.notificaciones-live');
    const limpiarBtn = document.createElement('button');
    limpiarBtn.innerHTML = '<i class="fas fa-broom"></i> Limpiar Notificaciones';
    limpiarBtn.style.cssText = `
        background: linear-gradient(135deg, #FF6B6B, #4ECDC4);
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 25px;
        cursor: pointer;
        margin-top: 15px;
        font-size: 14px;
    `;
    limpiarBtn.onclick = limpiarNotificaciones;
    
    const container = notificacionesSection.querySelector('.container');
    container.appendChild(limpiarBtn);
});

// Agregar estilos CSS adicionales
const estilosAdicionales = `
@keyframes slideOut {
    from {
        opacity: 1;
        transform: translateX(0);
    }
    to {
        opacity: 0;
        transform: translateX(-100%);
    }
}

.btn-adoptar.procesando {
    background: linear-gradient(135deg, #FFD166, #FFB347) !important;
    cursor: not-allowed;
}

.btn-adoptar.aprobado {
    background: linear-gradient(135deg, #06D6A0, #00B894) !important;
}

.btn-adoptar.rechazado {
    background: linear-gradient(135deg, #EF476F, #E84393) !important;
}

.fa-spinner {
    animation: spin 1s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.notificacion.envio {
    border-left-color: #2196F3;
    background: linear-gradient(135deg, #e3f2fd, #ffffff);
}

.notificacion.procesamiento {
    border-left-color: #FF9800;
    background: linear-gradient(135deg, #fff3e0, #ffffff);
}

.notificacion.respuesta {
    border-left-color: #4CAF50;
    background: linear-gradient(135deg, #e8f5e8, #ffffff);
}

.notificacion.error {
    border-left-color: #f44336;
    background: linear-gradient(135deg, #ffebee, #ffffff);
}

.notificacion.info {
    border-left-color: #2196F3;
    background: linear-gradient(135deg, #e3f2fd, #ffffff);
}
`;

// Injectar estilos
const styleSheet = document.createElement('style');
styleSheet.textContent = estilosAdicionales;
document.head.appendChild(styleSheet);