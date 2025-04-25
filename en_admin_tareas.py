import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

PROGRAMAS_DISPONIBLES = ["wordpad.exe", "calc.exe", "excel.exe"]
procesos_activos = []   # Lista de procesos mostrados (PID, Programa, Estado, Uso CPU (%), Uso RAM (MB)).
ultimos_tiempos_cpu = {}  # Almacena {pid: (tiempo_cpu, timestamp)}
intervalo_check = True  # Bandera para controlar el intervalo de actualización autoprogramado.
intervalo_id = None  # Almacena el ID del intervalo de actualización
intervalo_timeout = 4000 # Tiempo de espera para el intervalo de actualización (en milisegundos)


# Configuración de la ventana principal
root = tk.Tk()
root.title("Simulador de Administrador de Tareas")  # titulo.
root.geometry("1280x720")   # tamaño de la ventana.

# ruta del icono del heading
root.iconbitmap("iconos\explorador-archivos-16.ico") 

# Frame contenedor para agregar el Treeview y los Scrollbars
contenedor=tk.Frame(root)
contenedor.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Creacion del Treeview (la tabla para mostrar los procesos).
tree = ttk.Treeview(contenedor, columns=("PID", "Programa", "Estado", "CPU", "RAM"), show="headings")

# Creacion y configuracion de scrollbars (barras de desplazamiento).
scroll_y = ttk.Scrollbar(contenedor, orient="vertical", command=tree.yview)     # Barra de desplazamiento vertical.
scroll_x = ttk.Scrollbar(contenedor, orient="horizontal", command=tree.xview)   # Barra de desplazamiento horizontal.
tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)    # Configura el Treeview para que utilice las barras de desplazamiento.

# Configuración de los headings (encabezados de las columnas).
tree.heading("PID", text="PID")
tree.heading("Programa", text="Programa")
tree.heading("Estado", text="Estado")
tree.heading("CPU", text="Uso CPU (%)")
tree.heading("RAM", text="Uso RAM (MB)")

# Configuracion del layout (organización) usando grid.
tree.grid(row=0, column=0, sticky="nsew")
scroll_y.grid(row=0, column=1, sticky="ns")
scroll_x.grid(row=1, column=0, sticky="ew")

contenedor.grid_rowconfigure(0, weight=1)  # Permitir que el Treeview crezca
contenedor.grid_columnconfigure(0, weight=1)  # Permitir que el Treeview crezca

programa_seleccionado = tk.StringVar(value=PROGRAMAS_DISPONIBLES[0])

def obtener_tiempo_cpu_segundos(tiempo_cpu):
    # Convierte el tiempo de CPU (HH:MM:SS) a segundos
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
    #print(f"PID: {pid}, Tiempo actual: {tiempo_actual}, Intervalo: {intervalo}")
    # Calcula el porcentaje de uso de CPU basado en el cambio en el tiempo de CPU durante el intervalo.
    global ultimos_tiempos_cpu
    
    if pid in ultimos_tiempos_cpu:
        tiempo_anterior = ultimos_tiempos_cpu[pid]
        delta_cpu = tiempo_actual - tiempo_anterior
        porcentaje = (delta_cpu / intervalo) * 100
        ultimos_tiempos_cpu[pid] = tiempo_actual
        return round(porcentaje, 2)     # El porcentaje de uso de CPU, redondeado a dos decimales.

    # Si no hay datos anteriores
    ultimos_tiempos_cpu[pid] = tiempo_actual

    return 0.0

