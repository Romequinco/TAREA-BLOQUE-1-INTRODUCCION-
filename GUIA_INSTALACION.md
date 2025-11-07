# Guía de Instalación

Guía paso a paso para instalar y configurar el Sistema de Análisis Financiero.

## 📋 Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Conexión a internet (para descargar dependencias y datos)

## 🚀 Instalación Paso a Paso

### Paso 1: Verificar Python

```bash
# Verificar versión de Python
python --version
# Debe mostrar Python 3.8 o superior
```

Si no tienes Python instalado:
- **Windows**: Descarga desde [python.org](https://www.python.org/downloads/)
- **Linux/Mac**: Usa el gestor de paquetes del sistema

### Paso 2: Crear Entorno Virtual

**¿Por qué usar un entorno virtual?**
- Aísla las dependencias del proyecto
- Evita conflictos con otros proyectos
- Facilita la gestión de versiones

```bash
# Crear entorno virtual
python -m venv .venv
```

Esto crea una carpeta `.venv` con un Python independiente.

### Paso 3: Activar Entorno Virtual

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

Si PowerShell da error de ejecución de scripts:
```powershell
# Opción 1: Cambiar política de ejecución (solo para esta sesión)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Opción 2: Usar activate.bat
.venv\Scripts\activate.bat

# Opción 3: Ejecutar directamente sin activar
.venv\Scripts\python.exe [comando]
```

**Windows (CMD):**
```cmd
.venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

**Indicador de activación:**
Cuando el entorno está activado, verás `(.venv)` al inicio de la línea de comandos:
```
(.venv) PS C:\ruta\al\proyecto>
```

### Paso 4: Actualizar pip

```bash
# Actualizar pip a la última versión
python -m pip install --upgrade pip
```

### Paso 5: Instalar Dependencias

```bash
# Instalar todas las dependencias desde requirements.txt
pip install -r requirements.txt
```

**Dependencias principales que se instalarán:**
- `pandas`, `numpy` - Análisis de datos
- `yfinance` - Extracción de datos de Yahoo Finance
- `matplotlib`, `seaborn` - Visualizaciones
- `scipy` - Análisis estadístico
- `pytest`, `pytest-cov` - Testing
- `tabulate` - Formato de tablas
- Y más...

**Tiempo estimado:** 2-5 minutos dependiendo de la conexión.

### Paso 6: Verificar Instalación

```bash
# Verificar que las dependencias se instalaron correctamente
python -c "import pandas, numpy, yfinance, matplotlib; print('✓ Todas las dependencias instaladas')"
```

Si no hay errores, la instalación fue exitosa.

## ⚙️ Configuración Opcional

### API Key de Alpha Vantage (Opcional)

Alpha Vantage es opcional. Si quieres usarlo:

1. **Obtener API Key:**
   - Ve a [alphavantage.co](https://www.alphavantage.co/support/#api-key)
   - Regístrate (gratis)
   - Copia tu API key

2. **Configurar en el proyecto:**
   - Crea un archivo `.env` en la raíz del proyecto
   - Añade la siguiente línea:
   ```
   ALPHAVANTAGE_API_KEY=tu_clave_aqui
   ```

3. **Verificar:**
   ```python
   from dotenv import load_dotenv
   import os
   load_dotenv()
   print(os.getenv('ALPHAVANTAGE_API_KEY'))  # Debe mostrar tu clave
   ```

**Nota:** El proyecto funciona perfectamente sin Alpha Vantage usando solo Yahoo Finance.

## ✅ Verificar que Todo Funciona

### Test Rápido

```bash
# Ejecutar un test simple
python tests/test_preprocessing.py
```

Si ves output con separadores y mensajes `[OK]`, todo está funcionando.

### Test Completo

```bash
# Ejecutar todos los tests
python tests/run_all_tests.py
```

Esto ejecutará todos los tests y mostrará un resumen al final.

## 🔧 Solución de Problemas

### Error: "python no se reconoce como comando"

**Solución:**
- Asegúrate de que Python está en el PATH
- En Windows, marca la opción "Add Python to PATH" durante la instalación
- O usa `py` en lugar de `python`:
  ```bash
  py -m venv .venv
  ```

### Error: "pip no se reconoce"

**Solución:**
```bash
# Usar python -m pip en lugar de pip directamente
python -m pip install -r requirements.txt
```

### Error: "ModuleNotFoundError"

**Solución:**
1. Verifica que el entorno virtual está activado
2. Reinstala las dependencias:
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

### Error: "Permission denied" al instalar

**Solución:**
- En Windows: Ejecuta la terminal como Administrador
- En Linux/Mac: No uses `sudo` con entornos virtuales

### Error: "matplotlib no se puede importar"

**Solución:**
```bash
# Instalar matplotlib explícitamente
pip install matplotlib seaborn scipy
```

### Error: PowerShell "execution of scripts is disabled"

**Solución:**
```powershell
# Cambiar política solo para esta sesión
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# O usar CMD en lugar de PowerShell
```

## 📦 Reinstalación Completa

Si algo falla y quieres empezar de cero:

```bash
# 1. Eliminar entorno virtual
# Windows
rmdir /s .venv

# Linux/Mac
rm -rf .venv

# 2. Crear nuevo entorno virtual
python -m venv .venv

# 3. Activar
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 4. Instalar dependencias
pip install -r requirements.txt
```

## 🎯 Próximos Pasos

Una vez instalado:

1. **Lee el README.md** para entender cómo funciona el sistema
2. **Ejecuta los tests** para ver ejemplos:
   ```bash
   python tests/test_extractors.py
   ```
3. **Ejecuta el ejemplo real** para ver el sistema completo en acción:
   ```bash
   python ejemplo_real.py
   ```
   Esto generará outputs completos en `ejemplos_output/` mostrando:
   - Extracción de 5 activos reales
   - 10 portfolios diferentes con diferentes estrategias
   - Reportes y visualizaciones automáticas
   - Gráficos comparativos
4. **Explora el código** en `src/` para entender la implementación
5. **Crea tus propios scripts** usando los componentes del sistema

## 📝 Notas Adicionales

- **Espacio en disco:** El proyecto requiere aproximadamente 500MB para dependencias
- **Tiempo de instalación:** 2-5 minutos en conexión normal
- **Actualizaciones:** Para actualizar dependencias:
  ```bash
  pip install -r requirements.txt --upgrade
  ```

## 🆘 Obtener Ayuda

Si encuentras problemas:
1. Revisa la sección "Solución de Problemas" arriba
2. Verifica que todas las dependencias están instaladas: `pip list`
3. Ejecuta los tests para identificar el problema específico

