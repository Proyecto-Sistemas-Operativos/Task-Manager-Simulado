import tkinter as tk
from tkinter import ttk

PROGRAMAS_DISPONIBLES = ["write.exe", "calc.exe", "excel"]
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

contador_pid = 1000

USO_SIMULADO = {
    "write.exe": ("12", "25"),
    "calc.exe": ("7", "15"),
    "excel": ("30", "100")
}

programa_seleccionado = tk.StringVar(value=PROGRAMAS_DISPONIBLES[0])

def agregar_proceso():
    global contador_pid
    programa = programa_seleccionado.get()
    pid = str(contador_pid)
    cpu, ram = USO_SIMULADO.get(programa, ("5", "10"))
    tree.insert("", "end", iid=pid, values=(pid, programa, cpu, ram))
    procesos_activos.append((pid, programa))
    contador_pid += 1

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

            # Cerrar el proceso real (ajustar nombre de ejecutable si es Excel)
            exe_name = "EXCEL.EXE" if programa == "excel" else programa
            try:
                root.tk.call('exec', 'taskkill', '/IM', exe_name, '/F')
            except Exception as e:
                print(f"No se pudo cerrar {programa}: {e}")

def actualizar_recursos():
    for pid, _ in procesos_activos:
        valores = tree.item(pid)["values"]
        if valores:
            programa = valores[1]
            base = int(str(root.tk.call("clock", "milliseconds"))[-2:])
            cpu = str((base * 3) % 100)
            ram = str((base * 7) % 500 + 50)
            tree.item(pid, values=(valores[0], programa, cpu, ram))
    root.after(500, actualizar_recursos)

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
