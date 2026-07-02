"""
Script para convertir limpiador_temporal.py a .exe
Requiere: pyinstaller
pip install pyinstaller
"""

import subprocess
import os
import sys
from pathlib import Path

def crear_icono_base64():
    """Crea un icono simple en formato base64 (pequeño SVG convertido)"""
    # Esto crea un icono simple de limpieza
    icono_svg = '''
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
        <rect width="256" height="256" fill="#1E90FF"/>
        <path d="M128 40C84 40 48 76 48 120v80c0 22 18 40 40 40h160c22 0 40-18 40-40v-80c0-44-36-80-80-80z" fill="#FFD700"/>
        <rect x="80" y="50" width="96" height="20" fill="#FF6347"/>
        <circle cx="128" cy="140" r="35" fill="#00FF00" opacity="0.7"/>
        <path d="M100 140l15 15 35-35" stroke="#FFFFFF" stroke-width="4" fill="none"/>
    </svg>
    '''
    return icono_svg

def instalar_dependencias():
    """Instala las dependencias necesarias"""
    print("[*] Instalando dependencias necesarias...")
    
    dependencias = [
        'pyinstaller',
        'pillow',
        'psutil'
    ]
    
    for dep in dependencias:
        print(f"[*] Instalando {dep}...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', dep, '-q'], 
                         check=True, timeout=60)
            print(f"✓ {dep} instalado")
        except Exception as e:
            print(f"✗ Error instalando {dep}: {str(e)}")

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

def crear_exe():
    """Crea el .exe usando PyInstaller"""
    print("\n[*] Creando archivo .exe...")
    
    icono_path = crear_icono_ico()
    
    comando = [
        'pyinstaller',
        '--onefile',                          # Un solo archivo
        '--windowed',                         # Sin consola (comentar si quieres consola)
        '--icon=' + icono_path,              # Icono personalizado
        '--add-data=limpiador_temporal.log:.',  # Incluir log
        '--name=Limpiador-PC',               # Nombre del exe
        '--version-file=version.txt',        # Archivo de versión (opcional)
        'limpiador_temporal.py'
    ]
    
    try:
        print("[*] Compilando con PyInstaller...")
        print("    (Esto puede tomar 2-5 minutos)\n")
        
        subprocess.run(comando, check=True)
        
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

def crear_acceso_directo():
    """Crea un acceso directo en el Escritorio"""
    print("\n[*] Creando acceso directo en Escritorio...")
    
    script_vbs = '''Set oWS = WScript.CreateObject("WScript.Shell")
strDesktopPath = oWS.SpecialFolders("Desktop")
Set oLink = oWS.CreateShortcut(strDesktopPath & "\\Limpiador-PC.lnk")
oLink.TargetPath = "%CD%\\Limpiador-PC.exe"
oLink.WorkingDirectory = "%CD%"
oLink.WindowStyle = 1
oLink.IconLocation = "%CD%\\limpiador_icon.ico"
oLink.Save
'''
    
    with open('crear_acceso_directo.vbs', 'w', encoding='utf-8') as f:
        f.write(script_vbs)
    
    print("✓ Script VBS creado: crear_acceso_directo.vbs")

def crear_archivo_version():
    """Crea un archivo de versión para el exe"""
    print("\n[*] Creando información de versión...")
    
    version_info = '''# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=VS_FIXEDFILEINFO(
    # Contains as much info as Windows will allow...
    mask=0x3f,
    mask_invert=0x0,
    # Contains a bitmask that specifies the valid bits 'flags'r
    strFileInfo=(
      ('040904B0', {
        'CompanyName': 'Chava Soft',
        'FileDescription': 'Limpiador Integral de PC - Versión 5.0',
        'FileVersion': '5.0.0.0',
        'InternalName': 'Limpiador-PC',
        'LegalCopyright': '© 2026 Chava Soft. Todos los derechos reservados.',
        'OriginalFilename': 'Limpiador-PC.exe',
        'ProductName': 'Limpiador Integral de PC',
        'ProductVersion': '5.0.0.0'
      })
    ]),
  VarFileInfo=[('Translation', [1033, 1200])]
)
'''
    
    with open('version.txt', 'w', encoding='utf-8') as f:
        f.write(version_info)
    
    print("✓ Archivo de versión creado: version.txt")

