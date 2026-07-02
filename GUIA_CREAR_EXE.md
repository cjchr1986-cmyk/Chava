# 🧹 GUÍA COMPLETA: CONVERTIR A APLICACIÓN .EXE

## 📋 PASOS PARA CREAR TU APLICACIÓN

### **PASO 1: Descargar los archivos necesarios**

Descarga estos 2 archivos del repositorio:
1. `limpiador_temporal.py` - Tu programa principal
2. `build_exe.py` - Script para compilar

**📁 Coloca ambos archivos en la MISMA carpeta**

---

### **PASO 2: Abrir CMD/PowerShell**

#### Opción A: Desde la carpeta
1. Abre la carpeta donde están los archivos
2. Click derecho en espacio vacío
3. Selecciona: "Abrir terminal aquí" o "Abrir PowerShell aquí"

#### Opción B: Manual
1. Presiona `Win + R`
2. Escribe: `cmd`
3. Navega a tu carpeta:
```bash
cd C:\ruta\a\tu\carpeta
```

---

### **PASO 3: Instalar herramientas necesarias (UNA SOLA VEZ)**

En la terminal, ejecuta:

```bash
pip install pyinstaller pillow psutil
```

**Espera a que termine** (2-5 minutos)

---

### **PASO 4: Ejecutar el compilador**

En la misma terminal, escribe:

```bash
python build_exe.py
```

**Esto hará:**
✅ Crear icono personalizado (escoba verde)
✅ Generar archivo de versión
✅ Compilar a .exe
✅ Crear scripts batch
✅ Generar guía de instalación

**⏱️ Tiempo: 5-15 minutos (depende de tu PC)**

---

### **PASO 5: Verificar que se creó todo**

Si ves este mensaje:
```
============================================================
   ✓ COMPILACIÓN COMPLETADA EXITOSAMENTE
============================================================
```

**¡EXCELENTE!** Los archivos están listos.

---

## 📦 ARCHIVOS GENERADOS

Después de ejecutar `build_exe.py`, tendrás:

```
📁 Tu Carpeta/
├── 📁 dist/
│   └── 🎯 Limpiador-PC.exe ← TU APLICACIÓN
├── 📁 build/
├── limpiador_temporal.py
├── build_exe.py
├── limpiador_icon.ico ← Icono personalizado
├── version.txt
├── Ejecutar-Como-Admin.bat
├── Instalar.bat
├── README_INSTALACION.md
└── Limpiador-PC.spec
```

---

## 🚀 CÓMO USAR LA APLICACIÓN

### **Opción 1: Ejecución Rápida**
1. Ve a la carpeta `dist`
2. Haz doble clic en `Limpiador-PC.exe`
3. Si Windows muestra warning, haz clic en "Ejecutar de todas formas"

### **Opción 2: Como Administrador (RECOMENDADO)**
1. Click derecho en `Limpiador-PC.exe`
2. Selecciona: "Ejecutar como administrador"
3. Acepta el mensaje de Control de Cuentas de Usuario

### **Opción 3: Usar el script batch**
1. Haz doble clic en `Ejecutar-Como-Admin.bat`
2. Se ejecutará automáticamente con permisos

### **Opción 4: Crear acceso directo en Escritorio**
1. Haz doble clic en `Instalar.bat`
2. Selecciona opción 1 (Escritorio)
3. Aparecerá icono en tu Escritorio

---

## ⚙️ CONFIGURACIÓN AVANZADA

### Si quieres cambiar el nombre del .exe

Edita `build_exe.py` y busca:
```python
'--name=Limpiador-PC',
```

Cámbialo a:
```python
'--name=MiLimpiador',
```

### Si quieres agregar consola (para ver errores)

Busca esta línea:
```python
'--windowed',  # Sin consola
```

Cámbialo a:
```python
# '--windowed',  # Comentado para mostrar consola
```

### Si quieres cambiar el icono

1. Crea tu propio icono (.ico)
2. Colócalo en la carpeta
3. En `build_exe.py`, cambia:
```python
'--icon=' + icono_path,
```

A:
```python
'--icon=mi_icono.ico',
```

---

## 🆘 SOLUCIÓN DE PROBLEMAS

### **Error: "No se encuentra limpiador_temporal.py"**
**Solución:** 
- Verifica que ambos archivos estén en la misma carpeta
- Asegúrate de usar la ruta correcta

### **Error: "pip no es reconocido"**
**Solución:**
- Python no está en el PATH
- Descarga Python nuevamente desde python.org
- **✓ Marca la opción "Add Python to PATH" durante instalación**

### **Error: "pyinstaller no se encuentra"**
**Solución:**
```bash
pip install pyinstaller --upgrade
```

