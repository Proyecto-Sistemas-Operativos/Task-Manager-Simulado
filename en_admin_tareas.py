import tkinter as tk
from tkinter import ttk

PROGRAMAS_DISPONIBLES = ["wordpad.exe", "calc.exe", "firefox.exe"]
procesos_activos = []
ultimos_tiempos_cpu = {}  # Almacena {pid: (tiempo_cpu, timestamp)}
ultima_actualizacion = None  # Almacena el tiempo de la última actualización

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

def obtener_tiempo_cpu_segundos(tiempo_cpu):
    #Convierte el tiempo de CPU (HH:MM:SS) a segundos
    if not tiempo_cpu:
        return 0
    
    partes = tiempo_cpu.split(':')
    if len(partes) == 3:  # Formato HH:MM:SS
        horas, minutos, segundos = map(int, partes)
        return horas * 3600 + minutos * 60 + segundos
    elif len(partes) == 2:  # Formato MM:SS
        minutos, segundos = map(int, partes)
        return minutos * 60 + segundos
    return 0

def calcular_porcentaje_cpu(pid, tiempo_actual, intervalo):
    #Calcula el porcentaje de uso de CPU usando el intervalo de Tkinter
    global ultimos_tiempos_cpu
    
    if pid in ultimos_tiempos_cpu:
        tiempo_anterior = ultimos_tiempos_cpu[pid]
        delta_cpu = tiempo_actual - tiempo_anterior
        porcentaje = (delta_cpu / intervalo) * 100
        return round(porcentaje, 2)
    
    # Si no hay datos anteriores
    ultimos_tiempos_cpu[pid] = tiempo_actual
    return 0.0


def obtener_procesos():
    try:
        wordpad = root.tk.call('exec', 'tasklist','/FI','IMAGENAME eq wordpad.exe', '/V', '/FO', 'list')
        calc = root.tk.call('exec', 'tasklist','/FI','IMAGENAME eq CalculatorApp.exe', '/V', '/FO', 'list')
        firefox = root.tk.call('exec', 'tasklist','/FI','IMAGENAME eq firefox.exe', '/V', '/FO', 'list')
        if (wordpad.startswith("INFO")):
            wordpad = ""
        if (calc.startswith("INFO")):
            calc = ""
        if (firefox.startswith("INFO")):
            firefox = ""
        parse_lista_procesos([wordpad,calc,firefox])
    except Exception as e:
        print(f"Error: {e}")

def parse_lista_procesos(tasklists):
    procesos_activos.clear()

    intervalo=4.0
    for tasklist in tasklists:
        if (len(tasklist) > 0):
            procesos = tasklist.strip().split("\n\n")
            for proceso in procesos:
                lineas = proceso.strip().split("\n")
                data_proceso = {}
                for linea in lineas:
                    if ":" in linea:
                        key, value = linea.split(":",1)
                        data_proceso[key.strip()] = value.strip()
                pid = data_proceso.get("PID")
                programa = data_proceso.get("Image Name")
                ram = data_proceso.get("Mem Usage", "0 K").replace(",", "").split()[0]
                cpu = data_proceso.get("CPU Time", "0:00:00")
                #procesos_activos.append((pid,programa,cpu,ram))

                # Convertir RAM a MB
                try:
                    ram_mb = int(ram) / 1024
                except:
                    ram_mb = 0

                #Calcular uso de CPU
                tiempo_cpu_seg = obtener_tiempo_cpu_segundos(cpu)
                porcentaje_cpu = calcular_porcentaje_cpu(pid, tiempo_cpu_seg, intervalo)
                
                procesos_activos.append((pid, programa, f"{porcentaje_cpu:.2f}%",  f"{ram_mb:.2f}"))
    
def agregar_proceso():
    programa = programa_seleccionado.get()

    # Lanzar el programa real
    try:
        root.tk.call('exec', 'cmd', '/c', 'start', '', programa)
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
                root.tk.call('exec', 'taskkill', '/PID', pid, '/F')
                if pid in ultimos_tiempos_cpu:
                    del ultimos_tiempos_cpu[pid]
            except Exception as e:
                print(f"No se pudo cerrar {programa}: {e}")

def actualizar_recursos():
    for item in tree.get_children():
        tree.delete(item)

    obtener_procesos()

    for proceso in procesos_activos:
        tree.insert("", "end", iid=proceso[0], values=(proceso[0], proceso[1], proceso[2], proceso[3]))
    
    root.after(2000, actualizar_recursos)
    

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
