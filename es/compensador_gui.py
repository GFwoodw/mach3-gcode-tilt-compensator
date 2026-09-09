#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Compensador CNC - Interfaz grafica simple
Compatible Python 3.4+ / Tkinter
Opcion 1: Instalar Python 3.4.4 en XP y hacer doble-click en este archivo
Filas separadas X Y Z con boton Agregar punto
"""
import os
import re
import sys
try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except ImportError:
    import Tkinter as tk
    import tkFileDialog as filedialog
    import tkMessageBox as messagebox
    import ttk

# Importar nucleo logico (mismo directorio)
try:
    from compensador import (
        calcular_plano_minimos_cuadrados,
        altura_en_punto,
        procesar_gcode,
        verificar_ajuste_plano
    )
except ImportError:
    import compensador
    calcular_plano_minimos_cuadrados = compensador.calcular_plano_minimos_cuadrados
    altura_en_punto = compensador.altura_en_punto
    procesar_gcode = compensador.procesar_gcode
    verificar_ajuste_plano = compensador.verificar_ajuste_plano

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError


def parse_valor(s):
    """Convierte string a float aceptando coma decimal"""
    s = s.strip().replace(',', '.')
    if not s:
        raise ValueError("vacio")
    return float(s)


class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Compensador CNC - Mach3")
        self.geometry("720x660")
        try:
            self.minsize(640, 560)
        except:
            pass
        self.archivo_var = tk.StringVar()
        self.filas = []  # lista de dicts {frame, x_var, y_var, z_var}
        self.crear_widgets()
        # Puntos ejemplo iniciales (los 4 que usabas)
        ejemplos = [
            ("0.000", "0.000", "0.000"),
            ("100.000", "0.000", "0.120"),
            ("100.000", "80.000", "0.250"),
            ("0.000", "80.000", "0.080"),
        ]
        for x, y, z in ejemplos:
            self.agregar_punto(x, y, z)

    def crear_widgets(self):
        titulo = tk.Label(self, text="COMPENSADOR DE SUPERFICIE INCLINADA", font=("Arial", 12, "bold"))
        titulo.pack(pady=6)
        subt = tk.Label(self, text="Corrige G-code para pieza no paralela a Z (Mach3)", font=("Arial", 8))
        subt.pack()

        # Frame archivo
        frame_archivo = tk.LabelFrame(self, text="1. Archivo G-code a compensar", padx=8, pady=8)
        frame_archivo.pack(fill="x", padx=10, pady=8)
        fila1 = tk.Frame(frame_archivo)
        fila1.pack(fill="x")
        tk.Label(fila1, text="Archivo:").pack(side="left")
        entry_archivo = tk.Entry(fila1, textvariable=self.archivo_var)
        entry_archivo.pack(side="left", fill="x", expand=True, padx=6)
        btn_examinar = tk.Button(fila1, text="Examinar...", command=self.browse_file)
        btn_examinar.pack(side="left")
        tk.Label(frame_archivo, text="Ejemplo: example.txt  |  Tambien puedes escribir la ruta a mano", font=("Arial", 7), fg="gray").pack(anchor="w", pady=(4,0))

        # Frame puntos
        frame_puntos = tk.LabelFrame(self, text="2. Puntos medidos con la CNC  (minimo 3)  -  X  Y  Z", padx=8, pady=8)
        frame_puntos.pack(fill="both", expand=False, padx=10, pady=4)

        tk.Label(frame_puntos, text="Pulsa 'Agregar punto' y rellena X Y Z. Usa punto o coma para decimales.", font=("Arial", 7), fg="gray").pack(anchor="w")

        # Cabecera columnas
        header = tk.Frame(frame_puntos)
        header.pack(fill="x", pady=(6,2))
        tk.Label(header, text="#", width=3, font=("Arial", 8, "bold")).pack(side="left")
        tk.Label(header, text="X", width=18, font=("Arial", 8, "bold")).pack(side="left", padx=2)
        tk.Label(header, text="Y", width=18, font=("Arial", 8, "bold")).pack(side="left", padx=2)
        tk.Label(header, text="Z medido", width=18, font=("Arial", 8, "bold")).pack(side="left", padx=2)
        tk.Label(header, text="", width=6).pack(side="left")

        # Contenedor con scroll para filas
        cont_scroll = tk.Frame(frame_puntos)
        cont_scroll.pack(fill="both", expand=True)
        # Canvas + scrollbar para muchas filas
        self.canvas = tk.Canvas(cont_scroll, height=160, highlightthickness=0)
        scrollbar = tk.Scrollbar(cont_scroll, orient="vertical", command=self.canvas.yview)
        self.inner_frame = tk.Frame(self.canvas)
        self.inner_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Botones agregar/quitar
        frame_botones = tk.Frame(frame_puntos)
        frame_botones.pack(fill="x", pady=6)
        btn_add = tk.Button(frame_botones, text="+ Agregar punto", bg="#2196F3", fg="white", font=("Arial", 9, "bold"), command=lambda: self.agregar_punto("", "", ""), padx=10)
        btn_add.pack(side="left")
        btn_del = tk.Button(frame_botones, text="- Quitar ultimo", command=self.quitar_ultimo, padx=10)
        btn_del.pack(side="left", padx=6)
        btn_clear = tk.Button(frame_botones, text="Limpiar todo", command=self.limpiar_todo, padx=10)
        btn_clear.pack(side="left")

        # Boton compensar
        frame_btn = tk.Frame(self)
        frame_btn.pack(fill="x", padx=10, pady=8)
        self.btn_compensar = tk.Button(frame_btn, text=">>>  COMPENSAR  <<<", bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), command=self.accion_compensar, height=2)
        self.btn_compensar.pack(fill="x")

        # Log
        frame_log = tk.LabelFrame(self, text="Resultado / Log", padx=8, pady=4)
        frame_log.pack(fill="both", expand=True, padx=10, pady=4)
        log_frame = tk.Frame(frame_log)
        log_frame.pack(fill="both", expand=True)
        scrollbar2 = tk.Scrollbar(log_frame)
        scrollbar2.pack(side="right", fill="y")
        self.text_log = tk.Text(log_frame, height=10, width=80, yscrollcommand=scrollbar2.set, font=("Courier", 8), bg="#f5f5f5")
        self.text_log.pack(side="left", fill="both", expand=True)
        scrollbar2.config(command=self.text_log.yview)
        self.text_log.config(state="disabled")
        tk.Label(self, text="Salida: mismo nombre + _COMPENSADO.txt  en la misma carpeta", font=("Arial", 7), fg="gray").pack(pady=2)

        # Bind scroll wheel
        try:
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
            self.canvas.bind_all("<Button-4>", self._on_mousewheel)
            self.canvas.bind_all("<Button-5>", self._on_mousewheel)
        except:
            pass

    def _on_mousewheel(self, event):
        try:
            if hasattr(event, 'delta') and event.delta:
                self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            elif event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")
        except:
            pass

    def agregar_punto(self, x_val="", y_val="", z_val=""):
        idx = len(self.filas) + 1
        row = tk.Frame(self.inner_frame)
        row.pack(fill="x", pady=1)
        tk.Label(row, text=str(idx), width=3, font=("Courier", 9)).pack(side="left")
        x_var = tk.StringVar(value=x_val)
        y_var = tk.StringVar(value=y_val)
        z_var = tk.StringVar(value=z_val)
        e_x = tk.Entry(row, textvariable=x_var, width=18, font=("Courier", 9), justify="center")
        e_x.pack(side="left", padx=2)
        e_y = tk.Entry(row, textvariable=y_var, width=18, font=("Courier", 9), justify="center")
        e_y.pack(side="left", padx=2)
        e_z = tk.Entry(row, textvariable=z_var, width=18, font=("Courier", 9), justify="center")
        e_z.pack(side="left", padx=2)
        btn_x = tk.Button(row, text="X", fg="red", font=("Arial", 7, "bold"), width=3, command=lambda r=row: self.eliminar_fila(r))
        btn_x.pack(side="left", padx=2)
        # Hints placeholder
        if not x_val:
            e_x.insert(0, "")
        self.filas.append({"frame": row, "x_var": x_var, "y_var": y_var, "z_var": z_var})
        self.actualizar_numeros()
        self.canvas.yview_moveto(1.0)

    def eliminar_fila(self, row):
        for i, f in enumerate(self.filas):
            if f["frame"] == row:
                f["frame"].destroy()
                self.filas.pop(i)
                break
        self.actualizar_numeros()

    def quitar_ultimo(self):
        if self.filas:
            f = self.filas.pop()
            f["frame"].destroy()
            self.actualizar_numeros()

    def limpiar_todo(self):
        for f in list(self.filas):
            f["frame"].destroy()
        self.filas = []
        self.actualizar_numeros()

    def actualizar_numeros(self):
        for i, f in enumerate(self.filas, 1):
            for child in f["frame"].winfo_children():
                if isinstance(child, tk.Label):
                    child.config(text=str(i))
                    break

    def get_puntos(self):
        puntos = []
        for i, f in enumerate(self.filas, 1):
            sx = f["x_var"].get().strip()
            sy = f["y_var"].get().strip()
            sz = f["z_var"].get().strip()
            # Permitir fila vacia intermedia -> ignorar solo si las 3 vacias
            if not sx and not sy and not sz:
                continue
            if not sx or not sy or not sz:
                raise ValueError("Fila {}: rellena X, Y y Z (vacio detectado).".format(i))
            try:
                x = parse_valor(sx)
                y = parse_valor(sy)
                z = parse_valor(sz)
            except Exception as e:
                raise ValueError("Fila {}: valor no numerico ({}). Usa punto o coma.".format(i, e))
            puntos.append([x, y, z])
        return puntos

    def log(self, msg):
        self.text_log.config(state="normal")
        self.text_log.insert("end", msg + "\n")
        self.text_log.see("end")
        self.text_log.config(state="disabled")
        self.update_idletasks()

    def clear_log(self):
        self.text_log.config(state="normal")
        self.text_log.delete("1.0", "end")
        self.text_log.config(state="disabled")

    def browse_file(self):
        initial = os.path.dirname(self.archivo_var.get()) if self.archivo_var.get() else os.getcwd()
        try:
            filename = filedialog.askopenfilename(
                title="Selecciona archivo G-code",
                initialdir=initial,
                filetypes=[("G-code TXT", "*.txt"), ("Todos", "*.*")]
            )
        except:
            filename = filedialog.askopenfilename()
        if filename:
            self.archivo_var.set(filename)

    def accion_compensar(self):
        self.clear_log()
        archivo_entrada = self.archivo_var.get().strip().strip('"').strip("'")
        if not archivo_entrada:
            messagebox.showerror("Error", "Selecciona primero el archivo G-code a compensar.")
            return
        if not os.path.isfile(archivo_entrada):
            messagebox.showerror("Error", "No se encuentra el archivo:\n{}".format(archivo_entrada))
            return
        try:
            puntos = self.get_puntos()
        except Exception as e:
            messagebox.showerror("Error en puntos", str(e))
            self.log("ERROR puntos: {}".format(e))
            return
        if len(puntos) < 3:
            messagebox.showerror("Error", "Se necesitan al menos 3 puntos. Tienes {}.".format(len(puntos)))
            return
        self.log("Puntos cargados: {}".format(len(puntos)))
        for i, (x, y, z) in enumerate(puntos, 1):
            self.log("  P{}: X={:.3f}  Y={:.3f}  Z={:.4f}".format(i, x, y, z))
        try:
            A, B, C = calcular_plano_minimos_cuadrados(puntos)
            self.log("")
            self.log("Plano calculado: Z = {:.6f}*X + {:.6f}*Y + {:.6f}".format(A, B, C))
        except Exception as e:
            messagebox.showerror("Error calculo", "Error calculando plano:\n{}".format(e))
            self.log("ERROR plano: {}".format(e))
            return
        max_error = 0
        self.log("")
        self.log("Verificacion ajuste:")
        for i, (x, y, z_medido) in enumerate(puntos, 1):
            z_calc = altura_en_punto(x, y, A, B, C)
            err = abs(z_calc - z_medido)
            max_error = max(max_error, err)
            self.log("  P{} error {:.4f} mm (medido {:.4f} -> calc {:.4f})".format(i, err, z_medido, z_calc))
        self.log("Error maximo: {:.4f} mm".format(max_error))
        if max_error > 0.2:
            self.log("ADVERTENCIA: error alto, la pieza puede no ser plana.")
            if not messagebox.askyesno("Advertencia", "Error maximo {:.3f} mm excede 0.2 mm.\n¿Continuar de todos modos?".format(max_error)):
                self.log("Cancelado por usuario.")
                return
        elif max_error > 0.1:
            self.log("Nota: error >0.1 mm, revisa mediciones si el resultado no es perfecto.")
        base, ext = os.path.splitext(archivo_entrada)
        if not ext:
            ext = ".txt"
        archivo_salida = base + "_COMPENSADO" + ext
        self.log("")
        self.log("Procesando G-code...")
        self.log("Entrada: {}".format(archivo_entrada))
        self.log("Salida:  {}".format(archivo_salida))
        resultado = procesar_gcode(archivo_entrada, archivo_salida, A, B, C, mostrar_cambios=0)
        if resultado is None:
            messagebox.showerror("Error", "Fallo procesando G-code. Revisa el log.")
            self.log("ERROR: fallo en procesar_gcode")
            return
        lineas, cambios, stats = resultado
        self.log("")
        self.log("OK - Lineas procesadas: {}".format(lineas))
        self.log("Movimientos Z compensados: {}".format(cambios))
        if stats['min_original'] != float('inf'):
            self.log("Z original:   [{:.3f} a {:.3f}]".format(stats['min_original'], stats['max_original']))
            self.log("Z compensado: [{:.3f} a {:.3f}]".format(stats['min_compensado'], stats['max_compensado']))
        self.log("")
        self.log("ARCHIVO GENERADO: {}".format(archivo_salida))
        self.log("Cargalo en Mach3 y haz prueba en aire primero.")
        messagebox.showinfo("Completado", "Archivo generado:\n{}\n\nLineas: {}  |  Z compensados: {}".format(archivo_salida, lineas, cambios))


if __name__ == "__main__":
    app = App()
    app.mainloop()
