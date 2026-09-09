import sys
import re
import math

# =================================================================
# INTERPOLATION FUNCTIONS
# =================================================================

def calcular_plano_minimos_cuadrados(puntos):
    """
    Calculates the plane Z = A*X + B*Y + C that best fits the points
    using least squares. Works with 3 or more points.
    Compatible Python 3.4+ (no f-strings)
    """
    n = len(puntos)
    if n < 3:
        raise ValueError("At least 3 points required. You have {}.".format(n))
    
    sum_x = sum_y = sum_z = 0
    sum_x2 = sum_y2 = sum_xy = sum_xz = sum_yz = 0
    
    for x, y, z in puntos:
        sum_x += x
        sum_y += y
        sum_z += z
        sum_x2 += x * x
        sum_y2 += y * y
        sum_xy += x * y
        sum_xz += x * z
        sum_yz += y * z
    
    det = (sum_x2 * sum_y2 * n + 
           sum_xy * sum_y * sum_x + 
           sum_x * sum_xy * sum_y - 
           sum_x * sum_y2 * sum_x - 
           sum_xy * sum_xy * n - 
           sum_x2 * sum_y * sum_y)
    
    if abs(det) < 1e-10:
        p0, p1, p2 = puntos[0], puntos[1], puntos[-1]
        v1 = [p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]]
        v2 = [p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]]
        nx = v1[1] * v2[2] - v1[2] * v2[1]
        ny = v1[2] * v2[0] - v1[0] * v2[2]
        nz = v1[0] * v2[1] - v1[1] * v2[0]
        d = nx * p0[0] + ny * p0[1] + nz * p0[2]
        A = nx / nz if nz != 0 else 0
        B = ny / nz if nz != 0 else 0
        C = -d / nz if nz != 0 else 0
        return A, B, C
    
    det_A = (sum_xz * sum_y2 * n + 
             sum_xy * sum_y * sum_z + 
             sum_x * sum_yz * sum_y - 
             sum_x * sum_y2 * sum_z - 
             sum_xy * sum_yz * n - 
             sum_xz * sum_y * sum_y)
    
    det_B = (sum_x2 * sum_yz * n + 
             sum_xz * sum_y * sum_x + 
             sum_x * sum_xy * sum_z - 
             sum_x * sum_yz * sum_x - 
             sum_xz * sum_xy * n - 
             sum_x2 * sum_y * sum_z)
    
    det_C = (sum_x2 * sum_y2 * sum_z + 
             sum_xy * sum_yz * sum_x + 
             sum_xz * sum_xy * sum_y - 
             sum_xz * sum_y2 * sum_x - 
             sum_xy * sum_xy * sum_z - 
             sum_x2 * sum_yz * sum_y)
    
    A = det_A / det
    B = det_B / det
    C = det_C / det
    return A, B, C


def altura_en_punto(x, y, A, B, C):
    """Returns surface height Z at (x,y) for plane Z = A*x + B*y + C"""
    return A * x + B * y + C


# =================================================================
# G-CODE PROCESSING
# =================================================================

def extraer_coordenadas(linea):
    """
    Extracts X, Y, Z from a G-code line.
    Returns (x, y, z) where each may be None if not present.
    Handles: N100G00X-36.853Y-22.740Z5.000
    """
    x = y = z = None
    patrones = [
        (r'X([+-]?\d+\.?\d*)', 'x'),
        (r'Y([+-]?\d+\.?\d*)', 'y'),
        (r'Z([+-]?\d+\.?\d*)', 'z')
    ]
    for patron, var in patrones:
        match = re.search(patron, linea)
        if match:
            try:
                valor = float(match.group(1))
                if var == 'x':
                    x = valor
                elif var == 'y':
                    y = valor
                elif var == 'z':
                    z = valor
            except ValueError:
                pass
    return x, y, z


