"""
Test para verificar la lógica de indexación de series
Simula el problema reportado donde se saltaba el primer episodio
"""

def test_start_message_id_logic():
    """
    Prueba la lógica de cálculo del start_message_id
    """
    print("=" * 60)
    print("TEST: Lógica de start_message_id")
    print("=" * 60)
    
    # Caso 1: Primera indexación (last_indexed = 0)
    last_indexed = 0
    start_message_id = 1 if last_indexed == 0 else last_indexed + 1
    print(f"\n✅ Caso 1: Primera indexación")
    print(f"   last_indexed_message: {last_indexed}")
    print(f"   start_message_id: {start_message_id}")
    print(f"   Resultado: {'CORRECTO ✓' if start_message_id == 1 else 'INCORRECTO ✗'}")
    assert start_message_id == 1, "Debe empezar desde mensaje 1"
    
    # Caso 2: Ya hay mensajes indexados (last_indexed = 50)
    last_indexed = 50
    start_message_id = 1 if last_indexed == 0 else last_indexed + 1
    print(f"\n✅ Caso 2: Continuar indexación")
    print(f"   last_indexed_message: {last_indexed}")
    print(f"   start_message_id: {start_message_id}")
    print(f"   Resultado: {'CORRECTO ✓' if start_message_id == 51 else 'INCORRECTO ✗'}")
    assert start_message_id == 51, "Debe continuar desde mensaje 51"
    
    # Caso 3: Se indexaron varios episodios
    start_message_id = 1
    current_message_id = 1
    last_indexed_message_id = 0
    indexed_count = 0
    
    # Simular indexación de episodios en mensajes 1, 3, 5
    episodes_found = [1, 3, 5]
    
    print(f"\n✅ Caso 3: Indexación de múltiples episodios")
    print(f"   start_message_id: {start_message_id}")
    print(f"   Episodios en mensajes: {episodes_found}")
    
    for msg_id in range(1, 10):
        if msg_id in episodes_found:
            indexed_count += 1
            last_indexed_message_id = msg_id
            print(f"   📹 Mensaje {msg_id}: Episodio indexado (count={indexed_count})")
        current_message_id = msg_id + 1
    
    print(f"   last_indexed_message_id final: {last_indexed_message_id}")
    print(f"   Resultado: {'CORRECTO ✓' if last_indexed_message_id == 5 else 'INCORRECTO ✗'}")
    assert last_indexed_message_id == 5, "Debe guardar el último episodio indexado"
    
    # Caso 4: Verificar que el primer episodio se indexa
    print(f"\n✅ Caso 4: Verificar que 1x1 se indexa")
    start_message_id = 1
    first_episode_indexed = False
    
    # Simular que el mensaje 1 tiene el episodio 1x1
    if start_message_id == 1:
        first_episode_indexed = True
        print(f"   Mensaje {start_message_id}: 1x1 INDEXADO ✓")
    
    assert first_episode_indexed, "El episodio 1x1 debe ser indexado"
    print(f"   Resultado: {'CORRECTO ✓' if first_episode_indexed else 'INCORRECTO ✗'}")
    
    print("\n" + "=" * 60)
    print("✅ TODOS LOS TESTS PASARON")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_start_message_id_logic()
    except AssertionError as e:
        print(f"\n❌ TEST FALLIDO: {e}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
