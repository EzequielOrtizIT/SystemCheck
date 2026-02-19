import subprocess
import os
import json
import datetime

def iniciar_auditoria_silenciosa():
    script_path = "Check-PC.ps1"
    hostname = os.environ.get('COMPUTERNAME', 'PC_Desconocida')
    carpeta_logs = "Reportes"

    print(f"▶ Iniciando escaneo en: {hostname}...")

    # Creamos la carpeta de reportes si no existe
    if not os.path.exists(carpeta_logs):
        os.makedirs(carpeta_logs)

    # Nombre del archivo: Ej. "RECEPCION-01.json"
    archivo_salida = os.path.join(carpeta_logs, f"{hostname}.json")

    command = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path]

    try:
        # creationflags=subprocess.CREATE_NO_WINDOW evita que parpadee la ventana negra
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            encoding='utf-8', 
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                data["fecha_auditoria"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Guardamos el JSON
                with open(archivo_salida, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                    
                print(f"✅ Auditoría completada. Archivo generado: {archivo_salida}")
            except json.JSONDecodeError:
                print(f"❌ Error al interpretar los datos. Salida cruda:\n{result.stdout}")
        else:
            print(f"❌ Error ejecutando PowerShell:\n{result.stderr}")
            
    except Exception as e:
        print(f"❌ Error crítico:\n{e}")

if __name__ == "__main__":
    iniciar_auditoria_silenciosa()