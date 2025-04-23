import tkinter as tk
from tkinter import ttk

PROGRAMAS_DISPONIBLES = ["wordpad.exe", "calc.exe", "EXCEL.exe"]
procesos_activos = []   #Lista de procesos mostrados (PID, Programa, Estado, Uso CPU (%), Uso RAM (MB)).
ultimos_tiempos_cpu = {}  # Almacena {pid: (tiempo_cpu, timestamp)}
ultima_actualizacion = None  # Almacena el tiempo de la última actualización


# Configuración de la ventana principal
root = tk.Tk()
root.title("Simulador de Administrador de Tareas")  #titulo.
root.geometry("1280x720")   #tamaño de la ventana.

#ruta del icono del heading
root.iconbitmap("iconos\explorador-archivos-16.ico") 

#Frame contenedor para agregar el Treeview y los Scrollbars
contenedor=tk.Frame(root)
contenedor.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

#Creacion del Treeview (la tabla para mostrar los procesos).
tree = ttk.Treeview(contenedor, columns=("PID", "Programa", "Estado", "CPU", "RAM"), show="headings")

#Creacion y configuracion de scrollbars (barras de desplazamiento).
scroll_y = ttk.Scrollbar(contenedor, orient="vertical", command=tree.yview)     #Barra de desplazamiento vertical.
scroll_x = ttk.Scrollbar(contenedor, orient="horizontal", command=tree.xview)   #Barra de desplazamiento horizontal.
tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)    #Configura el Treeview para que utilice las barras de desplazamiento.

#Configuración de los headings (encabezados de las columnas).
tree.heading("PID", text="PID")
tree.heading("Programa", text="Programa")
tree.heading("Estado", text="Estado")
tree.heading("CPU", text="Uso CPU (%)")
tree.heading("RAM", text="Uso RAM (MB)")

#Configuracion del layout (organización) usando grid.
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
    # Calcula el porcentaje de uso de CPU basado en el cambio en el tiempo de CPU durante el intervalo.
    global ultimos_tiempos_cpu
    
    if pid in ultimos_tiempos_cpu:
        tiempo_anterior = ultimos_tiempos_cpu[pid]
        delta_cpu = tiempo_actual - tiempo_anterior
        porcentaje = (delta_cpu / intervalo) * 100
        return round(porcentaje, 2)     #El porcentaje de uso de CPU, redondeado a dos decimales.
    
    # Si no hay datos anteriores
    ultimos_tiempos_cpu[pid] = tiempo_actual
    return 0.0

def obtener_procesos():
    # Ejecuta el comando 'tasklist' de Windows para obtener información detallada (/V)
    #sobre los procesos de Wordpad, Calculadora y Excel, filtrando por el nombre de la imagen (/FI).
    try:
        wordpad = root.tk.call('exec', 'tasklist','/FI','IMAGENAME eq wordpad.exe', '/V', '/FO', 'list')
        calc = root.tk.call('exec', 'tasklist','/FI','IMAGENAME eq CalculatorApp.exe', '/V', '/FO', 'list')
        excel = root.tk.call('exec', 'tasklist','/FI','IMAGENAME eq excel.exe', '/V', '/FO', 'list')
        if (wordpad.startswith("INFO")):
            wordpad = ""                    #No se encontraron procesos con ese nombre y se establece la variable correspondiente a una cadena vacía.
        if (calc.startswith("INFO")):
            calc = ""                       #No se encontraron procesos con ese nombre y se establece la variable correspondiente a una cadena vacía.
        if (excel.startswith("INFO")):
            excel = ""                      #No se encontraron procesos con ese nombre y se establece la variable correspondiente a una cadena vacía.
        parse_lista_procesos([wordpad,calc,excel])      #Llamada a la función para procesar la información obtenida.
    except Exception as e:
        print(f"Error: {e}")

