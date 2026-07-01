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
import psutil

class LimpiadoTemporal:
    def __init__(self):
        self.archivos_eliminados = 0
        self.archivos_omitidos = 0
        self.archivos_reparados = 0
        self.archivos_ocultos_eliminados = 0
        self.amenazas_detectadas = 0
        self.archivos_cuarentenados = 0
        self.duplicados_encontrados = 0
        self.duplicados_eliminados = 0
        self.entradas_registro_eliminadas = 0
        self.espacio_liberado = 0
        self.errores = []
        self.log_file = "limpiador_temporal.log"
        self.quarantine_dir = "cuarentena_malware"
        self.duplicados_db = "duplicados.json"
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
    
    # ==================== ANÁLISIS DE DUPLICADOS ====================
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
    
    def buscar_duplicados(self, ruta, extensiones=None):
        """Busca archivos duplicados en un directorio"""
        print(f"\n[*] Buscando duplicados en: {ruta}")
        
        hashes = {}
        duplicados = {}
        archivos_procesados = 0
        
        if not os.path.exists(ruta):
            self.registrar(f"Directorio no existe: {ruta}", "ADVERTENCIA")
            return duplicados
        
        try:
            for root, dirs, files in os.walk(ruta):
                for archivo in files:
                    # Filtrar por extensión si se especifica
                    if extensiones:
                        if not any(archivo.lower().endswith(ext) for ext in extensiones):
                            continue
                    
                    ruta_archivo = os.path.join(root, archivo)
                    
                    try:
                        tamaño = os.path.getsize(ruta_archivo)
                        
                        # Ignorar archivos muy pequeños
                        if tamaño < 1024:  # Menor a 1KB
                            continue
                        
                        hash_archivo = self.calcular_hash_archivo(ruta_archivo)
                        
                        if hash_archivo:
                            archivos_procesados += 1
                            
                            if hash_archivo in hashes:
                                # Duplicado encontrado
                                if hash_archivo not in duplicados:
                                    duplicados[hash_archivo] = [hashes[hash_archivo]]
                                duplicados[hash_archivo].append({
                                    'ruta': ruta_archivo,
                                    'tamaño': tamaño
                                })
                                self.duplicados_encontrados += 1
                            else:
                                hashes[hash_archivo] = {
                                    'ruta': ruta_archivo,
                                    'tamaño': tamaño
                                }
                            
                            if archivos_procesados % 100 == 0:
                                print(f"   [{archivos_procesados} archivos analizados]", end='\r')
                    
                    except Exception as e:
                        self.registrar(f"Error procesando {ruta_archivo}: {str(e)}", "ERROR")
        
        except Exception as e:
            self.registrar(f"Error buscando duplicados: {str(e)}", "ERROR")
        
        print(f"\n✓ {archivos_procesados} archivos analizados")
        print(f"✓ {self.duplicados_encontrados} grupos de duplicados encontrados")
        
        return duplicados
    
    def mostrar_duplicados(self, duplicados):
        """Muestra los duplicados encontrados"""
        if not duplicados:
            print("\nNo se encontraron archivos duplicados.")
            return
        
        print("\n" + "-"*80)
        print("DUPLICADOS ENCONTRADOS\n")
        
        total_espacio_duplicado = 0
        
        for i, (hash_val, archivos) in enumerate(duplicados.items(), 1):
            print(f"\n{i}. Grupo de duplicados:")
            
            tamaño_grupo = 0
            for j, archivo in enumerate(archivos, 1):
                tamaño = archivo['tamaño']
                tamaño_grupo += tamaño
                print(f"   {j}. {archivo['ruta']}")
                print(f"      Tamaño: {self.obtener_tamaño_formateado(tamaño)}")
            
            # El espacio ahorrable es el tamaño de los duplicados (menos el original)
            espacio_ahorrable = (len(archivos) - 1) * archivos[0]['tamaño']
            total_espacio_duplicado += espacio_ahorrable
            print(f"   Espacio ahorrable: {self.obtener_tamaño_formateado(espacio_ahorrable)}")
        
        print(f"\n" + "-"*80)
        print(f"Espacio total duplicado: {self.obtener_tamaño_formateado(total_espacio_duplicado)}\n")
        
        return total_espacio_duplicado
    
    def eliminar_duplicados_automatico(self, duplicados, mantener_original=True):
        """Elimina duplicados automáticamente"""
        print("\n" + "-"*80)
        print("ELIMINACIÓN DE DUPLICADOS\n")
        
        confirmacion = input("¿Deseas eliminar los duplicados? (CUIDADO - Esta acción es irreversible) (s/n): ").strip().lower()
        
        if confirmacion != 's':
            print("Operación cancelada.")
            return
        
        for hash_val, archivos in duplicados.items():
            if mantener_original:
                # Mantener el primer archivo, eliminar el resto
                for archivo in archivos[1:]:
                    try:
                        tamaño = archivo['tamaño']
                        os.remove(archivo['ruta'])
                        self.duplicados_eliminados += 1
                        self.espacio_liberado += tamaño
                        self.registrar(f"✓ Duplicado eliminado: {archivo['ruta']}", "EXITO")
                    except Exception as e:
                        self.registrar(f"✗ Error eliminando: {archivo['ruta']}", "ERROR")
            else:
                # Eliminar todos
                for archivo in archivos:
                    try:
                        tamaño = archivo['tamaño']
                        os.remove(archivo['ruta'])
                        self.duplicados_eliminados += 1
                        self.espacio_liberado += tamaño
                        self.registrar(f"✓ Duplicado eliminado: {archivo['ruta']}", "EXITO")
                    except Exception as e:
                        self.registrar(f"✗ Error eliminando: {archivo['ruta']}", "ERROR")
    
    # ==================== OPTIMIZACIÓN DE RENDIMIENTO ====================
    def obtener_info_sistema(self):
        """Obtiene información detallada del sistema"""
        try:
            info = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'cpu_count': psutil.cpu_count(),
                'memory': psutil.virtual_memory(),
                'disk_usage': psutil.disk_usage('C:\\'),
                'boot_time': datetime.fromtimestamp(psutil.boot_time()),
                'procesos': len(psutil.pids())
            }
            return info
        except Exception as e:
            self.registrar(f"Error obteniendo información del sistema: {str(e)}", "ERROR")
            return None
    
    def mostrar_info_sistema(self):
        """Muestra información del sistema"""
        print("\n" + "-"*60)
        print("INFORMACIÓN DEL SISTEMA\n")
        
        info = self.obtener_info_sistema()
        
        if info:
            print(f"CPU:")
            print(f"  Núcleos: {info['cpu_count']}")
            print(f"  Uso: {info['cpu_percent']:.1f}%")
            
            mem = info['memory']
            print(f"\nMemoria RAM:")
            print(f"  Total: {self.obtener_tamaño_formateado(mem.total)}")
            print(f"  Usada: {self.obtener_tamaño_formateado(mem.used)} ({mem.percent:.1f}%)")
            print(f"  Disponible: {self.obtener_tamaño_formateado(mem.available)}")
            
            disk = info['disk_usage']
            print(f"\nDisco Duro (C:):")
            print(f"  Total: {self.obtener_tamaño_formateado(disk.total)}")
            print(f"  Usado: {self.obtener_tamaño_formateado(disk.used)} ({disk.percent:.1f}%)")
            print(f"  Disponible: {self.obtener_tamaño_formateado(disk.free)}")
            
            print(f"\nSistema:")
            print(f"  Iniciado: {info['boot_time']}")
            print(f"  Procesos activos: {info['procesos']}")
        
        print("-"*60)
    
    def optimizar_rendimiento(self):
        """Realiza optimizaciones de rendimiento"""
        print("\n" + "-"*60)
        print("OPTIMIZACIÓN DE RENDIMIENTO\n")
        
        opciones = {
            '1': 'Limpiar memoria caché',
            '2': 'Cerrar aplicaciones innecesarias',
            '3': 'Desfragmentar disco (si es HDD)',
            '4': 'Optimizar inicio rápido',
            '5': 'Limpiar eventos de Windows',
            '0': 'Cancelar'
        }
        
        print("Opciones de optimización:\n")
        for key, desc in opciones.items():
            print(f"{key}. {desc}")
        
        opcion = input("\nTu opción: ").strip()
        
        if opcion == '1':
            self.limpiar_cache_sistema()
        elif opcion == '2':
            self.cerrar_aplicaciones_innecesarias()
        elif opcion == '3':
            self.optimizar_disco()
        elif opcion == '4':
            self.optimizar_inicio()
        elif opcion == '5':
            self.limpiar_eventos_sistema()
        elif opcion == '0':
            return
        else:
            print("Opción no válida")
    
    def limpiar_cache_sistema(self):
        """Limpia la caché del sistema"""
        print("\n[*] Limpiando caché del sistema...")
        
        try:
            subprocess.run(['powershell', '-Command', 
                          'Clear-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\RunMRU" -Name * -Force -ErrorAction SilentlyContinue'], 
                          check=False, capture_output=True, timeout=10)
            self.registrar("✓ Caché del sistema limpiado", "EXITO")
            print("✓ Caché del sistema limpiado")
        except Exception as e:
            self.registrar(f"✗ Error limpiando caché: {str(e)}", "ERROR")
    
    def cerrar_aplicaciones_innecesarias(self):
        """Sugiere cerrar aplicaciones innecesarias"""
        print("\n[*] Analizando procesos en ejecución...")
        
        try:
            procesos_innecesarios = [
                'OneDrive.exe',
                'SynTPEnh.exe',
                'GoogleCrashHandler.exe',
                'AdobeUpdate.exe',
                'iTunesHelper.exe',
            ]
            
            procesos_activos = []
            
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
                try:
                    if any(proc.info['name'].lower() == p.lower() for p in procesos_innecesarios):
                        procesos_activos.append({
                            'pid': proc.info['pid'],
                            'nombre': proc.info['name'],
                            'memoria': proc.info['memory_percent']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if procesos_activos:
                print("\nAplicaciones innecesarias detectadas:\n")
                for p in procesos_activos:
                    print(f"- {p['nombre']}: {p['memoria']:.2f}% de memoria")
                print("\nConsideración: Cierra manualmente estas aplicaciones para liberar recursos")
            else:
                print("No se detectaron aplicaciones innecesarias")
        
        except Exception as e:
            self.registrar(f"Error analizando procesos: {str(e)}", "ERROR")
    
    def optimizar_disco(self):
        """Optimiza el disco duro"""
        print("\n[*] Optimizando disco...")
        
        try:
            subprocess.run(['powershell', '-Command', 
                          'Optimize-Volume -DriveLetter C -Defrag -ErrorAction SilentlyContinue'], 
                          check=False, capture_output=True, timeout=300)
            self.registrar("✓ Disco optimizado", "EXITO")
            print("✓ Disco optimizado")
        except Exception as e:
            self.registrar(f"Optimización de disco en progreso o no disponible: {str(e)}", "ADVERTENCIA")
    
    def optimizar_inicio(self):
        """Optimiza el inicio del sistema"""
        print("\n[*] Optimizando inicio del sistema...")
        
        try:
            # Desactivar servicios innecesarios
            servicios_innecesarios = [
                'DiagTrack',
                'dmwappushservice',
                'TabletInputService'
            ]
            
            for servicio in servicios_innecesarios:
                try:
                    subprocess.run(['powershell', '-Command', 
                                  f'Stop-Service -Name {servicio} -Force -ErrorAction SilentlyContinue'], 
                                  check=False, capture_output=True, timeout=5)
                except:
                    pass
            
            self.registrar("✓ Inicio del sistema optimizado", "EXITO")
            print("✓ Inicio del sistema optimizado")
        except Exception as e:
            self.registrar(f"Error optimizando inicio: {str(e)}", "ERROR")
    
    def limpiar_eventos_sistema(self):
        """Limpia los eventos del sistema"""
        print("\n[*] Limpiando eventos del sistema...")
        
        try:
            subprocess.run(['powershell', '-Command', 
                          'Clear-EventLog -LogName Application, System -Force -ErrorAction SilentlyContinue'], 
                          check=False, capture_output=True, timeout=10)
            self.registrar("✓ Eventos del sistema limpiados", "EXITO")
            print("✓ Eventos del sistema limpiados")
        except Exception as e:
            self.registrar(f"Error limpiando eventos: {str(e)}", "ERROR")
    
    # ==================== ANÁLISIS DE REGISTRO ====================
    def analizar_registro(self):
        """Analiza el Registro de Windows para entradas inválidas"""
        print("\n" + "-"*60)
        print("ANÁLISIS DEL REGISTRO DE WINDOWS\n")
        
        print("[*] Escaneando el Registro de Windows...")
        print("    (Este proceso puede tomar varios minutos)\n")
        
        entradas_invalidas = {
            'rutas_rotas': [],
            'programas_no_instalados': [],
            'extensiones_dañadas': [],
            'codecs_inválidos': []
        }
        
        try:
            # Buscar rutas rotas en el Registro
            entradas_invalidas['rutas_rotas'] = self.buscar_rutas_rotas_registro()
            
            # Buscar programas desinstalados
            entradas_invalidas['programas_no_instalados'] = self.buscar_programas_desinstalados()
            
            # Buscar extensiones dañadas
            entradas_invalidas['extensiones_dañadas'] = self.buscar_extensiones_dañadas()
        
        except Exception as e:
            self.registrar(f"Error analizando registro: {str(e)}", "ERROR")
        
        self.mostrar_resultado_registro(entradas_invalidas)
        self.ofrecer_reparar_registro(entradas_invalidas)
    
    def buscar_rutas_rotas_registro(self):
        """Busca rutas rotas en el Registro"""
        rutas_rotas = []
        
        try:
            # Usar PowerShell para buscar rutas inválidas
            resultado = subprocess.run(
                ['powershell', '-Command',
                 'Get-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\RecentDocs" | Get-Member -MemberType NoteProperty | Select-Object -ExpandProperty Name'],
                capture_output=True, text=True, timeout=10
            )
            
            if resultado.stdout:
                rutas_rotas.append({
                    'tipo': 'Documentos Recientes',
                    'cantidad': len(resultado.stdout.split('\n')) - 1
                })
        
        except:
            pass
        
        return rutas_rotas
    
    def buscar_programas_desinstalados(self):
        """Busca referencias a programas desinstalados"""
        programas_desinstalados = []
        
        try:
            resultado = subprocess.run(
                ['powershell', '-Command',
                 'Get-ItemProperty "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*", "HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*" | Where-Object DisplayName -match ".+" | Measure-Object | Select-Object -ExpandProperty Count'],
                capture_output=True, text=True, timeout=10
            )
            
            if resultado.stdout:
                cantidad = int(resultado.stdout.strip())
                programas_desinstalados.append({
                    'tipo': 'Programas en Registro',
                    'cantidad': cantidad
                })
        
        except:
            pass
        
        return programas_desinstalados
    
    def buscar_extensiones_dañadas(self):
        """Busca extensiones de archivo dañadas"""
        extensiones_dañadas = []
        
        try:
            resultado = subprocess.run(
                ['powershell', '-Command',
                 'Get-Item "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\FileExts" | Get-ChildItem | Measure-Object | Select-Object -ExpandProperty Count'],
                capture_output=True, text=True, timeout=10
            )
            
            if resultado.stdout:
                cantidad = int(resultado.stdout.strip())
                if cantidad > 50:  # Si hay demasiadas, es sospechoso
                    extensiones_dañadas.append({
                        'tipo': 'Extensiones Sospechosas',
                        'cantidad': cantidad,
                        'accion': 'Considerar limpiar'
                    })
        
        except:
            pass
        
        return extensiones_dañadas
    
    def mostrar_resultado_registro(self, entradas_invalidas):
        """Muestra los resultados del análisis de registro"""
        print("\n" + "="*60)
        print("RESULTADOS DEL ANÁLISIS DE REGISTRO\n")
        
        total_problemas = 0
        
        for categoria, problemas in entradas_invalidas.items():
            if problemas:
                print(f"📋 {categoria.upper()}:")
                for problema in problemas:
                    print(f"   • {problema}")
                    total_problemas += 1
                print()
        
        if total_problemas == 0:
            print("✓ No se detectaron problemas en el Registro")
        else:
            print(f"⚠️  Se detectaron {total_problemas} posibles problemas")
        
        print("="*60)
    
    def ofrecer_reparar_registro(self, entradas_invalidas):
        """Ofrece reparar el registro"""
        confirmacion = input("\n¿Deseas reparar el Registro? (CUIDADO - Hacer backup primero) (s/n): ").strip().lower()
        
        if confirmacion == 's':
            self.reparar_registro(entradas_invalidas)
    
    def reparar_registro(self, entradas_invalidas):
        """Repara el Registro de Windows"""
        print("\n[*] Reparando Registro de Windows...")
        
        try:
            # Hacer backup del Registro
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_backup = f"Registro_Backup_{timestamp}.reg"
            
            subprocess.run(
                ['powershell', '-Command',
                 f'reg export HKCU "C:\\{nombre_backup}" /y'],
                capture_output=True, timeout=30
            )
            
            self.registrar(f"✓ Backup del Registro creado: {nombre_backup}", "EXITO")
            print(f"✓ Backup creado: {nombre_backup}")
            
            # Limpiar documentos recientes inválidos
            subprocess.run(
                ['powershell', '-Command',
                 'Remove-Item -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\RecentDocs" -ErrorAction SilentlyContinue'],
                capture_output=True, timeout=10
            )
            
            self.entradas_registro_eliminadas += 1
            self.registrar("✓ Registro reparado", "EXITO")
            print("✓ Registro reparado exitosamente")
        
        except Exception as e:
            self.registrar(f"✗ Error reparando Registro: {str(e)}", "ERROR")
            print(f"✗ Error: {str(e)}")
    
    # ==================== FUNCIONES PREVIAS ADAPTADAS ====================
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
        
        nombre_lower = nombre_archivo.lower()
        for patron in self.malware_signatures['trojan']:
            if re.match(patron, nombre_lower):
                amenazas.append(f"Nombre sospechoso: {nombre_archivo}")
        
        _, extension = os.path.splitext(nombre_archivo)
        if extension.lower() in self.malware_signatures['suspicious_extensions']:
            if 'temp' in ruta.lower() or 'appdata' in ruta.lower():
                amenazas.append(f"Ejecutable sospechoso en directorio temporal: {extension}")
        
        try:
            with open(ruta, 'rb') as f:
                header = f.read(1024)
                
                if b'MZ' in header:
                    if nombre_lower.endswith(('.jpg', '.png', '.txt', '.pdf')):
                        amenazas.append("Posible PE oculto con extensión falsa")
                
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
                if root[len(ruta):].count(os.sep) > profundidad_max:
                    continue
                
                for archivo in files:
                    ruta_archivo = os.path.join(root, archivo)
                    archivos_escaneados += 1
                    
                    try:
                        amenazas = self.verificar_firma_malware(ruta_archivo, archivo)
                        
                        if amenazas:
                            self.amenazas_detectadas += 1
                            for amenaza in amenazas:
                                self.registrar(f"⚠️  AMENAZA DETECTADA: {ruta_archivo}", "ADVERTENCIA")
                                self.registrar(f"   └─ {amenaza}", "ADVERTENCIA")
                        
                        if archivos_escaneados % 100 == 0:
                            self.registrar(f"   [{archivos_escaneados} archivos escaneados]", "INFO")
                    
                    except Exception as e:
                        self.registrar(f"Error escaneando {ruta_archivo}: {str(e)}", "ERROR")
        
        except Exception as e:
            self.registrar(f"Error accediendo a {ruta}: {str(e)}", "ERROR")
        
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
    
    def limpiar_directorio(self, ruta, eliminar_ocultos=False, eliminar_inactivos=False, dias_inactivos=30):
        """Limpia un directorio específico con opciones avanzadas"""
        if not os.path.exists(ruta):
            self.registrar(f"Directorio no existe: {ruta}", "ADVERTENCIA")
            return
        
        self.registrar(f"Limpiando: {ruta}", "INFO")
        
        try:
            for root, dirs, files in os.walk(ruta, topdown=False):
                for archivo in files:
                    ruta_archivo = os.path.join(root, archivo)
                    
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
    
    def limpiar_cache_navegadores(self):
        """Limpia caché de navegadores"""
        usuario = os.environ.get('USERNAME')
        
        chrome_cache = f"C:\\Users\\{usuario}\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cache"
        if os.path.exists(chrome_cache):
            self.registrar("Limpiando caché de Google Chrome...", "INFO")
            self.limpiar_directorio(chrome_cache)
        
        firefox_cache = f"C:\\Users\\{usuario}\\AppData\\Local\\Mozilla\\Firefox"
        if os.path.exists(firefox_cache):
            self.registrar("Limpiando caché de Mozilla Firefox...", "INFO")
            self.limpiar_directorio(firefox_cache)
        
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
    
    def mostrar_menu(self):
        """Muestra el menú principal"""
        print("\n" + "="*80)
        print("   LIMPIADOR INTEGRAL DE PC - VERSIÓN 5.0 COMPLETA")
        print("   Reparación | Ocultos | Inactivos | Malware | Duplicados | Registro | Rendimiento")
        print("="*80)
        print("\n🔒 SEGURIDAD Y MALWARE:")
        print("1. 🔍 Escaneo completo de malware")
        print("2. ⚡ Escaneo rápido de malware")
        print("3. 📦 Gestor de cuarentena")
        print("\n🧹 LIMPIEZA GENERAL:")
        print("4. Limpieza RÁPIDA")
        print("5. Limpieza COMPLETA")
        print("6. Limpieza PERSONALIZADA")
        print("\n📊 DUPLICADOS Y ARCHIVOS:")
        print("7. 📋 Buscar archivos DUPLICADOS")
        print("8. 🗑️  Eliminar DUPLICADOS encontrados")
        print("\n📝 REGISTRO DEL SISTEMA:")
        print("9. 🔎 Analizar Registro de Windows")
        print("\n⚡ OPTIMIZACIÓN Y RENDIMIENTO:")
        print("10. 🖥️  Ver información del sistema")
        print("11. ⚙️  Optimizar rendimiento")
        print("12. 🚀 OPTIMIZACIÓN ULTRA COMPLETA (TODO)")
        print("\n📊 INFORMACIÓN:")
        print("13. Ver registro de actividades")
        print("0. Salir")
        print("\n" + "-"*80)
    
    def mostrar_resumen(self):
        """Muestra un resumen completo"""
        tiempo_transcurrido = datetime.now() - self.inicio
        
        print("\n" + "="*80)
        print("   RESUMEN COMPLETO DE LA OPERACIÓN")
        print("="*80)
        
        print("\n📊 LIMPIEZA:")
        print(f"  ✓ Archivos eliminados: {self.archivos_eliminados}")
        print(f"  ✓ Archivos ocultos eliminados: {self.archivos_ocultos_eliminados}")
        print(f"  ✓ Archivos reparados: {self.archivos_reparados}")
        print(f"  ⚠️  Archivos omitidos: {self.archivos_omitidos}")
        
        print("\n🔒 SEGURIDAD:")
        print(f"  ⚠️  Amenazas detectadas: {self.amenazas_detectadas}")
        print(f"  📦 Archivos cuarentenados: {self.archivos_cuarentenados}")
        
        print("\n📋 DUPLICADOS:")
        print(f"  📁 Duplicados encontrados: {self.duplicados_encontrados}")
        print(f"  🗑️  Duplicados eliminados: {self.duplicados_eliminados}")
        
        print("\n📝 REGISTRO:")
        print(f"  ✓ Entradas reparadas: {self.entradas_registro_eliminadas}")
        
        print("\n📊 ESPACIO:")
        print(f"  ↓ Espacio total liberado: {self.obtener_tamaño_formateado(self.espacio_liberado)}")
        print(f"  ⏱ Tiempo transcurrido: {tiempo_transcurrido}")
        
        if self.errores:
            print(f"\n✗ Errores encontrados: {len(self.errores)}")
        
        print("\n" + "="*80)
        print(f"📋 Registro guardado en: {self.log_file}")
        print(f"📦 Cuarentena: {self.quarantine_dir}\n")
    
    def ejecutar(self):
        """Loop principal"""
        while True:
            self.mostrar_menu()
            opcion = input("Ingresa tu opción: ").strip()
            
            if opcion == '0':
                print("\n¡Hasta luego! Gracias por usar el Limpiador Integral.\n")
                break
            elif opcion == '1':
                self.escaneo_malware_completo()
            elif opcion == '2':
                self.escaneo_malware_rapido()
            elif opcion == '3':
                self.gestor_cuarentena()
            elif opcion == '4':
                confirmacion = input("\n¿Continuar? (s/n): ").strip().lower()
                if confirmacion == 's':
                    self.limpieza_rapida()
            elif opcion == '5':
                confirmacion = input("\n¿Continuar? (s/n): ").strip().lower()
                if confirmacion == 's':
                    self.limpieza_completa()
            elif opcion == '6':
                self.limpieza_personalizada()
            elif opcion == '7':
                self.registrar("="*60, "INFO")
                self.registrar("INICIANDO BÚSQUEDA DE DUPLICADOS", "INFO")
                self.registrar("="*60, "INFO")
                usuario = os.environ.get('USERNAME')
                duplicados = self.buscar_duplicados(f"C:\\Users\\{usuario}\\Downloads")
                self.mostrar_duplicados(duplicados)
            elif opcion == '8':
                self.registrar("="*60, "INFO")
                self.registrar("INICIANDO ELIMINACIÓN DE DUPLICADOS", "INFO")
                self.registrar("="*60, "INFO")
                usuario = os.environ.get('USERNAME')
                duplicados = self.buscar_duplicados(f"C:\\Users\\{usuario}\\Downloads")
                if duplicados:
                    self.eliminar_duplicados_automatico(duplicados)
            elif opcion == '9':
                self.registrar("="*60, "INFO")
                self.registrar("INICIANDO ANÁLISIS DE REGISTRO", "INFO")
                self.registrar("="*60, "INFO")
                self.analizar_registro()
            elif opcion == '10':
                self.mostrar_info_sistema()
            elif opcion == '11':
                self.optimizar_rendimiento()
            elif opcion == '12':
                self.optimizacion_ultra_completa()
            elif opcion == '13':
                self.ver_registro()
            else:
                print("\n✗ Opción no válida. Intenta de nuevo.\n")
            
            if opcion in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '11', '12']:
                input("\nPresiona Enter para continuar...")
    
    def limpieza_rapida(self):
        """Limpieza rápida"""
        self.registrar("="*60, "INFO")
        self.registrar("INICIANDO LIMPIEZA RÁPIDA", "INFO")
        self.registrar("="*60, "INFO")
        
        usuario = os.environ.get('USERNAME')
        self.limpiar_directorio(os.path.expandvars(r'%TEMP%'))
        self.limpiar_directorio(f"C:\\Users\\{usuario}\\AppData\\Local\\Temp")
        self.limpiar_papelera()
        
        self.mostrar_resumen()
    
    def limpieza_completa(self):
        """Limpieza completa"""
        self.registrar("="*60, "INFO")
        self.registrar("INICIANDO LIMPIEZA COMPLETA", "INFO")
        self.registrar("="*60, "INFO")
        
        usuario = os.environ.get('USERNAME')
        self.limpiar_directorio(os.path.expandvars(r'%TEMP%'))
        self.limpiar_aplicaciones_temporales()
        self.limpiar_cache_navegadores()
        self.limpiar_papelera()
        
        self.mostrar_resumen()
    
    def limpieza_personalizada(self):
        """Limpieza personalizada"""
        print("\n" + "-"*60)
        print("LIMPIEZA PERSONALIZADA\n")
        
        opciones = {
            '1': ('Temporales', self.limpiar_directorio, os.path.expandvars(r'%TEMP%')),
            '2': ('Navegadores', self.limpiar_cache_navegadores, None),
            '3': ('Papelera', self.limpiar_papelera, None),
            '4': ('Aplicaciones', self.limpiar_aplicaciones_temporales, None),
        }
        
        print("Selecciona qué limpiar:\n")
        for key, (desc, _, _) in opciones.items():
            print(f"{key}. {desc}")
        print("0. Cancelar\n")
        
        seleccion = input("Tu selección: ").strip()
        
        if seleccion == '0':
            return
        
        if seleccion in opciones:
            desc, funcion, param = opciones[seleccion]
            if param:
                funcion(param)
            else:
                funcion()
            self.mostrar_resumen()
    
    def optimizacion_ultra_completa(self):
        """Ultra completa"""
        print("\n" + "-"*60)
        print("🚀 OPTIMIZACIÓN ULTRA COMPLETA\n")
        print("Esta operación realizará:")
        print("  1. Escaneo de malware")
        print("  2. Búsqueda de duplicados")
        print("  3. Análisis de Registro")
        print("  4. Optimización de rendimiento")
        print("  5. Limpieza completa")
        print("  ⚠️  Esto puede tomar 20-40 minutos\n")
        
        confirmacion = input("¿Continuar? (s/n): ").strip().lower()
        if confirmacion == 's':
            self.registrar("="*60, "INFO")
            self.registrar("INICIANDO OPTIMIZACIÓN ULTRA COMPLETA", "INFO")
            self.registrar("="*60, "INFO")
            
            print("\n[1/5] Escaneando malware...")
            usuario = os.environ.get('USERNAME')
            rutas = [os.path.expandvars(r'%TEMP%'), f"C:\\Users\\{usuario}\\Downloads"]
            for ruta in rutas:
                if os.path.exists(ruta):
                    self.escanear_malware_directorio(ruta, profundidad_max=2)
            
            print("\n[2/5] Buscando duplicados...")
            duplicados = self.buscar_duplicados(f"C:\\Users\\{usuario}\\Downloads")
            if duplicados:
                self.eliminar_duplicados_automatico(duplicados)
            
            print("\n[3/5] Analizando Registro...")
            self.analizar_registro()
            
            print("\n[4/5] Optimizando rendimiento...")
            self.limpiar_cache_sistema()
            
            print("\n[5/5] Limpiando archivos...")
            self.limpieza_completa()
            
            self.mostrar_resumen()
    
    def escaneo_malware_completo(self):
        """Escaneo malware completo"""
        print("\n" + "-"*60)
        print("ESCANEO DE MALWARE COMPLETO\n")
        
        usuario = os.environ.get('USERNAME')
        rutas = [
            os.path.expandvars(r'%TEMP%'),
            f"C:\\Users\\{usuario}\\Downloads",
            f"C:\\Users\\{usuario}\\AppData\\Local\\Temp",
        ]
        
        confirmacion = input("¿Continuar? (s/n): ").strip().lower()
        if confirmacion == 's':
            self.registrar("="*60, "INFO")
            self.registrar("INICIANDO ESCANEO DE MALWARE", "INFO")
            self.registrar("="*60, "INFO")
            
            for ruta in rutas:
                if os.path.exists(ruta):
                    self.escanear_malware_directorio(ruta)
            
            self.mostrar_resumen()
    
    def escaneo_malware_rapido(self):
        """Escaneo rápido"""
        print("\n" + "-"*60)
        print("ESCANEO RÁPIDO DE MALWARE\n")
        
        usuario = os.environ.get('USERNAME')
        rutas = [
            os.path.expandvars(r'%TEMP%'),
            f"C:\\Users\\{usuario}\\Downloads",
        ]
        
        confirmacion = input("¿Continuar? (s/n): ").strip().lower()
        if confirmacion == 's':
            self.registrar("="*60, "INFO")
            self.registrar("INICIANDO ESCANEO RÁPIDO", "INFO")
            self.registrar("="*60, "INFO")
            
            for ruta in rutas:
                if os.path.exists(ruta):
                    self.escanear_malware_directorio(ruta, profundidad_max=1)
            
            self.mostrar_resumen()
    
    def gestor_cuarentena(self):
        """Gestor cuarentena"""
        print("\n" + "-"*60)
        print("GESTOR DE CUARENTENA\n")
        
        if not os.path.exists(self.quarantine_dir):
            print("La cuarentena está vacía.")
            return
        
        archivos = os.listdir(self.quarantine_dir)
        
        if not archivos:
            print("La cuarentena está vacía.")
            return
        
        print(f"Archivos en cuarentena ({len(archivos)}):\n")
        for i, archivo in enumerate(archivos, 1):
            tamaño = os.path.getsize(os.path.join(self.quarantine_dir, archivo))
            print(f"{i}. {archivo} ({self.obtener_tamaño_formateado(tamaño)})")
        
        print("\nOpciones:")
        print("1. Eliminar archivo")
        print("2. Vaciar cuarentena")
        print("0. Volver\n")
        
        opcion = input("Tu opción: ").strip()
        
        if opcion == '1':
            try:
                num = int(input(f"Número del archivo: ")) - 1
                if 0 <= num < len(archivos):
                    ruta = os.path.join(self.quarantine_dir, archivos[num])
                    os.remove(ruta)
                    print("✓ Archivo eliminado")
            except:
                pass
        elif opcion == '2':
            confirmacion = input("¿Vaciar toda la cuarentena? (s/n): ").strip().lower()
            if confirmacion == 's':
                for archivo in archivos:
                    ruta = os.path.join(self.quarantine_dir, archivo)
                    os.remove(ruta)
                print("✓ Cuarentena vaciada")
    
    def ver_registro(self):
        """Ver registro"""
        print("\n" + "-"*60)
        print("REGISTRO DE ACTIVIDADES\n")
        
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lineas = f.readlines()[-50:]
                for linea in lineas:
                    print(linea.rstrip())
        else:
            print("No hay registro.")
        print("-"*60)

def main():
    """Punto de entrada"""
    print("\n" + "="*80)
    print("   LIMPIADOR INTEGRAL DE PC - VERSIÓN 5.0")
    print("   Limpieza | Reparación | Malware | Duplicados | Registro | Optimización")
    print("   Por favor ejecuta como ADMINISTRADOR")
    print("="*80 + "\n")
    
    try:
        import ctypes
        if os.name == 'nt':
            if not ctypes.windll.shell32.IsUserAnAdmin():
                print("⚠️  ADVERTENCIA: Ejecuta como ADMINISTRADOR\n")
                if input("¿Continuar? (s/n): ").strip().lower() != 's':
                    sys.exit(1)
    except:
        pass
    
    limpiador = LimpiadoTemporal()
    limpiador.ejecutar()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Programa interrumpido.")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        sys.exit(1)
