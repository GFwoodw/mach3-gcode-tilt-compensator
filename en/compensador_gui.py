#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CNC Tilt Compensator - Simple GUI
Compatible Python 3.4+ / Tkinter
For Windows XP: install Python 3.4.4 and double-click this file
Separate X Y Z rows with Add point button
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
    """Converts string to float accepting comma as decimal"""
    s = s.strip().replace(',', '.')
    if not s:
        raise ValueError("empty")
    return float(s)


class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("CNC Tilt Compensator - Mach3")
        self.geometry("720x660")
        try:
            self.minsize(640, 560)
        except:
            pass
        self.archivo_var = tk.StringVar()
        self.filas = []
        self.crear_widgets()
        ejemplos = [
            ("0.000", "0.000", "0.000"),
            ("100.000", "0.000", "0.120"),
            ("100.000", "80.000", "0.250"),
            ("0.000", "80.000", "0.080"),
        ]
        for x, y, z in ejemplos:
            self.agregar_punto(x, y, z)

    def crear_widgets(self):
        titulo = tk.Label(self, text="TILTED SURFACE COMPENSATOR", font=("Arial", 12, "bold"))
        titulo.pack(pady=6)
        subt = tk.Label(self, text="Correct G-code for workpiece not parallel to Z (Mach3)", font=("Arial", 8))
        subt.pack()
        frame_archivo = tk.LabelFrame(self, text="1. G-code file to compensate", padx=8, pady=8)
        frame_archivo.pack(fill="x", padx=10, pady=8)
        fila1 = tk.Frame(frame_archivo)
        fila1.pack(fill="x")
        tk.Label(fila1, text="File:").pack(side="left")
        entry_archivo = tk.Entry(fila1, textvariable=self.archivo_var)
        entry_archivo.pack(side="left", fill="x", expand=True, padx=6)
        btn_examinar = tk.Button(fila1, text="Browse...", command=self.browse_file)
        btn_examinar.pack(side="left")
        tk.Label(frame_archivo, text="Example: example.txt  |  You can also type path manually", font=("Arial", 7), fg="gray").pack(anchor="w", pady=(4,0))
        frame_puntos = tk.LabelFrame(self, text="2. Probe points with CNC (minimum 3)  -  X  Y  Z", padx=8, pady=8)
        frame_puntos.pack(fill="both", expand=False, padx=10, pady=4)
        tk.Label(frame_puntos, text="Click 'Add point' and fill X Y Z. Use dot or comma for decimals.", font=("Arial", 7), fg="gray").pack(anchor="w")
        header = tk.Frame(frame_puntos)
        header.pack(fill="x", pady=(6,2))
        tk.Label(header, text="#", width=3, font=("Arial", 8, "bold")).pack(side="left")
        tk.Label(header, text="X", width=18, font=("Arial", 8, "bold")).pack(side="left", padx=2)
        tk.Label(header, text="Y", width=18, font=("Arial", 8, "bold")).pack(side="left", padx=2)
        tk.Label(header, text="Z measured", width=18, font=("Arial", 8, "bold")).pack(side="left", padx=2)
        tk.Label(header, text="", width=6).pack(side="left")
        cont_scroll = tk.Frame(frame_puntos)
        cont_scroll.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(cont_scroll, height=160, highlightthickness=0)
        scrollbar = tk.Scrollbar(cont_scroll, orient="vertical", command=self.canvas.yview)
        self.inner_frame = tk.Frame(self.canvas)
        self.inner_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        frame_botones = tk.Frame(frame_puntos)
        frame_botones.pack(fill="x", pady=6)
        btn_add = tk.Button(frame_botones, text="+ Add point", bg="#2196F3", fg="white", font=("Arial", 9, "bold"), command=lambda: self.agregar_punto("", "", ""), padx=10)
        btn_add.pack(side="left")
        btn_del = tk.Button(frame_botones, text="- Remove last", command=self.quitar_ultimo, padx=10)
        btn_del.pack(side="left", padx=6)
        btn_clear = tk.Button(frame_botones, text="Clear all", command=self.limpiar_todo, padx=10)
        btn_clear.pack(side="left")
        frame_btn = tk.Frame(self)
        frame_btn.pack(fill="x", padx=10, pady=8)
        self.btn_compensar = tk.Button(frame_btn, text=">>>  COMPENSATE  <<<", bg="#4CAF50", fg="white", font=("Arial", 11, "bold"), command=self.accion_compensar, height=2)
        self.btn_compensar.pack(fill="x")
        frame_log = tk.LabelFrame(self, text="Result / Log", padx=8, pady=4)
        frame_log.pack(fill="both", expand=True, padx=10, pady=4)
        log_frame = tk.Frame(frame_log)
        log_frame.pack(fill="both", expand=True)
        scrollbar2 = tk.Scrollbar(log_frame)
        scrollbar2.pack(side="right", fill="y")
        self.text_log = tk.Text(log_frame, height=10, width=80, yscrollcommand=scrollbar2.set, font=("Courier", 8), bg="#f5f5f5")
        self.text_log.pack(side="left", fill="both", expand=True)
        scrollbar2.config(command=self.text_log.yview)
        self.text_log.config(state="disabled")
        tk.Label(self, text="Output: same name + _COMPENSATED.* in same folder", font=("Arial", 7), fg="gray").pack(pady=2)
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
            if not sx and not sy and not sz:
                continue
            if not sx or not sy or not sz:
                raise ValueError("Row {}: fill X, Y and Z (empty detected).".format(i))
            try:
                x = parse_valor(sx)
                y = parse_valor(sy)
                z = parse_valor(sz)
            except Exception as e:
                raise ValueError("Row {}: non-numeric value ({}). Use dot or comma.".format(i, e))
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
                title="Select G-code file",
                initialdir=initial,
                filetypes=[("G-code TXT", "*.txt"), ("All files", "*.*")]
            )
        except:
            filename = filedialog.askopenfilename()
        if filename:
            self.archivo_var.set(filename)

    def accion_compensar(self):
        self.clear_log()
        archivo_entrada = self.archivo_var.get().strip().strip('"').strip("'")
        if not archivo_entrada:
            messagebox.showerror("Error", "Select G-code file first.")
            return
        if not os.path.isfile(archivo_entrada):
            messagebox.showerror("Error", "File not found:\n{}".format(archivo_entrada))
            return
        try:
            puntos = self.get_puntos()
        except Exception as e:
            messagebox.showerror("Points error", str(e))
            self.log("ERROR points: {}".format(e))
            return
        if len(puntos) < 3:
            messagebox.showerror("Error", "At least 3 points required. You have {}.".format(len(puntos)))
            return
        self.log("Points loaded: {}".format(len(puntos)))
        for i, (x, y, z) in enumerate(puntos, 1):
            self.log("  P{}: X={:.3f}  Y={:.3f}  Z={:.4f}".format(i, x, y, z))
        try:
            A, B, C = calcular_plano_minimos_cuadrados(puntos)
            self.log("")
            self.log("Plane: Z = {:.6f}*X + {:.6f}*Y + {:.6f}".format(A, B, C))
        except Exception as e:
            messagebox.showerror("Calculation error", "Error calculating plane:\n{}".format(e))
            self.log("ERROR plane: {}".format(e))
            return
        max_error = 0
        self.log("")
        self.log("Fit verification:")
        for i, (x, y, z_medido) in enumerate(puntos, 1):
            z_calc = altura_en_punto(x, y, A, B, C)
            err = abs(z_calc - z_medido)
            max_error = max(max_error, err)
            self.log("  P{} error {:.4f} mm (measured {:.4f} -> calc {:.4f})".format(i, err, z_medido, z_calc))
        self.log("Max error: {:.4f} mm".format(max_error))
        if max_error > 0.2:
            self.log("WARNING: high error, workpiece may not be flat.")
            if not messagebox.askyesno("Warning", "Max error {:.3f} mm exceeds 0.2 mm.\nContinue anyway?".format(max_error)):
                self.log("Cancelled by user.")
                return
        elif max_error > 0.1:
            self.log("Note: error >0.1 mm, check measurements if result is not perfect.")
        base, ext = os.path.splitext(archivo_entrada)
        if not ext:
            ext = ".txt"
        archivo_salida = base + "_COMPENSATED" + ext
        self.log("")
        self.log("Processing G-code...")
        self.log("Input:  {}".format(archivo_entrada))
        self.log("Output: {}".format(archivo_salida))
        resultado = procesar_gcode(archivo_entrada, archivo_salida, A, B, C, mostrar_cambios=0)
        if resultado is None:
            messagebox.showerror("Error", "Failed processing G-code. Check log.")
            self.log("ERROR: procesar_gcode failed")
            return
        lineas, cambios, stats = resultado
        self.log("")
        self.log("OK - Lines processed: {}".format(lineas))
        self.log("Z moves compensated: {}".format(cambios))
        if stats['min_original'] != float('inf'):
            self.log("Z original:   [{:.3f} to {:.3f}]".format(stats['min_original'], stats['max_original']))
            self.log("Z compensated:[{:.3f} to {:.3f}]".format(stats['min_compensado'], stats['max_compensado']))
        self.log("")
        self.log("FILE GENERATED: {}".format(archivo_salida))
        self.log("Load in Mach3 and do an air run first.")
        messagebox.showinfo("Completed", "File generated:\n{}\n\nLines: {}  |  Z compensated: {}".format(archivo_salida, lineas, cambios))


if __name__ == "__main__":
    app = App()
    app.mainloop()
