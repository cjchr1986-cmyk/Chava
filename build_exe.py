"""
Script para convertir limpiador_temporal.py a .exe
Requiere: pyinstaller
pip install pyinstaller
"""

import subprocess
import os
import sys
from pathlib import Path

def crear_icono_ico():
    """Crea un archivo .ico personalizado"""
    print("\n[*] Creando icono personalizado...")
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Crear imagen
        img = Image.new('RGB', (256, 256), color='#1E90FF')
        draw = ImageDraw.Draw(img)
        
        # Dibujar un escoba/limpieza
        # Palo de escoba
        draw.rectangle([120, 50, 135, 200], fill='#8B4513')
        
        # Cabeza de escoba
        draw.ellipse([80, 30, 175, 50], fill='#FFD700', outline='#FF8C00', width=3)
        
        # Cerdas
        for i in range(8):
            x = 85 + (i * 10)
            draw.line([(x, 50), (x-5, 65)], fill='#FFD700', width=3)
            draw.line([(x, 50), (x+5, 65)], fill='#FFD700', width=3)
        
        # Checkmark (verificado)
        draw.line([(100, 150), (125, 175)], fill='#00FF00', width=6)
        draw.line([(125, 175), (170, 110)], fill='#00FF00', width=6)
        
        # Guardar como ICO
        icono_path = 'limpiador_icon.ico'
        img.save(icono_path, format='ICO')
        
        print(f"✓ Icono creado: {icono_path}")
        return icono_path
    
    except ImportError:
        print("✗ Pillow no está instalado. Instalando...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pillow', '-q'], check=True)
        return crear_icono_ico()

def instalar_dependencias():
    """Instala las dependencias necesarias"""
    print("[*] Verificando dependencias...")
    
    dependencias = [
        'pyinstaller',
        'pillow',
        'psutil'
    ]
    
    for dep in dependencias:
        try:
            __import__(dep)
            print(f"✓ {dep} ya instalado")
        except ImportError:
            print(f"[*] Instalando {dep}...")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', dep, '-q'], 
                             check=True, timeout=60)
                print(f"✓ {dep} instalado")
            except Exception as e:
                print(f"✗ Error instalando {dep}: {str(e)}")

def crear_exe():
    """Crea el .exe usando PyInstaller"""
    print("\n[*] Creando archivo .exe...")
    
    icono_path = crear_icono_ico()
    
    # Comando simplificado sin --add-data que causa problemas
    comando = [
        'pyinstaller',
        '--onefile',                 # Un solo archivo
        '--windowed',                # Sin consola
        '--icon=' + icono_path,      # Icono personalizado
        '--name=Limpiador-PC',       # Nombre del exe
        'limpiador_temporal.py'
    ]
    
    try:
        print("[*] Compilando con PyInstaller...")
        print("    (Esto puede tomar 2-5 minutos)\n")
        
        resultado = subprocess.run(comando, capture_output=True, text=True)
        
        if resultado.returncode != 0:
            print(f"✗ Error en la compilación:")
            print(resultado.stderr)
            return None
        
        exe_path = os.path.join('dist', 'Limpiador-PC.exe')
        
        if os.path.exists(exe_path):
            tamaño = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"\n✓ Aplicación creada exitosamente!")
            print(f"  📁 Ubicación: {exe_path}")
            print(f"  📊 Tamaño: {tamaño:.2f} MB")
            return exe_path
        else:
            print("✗ Error: El archivo .exe no se creó")
            return None
    
    except subprocess.CalledProcessError as e:
        print(f"✗ Error compilando: {str(e)}")
        return None
    except Exception as e:
        print(f"✗ Error inesperado: {str(e)}")
        return None

def crear_script_batch():
    """Crea un script batch para ejecutar como administrador"""
    print("\n[*] Creando script de ejecución...")
    
    script_batch = '''@echo off
REM Script para ejecutar Limpiador-PC como Administrador
REM Detectar si se ejecuta como admin
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✓ Ejecutando como Administrador...
    cd /d "%~dp0"
    start "" "Limpiador-PC.exe"
) else (
    echo ✗ Se requieren permisos de Administrador
    echo Solicitando elevación...
    powershell -Command "Start-Process '%~0' -Verb RunAs"
)
exit /b
'''
    
    with open('Ejecutar-Como-Admin.bat', 'w', encoding='utf-8') as f:
        f.write(script_batch)
    
    print("✓ Script batch creado: Ejecutar-Como-Admin.bat")

