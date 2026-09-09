import sys
import re
import math

# =================================================================
# FUNCIONES DE INTERPOLACION
# =================================================================

def calcular_plano_minimos_cuadrados(puntos):
    """
    Calcula el plano Z = A*X + B*Y + C que mejor se ajusta a los puntos
    usando minimos cuadrados. Funciona con 3 o mas puntos.
    Compatible Python 3.4+ (sin f-strings)
    """
    n = len(puntos)
    if n < 3:
        raise ValueError("Se necesitan al menos 3 puntos. Tienes {}.".format(n))
    
    # Inicializar sumatorias
    sum_x = sum_y = sum_z = 0
    sum_x2 = sum_y2 = sum_xy = sum_xz = sum_yz = 0
    
    # Calcular sumatorias
    for x, y, z in puntos:
        sum_x += x
        sum_y += y
        sum_z += z
        sum_x2 += x * x
        sum_y2 += y * y
        sum_xy += x * y
        sum_xz += x * z
        sum_yz += y * z
    
    # Matriz para minimos cuadrados:
    # [ sum_x2   sum_xy   sum_x ] [ A ]   [ sum_xz ]
    # [ sum_xy   sum_y2   sum_y ] [ B ] = [ sum_yz ]
    # [ sum_x    sum_y    n     ] [ C ]   [ sum_z  ]
    
    # Calcular determinante principal
    det = (sum_x2 * sum_y2 * n + 
           sum_xy * sum_y * sum_x + 
           sum_x * sum_xy * sum_y - 
           sum_x * sum_y2 * sum_x - 
           sum_xy * sum_xy * n - 
           sum_x2 * sum_y * sum_y)
    
    if abs(det) < 1e-10:
        # Puntos casi colineales, usar metodo alternativo
        # Tomar 3 puntos no colineales para definir plano
        p0, p1, p2 = puntos[0], puntos[1], puntos[-1]
        
        # Vectores
        v1 = [p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]]
        v2 = [p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]]
        
        # Producto cruzado para vector normal
        nx = v1[1] * v2[2] - v1[2] * v2[1]
        ny = v1[2] * v2[0] - v1[0] * v2[2]
        nz = v1[0] * v2[1] - v1[1] * v2[0]
        
        # Ecuacion del plano: nx*x + ny*y + nz*z = d
        d = nx * p0[0] + ny * p0[1] + nz * p0[2]
        
        A = nx / nz if nz != 0 else 0
        B = ny / nz if nz != 0 else 0
        C = -d / nz if nz != 0 else 0
        
        return A, B, C
    
    # Calcular A, B, C usando regla de Cramer
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
    """
    Calcula la altura Z de la superficie en el punto (x,y)
    usando el plano Z = A*x + B*y + C
    """
    return A * x + B * y + C


# =================================================================
# FUNCIONES PARA PROCESAR G-CODE
# =================================================================

def extraer_coordenadas(linea):
    """
    Extrae coordenadas X, Y, Z de una linea de G-code.
    Devuelve (x, y, z) donde cada uno puede ser None si no esta presente.
    Maneja formatos como: N100G00X-36.853Y-22.740Z5.000
    """
    x = y = z = None
    
    # Patrones para encontrar coordenadas con signo negativo
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
                pass  # Si no puede convertir, dejar como None
    
    return x, y, z


def reemplazar_coordenada_z(linea, nuevo_z, decimales=3):
    """
    Reemplaza el valor de Z en una linea de G-code manteniendo el formato.
    Compatible Python 3.4+
    """
    # Buscar el patron Z seguido de numero
    match = re.search(r'Z[+-]?\d+\.?\d*', linea)
    if match:
        # Reemplazar solo la parte numerica manteniendo la 'Z'
        viejo_z_str = match.group(0)
        # Formatear nuevo valor con el numero de decimales especificado
        fmt = "Z{0:." + str(decimales) + "f}"
        nuevo_z_str = fmt.format(nuevo_z)
        # Eliminar ceros decimales innecesarios
        # Para no eliminar ceros importantes, mantener al menos 3 decimales si necesario
        nuevo_z_str = nuevo_z_str.rstrip('0').rstrip('.')
        # Si termina en 'Z' o 'Z-' (caso borde), asegurar formato
        if nuevo_z_str == "Z" or nuevo_z_str == "Z-":
            nuevo_z_str = fmt.format(nuevo_z)
        # Reemplazar en la linea
        return linea.replace(viejo_z_str, nuevo_z_str, 1)
    
    # Si no encuentra Z (no deberia pasar si llamamos a esta funcion)
    return linea


