import os
import shutil
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import json
import stat
import hashlib
import re

class LimpiadoTemporal:
    def __init__(self):
        self.archivos_eliminados = 0
        self.archivos_omitidos = 0
        self.archivos_reparados = 0
        self.archivos_ocultos_eliminados = 0
        self.amenazas_detectadas = 0
        self.archivos_cuarentenados = 0
        self.espacio_liberado = 0
        self.errores = []
        self.log_file = "limpiador_temporal.log"
        self.quarantine_dir = "cuarentena_malware"
        self.inicio = datetime.now()
        
        # Crear directorio de cuarentena
        if not os.path.exists(self.quarantine_dir):
            os.makedirs(self.quarantine_dir)
        
        # Patrones de malware comunes
        self.malware_signatures = {
            'trojan': [
                r'.*trojan.*', r'.*backdoor.*', r'.*worm.*',
                r'.*ransomware.*', r'.*spyware.*'
            ],
            'suspicious_extensions': [
                '.exe', '.bat', '.cmd', '.scr', '.vbs', '.js',
                '.com', '.pif', '.msi', '.jar'
            ],
            'suspicious_paths': [
                r'.*appdata.*startup.*',
                r'.*programfiles.*random.*',
                r'.*windows.*system.*suspicious.*'
            ]
        }
        
        # Hashes de malware conocidos (base de datos simplificada)
        self.known_malware_hashes = {
            'eicar': 'X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*',
            # Agregar más hashes según sea necesario
        }
        
    def registrar(self, mensaje, tipo="INFO"):
        """Registra mensajes en consola y archivo de log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_mensaje = f"[{timestamp}] [{tipo}] {mensaje}"
        print(log_mensaje)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_mensaje + "\n")
    
    def obtener_tamaño_formateado(self, bytes):
        """Convierte bytes a formato legible"""
        for unidad in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unidad}"
            bytes /= 1024.0
        return f"{bytes:.2f} TB"
    
    def calcular_hash_archivo(self, ruta):
        """Calcula el hash MD5 de un archivo"""
        try:
            md5_hash = hashlib.md5()
            with open(ruta, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
            return md5_hash.hexdigest()
        except:
            return None
    
    def es_archivo_oculto(self, ruta):
        """Verifica si un archivo está oculto"""
        try:
            if os.name == 'nt':  # Windows
                import ctypes
                attrs = ctypes.windll.kernel32.GetFileAttributesW(str(ruta))
                return attrs != -1 and bool(attrs & 2)  # 2 = FILE_ATTRIBUTE_HIDDEN
            else:  # Linux/Mac
                return os.path.basename(ruta).startswith('.')
        except:
            return False
    
    def es_archivo_inactivo(self, ruta, dias=30):
        """Verifica si un archivo ha estado inactivo por más de X días"""
        try:
            tiempo_acceso = os.path.getatime(ruta)
            tiempo_actual = time.time()
            dias_inactivo = (tiempo_actual - tiempo_acceso) / (24 * 3600)
            return dias_inactivo > dias
        except:
            return False
    
    def verificar_firma_malware(self, ruta, nombre_archivo):
        """Verifica si el archivo tiene firmas de malware conocidas"""
        amenazas = []
        
        # Verificar nombre del archivo
        nombre_lower = nombre_archivo.lower()
        for patron in self.malware_signatures['trojan']:
            if re.match(patron, nombre_lower):
                amenazas.append(f"Nombre sospechoso: {nombre_archivo}")
        
        # Verificar extensión
        _, extension = os.path.splitext(nombre_archivo)
        if extension.lower() in self.malware_signatures['suspicious_extensions']:
            # Archivos ejecutables en directorios temporales son sospechosos
            if 'temp' in ruta.lower() or 'appdata' in ruta.lower():
                amenazas.append(f"Ejecutable sospechoso en directorio temporal: {extension}")
        
        # Verificar contenido (primeros bytes)
        try:
            with open(ruta, 'rb') as f:
                header = f.read(1024)
                
                # Detectar patrones comunes de malware
                if b'MZ' in header:  # Encabezado PE
                    if nombre_lower.endswith(('.jpg', '.png', '.txt', '.pdf')):
                        amenazas.append("Posible PE oculto con extensión falsa")
                
                # Detectar scripts sospechosos
                if b'powershell' in header.lower() or b'cmd.exe' in header.lower():
                    if not nombre_lower.endswith(('.bat', '.cmd', '.ps1')):
                        amenazas.append("Comando del sistema oculto detectado")
        except:
            pass
        
        return amenazas
    
    def escanear_malware_directorio(self, ruta, profundidad_max=3, profundidad_actual=0):
        """Escanea recursivamente un directorio en busca de malware"""
        if profundidad_actual > profundidad_max:
            return
        
        if not os.path.exists(ruta):
            self.registrar(f"Directorio no existe: {ruta}", "ADVERTENCIA")
            return
        
        self.registrar(f"Escaneando: {ruta}", "INFO")
        archivos_escaneados = 0
        
        try:
            for root, dirs, files in os.walk(ruta):
                # Limitar profundidad
                if root[len(ruta):].count(os.sep) > profundidad_max:
                    continue
                
                for archivo in files:
                    ruta_archivo = os.path.join(root, archivo)
                    archivos_escaneados += 1
                    
                    try:
                        # Verificar firmas
                        amenazas = self.verificar_firma_malware(ruta_archivo, archivo)
                        
                        if amenazas:
                            self.amenazas_detectadas += 1
                            for amenaza in amenazas:
                                self.registrar(f"⚠️  AMENAZA DETECTADA: {ruta_archivo}", "ADVERTENCIA")
                                self.registrar(f"   └─ {amenaza}", "ADVERTENCIA")
                        
                        # Mostrar progreso
                        if archivos_escaneados % 100 == 0:
                            self.registrar(f"   [{archivos_escaneados} archivos escaneados]", "INFO")
                    
                    except Exception as e:
                        self.registrar(f"Error escaneando {ruta_archivo}: {str(e)}", "ERROR")
        
        except Exception as e:
            self.registrar(f"Error accediendo a {ruta}: {str(e)}", "ERROR")
        
        self.registrar(f"Escaneo completado. {archivos_escaneados} archivos revisados. Amenazas: {self.amenazas_detectadas}", "INFO")
    
    def usar_windows_defender(self, ruta):
        """Usa Windows Defender para escanear (si está disponible)"""
        try:
            self.registrar("Utilizando Windows Defender para escaneo completo...", "INFO")
            
            cmd = [
                'powershell',
                '-Command',
                f'Start-MpScan -ScanPath "{ruta}" -ScanType Quick -ErrorAction SilentlyContinue'
            ]
            
            resultado = subprocess.run(cmd, capture_output=True, timeout=300)
            self.registrar("✓ Escaneo de Windows Defender completado", "EXITO")
            return True
        except Exception as e:
            self.registrar(f"Windows Defender no disponible: {str(e)}", "ADVERTENCIA")
            return False
    
    def cuarentenar_archivo(self, ruta_origen):
        """Mueve un archivo sospechoso a cuarentena"""
        try:
            nombre_archivo = os.path.basename(ruta_origen)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_cuarentena = f"{timestamp}_{nombre_archivo}"
            ruta_destino = os.path.join(self.quarantine_dir, nombre_cuarentena)
            
            shutil.move(ruta_origen, ruta_destino)
            self.archivos_cuarentenados += 1
            tamaño = os.path.getsize(ruta_destino)
            self.espacio_liberado += tamaño
            
            self.registrar(f"✓ Archivo cuarentenado: {nombre_cuarentena}", "EXITO")
            return True
        except Exception as e:
            self.registrar(f"✗ Error al cuarentenar: {str(e)}", "ERROR")
            return False
    
    def escaneo_malware_completo(self):
        """Realiza un escaneo completo de malware"""
        print("\n" + "-"*60)
        print("ESCANEO DE MALWARE - VERSIÓN COMPLETA\n")
        
        usuario = os.environ.get('USERNAME')
        rutas_criticas = [
            os.path.expandvars(r'%TEMP%'),
            os.path.expandvars(r'%SystemRoot%\Temp'),
            f"C:\\Users\\{usuario}\\AppData\\Local\\Temp",
            f"C:\\Users\\{usuario}\\Downloads",
            f"C:\\Users\\{usuario}\\AppData\\Roaming",
            f"C:\\Users\\{usuario}\\Desktop",
        ]
        
        print("Directorios a escanear:")
        for i, ruta in enumerate(rutas_criticas, 1):
            print(f"{i}. {ruta}")
        
        print("\nNota: Este escaneo puede tomar varios minutos...")
        confirmacion = input("\n¿Deseas continuar? (s/n): ").strip().lower()
        
        if confirmacion == 's':
            self.registrar("="*60, "INFO")
            self.registrar("INICIANDO ESCANEO DE MALWARE COMPLETO", "INFO")
            self.registrar("="*60, "INFO")
            
            for ruta in rutas_criticas:
                if os.path.exists(ruta):
                    self.escanear_malware_directorio(ruta)
            
            # Intentar usar Windows Defender
            print("\n[Integrando Windows Defender...]")
            self.usar_windows_defender(os.path.expandvars(r'%TEMP%'))
            
            self.mostrar_resumen_malware()
    
    def escaneo_malware_rapido(self):
        """Escaneo rápido solo de directorios temporales"""
        print("\n" + "-"*60)
        print("ESCANEO RÁPIDO DE MALWARE\n")
        
        usuario = os.environ.get('USERNAME')
        rutas_rapidas = [
            os.path.expandvars(r'%TEMP%'),
            f"C:\\Users\\{usuario}\\AppData\\Local\\Temp",
            f"C:\\Users\\{usuario}\\Downloads",
        ]
        
        confirmacion = input("¿Deseas escanear directorios temporales? (s/n): ").strip().lower()
        
        if confirmacion == 's':
            self.registrar("="*60, "INFO")
            self.registrar("INICIANDO ESCANEO RÁPIDO DE MALWARE", "INFO")
            self.registrar("="*60, "INFO")
            
            for ruta in rutas_rapidas:
                if os.path.exists(ruta):
                    self.escanear_malware_directorio(ruta, profundidad_max=2)
            
            self.mostrar_resumen_malware()
    
    def gestor_cuarentena(self):
        """Gestiona archivos en cuarentena"""
        print("\n" + "-"*60)
        print("GESTOR DE CUARENTENA\n")
        
        if not os.path.exists(self.quarantine_dir):
            print("No hay archivos en cuarentena.")
            return
        
        archivos_cuarentena = os.listdir(self.quarantine_dir)
        
        if not archivos_cuarentena:
            print("La cuarentena está vacía.")
            return
        
        print(f"Archivos en cuarentena ({len(archivos_cuarentena)}):\n")
        
        tamaño_total = 0
        for i, archivo in enumerate(archivos_cuarentena, 1):
            ruta = os.path.join(self.quarantine_dir, archivo)
            tamaño = os.path.getsize(ruta)
            tamaño_total += tamaño
            print(f"{i}. {archivo} ({self.obtener_tamaño_formateado(tamaño)})")
        
        print(f"\nTamaño total: {self.obtener_tamaño_formateado(tamaño_total)}")
        
        print("\nOpciones:")
        print("1. Ver detalles de un archivo")
        print("2. Restaurar un archivo (CUIDADO)")
        print("3. Eliminar un archivo de cuarentena")
        print("4. Vaciar toda la cuarentena")
        print("0. Volver\n")
        
        opcion = input("Tu opción: ").strip()
        
        if opcion == '1':
            try:
                num = int(input(f"Número del archivo (1-{len(archivos_cuarentena)}): ")) - 1
                if 0 <= num < len(archivos_cuarentena):
                    archivo = archivos_cuarentena[num]
                    ruta = os.path.join(self.quarantine_dir, archivo)
                    print(f"\nDetalles de: {archivo}")
                    print(f"Tamaño: {self.obtener_tamaño_formateado(os.path.getsize(ruta))}")
                    print(f"Ruta: {ruta}")
                    print(f"Creado: {datetime.fromtimestamp(os.path.getctime(ruta))}")
            except:
                print("Número inválido")
        
        elif opcion == '2':
            print("\n⚠️  ADVERTENCIA: Solo restaura archivos que confíes completamente")
            try:
                num = int(input(f"Número del archivo a restaurar (1-{len(archivos_cuarentena)}): ")) - 1
                if 0 <= num < len(archivos_cuarentena):
                    confirmacion = input("¿Estás seguro? (s/n): ").strip().lower()
                    if confirmacion == 's':
                        archivo = archivos_cuarentena[num]
                        ruta_origen = os.path.join(self.quarantine_dir, archivo)
                        nombre_original = '_'.join(archivo.split('_')[2:])
                        ruta_destino = os.path.join(os.path.expandvars(r'%USERPROFILE%\Desktop'), nombre_original)
                        shutil.move(ruta_origen, ruta_destino)
                        self.registrar(f"✓ Archivo restaurado en Desktop: {nombre_original}", "EXITO")
                        print("✓ Archivo restaurado en tu Desktop")
            except:
                print("Operación cancelada")
        
        elif opcion == '3':
            try:
                num = int(input(f"Número del archivo a eliminar (1-{len(archivos_cuarentena)}): ")) - 1
                if 0 <= num < len(archivos_cuarentena):
                    confirmacion = input("¿Estás seguro? (s/n): ").strip().lower()
                    if confirmacion == 's':
                        archivo = archivos_cuarentena[num]
                        ruta = os.path.join(self.quarantine_dir, archivo)
                        os.remove(ruta)
                        self.registrar(f"✓ Archivo eliminado de cuarentena: {archivo}", "EXITO")
                        print("✓ Archivo eliminado permanentemente")
            except:
                print("Operación cancelada")
        
        elif opcion == '4':
            confirmacion = input("⚠️  ¿Eliminar TODA la cuarentena? (s/n): ").strip().lower()
            if confirmacion == 's':
                for archivo in archivos_cuarentena:
                    ruta = os.path.join(self.quarantine_dir, archivo)
                    os.remove(ruta)
                self.registrar("✓ Cuarentena vaciada completamente", "EXITO")
                print("✓ Cuarentena vaciada")
    
    def mostrar_resumen_malware(self):
        """Muestra resumen del escaneo de malware"""
        tiempo_transcurrido = datetime.now() - self.inicio
        
        print("\n" + "="*60)
        print("   RESUMEN ESCANEO DE MALWARE")
        print("="*60)
        print(f"\n⚠️  Amenazas detectadas: {self.amenazas_detectadas}")
        print(f"📦 Archivos cuarentenados: {self.archivos_cuarentenados}")
        print(f"↓ Espacio liberado: {self.obtener_tamaño_formateado(self.espacio_liberado)}")
        print(f"⏱ Tiempo transcurrido: {tiempo_transcurrido}")
        
        if self.amenazas_detectadas > 0:
            print(f"\n🚨 Se detectaron {self.amenazas_detectadas} posibles amenazas")
            print("   Revisa el registro para más detalles")
        else:
            print("\n✓ No se detectaron amenazas")
        
        print("\n" + "="*60)
        print(f"Cuarentena: {self.quarantine_dir}")
        print(f"Registro: {self.log_file}\n")
    
    def reparar_archivo(self, ruta):
        """Intenta reparar un archivo corrupto o con permisos dañados"""
        try:
            # Intentar restaurar permisos
            if os.name == 'nt':
                os.chmod(ruta, stat.S_IWRITE | stat.S_IREAD)
            else:
                os.chmod(ruta, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
            
            # Verificar integridad del archivo
            if os.path.getsize(ruta) > 0:
                with open(ruta, 'rb') as f:
                    primer_byte = f.read(1)
                    if primer_byte:
                        self.archivos_reparados += 1
                        self.registrar(f"✓ Archivo reparado (permisos): {ruta}", "EXITO")
                        return True
        except Exception as e:
            self.registrar(f"✗ No se pudo reparar: {ruta} - {str(e)}", "ERROR")
        
        return False
    
    def limpiar_directorio(self, ruta, eliminar_ocultos=False, eliminar_inactivos=False, dias_inactivos=30):
        """Limpia un directorio específico con opciones avanzadas"""
        if not os.path.exists(ruta):
            self.registrar(f"Directorio no existe: {ruta}", "ADVERTENCIA")
            return
        
        self.registrar(f"Limpiando: {ruta}", "INFO")
        
        try:
            for root, dirs, files in os.walk(ruta, topdown=False):
                # Eliminar archivos
                for archivo in files:
                    ruta_archivo = os.path.join(root, archivo)
                    
                    # Verificar si es oculto y debe eliminarse
                    if eliminar_ocultos and self.es_archivo_oculto(ruta_archivo):
                        try:
                            tamaño = os.path.getsize(ruta_archivo)
                            os.remove(ruta_archivo)
                            self.archivos_ocultos_eliminados += 1
                            self.espacio_liberado += tamaño
                            self.registrar(f"✓ Archivo oculto eliminado: {ruta_archivo}", "EXITO")
                            continue
                        except Exception as e:
                            self.registrar(f"✗ Error al eliminar oculto: {ruta_archivo}", "ADVERTENCIA")
                    
                    # Verificar si está inactivo y debe eliminarse
                    if eliminar_inactivos and self.es_archivo_inactivo(ruta_archivo, dias_inactivos):
                        try:
                            tamaño = os.path.getsize(ruta_archivo)
                            os.remove(ruta_archivo)
                            self.archivos_eliminados += 1
                            self.espacio_liberado += tamaño
                            self.registrar(f"✓ Archivo inactivo eliminado: {ruta_archivo}", "EXITO")
                            continue
                        except Exception as e:
                            self.registrar(f"✗ Error al eliminar inactivo: {ruta_archivo}", "ADVERTENCIA")
                    
                    # Limpieza normal de archivos temporales
                    try:
                        tamaño = os.path.getsize(ruta_archivo)
                        os.remove(ruta_archivo)
                        self.archivos_eliminados += 1
                        self.espacio_liberado += tamaño
                        self.registrar(f"✓ Eliminado: {ruta_archivo}", "EXITO")
                    except PermissionError:
                        self.archivos_omitidos += 1
                        self.registrar(f"✗ Permiso denegado: {ruta_archivo}", "ADVERTENCIA")
                    except Exception as e:
                        self.archivos_omitidos += 1
                        self.registrar(f"✗ Error al eliminar {ruta_archivo}: {str(e)}", "ERROR")
                        self.errores.append(str(e))
                
                # Eliminar directorios vacíos
                for directorio in dirs:
                    ruta_dir = os.path.join(root, directorio)
                    try:
                        if not os.listdir(ruta_dir):
                            os.rmdir(ruta_dir)
                            self.registrar(f"✓ Carpeta vacía eliminada: {ruta_dir}", "EXITO")
                    except:
                        pass
        
        except Exception as e:
            self.registrar(f"Error procesando {ruta}: {str(e)}", "ERROR")
            self.errores.append(str(e))
    
    def escanear_y_reparar_directorio(self, ruta):
        """Escanea un directorio y repara archivos dañados"""
        if not os.path.exists(ruta):
            self.registrar(f"Directorio no existe: {ruta}", "ADVERTENCIA")
            return
        
        self.registrar(f"Escaneando y reparando: {ruta}", "INFO")
        archivos_escaneados = 0
        
        try:
            for root, dirs, files in os.walk(ruta):
                for archivo in files:
                    ruta_archivo = os.path.join(root, archivo)
                    archivos_escaneados += 1
                    
                    try:
                        # Verificar si el archivo tiene problemas
                        tamaño = os.path.getsize(ruta_archivo)
                        
                        # Intentar leer el archivo
                        with open(ruta_archivo, 'rb') as f:
                            f.read(min(1024, tamaño))  # Leer primeros 1KB
                        
                        # Si tiene permisos incorrectos, reparar
                        if not os.access(ruta_archivo, os.R_OK):
                            self.reparar_archivo(ruta_archivo)
                    
                    except Exception as e:
                        self.registrar(f"⚠ Archivo posiblemente dañado: {ruta_archivo}", "ADVERTENCIA")
                        self.reparar_archivo(ruta_archivo)
        
        except Exception as e:
            self.registrar(f"Error escaneando {ruta}: {str(e)}", "ERROR")
        
        self.registrar(f"Escaneo completado. {archivos_escaneados} archivos revisados.", "INFO")
    
    def limpiar_papelera(self):
        """Vacía la papelera de reciclaje"""
        try:
            self.registrar("Vaciando papelera de reciclaje...", "INFO")
            subprocess.run(['powershell', '-Command', 
                          'Clear-RecycleBin -Force -ErrorAction SilentlyContinue'], 
                          check=False, capture_output=True)
            self.registrar("✓ Papelera vaciada exitosamente", "EXITO")
        except Exception as e:
            self.registrar(f"✗ No se pudo vaciar papelera: {str(e)}", "ADVERTENCIA")
    
    def limpiar_prefetch(self):
        """Limpia los archivos prefetch"""
        prefetch_path = r"C:\Windows\Prefetch"
        if os.path.exists(prefetch_path):
            self.registrar("Limpiando archivos Prefetch...", "INFO")
            self.limpiar_directorio(prefetch_path)
    
    def limpiar_cache_navegadores(self):
        """Limpia caché de navegadores"""
        usuario = os.environ.get('USERNAME')
        
        # Chrome
        chrome_cache = f"C:\\Users\\{usuario}\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cache"
        if os.path.exists(chrome_cache):
            self.registrar("Limpiando caché de Google Chrome...", "INFO")
            self.limpiar_directorio(chrome_cache)
        
        # Firefox
        firefox_cache = f"C:\\Users\\{usuario}\\AppData\\Local\\Mozilla\\Firefox"
        if os.path.exists(firefox_cache):
            self.registrar("Limpiando caché de Mozilla Firefox...", "INFO")
            self.limpiar_directorio(firefox_cache)
        
        # Edge
        edge_cache = f"C:\\Users\\{usuario}\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Cache"
        if os.path.exists(edge_cache):
            self.registrar("Limpiando caché de Microsoft Edge...", "INFO")
            self.limpiar_directorio(edge_cache)
    
    def limpiar_aplicaciones_temporales(self):
        """Limpia archivos temporales de aplicaciones comunes"""
        usuario = os.environ.get('USERNAME')
        
        rutas_app = [
            f"C:\\Users\\{usuario}\\AppData\\Local\\Temp",
            f"C:\\Users\\{usuario}\\AppData\\Local\\CrashDumps",
            f"C:\\Users\\{usuario}\\AppData\\Local\\Microsoft\\Windows\\INetCache",
            f"C:\\ProgramData\\Package Cache",
        ]
        
        for ruta in rutas_app:
            if os.path.exists(ruta):
                self.limpiar_directorio(ruta)
    
    def limpiar_logs_sistema(self):
        """Limpia archivos de log antiguos"""
        usuario = os.environ.get('USERNAME')
        rutas_logs = [
            f"C:\\Users\\{usuario}\\AppData\\Local\\Microsoft\\Windows\\Explorer",
            f"C:\\Users\\{usuario}\\AppData\\Local\\Microsoft\\Windows\\INetCookies",
        ]
        
        for ruta in rutas_logs:
            if os.path.exists(ruta):
                self.limpiar_directorio(ruta)
    
    def obtener_espacio_disco(self):
        """Obtiene información del espacio en disco"""
        try:
            import psutil
            disk_usage = psutil.disk_usage('C:\\')
            return {
                'total': disk_usage.total,
                'usado': disk_usage.used,
                'libre': disk_usage.free,
                'porcentaje': disk_usage.percent
            }
        except ImportError:
            self.registrar("psutil no instalado. Use: pip install psutil", "ADVERTENCIA")
            return None
    
    def mostrar_menu(self):
        """Muestra el menú principal"""
        print("\n" + "="*70)
        print("   LIMPIADOR DE ARCHIVOS TEMPORALES - VERSIÓN 4.0")
        print("   CON REPARACIÓN, OCULTOS, INACTIVOS Y ESCANEO MALWARE")
        print("="*70)
        print("\n🔒 ESCANEO Y PROTECCIÓN:")
        print("1. 🔍 ESCANEO COMPLETO DE MALWARE")
        print("2. ⚡ ESCANEO RÁPIDO DE MALWARE")
        print("3. 📦 GESTOR DE CUARENTENA")
        print("\n🧹 LIMPIEZA:")
        print("4. Limpieza RÁPIDA (Temp, Prefetch, Papelera)")
        print("5. Limpieza COMPLETA (Incluye navegadores y logs)")
        print("6. Limpieza PERSONALIZADA")
        print("\n🔧 REPARACIÓN Y MANTENIMIENTO:")
        print("7. Reparar archivos dañados")
        print("8. Eliminar archivos ocultos")
        print("9. Eliminar archivos inactivos")
        print("10. 🚀 REPARACIÓN + LIMPIEZA + MALWARE")
        print("\n📊 INFORMACIÓN:")
        print("11. Ver información de espacio en disco")
        print("12. Ver registro de actividades")
        print("0. Salir")
        print("\n" + "-"*70)
    
    def limpieza_rapida(self):
        """Realiza una limpieza rápida"""
        self.registrar("="*60, "INFO")
        self.registrar("INICIANDO LIMPIEZA RÁPIDA", "INFO")
        self.registrar("="*60, "INFO")
        
        usuario = os.environ.get('USERNAME')
        self.limpiar_directorio(os.path.expandvars(r'%TEMP%'))
        self.limpiar_directorio(os.path.expandvars(r'%SystemRoot%\Temp'))
        self.limpiar_directorio(f"C:\\Users\\{usuario}\\AppData\\Local\\Temp")
        self.limpiar_prefetch()
        self.limpiar_papelera()
        
        self.mostrar_resumen()
    
    def limpieza_completa(self):
        """Realiza una limpieza completa"""
        self.registrar("="*60, "INFO")
        self.registrar("INICIANDO LIMPIEZA COMPLETA", "INFO")
        self.registrar("="*60, "INFO")
        
        usuario = os.environ.get('USERNAME')
        self.limpiar_directorio(os.path.expandvars(r'%TEMP%'))
        self.limpiar_directorio(os.path.expandvars(r'%SystemRoot%\Temp'))
        self.limpiar_aplicaciones_temporales()
        self.limpiar_prefetch()
        self.limpiar_cache_navegadores()
        self.limpiar_logs_sistema()
        self.limpiar_papelera()
        
        self.mostrar_resumen()
    
    def reparacion_ultra_completa(self):
        """Lo máximo: Reparación + Limpieza + Malware"""
        print("\n" + "-"*60)
        print("🚀 REPARACIÓN + LIMPIEZA + ESCANEO MALWARE ULTRA COMPLETO\n")
        
        usuario = os.environ.get('USERNAME')
        
        try:
            dias = int(input("¿Archivos inactivos hace cuántos días? (default 30): ") or "30")
        except ValueError:
            dias = 30
        
        print(f"\nEsta operación realizará:")
        print(f"  1. Escaneo de malware en directorios críticos")
        print(f"  2. Escaneo y reparación de archivos dañados")
        print(f"  3. Eliminación de archivos temporales")
        print(f"  4. Eliminación de archivos ocultos")
        print(f"  5. Eliminación de archivos inactivos (>{dias} días)")
        print(f"  6. Limpieza de caché y navegadores")
        print(f"  7. Vaciado de papelera")
        print(f"\n⚠️  Esta operación puede tomar 10-20 minutos")
        
        confirmacion = input("\n¿Continuar? (s/n): ").strip().lower()
        
        if confirmacion == 's':
            self.registrar("="*60, "INFO")
            self.registrar("INICIANDO OPERACIÓN ULTRA COMPLETA", "INFO")
            self.registrar("="*60, "INFO")
            
            # Fase 1: Escaneo malware
            print("\n[Fase 1/7] Escaneando malware...")
            rutas_criticas = [
                os.path.expandvars(r'%TEMP%'),
                f"C:\\Users\\{usuario}\\AppData\\Local\\Temp",
                f"C:\\Users\\{usuario}\\Downloads",
            ]
            for ruta in rutas_criticas:
                if os.path.exists(ruta):
                    self.escanear_malware_directorio(ruta, profundidad_max=2)
            
            # Fase 2: Reparar
            print("\n[Fase 2/7] Reparando archivos...")
            for ruta in rutas_criticas:
                self.escanear_y_reparar_directorio(ruta)
            
            # Fase 3: Limpiar normalmente
            print("\n[Fase 3/7] Limpiando archivos temporales...")
            self.limpiar_directorio(os.path.expandvars(r'%TEMP%'))
            self.limpiar_directorio(os.path.expandvars(r'%SystemRoot%\Temp'))
            
            # Fase 4: Eliminar ocultos
            print("\n[Fase 4/7] Eliminando archivos ocultos...")
            self.limpiar_directorio(os.path.expandvars(r'%TEMP%'), eliminar_ocultos=True)
            self.limpiar_directorio(f"C:\\Users\\{usuario}\\AppData\\Local\\Temp", eliminar_ocultos=True)
            
            # Fase 5: Eliminar inactivos
            print(f"\n[Fase 5/7] Eliminando archivos inactivos (>{dias} días)...")
            self.limpiar_directorio(f"C:\\Users\\{usuario}\\Downloads", eliminar_inactivos=True, dias_inactivos=dias)
            
            # Fase 6: Limpieza de caché
            print("\n[Fase 6/7] Limpiando caché y navegadores...")
            self.limpiar_aplicaciones_temporales()
            self.limpiar_cache_navegadores()
            self.limpiar_prefetch()
            
            # Fase 7: Papelera
            print("\n[Fase 7/7] Vaciando papelera...")
            self.limpiar_papelera()
            
            self.mostrar_resumen()
    
    def limpieza_personalizada(self):
        """Permite seleccionar qué limpiar"""
        print("\n" + "-"*60)
        print("LIMPIEZA PERSONALIZADA\n")
        
        opciones = {
            '1': ('Archivos Temporales de Windows', self.limpiar_directorio, 
                  os.path.expandvars(r'%TEMP%'), False, False),
            '2': ('Prefetch', self.limpiar_prefetch, None, False, False),
            '3': ('Caché de Navegadores', self.limpiar_cache_navegadores, None, False, False),
            '4': ('Papelera de Reciclaje', self.limpiar_papelera, None, False, False),
            '5': ('Logs del Sistema', self.limpiar_logs_sistema, None, False, False),
            '6': ('Aplicaciones Temporales', self.limpiar_aplicaciones_temporales, None, False, False),
        }
        
        print("Selecciona qué deseas limpiar:\n")
        for key, (desc, _, _, _, _) in opciones.items():
            print(f"{key}. {desc}")
        print("0. Cancelar\n")
        
        seleccion = input("Tu selección (puedes ingresar múltiples números separados por comas): ").strip()
        
        if seleccion == '0':
            return
        
        self.registrar("="*60, "INFO")
        self.registrar("INICIANDO LIMPIEZA PERSONALIZADA", "INFO")
        self.registrar("="*60, "INFO")
        
        for num in seleccion.split(','):
            num = num.strip()
            if num in opciones:
                desc, funcion, param, _, _ = opciones[num]
                print(f"\n[*] Limpiando {desc}...")
                if param:
                    funcion(param)
                else:
                    funcion()
        
        self.mostrar_resumen()
    
    def reparar_archivos(self):
        """Opción para reparar archivos dañados"""
        print("\n" + "-"*60)
        print("REPARACIÓN DE ARCHIVOS\n")
        
        usuario = os.environ.get('USERNAME')
        rutas_escaneo = [
            os.path.expandvars(r'%TEMP%'),
            os.path.expandvars(r'%SystemRoot%\Temp'),
            f"C:\\Users\\{usuario}\\AppData\\Local\\Temp",
            f"C:\\Users\\{usuario}\\Downloads",
        ]
        
        print("Se escanearán y repararán los siguientes directorios:")
        for i, ruta in enumerate(rutas_escaneo, 1):
            print(f"{i}. {ruta}")
        
        confirmacion = input("\n¿Deseas continuar? (s/n): ").strip().lower()
        if confirmacion == 's':
            self.registrar("="*60, "INFO")
            self.registrar("INICIANDO REPARACIÓN DE ARCHIVOS", "INFO")
            self.registrar("="*60, "INFO")
            
            for ruta in rutas_escaneo:
                self.escanear_y_reparar_directorio(ruta)
            
            self.mostrar_resumen()
    
    def eliminar_ocultos(self):
        """Elimina archivos ocultos"""
        print("\n" + "-"*60)
        print("ELIMINACIÓN DE ARCHIVOS OCULTOS\n")
        
        usuario = os.environ.get('USERNAME')
        rutas = [
            os.path.expandvars(r'%TEMP%'),
            os.path.expandvars(r'%SystemRoot%\Temp'),
            f"C:\\Users\\{usuario}\\AppData\\Local\\Temp",
        ]
        
        print("Directorios a escanear:")
        for i, ruta in enumerate(rutas, 1):
            print(f"{i}. {ruta}")
        
        confirmacion = input("\n¿Deseas eliminar los archivos ocultos encontrados? (s/n): ").strip().lower()
        if confirmacion == 's':
            self.registrar("="*60, "INFO")
            self.registrar("INICIANDO ELIMINACIÓN DE ARCHIVOS OCULTOS", "INFO")
            self.registrar("="*60, "INFO")
            
            for ruta in rutas:
                self.limpiar_directorio(ruta, eliminar_ocultos=True)
            
            self.mostrar_resumen()
    
    def eliminar_inactivos(self):
        """Elimina archivos inactivos"""
        print("\n" + "-"*60)
        print("ELIMINACIÓN DE ARCHIVOS INACTIVOS\n")
        
        try:
            dias = int(input("¿Cuántos días de inactividad? (default 30): ") or "30")
        except ValueError:
            dias = 30
        
        usuario = os.environ.get('USERNAME')
        rutas = [
            f"C:\\Users\\{usuario}\\Downloads",
            f"C:\\Users\\{usuario}\\AppData\\Local\\Temp",
            os.path.expandvars(r'%TEMP%'),
        ]
        
        print(f"\nEliminaremos archivos sin acceso hace más de {dias} días")
        confirmacion = input("¿Continuar? (s/n): ").strip().lower()
        
        if confirmacion == 's':
            self.registrar("="*60, "INFO")
            self.registrar(f"INICIANDO ELIMINACIÓN DE ARCHIVOS INACTIVOS (>{dias} días)", "INFO")
            self.registrar("="*60, "INFO")
            
            for ruta in rutas:
                self.limpiar_directorio(ruta, eliminar_inactivos=True, dias_inactivos=dias)
            
            self.mostrar_resumen()
    
    def mostrar_espacio_disco(self):
        """Muestra información del espacio en disco"""
        print("\n" + "-"*60)
        print("INFORMACIÓN DE ESPACIO EN DISCO\n")
        
        espacio = self.obtener_espacio_disco()
        if espacio:
            print(f"Unidad: C:\\")
            print(f"Total:       {self.obtener_tamaño_formateado(espacio['total'])}")
            print(f"Usado:       {self.obtener_tamaño_formateado(espacio['usado'])}")
            print(f"Disponible:  {self.obtener_tamaño_formateado(espacio['libre'])}")
            print(f"Porcentaje:  {espacio['porcentaje']:.1f}%")
        else:
            print("No se pudo obtener la información de espacio en disco.")
        print("-"*60)
    
    def ver_registro(self):
        """Muestra el archivo de registro"""
        print("\n" + "-"*60)
        print("REGISTRO DE ACTIVIDADES\n")
        
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r', encoding='utf-8') as f:
                ultimas_lineas = f.readlines()[-50:]  # Últimas 50 líneas
                for linea in ultimas_lineas:
                    print(linea.rstrip())
        else:
            print("No hay registro de actividades disponible.")
        print("-"*60)
    
    def mostrar_resumen(self):
        """Muestra un resumen de la operación"""
        tiempo_transcurrido = datetime.now() - self.inicio
        
        print("\n" + "="*60)
        print("   RESUMEN DE LA OPERACIÓN")
        print("="*60)
        print(f"\n✓ Archivos eliminados: {self.archivos_eliminados}")
        print(f"✓ Archivos ocultos eliminados: {self.archivos_ocultos_eliminados}")
        print(f"✓ Archivos reparados: {self.archivos_reparados}")
        print(f"⚠️  Amenazas detectadas: {self.amenazas_detectadas}")
        print(f"📦 Archivos cuarentenados: {self.archivos_cuarentenados}")
        print(f"⚠ Archivos omitidos: {self.archivos_omitidos}")
        print(f"↓ Espacio liberado: {self.obtener_tamaño_formateado(self.espacio_liberado)}")
        print(f"⏱ Tiempo transcurrido: {tiempo_transcurrido}")
        
        if self.errores:
            print(f"\n✗ Errores encontrados: {len(self.errores)}")
        
        print("\n" + "="*60)
        print(f"Registro guardado en: {self.log_file}")
        print(f"Cuarentena: {self.quarantine_dir}\n")
    
    def ejecutar(self):
        """Loop principal de la aplicación"""
        while True:
            self.mostrar_menu()
            opcion = input("Ingresa tu opción: ").strip()
            
            if opcion == '0':
                print("\n¡Hasta luego! Gracias por usar el Limpiador de Temporales.\n")
                break
            elif opcion == '1':
                self.escaneo_malware_completo()
            elif opcion == '2':
                self.escaneo_malware_rapido()
            elif opcion == '3':
                self.gestor_cuarentena()
            elif opcion == '4':
                confirmacion = input("\n¿Deseas continuar con la limpieza RÁPIDA? (s/n): ").strip().lower()
                if confirmacion == 's':
                    self.limpieza_rapida()
            elif opcion == '5':
                confirmacion = input("\n¿Deseas continuar con la limpieza COMPLETA? (s/n): ").strip().lower()
                if confirmacion == 's':
                    self.limpieza_completa()
            elif opcion == '6':
                self.limpieza_personalizada()
            elif opcion == '7':
                self.reparar_archivos()
            elif opcion == '8':
                self.eliminar_ocultos()
            elif opcion == '9':
                self.eliminar_inactivos()
            elif opcion == '10':
                self.reparacion_ultra_completa()
            elif opcion == '11':
                self.mostrar_espacio_disco()
            elif opcion == '12':
                self.ver_registro()
            else:
                print("\n✗ Opción no válida. Intenta de nuevo.\n")
            
            if opcion in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']:
                input("\nPresiona Enter para continuar...")

def main():
    """Punto de entrada del programa"""
    print("\n" + "="*70)
    print("   LIMPIADOR DE ARCHIVOS TEMPORALES - V4.0")
    print("   Con Reparación, Ocultos, Inactivos y ESCANEO MALWARE")
    print("   Por favor ejecuta como ADMINISTRADOR")
    print("="*70 + "\n")
    
    # Verificar si se ejecuta como administrador
    try:
        import ctypes
        if os.name == 'nt':
            if not ctypes.windll.shell32.IsUserAnAdmin():
                print("⚠️  ADVERTENCIA: Este programa debe ejecutarse como ADMINISTRADOR")
                print("   para acceder a todos los directorios.\n")
                continuacion = input("¿Deseas continuar de todas formas? (s/n): ").strip().lower()
                if continuacion != 's':
                    print("Programa cancelado.")
                    sys.exit(1)
    except:
        pass
    
    limpiador = LimpiadoTemporal()
    limpiador.ejecutar()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Programa interrumpido por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error fatal: {str(e)}")
        sys.exit(1)