def crear_readme_instalacion():
    """Crea un README con instrucciones de instalación"""
    readme = '''# 🧹 Limpiador Integral de PC - v5.0

## 📦 ¿Qué incluye?

- **Limpiador-PC.exe** - La aplicación principal
- **limpiador_icon.ico** - Icono personalizado
- **Ejecutar-Como-Admin.bat** - Script para ejecutar como administrador

## 🚀 Uso Rápido

### Opción 1: Ejecución Directa
1. Haz doble clic en **Limpiador-PC.exe**
2. Si Windows muestra warning, haz clic en "Ejecutar de todas formas"

### Opción 2: Como Administrador (RECOMENDADO)
1. Click derecho en **Limpiador-PC.exe**
2. Selecciona: **"Ejecutar como administrador"**
3. Acepta el mensaje de Control de Cuentas

### Opción 3: Usar el script batch
1. Haz doble clic en **Ejecutar-Como-Admin.bat**
2. Se ejecutará automáticamente con permisos elevados

## 📋 Funcionalidades Principales

### 🔒 SEGURIDAD Y MALWARE
- Escaneo completo de malware
- Escaneo rápido
- Gestor de cuarentena

### 🧹 LIMPIEZA
- Limpieza rápida
- Limpieza completa
- Limpieza personalizada
- Eliminar archivos ocultos
- Eliminar archivos inactivos

### 📋 DUPLICADOS Y ARCHIVOS
- Buscar archivos duplicados
- Eliminar duplicados automáticamente

### 📝 REGISTRO
- Analizar Registro de Windows
- Reparar entradas inválidas

### ⚡ OPTIMIZACIÓN
- Ver información del sistema
- Optimizar rendimiento
- Optimización ultra completa

## 🎯 Recomendaciones

**Ejecución Semanal:**
```
Opción 12: Optimización Ultra Completa (TODO)
- Tiempo: 20-40 minutos
- Resultado: PC completamente limpio y optimizado
```

**Ejecución Diaria:**
```
Opción 4: Limpieza Rápida
- Tiempo: 2-5 minutos
- Resultado: Archivos temporales eliminados
```

## ⚠️ ADVERTENCIAS IMPORTANTES

1. **SIEMPRE ejecuta como ADMINISTRADOR**
   - Sin permisos de admin no funciona correctamente

2. **Backup del Registro antes de reparar**
   - El programa hace backup automático
   - Pero es buena práctica hacer tu propio backup

3. **No cierres la aplicación durante operaciones largas**
   - Especialmente durante Registro o Duplicados

4. **Archivos en Cuarentena**
   - Se guardan en la carpeta "cuarentena_malware"
   - Puedes recuperarlos si es necesario

## 📊 CARACTERÍSTICAS

✅ Limpieza de archivos temporales  
✅ Detección de malware  
✅ Búsqueda de duplicados  
✅ Análisis de Registro  
✅ Optimización de rendimiento  
✅ Registro completo de actividades  
✅ Icono personalizado  
✅ Interfaz amigable  

---

**Versión:** 5.0  
**Última actualización:** 2026-07-02  
**Desarrollado para:** Windows 10/11  
**Requisitos:** Ejecutar como Administrador

¡Disfruta de tu PC más limpio y rápido! 🚀
'''
    
    with open('README_INSTALACION.md', 'w', encoding='utf-8') as f:
        f.write(readme)
    
    print("✓ Guía creada: README_INSTALACION.md")