def procesar_gcode(archivo_entrada, archivo_salida, A, B, C, mostrar_cambios=5):
    """
    Procesa el archivo G-code linea por linea aplicando la compensacion.
    """
    # Estado actual de la maquina
    x_actual = 0.0
    y_actual = 0.0
    z_actual = 0.0
    
    contador_lineas = 0
    contador_cambios = 0
    cambios_mostrados = 0
    
    # Estadisticas para el resumen
    estadisticas_z = {
        'min_original': float('inf'),
        'max_original': float('-inf'),
        'min_compensado': float('inf'),
        'max_compensado': float('-inf')
    }
    
    print("\nProcesando: {}".format(archivo_entrada))
    print("Coeficientes del plano: A={:.6f}, B={:.6f}, C={:.6f}".format(A, B, C))
    
    try:
        with open(archivo_entrada, 'r', encoding='utf-8', errors='ignore') as f_in, \
             open(archivo_salida, 'w', encoding='utf-8') as f_out:
            
            for linea_original in f_in:
                contador_lineas += 1
                linea = linea_original.rstrip('\n')
                linea_modificada = linea
                
                # Extraer coordenadas de esta linea
                x_linea, y_linea, z_linea = extraer_coordenadas(linea)
                
                # Actualizar posicion actual si hay nuevas coordenadas
                if x_linea is not None:
                    x_actual = x_linea
                if y_linea is not None:
                    y_actual = y_linea
                if z_linea is not None:
                    z_actual = z_linea
                
                # Aplicar compensacion si esta linea tiene coordenada Z
                if z_linea is not None and x_actual is not None and y_actual is not None:
                    # Calcular altura de la superficie en este punto
                    altura_superficie = altura_en_punto(x_actual, y_actual, A, B, C)
                    
                    # Aplicar compensacion: Z_nuevo = Z_original + Altura_superficie
                    z_nuevo = z_linea + altura_superficie
                    
                    # Actualizar estadisticas
                    estadisticas_z['min_original'] = min(estadisticas_z['min_original'], z_linea)
                    estadisticas_z['max_original'] = max(estadisticas_z['max_original'], z_linea)
                    estadisticas_z['min_compensado'] = min(estadisticas_z['min_compensado'], z_nuevo)
                    estadisticas_z['max_compensado'] = max(estadisticas_z['max_compensado'], z_nuevo)
                    
                    # Reemplazar Z en la linea
                    linea_modificada = reemplazar_coordenada_z(linea, z_nuevo, decimales=4)
                    
                    contador_cambios += 1
                    
                    # Mostrar algunos cambios para verificacion
                    if cambios_mostrados < mostrar_cambios and linea_modificada != linea:
                        cambios_mostrados += 1
                        print("\n--- Cambio {} ---".format(cambios_mostrados))
                        print("Linea: {}".format(contador_lineas))
                        print("Posicion: X={:.3f}, Y={:.3f}".format(x_actual, y_actual))
                        print("Altura superficie: {:.4f} mm".format(altura_superficie))
                        print("Z original: {:.4f}".format(z_linea))
                        print("Z compensado: {:.4f}".format(z_nuevo))
                        print("Original: {}...".format(linea[:80]))
                        print("Modificado: {}...".format(linea_modificada[:80]))
                
                # Escribir linea (modificada o no) al archivo de salida
                f_out.write(linea_modificada + '\n')
                
                # Mostrar progreso cada 10000 lineas
                if contador_lineas % 10000 == 0:
                    print("  Procesadas {} lineas...".format(contador_lineas))
    
    except FileNotFoundError:
        print("ERROR: No se encuentra el archivo '{}'".format(archivo_entrada))
        return None
    except Exception as e:
        print("ERROR procesando archivo: {}".format(e))
        return None
    
    return contador_lineas, contador_cambios, estadisticas_z