def crear_readme_instalacion():
    """Crea un README con instrucciones de instalación"""
    readme = '''# 🧹 Limpiador Integral de PC - v5.0

## Guía de Instalación y Uso

### 📦 ¿Qué incluye?

- **Limpiador-PC.exe** - La aplicación principal
- **limpiador_icon.ico** - Icono personalizado
- **Ejecutar-Como-Admin.bat** - Script para ejecutar como administrador
- **crear_acceso_directo.vbs** - Script para crear acceso directo

### 🚀 Instalación Rápida

1. **Descarga todos los archivos**
   - Limpiador-PC.exe
   - limpiador_icon.ico
   - Ejecutar-Como-Admin.bat

2. **Crea una carpeta** (Ej: C:\\Limpiador-PC)

3. **Coloca todos los archivos en la carpeta**

4. **Crea acceso directo en Escritorio:**
   - Click derecho en Limpiador-PC.exe
   - Enviar a > Escritorio (crear acceso directo)

### ⚙️ Cómo Usar

#### Opción 1: Ejecutar directamente
```
1. Haz doble clic en Limpiador-PC.exe
2. Selecciona "Ejecutar de todas formas" si aparece warning
```

#### Opción 2: Ejecutar como Administrador
```
1. Click derecho en Limpiador-PC.exe
2. Selecciona "Ejecutar como administrador"
3. Acepta el mensaje de control de usuarios
```

#### Opción 3: Usar el script batch
```
1. Haz doble clic en Ejecutar-Como-Admin.bat
2. Se ejecutará automáticamente con permisos elevados
```

### 📋 Funcionalidades Principales

#### 🔒 SEGURIDAD Y MALWARE
- Escaneo completo de malware
- Escaneo rápido
- Gestor de cuarentena

#### 🧹 LIMPIEZA
- Limpieza rápida
- Limpieza completa
- Limpieza personalizada
- Eliminar archivos ocultos
- Eliminar archivos inactivos

#### 📋 DUPLICADOS Y ARCHIVOS
- Buscar archivos duplicados
- Eliminar duplicados automáticamente

#### 📝 REGISTRO
- Analizar Registro de Windows
- Reparar entradas inválidas

#### ⚡ OPTIMIZACIÓN
- Ver información del sistema
- Optimizar rendimiento
- Optimización ultra completa

### 🎯 Recomendaciones

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

### ⚠️ ADVERTENCIAS IMPORTANTES

1. **SIEMPRE ejecuta como ADMINISTRADOR**
   - Sin permisos de admin no funciona correctamente

2. **Backup antes de reparar Registro**
   - El programa hace backup automático
   - Pero es buena práctica hacer tu propio backup

3. **No cierres la aplicación durante operaciones largas**
   - Especialmente durante Registro o Duplicados

4. **Archivos en Cuarentena**
   - Se guardan en la carpeta "cuarentena_malware"
   - Puedes recuperarlos si es necesario

### 📊 RESUMEN MEJORADO

La aplicación reporta:
```
📊 LIMPIEZA:
✓ Archivos eliminados
✓ Archivos reparados
✓ Espacio liberado

🔒 SEGURIDAD:
⚠️ Amenazas detectadas
📦 Archivos cuarentenados

📋 DUPLICADOS:
📁 Duplicados encontrados
🗑️ Duplicados eliminados

📝 REGISTRO:
✓ Entradas reparadas
```

### 🆘 Solución de Problemas

**Error: "No tienes permisos"**
- Solución: Ejecuta como administrador

**Error: "Windows Defender bloqueó la aplicación"**
- Solución: Click en "Más información" > "Ejecutar de todas formas"

**La aplicación se cierra sin hacer nada**
- Solución: Abre desde CMD como admin para ver el error

```bash
cd C:\\Limpiador-PC
Limpiador-PC.exe
```

**Escaneo de malware muy lento**
- Normal: Primer escaneo puede tomar 10+ minutos
- Solución: Usa Opción 2 (Escaneo Rápido)

### 📞 Soporte

- **Registro de Actividades:** limpiador_temporal.log
- **Cuarentena:** carpeta "cuarentena_malware"

Todos los eventos se registran en limpiador_temporal.log

---

**Versión:** 5.0  
**Última actualización:** 2026-07-01  
**Desarrollado para:** Windows 10/11  
**Requisitos:** .NET Framework 4.7+ (incluido en Windows)

¡Disfruta de tu PC más limpio y rápido! 🚀
'''
    
    with open('README_INSTALACION.md', 'w', encoding='utf-8') as f:
        f.write(readme)
    
    print("✓ Guía creada: README_INSTALACION.md")

