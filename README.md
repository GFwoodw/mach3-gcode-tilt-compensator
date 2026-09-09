# Mach3 G-Code Tilt Compensator — Simple CNC Surface Leveling for Old PCs

**v0.1 — functional, initial version**

> **Keywords:** Mach3, G-code, CNC, tilt compensation, surface leveling, autolevel alternative, parallel port, Windows XP, wood warping, Vectric

Simple Python tool to compensate tilted or slightly warped wood workpieces on CNC routers. Probe 4–7 points with the spindle itself, correct any G-code keeping syntax, and generate a `_COMPENSATED` file ready for Mach3. No bloat, works offline on **Pentium 4 / Windows XP, Windows 7, Ubuntu Linux**.

[Leer en español → README.es.md](README.es.md)

---

## The Problem

I often need to engrave, carve and do marquetry on irregular pieces with faces and shapes that are not parallel, where I cannot run a large end-mill pass to flatten them.

Clamping this kind of workpiece to the machine table perfectly parallel to the Z axis is a real torture, if not impossible. And wood is never perfectly flat: it bows, shrinks and swells with humidity.

On old machines with **parallel port controllers (Mach3 on Windows XP / Win7)** it's worse — modern autolevel tools are heavy, need internet or simply don't work well. You need probes, touch plates and extra hardware. With this program you need absolutely nothing. I spent a very long time looking for something so simple that just worked, and I couldn't find it.

This is the program I use in my workshop:

1. Clamp the irregular piece (one flat face to mill).
2. Set the start coordinates to 0 with the mounted tool and probe (paper method) **3 or more points** in any order, reading the coordinates shown by Mach3.
3. Type `X Y Z` in the GUI, select your G-code file and press **Compensate**.
4. Load `*_COMPENSATED.txt` in Mach3 — depth is now constant relative to the real surface.

Uses least-squares plane `Z = A*X + B*Y + C`. Keeps `X/Y/I/J/F` untouched, only shifts `Z` as `Z_new = Z_orig + height(X,Y)`.

## Why This vs Autolevel?

- **2 files, no dependencies** — just Python + Tkinter (included with Python).
- **Offline via USB pendrive** — ideal for XP without internet.
- **Works on very old PCs** — tested on Pentium 4 / Windows XP.
- **Keeps G-code syntax** — `N...G1X...Y...Z...F...` only Z changes.
- **Simple UI** — `X [ ] Y [ ] Z [ ]` rows with **Add point** button, no code editing.
- **No probes, touch plates or similar tools required.**

## Compatibility

| OS | Status | Python required |
|---|---|---|
| **Ubuntu 22.04 / 24.04** | ✅ Tested | `sudo apt install python3-tk` then `python3 compensador_gui.py` |
| **Windows XP (32-bit)** | ✅ Tested with real job | **Exactly Python 3.4.4 MSI** (with Tcl/Tk). Newer Python does NOT install on XP. See `README` in `en/` folder. Via pendrive. |
| **Windows 7 (no updates)** | ⚠️ Not yet verified — please test & report | Python 3.8.x expected (last for Win7). Should work, not yet run on real machine. |
| **Windows 10/11** | ✅ Expected | Any Python 3.x with Tk |

All versions are **Python 3.4+ compatible** (no f-strings).

## Quick Start

### English version
```bash
cd en
python3 compensador_gui.py   # or double-click on Windows
```
1. **Browse** your G-code (`.txt` only — other extensions not tested)
2. Click **Add point** and fill `X Y Z` (dot or comma). Minimum 3, 4–7 recommended, any order.
3. **Compensate** → `example_COMPENSATED.txt` in same folder. Load in Mach3 and do an air run first.

### Spanish version
```bash
cd es
python3 compensador_gui.py
```

## Example

Input:
```
G1 X18.945 Y13.000 Z-0.500
```

After compensation (example plane):
```
G1 X18.945 Y13.000 Z-0.2073
```

Only Z changes. Feeds, arcs (`G2/G3 I/J`), line numbers untouched.

Probe example (any order):
```
0.000 0.000 0.000
100.000 0.000 0.120
100.000 80.000 0.250
0.000 80.000 0.080
```

## Installation via Pendrive (XP Offline)

1. On internet PC, download `python-3.4.4.msi` (Windows x86 MSI, 20 MB) from python.org → copy to USB.
2. On XP, double-click MSI → Next → keep **Tcl/Tk** checked → installs to `C:\Python34`.
3. Copy `en/` or `es/` folder (both `compensador.py` + `compensador_gui.py` together) to XP Desktop or anywhere.
4. Double-click `compensador_gui.py` → if asked, choose `C:\Python34\pythonw.exe` and check *Always use*.

No network, no `pip`, no Wine.

## Repository Layout

```
.
├── en/                 # English version
├── es/                 # Spanish version
├── examples/
│   └── example.txt   # generic placeholder (create your own test file, .txt only)
├── LICENSE             # CC BY-NC 4.0
└── README.md / README.es.md
```


## License

**CC BY-NC 4.0** — Free for non-commercial use, share & adapt with attribution. No commercial use. No warranty. See [LICENSE](LICENSE). For commercial licensing contact authors.

## Contributing

v0.1 functional but Win7 unverified. Please open Issues/PRs with your OS, Python version and Mach3 results. Add more points if wood is badly warped (log warns if error >0.2mm).

---
*Simple tool that actually works — no more searching for hours like I did.*
