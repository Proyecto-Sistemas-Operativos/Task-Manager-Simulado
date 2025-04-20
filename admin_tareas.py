import tkinter as tk
from tkinter import ttk
import subprocess
import time
import threading

PROGRAMAS_DISPONIBLES = ["wordpad.exe", "calc.exe", "EXCEL.EXE"]
procesos_activos = []

root = tk.Tk()
root.title("Simulador de Administrador de Tareas")
root.geometry("700x450")

tree = ttk.Treeview(root, columns=("PID", "Programa", "CPU", "RAM"), show="headings")
tree.heading("PID", text="PID")
tree.heading("Programa", text="Programa")
tree.heading("CPU", text="Uso CPU (%)")
tree.heading("RAM", text="Uso RAM (MB)")
tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

programa_seleccionado = tk.StringVar(value=PROGRAMAS_DISPONIBLES[0])

def ejecutar_powershell(cmd):
    try:
        salida = subprocess.check_output(["powershell", "-Command", cmd], text=True)
        return salida.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando PowerShell: {e}")
        return ""

def obtener_procesos():
    try:
        wordpad = ejecutar_powershell('tasklist /FI "IMAGENAME eq wordpad.exe" /V /FO list')
        calc = ejecutar_powershell('tasklist /FI "IMAGENAME eq CalculatorApp.exe" /V /FO list')
        excel = ejecutar_powershell('tasklist /FI "IMAGENAME eq EXCEL.exe" /V /FO list')
        if wordpad.startswith("INFOR"):
            wordpad = ""
        if calc.startswith("INFOR"):
            calc = ""
        if excel.startswith("INFOR"):
            excel = ""
        parse_lista_procesos([wordpad, calc, excel])
    except Exception as e:
        print(f"Error al obtener procesos: {e}")

def parse_lista_procesos(tasklists):
    procesos_activos.clear()
    for tasklist in tasklists:
        if len(tasklist) > 0:
            procesos = tasklist.strip().split("\n\n")
            for proceso in procesos:
                lineas = proceso.strip().split("\n")
                data_proceso = {}
                for linea in lineas:
                    if ":" in linea:
                        key, value = linea.split(":", 1)
                        data_proceso[key.strip()] = value.strip()
                pid = data_proceso.get("PID")
                programa = data_proceso.get("Nombre de imagen")
                ram = data_proceso.get("Uso de memoria")
                cpu = "..."
                if pid and pid.isdigit():
                    procesos_activos.append((pid, programa, cpu, ram))

def estimar_uso_cpu_threaded(pid, nombre, callback):
    def worker():
        try:
            print(f"Obteniendo uso de CPU para PID {pid} ({nombre})")

            salida1 = ejecutar_powershell(f"(Get-Process -Id {pid}).TotalProcessorTime.TotalSeconds")
            if not salida1:
                raise ValueError("Salida1 vacía")
            cpu1 = float(salida1.replace(",", "."))
            print(f"CPU 1: {cpu1}")

            time.sleep(1)

            verificar = ejecutar_powershell(f"if (Get-Process -Id {pid} -ErrorAction SilentlyContinue) {{ 'ok' }} else {{ 'no' }}")
            print(f"Verificación existencia PID {pid}: {verificar}")
            if verificar.strip() != "ok":
                uso_cpu = "-"
            else:
                salida2 = ejecutar_powershell(f"(Get-Process -Id {pid}).TotalProcessorTime.TotalSeconds")
                if not salida2:
                    raise ValueError("Salida2 vacía")
                cpu2 = float(salida2.replace(",", "."))
                print(f"CPU 2: {cpu2}")
                uso_cpu = round((cpu2 - cpu1) * 100, 2)

        except Exception as e:
            print(f"Error al estimar CPU para PID {pid}: {e}")
            uso_cpu = "-"

        root.after(0, lambda: callback(pid, uso_cpu))

    threading.Thread(target=worker).start()

def agregar_proceso():
    programa = programa_seleccionado.get()
    try:
        subprocess.Popen(["cmd", "/c", "start", "", programa], shell=True)
    except Exception as e:
        print(f"No se pudo abrir {programa}: {e}")

def cerrar_proceso():
    seleccionado = tree.selection()
    for pid in seleccionado:
        valores = tree.item(pid)["values"]
        if valores:
            programa = valores[1]
            tree.delete(pid)
            procesos_activos[:] = [p for p in procesos_activos if p[0] != pid]
            try:
                subprocess.run(["taskkill", "/PID", str(pid), "/F"])
            except Exception as e:
                print(f"No se pudo cerrar {programa}: {e}")

def actualizar_recursos():
    for item in tree.get_children():
        tree.delete(item)

    obtener_procesos()

    def actualizar_cpu(pid_interno, uso_cpu):
        if tree.exists(pid_interno):
            valores_actuales = tree.item(pid_interno)["values"]
            nuevos_valores = (
                valores_actuales[0],
                valores_actuales[1],
                f"{uso_cpu}%" if isinstance(uso_cpu, float) else uso_cpu,
                valores_actuales[3],
            )
            tree.item(pid_interno, values=nuevos_valores)

    for proceso in procesos_activos:
        pid, nombre, _, ram = proceso
        tree.insert("", "end", iid=pid, values=(pid, nombre, "Calculando...", ram))
        estimar_uso_cpu_threaded(pid, nombre, actualizar_cpu)

    root.after(5000, actualizar_recursos)

# --- Interfaz de controles ---
frame_botones = tk.Frame(root)
frame_botones.pack(pady=10)

menu_programas = tk.OptionMenu(frame_botones, programa_seleccionado, *PROGRAMAS_DISPONIBLES)
menu_programas.pack(side=tk.LEFT, padx=5)

btn_agregar = tk.Button(frame_botones, text="Abrir programa", command=agregar_proceso)
btn_agregar.pack(side=tk.LEFT, padx=5)

btn_cerrar = tk.Button(frame_botones, text="Cerrar programa", command=cerrar_proceso)
btn_cerrar.pack(side=tk.LEFT, padx=5)

btn_actualizar = tk.Button(frame_botones, text="Actualizar recursos", command=actualizar_recursos)
btn_actualizar.pack(side=tk.LEFT, padx=5)

actualizar_recursos()
root.mainloop()