def obtener_procesos():
    # Ejecuta el comando 'tasklist' de Windows para obtener información detallada (/V)
    # sobre los procesos de Wordpad, Calculadora y Excel, filtrando por el nombre de la imagen (/FI).
    try:
        wordpad = root.tk.call('exec', 'tasklist','/FI','IMAGENAME eq wordpad.exe', '/V', '/FO', 'list')
        calc = root.tk.call('exec', 'tasklist','/FI','IMAGENAME eq CalculatorApp.exe', '/V', '/FO', 'list')
        excel = root.tk.call('exec', 'tasklist','/FI','IMAGENAME eq excel.exe', '/V', '/FO', 'list')

        if (wordpad.startswith("INFO")):
            wordpad = ""                    # No se encontraron procesos con ese nombre y se establece la variable correspondiente a una cadena vacía.
        if (calc.startswith("INFO")):
            calc = ""                       # No se encontraron procesos con ese nombre y se establece la variable correspondiente a una cadena vacía.
        if (excel.startswith("INFO")):
            excel = ""                      # No se encontraron procesos con ese nombre y se establece la variable correspondiente a una cadena vacía.

        parse_lista_procesos([wordpad,calc,excel])      # Llamada a la función para procesar la información obtenida.
    except Exception as e:
        print(f"Error: {e}")

def ordenar_lista_procesos_activos(list):
    return

def parse_lista_procesos(tasklists):
    global procesos_activos
    # Parsea la salida del comando 'tasklist' para extraer información relevante de los procesos y actualizar la lista global 'procesos_activos'.
    procesos_activos.clear()    # Limpia la lista de procesos activos.
    contador_programas = {}     # Lleva un registro de los nombres de los programas ya encontrados
    lista = []
    traduccion_estados = {
        "Running": "En Ejecución",
        "Suspend": "Suspendido",
        "Waiting": "En Espera",
        "Unknown": "En Ejecución"  
    }
    
    for tasklist in tasklists:
        # Itera a través de cada cadena de salida del comando 'tasklist'.
        if (len(tasklist) > 0):
            procesos = tasklist.strip().split("\n\n")   # Elimina espacios en blanco y divide en una lista de cadenas.
            for proceso in procesos:
                lineas = proceso.strip().split("\n")
                data_proceso = {}       # Crea un diccionario vacío para almacenar la información clave-valor de cada proceso.
                for linea in lineas:
                    if ":" in linea:    # Verifica si la línea contiene un signo de dos puntos.
                        key, value = linea.split(":",1)     # Divide la línea en dos partes. El argumento '1' asegura que solo se realice una división.
                        data_proceso[key.strip()] = value.strip()

                pid = data_proceso.get("PID")   # Obtiene el valor asociado a la clave "PID" del diccionario 'data_proceso'.
                programa = data_proceso.get("Image Name")     # Obtiene el valor asociado a la clave "Nombre de imagen" del diccionario 'data_proceso'

                if not programa:
                    continue

                estado_original=data_proceso.get("Status", "Desconocido")   # Obtiene el valor asociado a la clave "Estado" del diccionario 'data_proceso'.

                estado=traduccion_estados.get(estado_original, "En Ejecucion")

                if estado_original in traduccion_estados.values():
                    # Verifica si el 'estado_original' ya está en los valores de nuestro diccionario de traducción (en español).
                    estado=estado_original

                # Determinar estado
                if programa in contador_programas:
                    estado = "Repetido"
                else:
                    contador_programas[programa] = pid      # Se añade el nombre del programa al 'contador_programas' con su PID asociado.

                ram = data_proceso.get("Mem Usage", "0 K").replace(".", "").split()[0]     # Obtiene el valor asociado a la clave "Uso de memoria"
                cpu = data_proceso.get("CPU Time", "0:00:00")      # Obtiene el valor asociado a la clave "Tiempo de CPU"
                ram_mb = int(ram) / 1024 if ram.isdigit() else 0      # Convierte el uso de RAM de kilobytes (K) a megabytes (MB).

                # Calcular uso de CPU
                tiempo_cpu_seg = obtener_tiempo_cpu_segundos(cpu)
                porcentaje_cpu = calcular_porcentaje_cpu(pid, tiempo_cpu_seg, 2.0)

                # Agregar a lista temporal de procesos activos
                lista.append((pid, programa, estado, f"{porcentaje_cpu:.2f}%", f"{ram_mb:.2f}", porcentaje_cpu, ram_mb))     # Añade la información del proceso a la lista 'lista'.
    
    # Definir nueva lista de procesos activos.
    procesos_activos = sorted(lista, key=lambda x: (x[5] * 0.7 + x[6] * 0.3), reverse=True)
    
