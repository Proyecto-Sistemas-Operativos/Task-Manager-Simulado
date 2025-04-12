import tkinter as tk
from tkinter import ttk

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

def obtener_procesos():
    try:
        wordpad = root.tk.call('exec', 'tasklist','/FI','IMAGENAME eq wordpad.exe', '/V', '/FO', 'list')
        calc = root.tk.call('exec', 'tasklist','/FI','IMAGENAME eq CalculatorApp.exe', '/V', '/FO', 'list')
        excel = root.tk.call('exec', 'tasklist','/FI','IMAGENAME eq EXCEL.exe', '/V', '/FO', 'list')
        if (wordpad.startswith("INFOR")):
            wordpad = ""
        if (calc.startswith("INFOR")):
            calc = ""
        if (excel.startswith("INFOR")):
            excel = ""
        parse_lista_procesos([wordpad,calc,excel])
    except Exception as e:
        print(f"Error: {e}")

def parse_lista_procesos(tasklists):
    procesos_activos.clear()
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
                programa = data_proceso.get("Nombre de imagen")
                ram = data_proceso.get("Uso de memoria")
                cpu = data_proceso.get("Tiempo de CPU")
                procesos_activos.append((pid,programa,cpu,ram))
    
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
            except Exception as e:
                print(f"No se pudo cerrar {programa}: {e}")

def actualizar_recursos():
    for item in tree.get_children():
        tree.delete(item)

    obtener_procesos()

    for proceso in procesos_activos:
        tree.insert("", "end", iid=proceso[0], values=(proceso[0], proceso[1], proceso[2], proceso[3]))
    
    root.after(4000, actualizar_recursos)
    

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
