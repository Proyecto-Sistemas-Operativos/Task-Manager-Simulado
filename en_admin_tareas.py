import tkinter as tk
from tkinter import ttk

PROGRAMAS_DISPONIBLES = ["wordpad.exe", "CalculatorApp.exe", "excel.exe"]
procesos_activos = []
ultimos_tiempos_cpu = {}  # Almacena {pid: (tiempo_cpu, timestamp)}
ultima_actualizacion = None  # Almacena el tiempo de la última actualización


root = tk.Tk()
root.title("Simulador de Administrador de Tareas")
root.geometry("700x450")

#ruta del icono del heading
root.iconbitmap("iconos\explorador-archivos-16.ico") 

#Frame contenedor para agregar el Treeview y los Scrollbars
contenedor=tk.Frame(root)
contenedor.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

#Creacion del Treeview
tree = ttk.Treeview(contenedor, columns=("PID", "Programa", "Estado", "CPU", "RAM"), show="headings")

#Creacion y configuracion de scrollbars
scroll_y = ttk.Scrollbar(contenedor, orient="vertical", command=tree.yview)
scroll_x = ttk.Scrollbar(contenedor, orient="horizontal", command=tree.xview)
tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

#Configuración de los headings
tree.heading("PID", text="PID")
tree.heading("Programa", text="Programa")
tree.heading("Estado", text="Estado")
tree.heading("CPU", text="Uso CPU (%)")
tree.heading("RAM", text="Uso RAM (MB)")

#Configuracion del layout usando grid
tree.grid(row=0, column=0, sticky="nsew")
scroll_y.grid(row=0, column=1, sticky="ns")
scroll_x.grid(row=1, column=0, sticky="ew")

contenedor.grid_rowconfigure(0, weight=1)  # Permitir que el Treeview crezca
contenedor.grid_columnconfigure(0, weight=1)  # Permitir que el Treeview crezca

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
        excel = root.tk.call('exec', 'tasklist','/FI','IMAGENAME eq excel.exe', '/V', '/FO', 'list')
        if (wordpad.startswith("INFO")):
            wordpad = ""
        if (calc.startswith("INFO")):
            calc = ""
        if (excel.startswith("INFO")):
            excel = ""
        parse_lista_procesos([wordpad,calc,excel])
    except Exception as e:
        print(f"Error: {e}")

def parse_lista_procesos(tasklists):
    procesos_activos.clear()
    contador_programas = {}

    traduccion_estados = {
        "Running": "En ejecución",
        "Suspend": "Suspendido",
        "Waiting": "En espera",
        "Unknown": "En ejecución"  
    }
    
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

                if not programa:
                    continue

                estado_original=data_proceso.get("Status", "Desconocido")

                estado=traduccion_estados.get(estado_original, "En Ejecucion")

                if estado_original in traduccion_estados.values():
                    estado=estado_original

                # Determinar estado
                if programa in contador_programas:
                    estado = "Repetido"
                else:
                    contador_programas[programa] = pid
                   
                    
                
                ram = data_proceso.get("Mem Usage", "0 K").replace(",", "").split()[0]
                cpu = data_proceso.get("CPU Time", "0:00:00")
                ram_mb = int(ram) / 1024 if ram.isdigit() else 0
                #procesos_activos.append((pid,programa,cpu,ram))


                #Calcular uso de CPU
                tiempo_cpu_seg = obtener_tiempo_cpu_segundos(cpu)
                porcentaje_cpu = calcular_porcentaje_cpu(pid, tiempo_cpu_seg, 2.0)
                
                procesos_activos.append((
                    pid, 
                    programa, 
                    estado,
                    f"{porcentaje_cpu:.2f}%",  
                    f"{ram_mb:.2f}"))
    
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
        if valores and valores[0]:
            try:
                #Convertir PID a entero para corregir caracteres no deseados
                pid_int = int(valores[0])
                programa = valores[1]

                #Eliminar proceso en Windows
                root.tk.call('exec', 'taskkill', '/PID', str(pid_int), '/F')

                #Actualizar interfaz
                tree.delete(pid)
                procesos_activos[:] = [p for p in procesos_activos if p[0] != valores[0]]
                
                if valores[0] in ultimos_tiempos_cpu:
                    del ultimos_tiempos_cpu[pid]

            except ValueError:
                print(f"Error: PID '{valores[0]}' no es numérico")
                
            except Exception as e:
                print(f"No se pudo cerrar {programa}: {e}")

def actualizar_recursos():
    actuales = set(tree.get_children())
    obtener_procesos()

    for proceso in procesos_activos:
        if (proceso[0] in actuales):
            tree.item(proceso[0], values=(proceso[0], proceso[1], proceso[2],
        proceso[3], proceso[4]))
            actuales.discard(proceso[0])
        else:
            tree.insert("", "end", iid=proceso[0], values=(proceso[0], proceso[1], proceso[2],
        proceso[3], proceso[4]))

    for item in actuales:
        tree.delete(item)
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