def crear_script_instalacion():
    """Crea script de instalación simple"""
    print("\n[*] Creando script de instalación...")
    
    script_bat = '''@echo off
REM Script de instalación del Limpiador-PC
title Instalador - Limpiador PC v5.0
color 0A

cls
echo ============================================================
echo   INSTALADOR - LIMPIADOR INTEGRAL DE PC v5.0
echo ============================================================
echo.
echo [1] Crear acceso directo en Escritorio
echo [2] Crear acceso directo en Menu Inicio
echo [3] Crear acceso directo en ambos lugares
echo [4] Solo ejecutar
echo [5] Salir
echo.
set /p opcion="Selecciona una opcion: "

if "%opcion%"=="1" goto escritorio
if "%opcion%"=="2" goto inicio
if "%opcion%"=="3" goto ambos
if "%opcion%"=="4" goto ejecutar
if "%opcion%"=="5" goto salir

:escritorio
echo.
echo [*] Creando acceso directo en Escritorio...
set desktop=%USERPROFILE%\Desktop
cd /d "%~dp0"
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%desktop%\Limpiador-PC.lnk');$s.TargetPath='%cd%\Limpiador-PC.exe';$s.IconLocation='%cd%\limpiador_icon.ico';$s.Save()"
if %errorLevel% == 0 (
    echo [OK] Acceso directo creado en Escritorio
) else (
    echo [ERROR] No se pudo crear el acceso directo
)
pause
goto fin

:inicio
echo.
echo [*] Creando acceso directo en Menu Inicio...
set startmenu=%APPDATA%\Microsoft\Windows\Start Menu\Programs
cd /d "%~dp0"
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%startmenu%\Limpiador-PC.lnk');$s.TargetPath='%cd%\Limpiador-PC.exe';$s.IconLocation='%cd%\limpiador_icon.ico';$s.Save()"
if %errorLevel% == 0 (
    echo [OK] Acceso directo creado en Menu Inicio
) else (
    echo [ERROR] No se pudo crear el acceso directo
)
pause
goto fin

:ambos
echo.
echo [*] Creando accesos directos...
set desktop=%USERPROFILE%\Desktop
set startmenu=%APPDATA%\Microsoft\Windows\Start Menu\Programs
cd /d "%~dp0"
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut('%desktop%\Limpiador-PC.lnk');$s.TargetPath='%cd%\Limpiador-PC.exe';$s.IconLocation='%cd%\limpiador_icon.ico';$s.Save();$s2=(New-Object -COM WScript.Shell).CreateShortcut('%startmenu%\Limpiador-PC.lnk');$s2.TargetPath='%cd%\Limpiador-PC.exe';$s2.IconLocation='%cd%\limpiador_icon.ico';$s2.Save()"
echo [OK] Accesos directos creados en ambos lugares
pause
goto fin

:ejecutar
echo.
echo [*] Ejecutando Limpiador-PC...
cd /d "%~dp0"
powershell -Command "Start-Process '%cd%\Limpiador-PC.exe' -Verb RunAs"
goto fin

:salir
exit /b

:fin
cls
echo.
echo ============================================================
echo [OK] Operacion completada
echo.
echo Puedes ejecutar Limpiador-PC desde:
echo - Escritorio (si lo seleccionaste)
echo - Menu Inicio (si lo seleccionaste)
echo - O haz doble clic en Limpiador-PC.exe
echo.
echo ============================================================
pause
'''
    
    with open('Instalar.bat', 'w', encoding='utf-8') as f:
        f.write(script_bat)
    
    print("✓ Script de instalación creado: Instalar.bat")

def main():
    """Función principal"""
    print("\n" + "="*60)
    print("   CONVERTIDOR PYTHON A .EXE")
    print("   Limpiador Integral de PC v5.0")
    print("="*60 + "\n")
    
    # Verificar que el archivo Python existe
    if not os.path.exists('limpiador_temporal.py'):
        print("✗ Error: No se encuentra limpiador_temporal.py")
        print("  Coloca este script en la misma carpeta que limpiador_temporal.py")
        sys.exit(1)
    
    print("[*] Iniciando proceso de compilación...\n")
    
    # Instalar dependencias
    instalar_dependencias()
    
    # Crear archivos necesarios
    crear_icono_ico()
    crear_script_batch()
    crear_readme_instalacion()
    crear_script_instalacion()
    
    # Crear EXE
    exe_path = crear_exe()
    
    if exe_path:
        print("\n" + "="*60)
        print("   ✓ COMPILACIÓN COMPLETADA EXITOSAMENTE")
        print("="*60)
        print("\n📁 Archivos generados:\n")
        print("  1. dist/Limpiador-PC.exe - Aplicación principal")
        print("  2. limpiador_icon.ico - Icono personalizado")
        print("  3. Ejecutar-Como-Admin.bat - Ejecutar con permisos")
        print("  4. Instalar.bat - Crear accesos directos")
        print("  5. README_INSTALACION.md - Guía de uso")
        print("\n🚀 Próximos pasos:\n")
        print("  1. Copia estos archivos a una carpeta:")
        print("     - dist/Limpiador-PC.exe")
        print("     - limpiador_icon.ico")
        print("     - Ejecutar-Como-Admin.bat")
        print("     - Instalar.bat")
        print("     - README_INSTALACION.md")
        print("\n  2. Ejecuta Instalar.bat para crear accesos directos")
        print("\n  3. O haz doble clic en Limpiador-PC.exe")
        print("\n⚠️  IMPORTANTE:")
        print("  - Siempre ejecuta como ADMINISTRADOR")
        print("  - Coloca limpiador_icon.ico en la misma carpeta que el .exe")
        print("\n" + "="*60 + "\n")
    else:
        print("\n✗ Error en la compilación")
        print("Intenta estos pasos:")
        print("  1. Verifica que Python está instalado: python --version")
        print("  2. Reinstala pyinstaller: pip install --upgrade pyinstaller")
        print("  3. Vuelve a ejecutar este script")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Proceso cancelado por el usuario.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error inesperado: {str(e)}")
        sys.exit(1)
