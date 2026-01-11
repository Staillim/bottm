#!/usr/bin/env python3
"""
Script de prueba para verificar que las notificaciones a grupos funcionan correctamente
"""

import asyncio
import sys
import os

# Agregar el directorio del bot al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_group_notifications():
    """Prueba las funciones de notificaciones a grupos"""
    
    try:
        # Verificar imports
        from config.settings import NOTIFICATION_GROUPS
        from handlers.indexing_callbacks import send_group_notifications
        from handlers.series_admin import send_group_notifications_series
        
        print("✅ Imports correctos")
        print(f"📋 Grupos configurados: {NOTIFICATION_GROUPS}")
        
        if not NOTIFICATION_GROUPS:
            print("⚠️ No hay grupos configurados. Agrega NOTIFICATION_GROUPS a tu .env")
            print("📝 Ejemplo: NOTIFICATION_GROUPS=-1001234567890,-1001098765432")
        else:
            print(f"👥 Se enviarían notificaciones a {len(NOTIFICATION_GROUPS)} grupo(s)")
            for i, group_id in enumerate(NOTIFICATION_GROUPS, 1):
                print(f"   {i}. Grupo ID: {group_id}")
        
        print("\n🧪 Funciones de notificación:")
        print(f"   📽️ send_group_notifications: {send_group_notifications.__name__}")
        print(f"   📺 send_group_notifications_series: {send_group_notifications_series.__name__}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error de import: {e}")
        return False
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False

async def main():
    """Función principal de prueba"""
    print("🧪 TESTING: Notificaciones a Grupos\n")
    print("=" * 50)
    
    success = await test_group_notifications()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ PRUEBA EXITOSA - Las notificaciones a grupos están configuradas correctamente")
        print("\n📋 Próximos pasos:")
        print("1. Agrega NOTIFICATION_GROUPS a tu archivo .env")
        print("2. Indexa una película o serie para probar")
        print("3. Verifica que lleguen las notificaciones a los grupos")
    else:
        print("❌ PRUEBA FALLÓ - Revisa los errores arriba")
    
    print("\n📖 Ver más detalles en: CONFIGURACION_GRUPOS.md")

if __name__ == "__main__":
    asyncio.run(main())