### **El .exe no se ejecuta**
**Solución:**
1. Asegúrate de tener `limpiador_icon.ico` en la misma carpeta que el .exe
2. Ejecuta como Administrador
3. Verifica que no esté en carpeta protegida (Programa Files)

### **Windows Defender bloqueó el archivo**
**Normal y seguro.** Haz clic en:
- "Más información"
- "Ejecutar de todas formas"

### **El programa se cierra inmediatamente**
**Solución:** Ejecuta desde terminal para ver el error:
```bash
cd dist
Limpiador-PC.exe
```

---

## 📊 ESTRUCTURA DE LA APLICACIÓN

```
LIMPIADOR-PC v5.0
├── 🔒 SEGURIDAD Y MALWARE
│   ├── Escaneo completo
│   ├── Escaneo rápido
│   └── Gestor de cuarentena
├── 🧹 LIMPIEZA
│   ├── Limpieza rápida
│   ├── Limpieza completa
│   └── Limpieza personalizada
├── 📋 DUPLICADOS
│   ├── Buscar duplicados
│   └── Eliminar duplicados
├── 📝 REGISTRO
│   └── Analizar y reparar
└── ⚡ OPTIMIZACIÓN
    ├── Info del sistema
    ├── Optimizar rendimiento
    └── Ultra completa
```

---

## 💾 DISTRIBUCIÓN Y PORTABILIDAD

### **Tu aplicación es PORTABLE**
✅ Puedes copiarla a USB  
✅ Funciona sin instalador  
✅ No requiere archivos adicionales  
✅ Se ejecuta desde cualquier lado  

### **Para compartir con otros:**
1. Copia estos archivos a una carpeta:
   - `Limpiador-PC.exe`
   - `limpiador_icon.ico`
   - `README_INSTALACION.md`

2. Crea un ZIP con los 3 archivos

3. Comparte el ZIP

### **La otra persona:**
1. Descarga y descomprime
2. Haz doble clic en `Limpiador-PC.exe`
3. ¡Listo!

---

## 🎯 OPTIMIZACIONES ÚTILES

### Si quieres un .exe más pequeño (15-20 MB):
Usa esta opción:
```python
'--onefile',
'--optimize=2',  # Agregar esto
```

### Si quieres incluir archivos adicionales:
```python
'--add-data=archivo.txt:.',
'--add-data=carpeta:carpeta',
```

### Si quieres icono en la barra de tareas:
Ya está incluido en el código

---

## 📝 CHECKLIST FINAL

- [ ] Descargué `limpiador_temporal.py` y `build_exe.py`
- [ ] Están en la MISMA carpeta
- [ ] Instalé Python 3.8+ con PATH
- [ ] Instalé dependencias: `pip install pyinstaller pillow psutil`
- [ ] Ejecuté: `python build_exe.py`
- [ ] Recibí mensaje de éxito
- [ ] Encontré `Limpiador-PC.exe` en carpeta `dist/`
- [ ] Probé ejecutar como Administrador
- [ ] ¡Funciona perfecto!

---

## 🚀 PRÓXIMOS PASOS

1. **Crear carpeta de instalación:**
   ```bash
   mkdir C:\Limpiador-PC
   ```

2. **Copiar archivos necesarios:**
   - `dist\Limpiador-PC.exe`
   - `limpiador_icon.ico`
   - `Ejecutar-Como-Admin.bat`

3. **Crear accesos directos:**
   - Click derecho en `Limpiador-PC.exe`
   - "Enviar a" → "Escritorio"

4. **¡A disfrutar!**

---

## 📞 INFORMACIÓN TÉCNICA

- **Lenguaje:** Python 3.8+
- **Empaquetador:** PyInstaller
- **Tamaño .exe:** ~40-50 MB
- **Requisitos:** Windows 10/11
- **Permisos:** Administrador (requerido)
- **Dependencias incluidas:** psutil, pillow

---

## ✨ CARACTERÍSTICAS

✅ Limpieza de archivos temporales  
✅ Detección de malware  
✅ Búsqueda de duplicados  
✅ Análisis de Registro  
✅ Optimización de rendimiento  
✅ Registro completo de actividades  
✅ Icono personalizado  
✅ Interfaz en consola  

---

## 📞 SOPORTE

Si algo no funciona:

1. **Verifica los requisitos:**
   ```bash
   python --version
   pip --version
   ```

2. **Reinstala las dependencias:**
   ```bash
   pip install --upgrade pyinstaller pillow psutil
   ```

3. **Ejecuta en modo verbose:**
   ```bash
   python build_exe.py
   ```

---

**¡Tu aplicación está lista para usar! 🎉**

Versión: 5.0  
Última actualización: 2026-07-02  
Desarrollado para: Windows 10/11