def agregar_proceso():
    # Obtiene el programa seleccionado del menú desplegable.
    programa = programa_seleccionado.get()

    # Lanzar el programa real
    try:
        root.tk.call('exec', 'cmd', '/c', 'start', '', programa)

        reiniciar_bucle_actualizador(intervalo_timeout)
    except Exception as e:
        print(f"No se pudo abrir {programa}: {e}")

def cerrar_proceso():
    seleccionado = tree.selection()

    if len(seleccionado) == 0:
        mostrar_alerta("error", "No se ha seleccionado ningún proceso.")
        return

    for pid in seleccionado:
        valores = tree.item(pid)["values"]

        if valores and valores[0]:
            try:
                # Convertir PID a entero para corregir caracteres no deseados
                pid_int = int(valores[0])
                programa = valores[1]

                # Eliminar proceso en Windows
                root.tk.call('exec', 'taskkill', '/PID', str(pid_int), '/F')

                # Actualizar interfaz
                tree.delete(pid)
                procesos_activos[:] = [p for p in procesos_activos if p[0] != valores[0]]
                
                if valores[0] in ultimos_tiempos_cpu:
                    del ultimos_tiempos_cpu[pid]

                # Reiniciar el bucle de actualización
                reiniciar_bucle_actualizador(intervalo_timeout)

            except ValueError:
                print(f"Error: PID '{valores[0]}' no es numérico")      # Imprime un mensaje de error en la consola indicando que el PID no es numérico.
                
            except Exception as e:
                print(f"No se pudo cerrar {programa}: {e}")     # Imprime un mensaje de error en la consola indicando qué programa no se pudo cerrar y la descripción del error.              

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

def detener_bucle_actualizador():
    global intervalo_id, intervalo_check

    intervalo_check = False

    if intervalo_id is None:
        return
    
    # Cancela el bucle de actualización de recursos.
    root.after_cancel(intervalo_id)
    intervalo_id = None

def reiniciar_bucle_actualizador(tiempo = 2000):
    global intervalo_id

    if intervalo_id is not None:
        root.after_cancel(intervalo_id)

    actualizar_recursos()
    intervalo_id = root.after(tiempo, lambda: reiniciar_bucle_actualizador(tiempo) if intervalo_check else None)

def mostrar_alerta(tipo, mensaje):
    match tipo:
        case "info":
            messagebox.showinfo("Información", mensaje)
        case "error":
            messagebox.showerror("Error", mensaje)
        case _:
            print("Tipo de alerta no válido.")

# --- Interfaz de controles ---
frame_botones = tk.Frame(root)      # Crea un Frame para contener los botones y el menú.
frame_botones.pack(pady=10)

menu_programas = tk.OptionMenu(frame_botones, programa_seleccionado, *PROGRAMAS_DISPONIBLES)    # Crea el menú desplegable de programas.
menu_programas.pack(side=tk.LEFT, padx=5)

btn_agregar = tk.Button(frame_botones, text="Abrir programa", command=agregar_proceso)      # Crea el botón para abrir el programa.
btn_agregar.pack(side=tk.LEFT, padx=5)

btn_cerrar = tk.Button(frame_botones, text="Cerrar programa", command=cerrar_proceso)   # Crea el botón para cerrar el programa.
btn_cerrar.pack(side=tk.LEFT, padx=5)

#btn_actualizar = tk.Button(frame_botones, text="Actualizar recursos", command=actualizar_recursos)      # Crea el botón para actualizar manualmente.
#btn_actualizar.pack(side=tk.LEFT, padx=5)

reiniciar_bucle_actualizador(intervalo_timeout)

try:
    root.mainloop()
except KeyboardInterrupt:
    print("Programa cerrado por el usuario.")
finally:
    detener_bucle_actualizador()