def crear_script_completo():
    """Crea un script todo en uno"""
    print("\n[*] Creando script de instalación completa...")
    
    script_completo = '''@echo off
REM Script de instalación del Limpiador-PC
title Instalador - Limpiador PC v5.0
color 0A

cls
echo ============================================================
echo   INSTALADOR - LIMPIADOR INTEGRAL DE PC v5.0
echo ============================================================
echo.
echo [1] Crear acceso directo en Escritorio
echo [2] Crear acceso directo en Inicio
echo [3] Crear acceso directo en ambos lugares
echo [4] Salir
echo.
set /p opcion="Selecciona una opcion: "

if "%opcion%"=="1" goto escritorio
if "%opcion%"=="2" goto inicio
if "%opcion%"=="3" goto ambos
if "%opcion%"=="4" goto salir
goto inicio

:escritorio
echo.
echo [*] Creando acceso directo en Escritorio...
set desktop=%USERPROFILE%\Desktop
mklink "%desktop%\Limpiador-PC.lnk" "%CD%\Limpiador-PC.exe" >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Acceso directo creado en Escritorio
) else (
    echo [ERROR] No se pudo crear el acceso directo
)
pause
goto fin

:inicio
echo.
echo [*] Creando acceso directo en Menú Inicio...
set startmenu=%APPDATA%\Microsoft\Windows\Start Menu\Programs
mklink "%startmenu%\Limpiador-PC.lnk" "%CD%\Limpiador-PC.exe" >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Acceso directo creado en Menú Inicio
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
mklink "%desktop%\Limpiador-PC.lnk" "%CD%\Limpiador-PC.exe" >nul 2>&1
mklink "%startmenu%\Limpiador-PC.lnk" "%CD%\Limpiador-PC.exe" >nul 2>&1
echo [OK] Accesos directos creados en ambos lugares
pause
goto fin

:salir
exit /b

:fin
cls
echo.
echo ============================================================
echo [OK] Instalacion completada
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
        f.write(script_completo)
    
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
    crear_archivo_version()
    crear_icono_ico()
    crear_script_batch()
    crear_acceso_directo()
    crear_readme_instalacion()
    crear_script_completo()
    
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
        print("  1. Copia todos los archivos a una carpeta (Ej: C:\\Limpiador-PC)")
        print("  2. Ejecuta Instalar.bat para crear accesos directos")
        print("  3. O haz doble clic en Limpiador-PC.exe")
        print("\n⚠️  IMPORTANTE:")
        print("  - Siempre ejecuta como ADMINISTRADOR")
        print("  - Coloca limpiador_icon.ico en la misma carpeta")
        print("\n" + "="*60 + "\n")
    else:
        print("\n✗ Error en la compilación")
        sys.exit(1)

if __name__ == "__main__":
    main()
