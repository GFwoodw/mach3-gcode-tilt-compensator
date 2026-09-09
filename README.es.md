# Compensador de Inclinación G-Code para Mach3 — Nivelado Simple para PCs Viejos

**v0.1 — versión funcional inicial**

> **Palabras clave:** Mach3, G-code, CNC, compensación inclinación, nivelado superficie, alternativa autolevel, puerto paralelo, Windows XP, madera alabeada, Vectric

Herramienta simple en Python para compensar piezas de madera inclinadas o ligeramente alabeadas en CNC. Mide 4–7 puntos con la propia fresa, corrige cualquier G-code manteniendo sintaxis y genera archivo `_COMPENSADO` listo para Mach3. Sin instalaciones raras, funciona offline en **Pentium 4 / Windows XP, Windows 7, Ubuntu Linux**.

[Read in English → README.md](README.md)

---

## El Problema

En muchas ocasiones tengo que hacer grabados, tallados y marqueterías en piezas irregulares, con caras y formas que no son paralelas y a las que no puedo hacer una pasada con fresa grande para aplanar.

Sujetar este tipo de piezas en la mesa de la máquina completamente paralelas respecto al eje Z es un auténtico suplicio, por no decir imposible. Además, la madera nunca es perfectamente plana: comba, merma e hincha con la humedad.

En máquinas viejas con **controladora por puerto paralelo (Mach3 en Windows XP / Win7)** es peor — los autolevel modernos son pesados, necesitan internet o simplemente no funcionan bien. Necesitas sondas, palpadores y demás. Con este programa no necesitas absolutamente nada. Me tiré muchísimo tiempo buscando algo tan simple y que funcionara, y no lo encontré.

Este programa es el que uso en mi taller:

1. Coloco la pieza irregular (una cara plana a trabajar).
2. Ajusto las coordenadas de inicio a 0 con la herramienta montada y palpo (método del papel) **3 o más puntos** en cualquier orden, mirando las coordenadas que indica Mach3.
3. Escribo `X Y Z` en la GUI, elijo el archivo G-code y pulso **Compensar**.
4. Cargo `*_COMPENSADO.txt` en Mach3 — la profundidad ya es constante respecto a la superficie real.

Usa plano por mínimos cuadrados `Z = A*X + B*Y + C`. Mantiene `X/Y/I/J/F` intactos, solo desplaza `Z` como `Z_nuevo = Z_orig + altura(X,Y)`.

## ¿Por qué esto y no Autolevel?

- **2 archivos, sin dependencias** — solo Python + Tkinter (viene con Python).
- **Offline por pendrive USB** — ideal para XP sin internet.
- **Funciona en PCs muy viejos** — probado en Pentium 4 / Windows XP.
- **Respeta sintaxis G-code** — `N...G1X...Y...Z...F...` solo cambia Z.
- **UI simple** — filas `X [ ] Y [ ] Z [ ]` con botón **Agregar punto**, sin tocar código.
- **No se necesitan sondas, palpadores ni herramientas similares.**

## Compatibilidad

| SO | Estado | Python necesario |
|---|---|---|
| **Ubuntu 22.04 / 24.04** | ✅ Probado | `sudo apt install python3-tk` luego `python3 compensador_gui.py` |
| **Windows XP (32-bit)** | ✅ Probado con trabajo real | **Exactamente Python 3.4.4 MSI** (con Tcl/Tk). Versiones nuevas NO instalan en XP. Ver `LEEME.txt`. Por pendrive. |
| **Windows 7 (sin updates)** | ⚠️ Aún no verificado — por favor, prueba y reporta | Python 3.8.x esperado (último para Win7). Debería funcionar, aún no probado en máquina real. |
| **Windows 10/11** | ✅ Esperado | Cualquier Python 3.x con Tk |

Todo compatible **Python 3.4+** (sin f-strings).

## Inicio Rápido

### Versión español
```bash
cd es
python3 compensador_gui.py   # o doble-click en Windows
```
1. **Examinar** tu G-code (`.txt` solo — otras extensiones no probadas)
2. Pulsa **Agregar punto** y rellena `X Y Z` (punto o coma). Mínimo 3, 4–7 recomendados, cualquier orden.
3. **Compensar** → `ejemplo_COMPENSADO.txt` en misma carpeta. Carga en Mach3 y haz prueba en aire primero.

### Versión inglés
```bash
cd en
python3 compensador_gui.py
```

## Ejemplo

Entrada:
```
G1 X18.945 Y13.000 Z-0.500
```

Tras compensar (plano ejemplo):
```
G1 X18.945 Y13.000 Z-0.2073
```

Solo Z cambia. Avances, arcos (`G2/G3 I/J`), números de línea intactos.

Ejemplo palpado (cualquier orden):
```
0.000 0.000 0.000
100.000 0.000 0.120
100.000 80.000 0.250
0.000 80.000 0.080
```

## Instalación por Pendrive (XP sin internet)

1. En PC con internet, descarga `python-3.4.4.msi` (Windows x86 MSI, 20 MB) de python.org → copia a USB.
2. En XP, doble-click MSI → Siguiente → deja marcado **Tcl/Tk** → se instala en `C:\Python34`.
3. Copia carpeta `es/` o `en/` (ambos `compensador.py` + `compensador_gui.py` juntos) al Escritorio del XP o donde quieras.
4. Doble-click `compensador_gui.py` → si pregunta, elige `C:\Python34\pythonw.exe` y marca *Usar siempre*.

Sin red, sin `pip`, sin Wine.

## Estructura Repo

```
.
├── en/                 # Versión inglés
├── es/                 # Versión español
├── examples/
│   └── example.txt   # placeholder genérico (crea tu propio archivo de prueba, solo .txt)
├── LICENSE             # CC BY-NC 4.0
└── README.md / README.es.md
```


## Licencia

**CC BY-NC 4.0** — Libre para uso no comercial, compartir y adaptar con atribución. Sin uso comercial. Sin garantía. Ver [LICENSE](LICENSE). Para licencia comercial contactar autores.

## Contribuir

v0.1 funcional pero Win7 sin verificar. Abre Issues/PRs con tu SO, versión Python y resultado en Mach3. Añade más puntos si la madera está muy alabeada (log avisa si error >0.2mm).

---
*Programa simple que funciona — por fin, sin buscar horas.*
