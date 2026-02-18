# 🖥️ SystemCheck - Auditor de Hardware y Red

![Python](https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python)
![PowerShell](https://img.shields.io/badge/PowerShell-Scripting-blue?style=for-the-badge&logo=powershell)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows)

**SystemCheck** es una herramienta de diagnóstico portátil diseñada para técnicos de soporte IT y administradores de sistemas. Combina la potencia de **PowerShell** para la extracción de datos de bajo nivel (WMI/CIM) con una interfaz gráfica moderna y ligera construida en **Python (PySide6)**.

> 🔒 **Privacidad Total:** Esta herramienta se ejecuta 100% en local. No recopila, almacena ni envía telemetría a servidores externos.

---

## 🚀 Características Principales

### 🛠️ Diagnóstico de Hardware
* **CPU & Motherboard:** Detección exacta de modelos y socket.
* **RAM Detallada:** Visualización de módulos individuales, capacidad y **velocidad (MHz)** para detectar cuellos de botella.
* **Almacenamiento Inteligente:** Identifica tecnología (NVMe vs SATA vs HDD), salud del disco y alerta visual de espacio libre crítico. Detecta automáticamente el disco de sistema (C:).
* **Gráficos (GPU):** Detección de múltiples tarjetas y lectura corregida de VRAM para tarjetas modernas (+4GB) mediante registro.

### 🌐 Diagnóstico de Red
* **Velocidad de Enlace:** Detecta si la conexión es Gigabit o está limitada a 100Mbps (cable dañado).
* **Conectividad:** Ping automático a Gateway y Google DNS para validar salida a internet.
* **Configuración:** Visualización rápida de IP, MAC, Gateway y DNS actuales.

### 📄 Reportes
* Exportación de toda la información a un archivo de texto (`.txt`) con fecha y hora para entregar al cliente.

---

## 🔧 Instalación y Uso

### Opción A: Ejecutable Portátil (Recomendado)
1.  Ve a la sección de [Releases](https://github.com/EzequielOrtizIT/SystemCheck/releases) (próximamente).
2.  Descarga el archivo `AuditorHardware.exe`.
3.  Ejecuta en cualquier PC con Windows 10/11 (No requiere instalación de Python ni dependencias).

### Opción B: Ejecutar desde el código fuente
Si deseas modificar o probar el código:

1.  Clona el repositorio:
    ```bash
    git clone [https://github.com/EzequielOrtizIT/SystemCheck.git](https://github.com/EzequielOrtizIT/SystemCheck.git)
    ```
2.  Instala las dependencias:
    ```bash
    pip install -r requirements.txt
    ```
3.  Ejecuta la aplicación:
    ```bash
    python main.py
    ```

---

## 📦 Compilación (Crear .exe)

Si quieres generar tu propio ejecutable portátil, utiliza **PyInstaller**. El archivo `.spec` ya está incluido en el repositorio para facilitar la tarea.

Ejecuta el siguiente comando en la raíz del proyecto:

```Bash
pyinstaller AuditorHardware.spec

```
O manualmente:


```Bash

pyinstaller --noconsole --onefile --name="AuditorHardware" --add-data "Check-PC.ps1;." --add-data "diseño.ui;." main.py

```
El ejecutable resultante aparecerá en la carpeta dist/.

🛠️ Tecnologías Usadas
Frontend: Python + PySide6 (Qt Designer).

Backend: PowerShell Scripting (WMI, CIM, NetAdapter).

Comunicación: Subprocess & JSON parsing.

📝 Licencia
Este proyecto es de código abierto. Siéntete libre de usarlo, modificarlo y mejorarlo para tus propias necesidades de soporte técnico.

Desarrollado por Ezequiel Ortiz 🇦🇷