# =================================================================
# FUNCIONES DE VERIFICACION Y UTILIDAD
# =================================================================

def verificar_ajuste_plano(puntos, A, B, C, tolerancia_max=0.1):
    """
    Verifica que el plano calculado se ajusta bien a los puntos medidos.
    """
    print("\n" + "="*70)
    print("VERIFICACION DEL AJUSTE DEL PLANO")
    print("="*70)
    
    max_error = 0
    puntos_con_error = []
    
    for i, (x, y, z_medido) in enumerate(puntos, 1):
        z_calculado = altura_en_punto(x, y, A, B, C)
        error = abs(z_calculado - z_medido)
        max_error = max(max_error, error)
        
        if error > 0.01:  # Solo mostrar si error > 0.01 mm
            puntos_con_error.append((i, x, y, z_medido, z_calculado, error))
        
        print("Punto {}: X={:9.3f}, Y={:9.3f}".format(i, x, y))
        print("  Z medido:    {:7.4f} mm".format(z_medido))
        print("  Z calculado: {:7.4f} mm".format(z_calculado))
        print("  Error:       {:7.4f} mm".format(error))
        if error <= tolerancia_max:
            print("  OK Aceptable")
        else:
            print("  !! Alto")
        print("")
    
    print("Error maximo: {:.4f} mm".format(max_error))
    
    if max_error > tolerancia_max:
        print("\nADVERTENCIA: El error maximo ({:.3f} mm) excede la tolerancia.".format(max_error))
        print("   Considera:")
        print("   1. Verificar las mediciones")
        print("   2. Anadir mas puntos de medicion")
        print("   3. La pieza podria no ser completamente plana")
    
    return max_error


def mostrar_resumen(contador_lineas, contador_cambios, estadisticas_z, archivo_salida):
    """
    Muestra un resumen del procesamiento.
    """
    print("\n" + "="*70)
    print("RESUMEN DEL PROCESAMIENTO")
    print("="*70)
    print("Lineas totales procesadas: {}".format(contador_lineas))
    print("Movimientos Z compensados: {}".format(contador_cambios))
    print("Archivo generado: {}".format(archivo_salida))
    
    if estadisticas_z['min_original'] != float('inf'):
        print("\nEstadisticas de valores Z:")
        print("  Original:   [{:.3f} a {:.3f}]".format(estadisticas_z['min_original'], estadisticas_z['max_original']))
        print("  Compensado: [{:.3f} a {:.3f}]".format(estadisticas_z['min_compensado'], estadisticas_z['max_compensado']))


# =================================================================
# CONFIGURACION PRINCIPAL - MODO CLI ORIGINAL
# =================================================================

