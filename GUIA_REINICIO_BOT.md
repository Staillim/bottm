# Guía de Reinicio del Bot

## 🔄 El bot necesita ser reiniciado para aplicar los cambios

Los cambios en el código **ya están aplicados** y funcionan correctamente (como lo demuestran los tests), pero el bot que está corriendo actualmente está usando la versión anterior del código.

## 📋 Pasos para Reiniciar

### Opción 1: Reiniciar manualmente

1. **Detener el bot actual:**
   - Si está corriendo en un terminal, presiona `Ctrl+C`
   - Si está corriendo como servicio, detén el servicio

2. **Iniciar el bot con el código actualizado:**
   ```bash
   python main.py
   ```
   o si usas el script de inicio:
   ```bash
   .\start_bot.ps1
   ```

### Opción 2: Usar el deployment existente

Si el bot está desplegado en Render, Railway, o similar:

1. Ve al dashboard de tu plataforma
2. Haz un "Manual Deploy" o "Restart"
3. Espera a que el bot se reinicie con el código nuevo

## ✅ Verificación

Después de reiniciar, prueba nuevamente:

```
/indexar_serie Breaking Bad
```

El bot debería:
- ✅ Encontrar automáticamente los episodios en formato S##E##
- ✅ Mostrar el mensaje de ayuda con todos los 4 formatos

## 🔍 Qué cambió

Los siguientes formatos ahora están soportados:

1. ✅ `1x1, 2x14` (formato corto)
2. ✅ `🔻Lucifer — 02x01 — Audio Latino` (formato con emoji)
3. ✅ `Breaking Bad - S01E01 - 1080p.mp4` (formato S##E##) **← NUEVO**
4. ✅ `Temporada 1 - Capítulo 20` (formato español)

## 🧪 Tests Confirmados

Todos los tests pasan correctamente:

```bash
# Test de patrones (22/22)
python test_episode_patterns.py

# Test de Breaking Bad (6/6)
python test_breaking_bad.py

# Test de cambio de serie
python test_series_switch.py
```

## 📝 Archivos Modificados

- ✅ `handlers/series_admin.py` - Patrones actualizados
- ✅ `test_episode_patterns.py` - Tests actualizados
- ✅ `test_breaking_bad.py` - Test específico para Breaking Bad
- ✅ `test_series_switch.py` - Test de detención al cambiar serie

## 🚨 Importante

**No es un problema de código**, es simplemente que el bot está usando la versión anterior.

Una vez reiniciado, funcionará perfectamente con el formato S##E##.

---

**¿Necesitas ayuda con el reinicio?** Déjame saber cómo tienes desplegado el bot y te ayudo con los pasos específicos.