def parse_lista_procesos(tasklists):
    #Parsea la salida del comando 'tasklist' para extraer información relevante de los procesos y actualizar la lista global 'procesos_activos'.
    procesos_activos.clear()    #Limpia la lista de procesos activos.
    contador_programas = {}     #Lleva un registro de los nombres de los programas ya encontrados

    traduccion_estados = {
        "Running": "En ejecución",
        "Suspend": "Suspendido",
        "Waiting": "En espera",
        "Unknown": "En ejecución"  
    }
    
    for tasklist in tasklists:
        #Itera a través de cada cadena de salida del comando 'tasklist'.
        if (len(tasklist) > 0):
            procesos = tasklist.strip().split("\n\n")   #Elimina espacios en blanco y divide en una lista de cadenas.
            for proceso in procesos:
                lineas = proceso.strip().split("\n")
                data_proceso = {}       #Crea un diccionario vacío para almacenar la información clave-valor de cada proceso.
                for linea in lineas:
                    if ":" in linea:    #Verifica si la línea contiene un signo de dos puntos.
                        key, value = linea.split(":",1)     #Divide la línea en dos partes. El argumento '1' asegura que solo se realice una división.
                        data_proceso[key.strip()] = value.strip()

                pid = data_proceso.get("PID")   #Obtiene el valor asociado a la clave "PID" del diccionario 'data_proceso'.
                programa = data_proceso.get("Nombre de imagen")     #Obtiene el valor asociado a la clave "Nombre de imagen" del diccionario 'data_proceso'

                if not programa:
                    continue

                estado_original=data_proceso.get("Estado", "Desconocido")   #Obtiene el valor asociado a la clave "Estado" del diccionario 'data_proceso'.

                estado=traduccion_estados.get(estado_original, "En Ejecucion")

                if estado_original in traduccion_estados.values():
                    #Verifica si el 'estado_original' ya está en los valores de nuestro diccionario de traducción (en español).
                    estado=estado_original

                # Determinar estado
                if programa in contador_programas:
                    estado = "Repetido"
                else:
                    contador_programas[programa] = pid      #Se añade el nombre del programa al 'contador_programas' con su PID asociado.
                   
                    
                
                ram = data_proceso.get("Uso de memoria", "0 K").replace(".", "").split()[0]     # Obtiene el valor asociado a la clave "Uso de memoria"
                cpu = data_proceso.get("Tiempo de CPU", "0:00:00")      #Obtiene el valor asociado a la clave "Tiempo de CPU"
                ram_mb = int(ram) / 1024 if ram.isdigit() else 0      #Convierte el uso de RAM de kilobytes (K) a megabytes (MB).
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
    #Obtiene el programa seleccionado del menú desplegable.
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
                print(f"Error: PID '{valores[0]}' no es numérico")      #Imprime un mensaje de error en la consola indicando que el PID no es numérico.
                
            except Exception as e:
                print(f"No se pudo cerrar {programa}: {e}")     #Imprime un mensaje de error en la consola indicando qué programa no se pudo cerrar y la descripción del error.              

def actualizar_recursos():
    #Actualiza la lista de procesos mostrada en el Treeview.
    actuales = set(tree.get_children())
    obtener_procesos()

    for proceso in procesos_activos:
        #Itera a través de cada tupla de información de proceso en la lista 'procesos_activos'.
        if (proceso[0] in actuales):
            tree.item(proceso[0], values=(proceso[0], proceso[1], proceso[2],
        proceso[3], proceso[4]))
            actuales.discard(proceso[0])        #Elimina el PID del conjunto 'actuales', ya que se ha encontrado y/o actualizado en el Treeview.
        else:
            tree.insert("", "end", iid=proceso[0], values=(proceso[0], proceso[1], proceso[2],
        proceso[3], proceso[4]))        #Se inserta una nueva fila en el Treeview al final ("end") con la información del nuevo proceso.

    for item in actuales:
        tree.delete(item)       #Elimina la fila correspondiente al proceso inactivo del Treeview.
    root.after(2000, actualizar_recursos)
    

# --- Interfaz de controles ---
frame_botones = tk.Frame(root)      # Crea un Frame para contener los botones y el menú.
frame_botones.pack(pady=10)

menu_programas = tk.OptionMenu(frame_botones, programa_seleccionado, *PROGRAMAS_DISPONIBLES)    # Crea el menú desplegable de programas.
menu_programas.pack(side=tk.LEFT, padx=5)

btn_agregar = tk.Button(frame_botones, text="Abrir programa", command=agregar_proceso)      # Crea el botón para abrir el programa.
btn_agregar.pack(side=tk.LEFT, padx=5)

btn_cerrar = tk.Button(frame_botones, text="Cerrar programa", command=cerrar_proceso)   # Crea el botón para cerrar el programa.
btn_cerrar.pack(side=tk.LEFT, padx=5)

btn_actualizar = tk.Button(frame_botones, text="Actualizar recursos", command=actualizar_recursos)      # Crea el botón para actualizar manualmente.
btn_actualizar.pack(side=tk.LEFT, padx=5)

actualizar_recursos()
root.mainloop()