def main():
    print("="*70)
    print("COMPENSADOR DE SUPERFICIE INCLINADA PARA CNC")
    print("="*70)
    
    # =============================================================
    # 1. CONFIGURACION: PON TUS PUNTOS AQUI (modo CLI)
    # =============================================================
    # Formato: [X, Y, Z] donde Z es la altura MEDIDA de la superficie
    # Z positivo = la superficie esta MAS ALTA que el punto de referencia
    # Puedes anadir tantos puntos como quieras (minimo 3)
    
    PUNTOS_MEDIDOS = [
         # Ejemplo generico:
        [0.000, 0.000, 0.000],   # P1: Esquina superior izquierda
        [100.000, 0.000, 0.120],   # P2: Esquina superior derecha
        [100.000, 80.000, 0.250],   # P3: Esquina inferior derecha
        [0.000, 80.000, 0.080],  # P4: Esquina inferior izquierda
        
        # Puedes anadir mas puntos aqui:
        # [x, y, z],
        # [x, y, z],
    ]
    
    # =============================================================
    # 2. CONFIGURACION DE ARCHIVOS
    # =============================================================
    ARCHIVO_ENTRADA = "Grabadotrskelion.txt"    # Tu archivo G-code original
    ARCHIVO_SALIDA = "Grabadotrskelion_COMPENSADO.txt"  # Archivo compensado
    
    # =============================================================
    # 3. EJECUCION
    # =============================================================
    
    # Verificar que tenemos suficientes puntos
    if len(PUNTOS_MEDIDOS) < 3:
        print("ERROR: Necesitas al menos 3 puntos. Tienes {}.".format(len(PUNTOS_MEDIDOS)))
        print("   Anade mas puntos a la lista PUNTOS_MEDIDOS.")
        return
    
    print("\nPuntos de medicion cargados: {}".format(len(PUNTOS_MEDIDOS)))
    print("Coordenadas (X, Y, Z):")
    for i, (x, y, z) in enumerate(PUNTOS_MEDIDOS, 1):
        print("  P{}: X={:9.3f}, Y={:9.3f}, Z={:7.4f}".format(i, x, y, z))
    
    # Calcular el plano que mejor se ajusta
    print("\nCalculando plano de ajuste...")
    try:
        A, B, C = calcular_plano_minimos_cuadrados(PUNTOS_MEDIDOS)
        print("Plano calculado: Z = {:.6f}*X + {:.6f}*Y + {:.6f}".format(A, B, C))
    except Exception as e:
        print("Error calculando el plano: {}".format(e))
        return
    
    # Verificar calidad del ajuste
    max_error = verificar_ajuste_plano(PUNTOS_MEDIDOS, A, B, C, tolerancia_max=0.1)
    
    # Preguntar si continuar si el error es alto
    if max_error > 0.2:
        try:
            respuesta = input("\nEl error maximo es {:.2f} mm. Continuar? (s/n): ".format(max_error))
        except:
            respuesta = "s"
        if respuesta.lower() != 's':
            print("Proceso cancelado.")
            return
    
    # Procesar el archivo G-code
    print("\n" + "="*70)
    print("PROCESANDO G-CODE")
    print("="*70)
    
    resultado = procesar_gcode(ARCHIVO_ENTRADA, ARCHIVO_SALIDA, A, B, C, mostrar_cambios=5)
    
    if resultado is None:
        print("Error en el procesamiento. Revisa los mensajes anteriores.")
        return
    
    contador_lineas, contador_cambios, estadisticas_z = resultado
    
    # Mostrar resumen
    mostrar_resumen(contador_lineas, contador_cambios, estadisticas_z, ARCHIVO_SALIDA)
    
    # =============================================================
    # 4. INSTRUCCIONES FINALES
    # =============================================================
    print("\n" + "="*70)
    print("INSTRUCCIONES DE VERIFICACION Y USO")
    print("="*70)
    print("1. El archivo compensado ya esta generado.")
    print("2. VERIFICA algunos puntos clave en el archivo compensado:")
    print("   a) Busca coordenadas cerca de P2 (X~ -25, Y~ -20)")
    print("      Z original -1.000 deberia ser ~ -0.310")
    print("   b) Busca coordenadas cerca de P3 (X~ -42, Y~ -164)")
    print("      Z original -1.000 deberia ser ~ -0.190")
    print("3. HAZ UNA PRUEBA EN AIRE:")
    print("   - Carga el archivo en Mach3")
    print("   - Ejecuta con la fresa LEJOS de la pieza")
    print("   - Observa que el movimiento Z es suave")
    print("4. PRUEBA EN MATERIAL DE DESECHO:")
    print("   - Usa espuma o madera barata")
    print("   - Ejecuta con profundidad minima (ej: 0.2 mm)")
    print("   - Mide la profundidad resultante en varios puntos")
    print("5. Cuando las pruebas sean correctas, usa en tu pieza final.")
    print("\nRECUERDA: La compensacion se aplica a TODOS los valores Z,")
    print("   incluyendo diferentes profundidades y pasadas.")
    
    # Ejemplo de calculo para verificacion
    print("\n" + "="*70)
    print("EJEMPLO DE CALCULO PARA P2 (X=100.000, Y=0.000):")
    print("="*70)
    altura_p2 = altura_en_punto(100.000, 0.000, A, B, C)
    print("Altura de la superficie en P2: {:.4f} mm".format(altura_p2))
    print("Si el G-code pide Z = -1.000 mm:")
    print("Z compensado = -1.000 + {:.4f} = {:.4f} mm".format(altura_p2, (-1.000 + altura_p2)))
    print("Profundidad resultante: {:.4f} - {:.4f} = 1.000 mm".format(altura_p2, (-1.000 + altura_p2)))


if __name__ == "__main__":
    main()
