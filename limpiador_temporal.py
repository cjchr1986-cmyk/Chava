import os
import shutil
import sys
import time
from pathlib import Path
from datetime import datetime
import subprocess
import json

class LimpiadoTemporal:
    def __init__(self):
        self.archivos_eliminados = 0
        self.archivos_omitidos = 0
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
    
    def limpiar_directorio(self, ruta):
        """Limpia un directorio específico"""
        if not os.path.exists(ruta):
            self.registrar(f"Directorio no existe: {ruta}", "ADVERTENCIA")
            return
        
        self.registrar(f"Limpiando: {ruta}", "INFO")
        
        try:
            for root, dirs, files in os.walk(ruta, topdown=False):
                # Eliminar archivos
                for archivo in files:
                    ruta_archivo = os.path.join(root, archivo)
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
                    except PermissionError:
                        pass
                    except Exception as e:
                        pass
        
        except Exception as e:
            self.registrar(f"Error procesando {ruta}: {str(e)}", "ERROR")
            self.errores.append(str(e))
    
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
        print("   LIMPIADOR DE ARCHIVOS TEMPORALES - VERSIÓN 2.0")
        print("="*60)
        print("\nSelecciona una opción:\n")
        print("1. Limpieza RÁPIDA (Temp, Prefetch, Papelera)")
        print("2. Limpieza COMPLETA (Incluye navegadores y logs)")
        print("3. Limpieza PERSONALIZADA (Selecciona qué limpiar)")
        print("4. Ver información de espacio en disco")
        print("5. Ver registro de actividades")
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
    
    def limpieza_personalizada(self):
        """Permite seleccionar qué limpiar"""
        print("\n" + "-"*60)
        print("LIMPIEZA PERSONALIZADA\n")
        
        opciones = {
            '1': ('Archivos Temporales de Windows', self.limpiar_directorio, 
                  os.path.expandvars(r'%TEMP%')),
            '2': ('Prefetch', self.limpiar_prefetch, None),
            '3': ('Caché de Navegadores', self.limpiar_cache_navegadores, None),
            '4': ('Papelera de Reciclaje', self.limpiar_papelera, None),
            '5': ('Logs del Sistema', self.limpiar_logs_sistema, None),
            '6': ('Aplicaciones Temporales', self.limpiar_aplicaciones_temporales, None),
        }
        
        print("Selecciona qué deseas limpiar:\n")
        for key, (desc, _, _) in opciones.items():
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
                desc, funcion, param = opciones[num]
                print(f"\n[*] Limpiando {desc}...")
                if param:
                    funcion(param)
                else:
                    funcion()
        
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
        print("   RESUMEN DE LA LIMPIEZA")
        print("="*60)
        print(f"\n✓ Archivos eliminados: {self.archivos_eliminados}")
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
                self.mostrar_espacio_disco()
            elif opcion == '5':
                self.ver_registro()
            else:
                print("\n✗ Opción no válida. Intenta de nuevo.\n")
            
            if opcion in ['1', '2', '3']:
                input("\nPresiona Enter para continuar...")

def main():
    """Punto de entrada del programa"""
    print("\n" + "="*60)
    print("   LIMPIADOR DE ARCHIVOS TEMPORALES")
    print("   Versión 2.0 - Por favor ejecuta como ADMINISTRADOR")
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
