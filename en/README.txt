CNC COMPENSATOR - INSTRUCTIONS (Ubuntu / Windows XP offline)
===================================================================

CONTENTS OF THIS FOLDER:
- compensador.py        -> core (do not edit)
- compensador_gui.py    -> GUI (double-click)
- example.txt           -> generic G-code example
- README.txt            -> this file

-------------------------------------------------------------------
A) ON UBUNTU / LINUX
-------------------------------------------------------------------
1. Install Tkinter if missing:
   sudo apt update && sudo apt install python3-tk -y

2. Run:
   python3 compensador_gui.py

3. Use:
   - [Browse...] select your G-code file (.txt only)
   - Click "Add point" and fill X  Y  Z per row:
        X [0.000]     Y [0.000]    Z [0.000]
        X [100.000]   Y [0.000]    Z [0.120]
     Minimum 3 points, 4-7 recommended. Use dot or comma.
   - Press COMPENSATE
   - Creates file_COMPENSATED.txt in same folder.

-------------------------------------------------------------------
B) ON WINDOWS XP (offline)
-------------------------------------------------------------------
1. On internet PC download python-3.4.4.msi (20MB) from python.org to pendrive.
2. On XP double-click -> Next -> check Tcl/Tk -> C:\Python34
3. Copy compensador.py + compensador_gui.py TOGETHER to same folder.
4. Double-click compensador_gui.py -> Open with C:\Python34\pythonw.exe.

Same use as Ubuntu.

-------------------------------------------------------------------
C) GENERAL TIPS
-------------------------------------------------------------------
- Set real machine 0 coordinates and always probe with the same tool that will mill.
- Try to cover the whole surface to mill (corners and center).
- If log shows "Max error >0.2mm" check measurements.
- Always do an air run before milling. Raise Z axis exactly 5 mm (for example), confirm that's the new Z 0 and test. Then lower -5 mm, set to 0 and mill for real.

-------------------------------------------------------------------
DISCLAIMER - USE AT YOUR OWN RISK
-------------------------------------------------------------------
This program is provided "as is", without warranty. The author assumes no liability for any damage to machine, workpiece, tool or personal injury from its use or generated G-code. You are solely responsible for verifying the file and doing an air run (raise Z +5mm) before milling. Use at your own risk.
