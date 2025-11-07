"""
Script para ejecutar todos los tests y verificar que funcionen correctamente.
"""

import sys
import os
from pathlib import Path

# Detectar automáticamente el directorio raíz del proyecto
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
for potential_root in [current_dir.parent, current_dir.parent.parent]:
    if (potential_root / "src").exists() and (potential_root / "tests").exists():
        project_root = potential_root
        break

sys.path.insert(0, str(project_root))
os.chdir(project_root)

# Lista de tests a ejecutar
tests = [
    "test_extractors",
    "test_data_models",
    "test_preprocessing",
    "test_analysis",
    "test_reporting",
    "test_flujo_completo",  # Test del flujo completo end-to-end
]

def run_test(test_name):
    """Ejecuta un test y devuelve True si fue exitoso"""
    print(f"\n{'='*80}")
    print(f"EJECUTANDO: {test_name}")
    print(f"{'='*80}\n")
    
    try:
        # Importar y ejecutar el módulo
        module = __import__(f"tests.{test_name}", fromlist=[test_name])
        if hasattr(module, 'main'):
            module.main()
            print(f"\n[OK] {test_name} completado exitosamente")
            return True
        else:
            print(f"\n[WARNING] {test_name} no tiene función main()")
            return False
    except Exception as e:
        print(f"\n[ERROR] {test_name} falló: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecuta todos los tests"""
    print("="*80)
    print("EJECUTANDO TODOS LOS TESTS")
    print("="*80)
    
    results = {}
    for test in tests:
        results[test] = run_test(test)
    
    # Resumen
    print("\n" + "="*80)
    print("RESUMEN DE TESTS")
    print("="*80)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, success in results.items():
        status = "[OK]" if success else "[FAIL]"
        print(f"{status} {test}")
    
    print(f"\nTotal: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("\n[SUCCESS] Todos los tests pasaron exitosamente!")
        return 0
    else:
        print(f"\n[FAILURE] {total - passed} test(s) fallaron")
        return 1

if __name__ == "__main__":
    sys.exit(main())

