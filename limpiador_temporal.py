import os
import shutil
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import json
import stat

class LimpiadoTemporal:
    def __init__(self):
        self.archivos_eliminados = 0
        self.archivos_omitidos = 0
        self.archivos_reparados = 0
        self.archivos_ocultos_eliminados = 0
        self.espacio_liberado = 0
        self.errores = []
        self.log_file = "limpiador_temporal.log"
        self.inicio = datetime.now()
        
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
        print("\n" + "="*60)
        print("   LIMPIADOR DE ARCHIVOS TEMPORALES - VERSIÓN 3.0")
        print("   CON REPARACIÓN Y ELIMINACIÓN AVANZADA")
        print("="*60)
        print("\nSelecciona una opción:\n")
        print("1. Limpieza RÁPIDA (Temp, Prefetch, Papelera)")
        print("2. Limpieza COMPLETA (Incluye navegadores y logs)")
        print("3. Limpieza PERSONALIZADA (Selecciona qué limpiar)")
        print("4. 🔧 REPARAR ARCHIVOS DAÑADOS")
        print("5. 🗑️  ELIMINAR ARCHIVOS OCULTOS")
        print("6. ⏰ ELIMINAR ARCHIVOS INACTIVOS")
        print("7. 🔍 REPARACIÓN + LIMPIEZA COMPLETA")
        print("8. Ver información de espacio en disco")
        print("9. Ver registro de actividades")
        print("0. Salir")
        print("\n" + "-"*60)
    
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
    
    def reparacion_completa_avanzada(self):
        """Reparación + Limpieza completa + Eliminación de ocultos"""
        print("\n" + "-"*60)
        print("REPARACIÓN + LIMPIEZA COMPLETA AVANZADA\n")
        
        usuario = os.environ.get('USERNAME')
        
        try:
            dias = int(input("¿Archivos inactivos hace cuántos días? (default 30): ") or "30")
        except ValueError:
            dias = 30
        
        print(f"\nEsta operación realizará:")
        print(f"  1. Escaneo y reparación de archivos dañados")
        print(f"  2. Eliminación de archivos temporales")
        print(f"  3. Eliminación de archivos ocultos")
        print(f"  4. Eliminación de archivos inactivos (>{dias} días)")
        print(f"  5. Limpieza de caché y navegadores")
        print(f"  6. Vaciado de papelera")
        
        confirmacion = input("\n¿Continuar? (s/n): ").strip().lower()
        
        if confirmacion == 's':
            self.registrar("="*60, "INFO")
            self.registrar("INICIANDO REPARACIÓN + LIMPIEZA COMPLETA AVANZADA", "INFO")
            self.registrar("="*60, "INFO")
            
            # Fase 1: Reparar
            print("\n[Fase 1/5] Reparando archivos...")
            rutas_escaneo = [
                os.path.expandvars(r'%TEMP%'),
                os.path.expandvars(r'%SystemRoot%\Temp'),
                f"C:\\Users\\{usuario}\\AppData\\Local\\Temp",
            ]
            for ruta in rutas_escaneo:
                self.escanear_y_reparar_directorio(ruta)
            
            # Fase 2: Limpiar normalmente
            print("\n[Fase 2/5] Limpiando archivos temporales...")
            self.limpiar_directorio(os.path.expandvars(r'%TEMP%'))
            self.limpiar_directorio(os.path.expandvars(r'%SystemRoot%\Temp'))
            
            # Fase 3: Eliminar ocultos
            print("\n[Fase 3/5] Eliminando archivos ocultos...")
            self.limpiar_directorio(os.path.expandvars(r'%TEMP%'), eliminar_ocultos=True)
            self.limpiar_directorio(f"C:\\Users\\{usuario}\\AppData\\Local\\Temp", eliminar_ocultos=True)
            
            # Fase 4: Eliminar inactivos
            print(f"\n[Fase 4/5] Eliminando archivos inactivos (>{dias} días)...")
            self.limpiar_directorio(f"C:\\Users\\{usuario}\\Downloads", eliminar_inactivos=True, dias_inactivos=dias)
            
            # Fase 5: Limpieza completa
            print("\n[Fase 5/5] Completando limpieza...")
            self.limpiar_aplicaciones_temporales()
            self.limpiar_cache_navegadores()
            self.limpiar_prefetch()
            self.limpiar_papelera()
            
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
        """Muestra un resumen de la limpieza"""
        tiempo_transcurrido = datetime.now() - self.inicio
        
        print("\n" + "="*60)
        print("   RESUMEN DE LA OPERACIÓN")
        print("="*60)
        print(f"\n✓ Archivos eliminados: {self.archivos_eliminados}")
        print(f"✓ Archivos ocultos eliminados: {self.archivos_ocultos_eliminados}")
        print(f"✓ Archivos reparados: {self.archivos_reparados}")
        print(f"⚠ Archivos omitidos: {self.archivos_omitidos}")
        print(f"↓ Espacio liberado: {self.obtener_tamaño_formateado(self.espacio_liberado)}")
        print(f"⏱ Tiempo transcurrido: {tiempo_transcurrido}")
        
        if self.errores:
            print(f"\n✗ Errores encontrados: {len(self.errores)}")
        
        print("\n" + "="*60)
        print(f"Registro guardado en: {self.log_file}\n")
    
    def ejecutar(self):
        """Loop principal de la aplicación"""
        while True:
            self.mostrar_menu()
            opcion = input("Ingresa tu opción: ").strip()
            
            if opcion == '0':
                print("\n¡Hasta luego! Gracias por usar el Limpiador de Temporales.\n")
                break
            elif opcion == '1':
                confirmacion = input("\n¿Deseas continuar con la limpieza RÁPIDA? (s/n): ").strip().lower()
                if confirmacion == 's':
                    self.limpieza_rapida()
            elif opcion == '2':
                confirmacion = input("\n¿Deseas continuar con la limpieza COMPLETA? (s/n): ").strip().lower()
                if confirmacion == 's':
                    self.limpieza_completa()
            elif opcion == '3':
                self.limpieza_personalizada()
            elif opcion == '4':
                self.reparar_archivos()
            elif opcion == '5':
                self.eliminar_ocultos()
            elif opcion == '6':
                self.eliminar_inactivos()
            elif opcion == '7':
                self.reparacion_completa_avanzada()
            elif opcion == '8':
                self.mostrar_espacio_disco()
            elif opcion == '9':
                self.ver_registro()
            else:
                print("\n✗ Opción no válida. Intenta de nuevo.\n")
            
            if opcion in ['1', '2', '3', '4', '5', '6', '7']:
                input("\nPresiona Enter para continuar...")
    
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

def main():
    """Punto de entrada del programa"""
    print("\n" + "="*60)
    print("   LIMPIADOR DE ARCHIVOS TEMPORALES - V3.0")
    print("   Con Reparación, Ocultos e Inactivos")
    print("   Por favor ejecuta como ADMINISTRADOR")
    print("="*60 + "\n")
    
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
