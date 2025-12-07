# Sistema de Puntos y Referidos 🎯💰

## Descripción General

El sistema de puntos y referidos es una funcionalidad completa que permite a los usuarios ganar puntos viendo videos y referir amigos para obtener beneficios adicionales. Incluye medidas anti-farming para mantener la equidad.

## Características Principales

### 🎯 Sistema de Puntos
- **Solo por referidos**: 5 puntos por amigo que se una usando tu código
- **Sin límites diarios**: No hay restricciones en la cantidad de puntos
- **Videos premium**: 1 punto = 1 video sin anuncio
- **Balance persistente**: Los puntos no expiran

### 👥 Sistema de Referidos
- **Códigos únicos**: Cada usuario tiene su propio código de referido
- **Enlaces compartibles**: `https://t.me/botusername?start=ref_CODIGO`
- **Bonificación**: 5 puntos por referido completado
- **Anti-farming**: Un referido por persona, validación de actividad

### 🎬 Sistema de Videos
- **Opción dual**: Ver anuncio gratis o usar puntos para saltar anuncio
- **Elección del usuario**: El usuario decide cómo ver cada video
- **Sin límites**: Siempre se puede ver videos (con o sin puntos)
- **Premium**: Videos sin anuncio usando puntos

### 🔒 Medidas de Seguridad
- **Verificación de referidos**: Solo referidos activos y únicos cuentan
- **Validación de códigos**: Códigos expiran en 30 días
- **Prevención de auto-referidos**: No puedes referirte a ti mismo
- **Sin límites de videos**: Siempre se puede ver contenido

## Comandos Disponibles

### `/referral` - Gestionar referidos
- Muestra tu código de referido actual
- Estadísticas de referidos completados
- Enlace para compartir con amigos
- Opción para generar nuevo código

### `/points` - Ver balance de puntos
- Balance total y disponible
- Puntos usados y ganados
- Historial de transacciones
- Puntos ganados hoy

## Funcionamiento Técnico

### Arquitectura
```
database/models.py          # Modelos SQLAlchemy
database/db_manager.py       # Métodos de BD
utils/referral_system.py     # Lógica de referidos
utils/points_manager.py      # Gestión de puntos
handlers/referral_commands.py # Comandos del bot
handlers/start.py           # Integración en flujo de videos
```

### Base de Datos

#### Tabla `user_points`
```sql
- user_id: ID del usuario (FK a users.telegram_id)
- total_points: Puntos totales acumulados
- available_points: Puntos disponibles para usar
- used_points: Puntos ya utilizados
- last_activity: Última actividad
```

#### Tabla `referrals`
```sql
- referral_code: Código único de 8 caracteres
- referrer_id: Usuario que refiere (FK)
- referred_id: Usuario referido (FK, nullable)
- status: pending/completed/expired
- expires_at: Fecha de expiración
```

#### Tabla `points_transactions`
```sql
- user_points_id: FK a user_points
- transaction_type: earned/used/bonus/referral
- amount: Cantidad de puntos
- description: Descripción de la transacción
- reference_id: ID de referencia opcional
```

## Instalación y Configuración

### 1. Ejecutar Migración
```bash
python migration_points_system.py
```

### 2. Verificar Instalación
```bash
python test_points_system.py
```

### 3. Reiniciar Bot
```bash
python main.py
```

## Uso del Sistema

### Para Usuarios
1. **Ver videos**: Elige entre ver anuncio gratis o usar puntos para saltar anuncio
2. **Referir amigos**: Usa `/referral` para obtener enlace y ganar 5 puntos por referido
3. **Ver balance**: Usa `/points` para ver tus puntos disponibles
4. **Videos premium**: Usa puntos para ver videos sin anuncios

### Flujo de Visualización de Videos
1. Usuario hace clic en "Ver Ahora"
2. Sistema muestra opciones:
   - 📺 **Ver anuncio gratis** (opción por defecto)
   - 💰 **Usar puntos** (si tiene suficientes, sin anuncio)
3. Usuario elige opción y ve el video correspondiente

## Flujo de Integración

### Envio de Videos
1. Usuario hace clic en "Ver Ahora"
2. Sistema verifica si puede ver video:
   - Si tiene puntos → usa automáticamente
   - Si no tiene puntos pero < 5/día → permite ver gratis
   - Si no tiene puntos y >= 5/día → bloquea
3. Registra transacción si usó puntos
4. Muestra mensaje correspondiente

### Referidos por Deep Link
1. Usuario comparte enlace `?start=ref_CODIGO`
2. Nuevo usuario se une con el código
3. Sistema valida código y procesa referido
4. Otorga 5 puntos al referrer
5. Registra transacción

## Configuración

Los valores por defecto se pueden modificar en `utils/points_manager.py`:

```python
POINTS_PER_VIDEO = 0.5      # Puntos por video visto
MAX_POINTS_PER_DAY = 5.0    # Límite diario
REFERRAL_POINTS = 5.0       # Puntos por referido
VIDEO_COST = 1.0           # Costo de video premium
```

## Monitoreo y Logs

### Logs Importantes
- Generación de códigos de referido
- Procesamiento de referidos
- Otorgamiento de puntos
- Uso de puntos en videos
- Errores de validación

### Métricas Útiles
- Total de puntos en circulación
- Referidos completados vs pendientes
- Uso diario de puntos
- Tasa de conversión de referidos

## Solución de Problemas

### Usuario no gana puntos
- Verificar límite diario (5 puntos máximo)
- Revisar logs de transacción
- Confirmar que el video se vio completamente

### Código de referido no funciona
- Verificar expiración (30 días)
- Comprobar que no fue usado antes
- Validar formato del código

### Puntos no se usan
- Verificar balance disponible
- Confirmar integración en send_video_by_message_id
- Revisar logs de error

## Consideraciones de Rendimiento

### Optimizaciones Implementadas
- Índices en campos de búsqueda frecuente
- Consultas asíncronas con SQLAlchemy
- Cache de estados de usuario
- Validaciones eficientes

### Escalabilidad
- Diseño preparado para alto volumen
- Consultas optimizadas
- Manejo eficiente de concurrencia

## Seguridad

### Medidas Implementadas
- Validación de entrada en todos los puntos
- Prevención de SQL injection (ORM)
- Control de rate limiting integrado
- Logs detallados para auditoría

### Mejores Prácticas
- Nunca exponer IDs internos
- Validar todas las operaciones
- Mantener logs de seguridad
- Monitorear uso sospechoso

## Futuras Mejoras

### Funcionalidades Pendientes
- Sistema de niveles de usuario
- Recompensas especiales
- Torneos de referidos
- Integración con pagos

### Optimizaciones
- Cache Redis para balances
- Webhooks para eventos
- Dashboard administrativo
- Analytics avanzados

---

## Soporte

Para problemas o preguntas sobre el sistema:
1. Revisar logs del bot
2. Ejecutar pruebas: `python test_points_system.py`
3. Verificar base de datos: consultas directas
4. Revisar configuración en settings.py

¡El sistema está diseñado para ser robusto, equitativo y escalable! 🚀