def reemplazar_coordenada_z(linea, nuevo_z, decimales=3):
    """Replaces Z value in a G-code line. Compatible Python 3.4+"""
    match = re.search(r'Z[+-]?\d+\.?\d*', linea)
    if match:
        viejo_z_str = match.group(0)
        fmt = "Z{0:." + str(decimales) + "f}"
        nuevo_z_str = fmt.format(nuevo_z)
        nuevo_z_str = nuevo_z_str.rstrip('0').rstrip('.')
        if nuevo_z_str == "Z" or nuevo_z_str == "Z-":
            nuevo_z_str = fmt.format(nuevo_z)
        return linea.replace(viejo_z_str, nuevo_z_str, 1)
    return linea


def procesar_gcode(archivo_entrada, archivo_salida, A, B, C, mostrar_cambios=5):
    """Processes G-code line by line applying compensation."""
    x_actual = 0.0
    y_actual = 0.0
    z_actual = 0.0
    contador_lineas = 0
    contador_cambios = 0
    cambios_mostrados = 0
    estadisticas_z = {
        'min_original': float('inf'),
        'max_original': float('-inf'),
        'min_compensado': float('inf'),
        'max_compensado': float('-inf')
    }
    print("\nProcessing: {}".format(archivo_entrada))
    print("Plane coefficients: A={:.6f}, B={:.6f}, C={:.6f}".format(A, B, C))
    try:
        with open(archivo_entrada, 'r', encoding='utf-8', errors='ignore') as f_in, \
             open(archivo_salida, 'w', encoding='utf-8') as f_out:
            for linea_original in f_in:
                contador_lineas += 1
                linea = linea_original.rstrip('\n')
                linea_modificada = linea
                x_linea, y_linea, z_linea = extraer_coordenadas(linea)
                if x_linea is not None:
                    x_actual = x_linea
                if y_linea is not None:
                    y_actual = y_linea
                if z_linea is not None:
                    z_actual = z_linea
                if z_linea is not None and x_actual is not None and y_actual is not None:
                    altura_superficie = altura_en_punto(x_actual, y_actual, A, B, C)
                    z_nuevo = z_linea + altura_superficie
                    estadisticas_z['min_original'] = min(estadisticas_z['min_original'], z_linea)
                    estadisticas_z['max_original'] = max(estadisticas_z['max_original'], z_linea)
                    estadisticas_z['min_compensado'] = min(estadisticas_z['min_compensado'], z_nuevo)
                    estadisticas_z['max_compensado'] = max(estadisticas_z['max_compensado'], z_nuevo)
                    linea_modificada = reemplazar_coordenada_z(linea, z_nuevo, decimales=4)
                    contador_cambios += 1
                    if cambios_mostrados < mostrar_cambios and linea_modificada != linea:
                        cambios_mostrados += 1
                        print("\n--- Change {} ---".format(cambios_mostrados))
                        print("Line: {}".format(contador_lineas))
                        print("Position: X={:.3f}, Y={:.3f}".format(x_actual, y_actual))
                        print("Surface height: {:.4f} mm".format(altura_superficie))
                        print("Z original: {:.4f}".format(z_linea))
                        print("Z compensated: {:.4f}".format(z_nuevo))
                        print("Original: {}...".format(linea[:80]))
                        print("Modified: {}...".format(linea_modificada[:80]))
                f_out.write(linea_modificada + '\n')
                if contador_lineas % 10000 == 0:
                    print("  Processed {} lines...".format(contador_lineas))
    except FileNotFoundError:
        print("ERROR: File not found '{}'".format(archivo_entrada))
        return None
    except Exception as e:
        print("ERROR processing file: {}".format(e))
        return None
    return contador_lineas, contador_cambios, estadisticas_z


# =================================================================
# VERIFICATION
# =================================================================

