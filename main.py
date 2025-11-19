import sys
import subprocess
import os
import json
import datetime
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QThread, Signal


def resource_path(relative_path):
    """ Devuelve la ruta absoluta al recurso, funcione como script o como exe """
    try:
        # PyInstaller crea una carpeta temporal en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Si estamos en modo normal (desarrollo)
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- MODIFICAMOS LAS RUTAS GLOBALES ---
# En lugar de poner el nombre directo, lo pasamos por la función mágica
UI_FILE = resource_path("diseño.ui")
SCRIPT_FILE = resource_path("Check-PC.ps1")


class WorkerThread(QThread):
    finished = Signal(dict)
    error = Signal(str)

    def run(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(base_path, SCRIPT_FILE)

        if not os.path.exists(script_path):
            self.error.emit(f"No encuentro: {script_path}")
            return

        command = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path]

        try:
            # Usamos utf-8 porque forzamos utf-8 en el script de powershell al principio
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                encoding='utf-8', 
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if result.returncode == 0:
                try:
                    # AQUI ESTÁ LA MAGIA: Convertimos el texto JSON a Variables Python
                    data_dict = json.loads(result.stdout)
                    self.finished.emit(data_dict)
                except json.JSONDecodeError:
                    self.error.emit(f"Error al leer datos: {result.stdout}")
            else:
                self.error.emit(f"Error script: {result.stderr}")

        except Exception as e:
            self.error.emit(f"Error crítico: {e}")

class MiApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui_file = QFile(UI_FILE)
        if not self.ui_file.open(QFile.ReadOnly): sys.exit()
        loader = QUiLoader()
        self.window = loader.load(self.ui_file)
        self.ui_file.close()
        self.window.show()

        # --- CONEXIONES ---
        self.btn_scan = self.window.findChild(object, "btn_scan")
        self.btn_save = self.window.findChild(object, "btn_save")
        self.action_about = self.window.findChild(object, "actionacerca")
        
        # Inputs
        self.input_cpu = self.window.findChild(object, "input_cpu")
        self.input_mobo = self.window.findChild(object, "input_mobo")
        self.input_ram = self.window.findChild(object, "input_ram")
        self.input_os = self.window.findChild(object, "input_os")
        self.input_vga = self.window.findChild(object, "input_vga")
        self.txt_disk = self.window.findChild(object, "txt_disk")

        self.input_net_name = self.window.findChild(object, "input_net_name")
        self.input_net_mac = self.window.findChild(object, "input_net_mac")
        self.input_net_speed = self.window.findChild(object, "input_net_speed")
        self.input_net_ip = self.window.findChild(object, "input_net_ip")
        self.input_net_ping = self.window.findChild(object, "input_net_ping")

        # Lógica del Botón Scan
        if self.btn_scan:
            self.btn_scan.clicked.connect(self.iniciar_escaneo)

        # Lógica del Botón Save (NUEVO)
        if self.btn_save:
            self.btn_save.clicked.connect(self.guardar_reporte)
            self.btn_save.setEnabled(False) # Desactivado hasta que haya datos

        if self.action_about:
            # En los menús, la señal no es 'clicked', es 'triggered'
            self.action_about.triggered.connect(self.mostrar_acerca_de)
        else:
            print("⚠️ Advertencia: No encontré 'actionacerca' en el diseño.")    

    def iniciar_escaneo(self):
        if self.btn_scan: 
            self.btn_scan.setEnabled(False)
            self.btn_scan.setText("Escaneando...")
        
        # Desactivamos guardar mientras escanea
        if self.btn_save: self.btn_save.setEnabled(False)

        self.worker = WorkerThread()
        self.worker.finished.connect(self.rellenar_datos)
        self.worker.error.connect(self.mostrar_error)
        self.worker.start()

    def rellenar_datos(self, data):
        # Rellenamos las cajas
        if self.input_cpu: self.input_cpu.setText(data.get("cpu", ""))
        if self.input_mobo: self.input_mobo.setText(data.get("mobo", ""))
        if self.input_ram: self.input_ram.setText(data.get("ram", ""))
        if self.input_os: self.input_os.setText(data.get("os", ""))
        if self.input_vga: self.input_vga.setText(data.get("vga", ""))
        if self.txt_disk: self.txt_disk.setText(data.get("disk", ""))

        if self.input_net_name: self.input_net_name.setText(data.get("net_name", ""))
        if self.input_net_mac: self.input_net_mac.setText(data.get("net_mac", ""))
        if self.input_net_speed: self.input_net_speed.setText(data.get("net_speed", ""))
        
        ip_info = f"IP: {data.get('net_ip','')} | GW: {data.get('net_gw','')}"
        if self.input_net_ip: self.input_net_ip.setText(ip_info)
        
        if self.input_net_ping: self.input_net_ping.setText(data.get("net_ping", ""))

        # Reactivamos botones
        if self.btn_scan: 
            self.btn_scan.setEnabled(True)
            self.btn_scan.setText("Escanear de nuevo")
        
        # Habilitamos el botón de guardar porque ya hay datos
        if self.btn_save: self.btn_save.setEnabled(True)

    def guardar_reporte(self):
        # 1. Preguntar dónde guardar
        nombre_archivo, _ = QFileDialog.getSaveFileName(
            self.window, 
            "Guardar Reporte Técnico", 
            "Reporte_PC.txt", 
            "Archivos de Texto (*.txt)"
        )

        if not nombre_archivo: return # Si cancela, no hacemos nada

        # 2. Armar el texto bonito con fecha
        fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Usamos f-strings para capturar el texto de cada caja
        # Agregamos validaciones simples (por si algún campo no existe, poner guión)
        
        net_adapter = self.input_net_name.text() if self.input_net_name else "-"
        net_mac = self.input_net_mac.text() if self.input_net_mac else "-"
        net_speed = self.input_net_speed.text() if self.input_net_speed else "-"
        net_ip = self.input_net_ip.text() if self.input_net_ip else "-"
        net_ping = self.input_net_ping.text() if self.input_net_ping else "-"

        reporte = f"""========================================
REPORTE TÉCNICO DE HARDWARE
Fecha: {fecha}
========================================

[ SISTEMA OPERATIVO ]
{self.input_os.text()}

[ PLACA BASE ]
{self.input_mobo.text()}

[ PROCESADOR ]
{self.input_cpu.text()}

[ MEMORIA RAM ]
{self.input_ram.text()}

[ GRAFICOS ]
{self.input_vga.text()}

[ ALMACENAMIENTO ]
{self.txt_disk.toPlainText()}

[ RED Y CONECTIVIDAD ]
Adaptador: {net_adapter}
Dirección MAC: {net_mac}
Velocidad: {net_speed}
Configuración: {net_ip}
Estado Internet: {net_ping}

========================================
Generado por Ezequiel Ortiz - Hardware Check
"""

        # 3. Guardar en disco
        try:
            with open(nombre_archivo, 'w', encoding='utf-8') as f:
                f.write(reporte)
            
            QMessageBox.information(self.window, "Éxito", "El reporte se guardó correctamente.")
            
        except Exception as e:
            QMessageBox.critical(self.window, "Error", f"No se pudo guardar el archivo:\n{e}")

    def mostrar_error(self, mensaje):
        if self.txt_disk: self.txt_disk.setText(f"ERROR: {mensaje}")
        if self.btn_scan: 
            self.btn_scan.setEnabled(True)
            self.btn_scan.setText("Reintentar")

    def mostrar_acerca_de(self):
        QMessageBox.information(
            self.window, 
            "Acerca de Escaner de sistema", 
            """
            🚀 Escaner de Sistema v1.0
            
            Desarrollado por: Ezequiel Ortiz
            Tecnologías: Python + PowerShell + PySide6
            
            Esta herramienta escanea el hardware y la red local 
            para facilitar el diagnóstico técnico.

            No recopila información de ningun tipo.
            """
        )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mi_app = MiApp()
    sys.exit(app.exec())