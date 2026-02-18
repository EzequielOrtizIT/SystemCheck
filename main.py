import sys
import subprocess
import os
import json
import datetime
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile, QThread, Signal

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

UI_FILE = resource_path("diseño.ui")
SCRIPT_FILE = resource_path("Check-PC.ps1")

class WorkerThread(QThread):
    finished = Signal(dict)
    error = Signal(str)

    def run(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        script_path = os.path.join(base_path, SCRIPT_FILE)
        
        # Opcion de seguridad: si no encuentra el script
        if not os.path.exists(script_path):
            # Fallback para desarrollo si el script está en la raiz
            if os.path.exists("Check-PC.ps1"):
                script_path = "Check-PC.ps1"
            else:
                self.error.emit(f"No encuentro: {script_path}")
                return

        command = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path]

        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                encoding='utf-8', 
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            if result.returncode == 0:
                try:
                    data_dict = json.loads(result.stdout)
                    self.finished.emit(data_dict)
                except json.JSONDecodeError:
                    self.error.emit(f"Error al leer datos (JSON Malformado): {result.stdout}")
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

        # --- DATOS EN MEMORIA ---
        self.data_actual = {}

        # --- CONEXIONES UI ---
        self.btn_scan = self.window.findChild(object, "btn_scan")
        self.btn_save = self.window.findChild(object, "btn_save")
        self.action_about = self.window.findChild(object, "actionacerca")
        
        # --- INPUTS (Inventario y Salud) ---
        self.input_user = self.window.findChild(object, "input_user")
        self.input_av = self.window.findChild(object, "input_av")
        self.input_uptime = self.window.findChild(object, "input_uptime")
        self.input_reboot = self.window.findChild(object, "input_reboot")
        
        self.input_os = self.window.findChild(object, "input_os")
        self.input_cpu = self.window.findChild(object, "input_cpu")
        self.input_mobo = self.window.findChild(object, "input_mobo")
        self.input_ram = self.window.findChild(object, "input_ram")
        # Video no está en la UI nueva, pero si querés podes reusar algun campo o agregarlo
        # En el diseño actual dejamos Espacio para Discos
        self.txt_disk = self.window.findChild(object, "txt_disk")

        # --- INPUTS (Red) ---
        self.input_net_name = self.window.findChild(object, "input_net_name")
        self.input_net_mac = self.window.findChild(object, "input_net_mac")
        self.input_net_speed = self.window.findChild(object, "input_net_speed")
        self.input_net_ip = self.window.findChild(object, "input_net_ip")
        self.input_net_ping = self.window.findChild(object, "input_net_ping")

        # Lógica Botones
        if self.btn_scan: self.btn_scan.clicked.connect(self.iniciar_escaneo)
        if self.btn_save: 
            self.btn_save.clicked.connect(self.guardar_reporte)
            self.btn_save.setEnabled(False)

        if self.action_about: self.action_about.triggered.connect(self.mostrar_acerca_de)

    def iniciar_escaneo(self):
        if self.btn_scan: 
            self.btn_scan.setEnabled(False)
            self.btn_scan.setText("Analizando equipo...")
        if self.btn_save: self.btn_save.setEnabled(False)

        self.worker = WorkerThread()
        self.worker.finished.connect(self.rellenar_datos)
        self.worker.error.connect(self.mostrar_error)
        self.worker.start()

    def rellenar_datos(self, data):
        self.data_actual = data # Guardamos para exportar después

        # Identidad y Salud
        if self.input_user: 
            usuario = f"{data.get('domain','')}\\{data.get('user','')}"
            self.input_user.setText(usuario)
        
        if self.input_av: 
            av = data.get("av", "No detectado")
            self.input_av.setText(av)
            if "Kaspersky" in av:
                self.input_av.setStyleSheet("color: #000000; background-color: #d4edda; font-weight: bold;") # Verde suave
            else:
                 self.input_av.setStyleSheet("color: #000000; background-color: #f8d7da;") # Rojo suave
        
        if self.input_uptime: self.input_uptime.setText(data.get("uptime", ""))
        
        if self.input_reboot: 
            estado = data.get("reboot", "")
            self.input_reboot.setText(estado)
            if "PENDIENTE" in estado or "RECOMENDADO" in estado:
                self.input_reboot.setStyleSheet("color: red; background-color: #f0f0f0; font-weight: bold;")
            else:
                self.input_reboot.setStyleSheet("color: green; background-color: #f0f0f0; font-weight: bold;")

        # Hardware
        if self.input_os: self.input_os.setText(data.get("os", ""))
        if self.input_cpu: self.input_cpu.setText(data.get("cpu", ""))
        if self.input_mobo: self.input_mobo.setText(data.get("mobo", ""))
        if self.input_ram: self.input_ram.setText(data.get("ram", ""))
        
        if self.txt_disk: self.txt_disk.setText(data.get("disk", ""))

        # Red
        if self.input_net_name: self.input_net_name.setText(data.get("net_name", ""))
        if self.input_net_mac: self.input_net_mac.setText(data.get("net_mac", ""))
        if self.input_net_speed: self.input_net_speed.setText(data.get("net_speed", ""))
        
        ip_info = f"{data.get('net_ip','')} (GW: {data.get('net_gw','')})"
        if self.input_net_ip: self.input_net_ip.setText(ip_info)
        
        if self.input_net_ping: self.input_net_ping.setText(data.get("net_ping", ""))

        # Botones
        if self.btn_scan: 
            self.btn_scan.setEnabled(True)
            self.btn_scan.setText("Escanear de nuevo")
        if self.btn_save: self.btn_save.setEnabled(True)

    def guardar_reporte(self):
        # Permitimos guardar como TXT o JSON
        nombre_archivo, filtro = QFileDialog.getSaveFileName(
            self.window, 
            "Exportar Datos", 
            f"Reporte_{os.environ.get('USERNAME', 'PC')}.txt", 
            "Archivo de Texto (*.txt);;Archivo JSON (*.json)"
        )

        if not nombre_archivo: return

        if nombre_archivo.endswith(".json"):
            # GUARDAR JSON
            try:
                with open(nombre_archivo, 'w', encoding='utf-8') as f:
                    # Agregamos fecha de exportacion al json
                    self.data_actual["fecha_exportacion"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    json.dump(self.data_actual, f, indent=4, ensure_ascii=False)
                QMessageBox.information(self.window, "Exportado", "JSON generado correctamente.")
            except Exception as e:
                QMessageBox.critical(self.window, "Error", f"Error al guardar JSON: {e}")
        else:
            # GUARDAR TXT (Formato Informe)
            fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data = self.data_actual
            
            # Recuperamos valores seguros
            usuario = f"{data.get('domain','')}\\{data.get('user','')}"
            
            reporte = f"""========================================
REPORTE DE AUDITORÍA TÉCNICA
Fecha: {fecha}
========================================

[ 👤 IDENTIDAD Y ACCESO ]
Usuario:      {usuario}
Antivirus:    {data.get('av', 'No detectado')}

[ 🏥 ESTADO DE SALUD ]
Uptime:       {data.get('uptime', '-')}
Estado:       {data.get('reboot', '-')}

[ 💻 HARDWARE PRINCIPAL ]
OS:           {data.get('os', '-')}
CPU:          {data.get('cpu', '-')}
RAM:          {data.get('ram', '-')}
Motherboard:  {data.get('mobo', '-')}

[ 💾 ALMACENAMIENTO ]
{data.get('disk', '-')}

[ 🌐 CONECTIVIDAD ]
Adaptador:    {data.get('net_name', '-')}
MAC:          {data.get('net_mac', '-')}
IP / GW:      {data.get('net_ip', '-')} / {data.get('net_gw', '-')}
DNS:          {data.get('net_dns', '-')}
Velocidad:    {data.get('net_speed', '-')}
Estado:       {data.get('net_ping', '-')}

========================================
Generado por Auditor IT - AyudaTecno
"""
            try:
                with open(nombre_archivo, 'w', encoding='utf-8') as f:
                    f.write(reporte)
                QMessageBox.information(self.window, "Exportado", "Reporte TXT generado correctamente.")
            except Exception as e:
                QMessageBox.critical(self.window, "Error", f"Error al guardar TXT: {e}")

    def mostrar_error(self, mensaje):
        if self.txt_disk: self.txt_disk.setText(f"ERROR: {mensaje}")
        if self.btn_scan: 
            self.btn_scan.setEnabled(True)
            self.btn_scan.setText("Reintentar")

    def mostrar_acerca_de(self):
        QMessageBox.information(self.window, "SystemCheck", "Herramienta de Auditoría IT\nVersión 2.0 (JSON + AV Support)")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mi_app = MiApp()
    sys.exit(app.exec())