def verificar_ajuste_plano(puntos, A, B, C, tolerancia_max=0.1):
    """Checks plane fit against measured points."""
    print("\n" + "="*70)
    print("PLANE FIT VERIFICATION")
    print("="*70)
    max_error = 0
    puntos_con_error = []
    for i, (x, y, z_medido) in enumerate(puntos, 1):
        z_calculado = altura_en_punto(x, y, A, B, C)
        error = abs(z_calculado - z_medido)
        max_error = max(max_error, error)
        if error > 0.01:
            puntos_con_error.append((i, x, y, z_medido, z_calculado, error))
        print("Point {}: X={:9.3f}, Y={:9.3f}".format(i, x, y))
        print("  Z measured:    {:7.4f} mm".format(z_medido))
        print("  Z calculated:  {:7.4f} mm".format(z_calculado))
        print("  Error:         {:7.4f} mm".format(error))
        if error <= tolerancia_max:
            print("  OK")
        else:
            print("  !! High")
        print("")
    print("Max error: {:.4f} mm".format(max_error))
    if max_error > tolerancia_max:
        print("\nWARNING: Max error ({:.3f} mm) exceeds tolerance.".format(max_error))
        print("   Consider:")
        print("   1. Check measurements")
        print("   2. Add more probe points")
        print("   3. Workpiece may not be perfectly flat")
    return max_error


def mostrar_resumen(contador_lineas, contador_cambios, estadisticas_z, archivo_salida):
    print("\n" + "="*70)
    print("PROCESSING SUMMARY")
    print("="*70)
    print("Total lines: {}".format(contador_lineas))
    print("Z moves compensated: {}".format(contador_cambios))
    print("Output file: {}".format(archivo_salida))
    if estadisticas_z['min_original'] != float('inf'):
        print("\nZ statistics:")
        print("  Original:   [{:.3f} to {:.3f}]".format(estadisticas_z['min_original'], estadisticas_z['max_original']))
        print("  Compensated:[{:.3f} to {:.3f}]".format(estadisticas_z['min_compensado'], estadisticas_z['max_compensado']))


# =================================================================
# CLI
# =================================================================

def main():
    print("="*70)
    print("CNC TILTED SURFACE COMPENSATOR")
    print("="*70)
    PUNTOS_MEDIDOS = [
        # Generic example:
        [0.000, 0.000, 0.000],
        [100.000, 0.000, 0.120],
        [100.000, 80.000, 0.250],
        [0.000, 80.000, 0.080],
    ]
    ARCHIVO_ENTRADA = "example.gcode"
    ARCHIVO_SALIDA = "example_COMPENSATED.gcode"
    if len(PUNTOS_MEDIDOS) < 3:
        print("ERROR: At least 3 points required. You have {}.".format(len(PUNTOS_MEDIDOS)))
        return
    print("\nProbe points: {}".format(len(PUNTOS_MEDIDOS)))
    for i, (x, y, z) in enumerate(PUNTOS_MEDIDOS, 1):
        print("  P{}: X={:9.3f}, Y={:9.3f}, Z={:7.4f}".format(i, x, y, z))
    print("\nCalculating best-fit plane...")
    try:
        A, B, C = calcular_plano_minimos_cuadrados(PUNTOS_MEDIDOS)
        print("Plane: Z = {:.6f}*X + {:.6f}*Y + {:.6f}".format(A, B, C))
    except Exception as e:
        print("Error calculating plane: {}".format(e))
        return
    max_error = verificar_ajuste_plano(PUNTOS_MEDIDOS, A, B, C, tolerancia_max=0.1)
    if max_error > 0.2:
        try:
            respuesta = input("\nMax error is {:.2f} mm. Continue? (y/n): ".format(max_error))
        except:
            respuesta = "y"
        if respuesta.lower() != 'y':
            print("Cancelled.")
            return
    print("\n" + "="*70)
    print("PROCESSING G-CODE")
    print("="*70)
    resultado = procesar_gcode(ARCHIVO_ENTRADA, ARCHIVO_SALIDA, A, B, C, mostrar_cambios=5)
    if resultado is None:
        print("Processing failed.")
        return
    contador_lineas, contador_cambios, estadisticas_z = resultado
    mostrar_resumen(contador_lineas, contador_cambios, estadisticas_z, ARCHIVO_SALIDA)
    print("\n" + "="*70)
    print("DONE - Load compensated file in Mach3 and do an air run first.")
    print("="*70)
    altura_p2 = altura_en_punto(100.000, 0.000, A, B, C)
    print("Example P2 (X=100.000, Y=0.000): height {:.4f} mm".format(altura_p2))
    print("If G-code requests Z=-1.000 -> Z comp = {:.4f}".format(-1.000 + altura_p2))


if __name__ == "__main__":
    main()
