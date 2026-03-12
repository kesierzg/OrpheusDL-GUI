# Lokaal Testen van Installers

Deze gids beschrijft hoe je de OrpheusDL-GUI installers offline kunt testen op virtuele machines (Windows, macOS, Linux) voordat je ze naar GitHub pusht.

## Voorbereiding (Alle Platformen)

Omdat je lokaal aan het testen bent, is het het makkelijkst om je hele projectmap (`OrpheusDL-GUI`) naar de VM te kopiëren. Zo test je exact met de bestanden en modules die je nu hebt.

Zorg dat op elke VM **Python 3.10 of hoger** geïnstalleerd is.

---

## 🪟 Windows VM

### 1. Omgeving Opzetten
1. Installeer Python (zorg dat je "Add Python to PATH" aanvinkt tijdens installatie).
2. Open PowerShell of Command Prompt in de projectmap.
3. Installeer dependencies en build tools:
   ```powershell
   pip install -r requirements.txt
   pip install -r requirements-gui.txt
   pip install pyinstaller
   ```
4. **Installeer Inno Setup:**
   - Download en installeer Inno Setup 6+: [jrsoftware.org](https://jrsoftware.org/isinfo.php)
   - Standaard installatielocatie is prima (`C:\Program Files (x86)\Inno Setup 6`).

### 2. Installer Bouwen
Draai het build script:
```powershell
python build_all_installers.py --windows
```

### 3. Testen
- Ga naar de map `dist/`.
- Dubbelklik op `OrpheusDL_GUI-Setup-1.0.0.exe`.
- **Checklist:**
  - [ ] Start de installer op?
  - [ ] Zie je het scherm om Modules te selecteren?
  - [ ] Wordt de applicatie geïnstalleerd in de juiste map?
  - [ ] Werkt de snelkoppeling op het bureaublad?
  - [ ] Start de app correct op na installatie?

---

## 🍎 macOS VM

### 1. Omgeving Opzetten
1. Zorg dat Python 3 geïnstalleerd is (vaak standaard, anders via [python.org](https://www.python.org/downloads/macos/)).
2. Installeer Homebrew (als je dat nog niet hebt) om `create-dmg` te installeren:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
3. Installeer dependencies:
   ```bash
   pip3 install -r requirements.txt
   pip3 install -r requirements-gui.txt
   pip3 install pyinstaller
   brew install create-dmg
   ```

### 2. Installer Bouwen
Draai het build script in Terminal:
```bash
python3 build_all_installers.py --macos
```

### 3. Testen
- Ga naar de map `dist/`.
- Open `OrpheusDL_GUI-Installer.dmg`.
- **Checklist:**
  - [ ] Opent het DMG venster met de achtergrond en iconen?
  - [ ] Kun je de app naar 'Applications' slepen?
  - [ ] Start de app vanuit de Applications map?
  - *Note:* Omdat de app niet gesigneerd is met een Apple Developer ID, moet je bij de eerste keer openen waarschijnlijk via Rechtermuisknop -> Open gaan en bevestigen.

---

## 🐧 Linux (Ubuntu) VM

### 1. Omgeving Opzetten
1. Open een terminal.
2. Installeer systeemvereisten en Python tools:
   ```bash
   sudo apt update
   sudo apt install -y python3-pip python3-venv libfuse2
   ```
   *(Note: `libfuse2` is nodig om AppImage tools te draaien op nieuwere Ubuntu versies)*

3. Installeer Python dependencies:
   ```bash
   pip3 install -r requirements.txt
   pip3 install -r requirements-gui.txt
   pip3 install pyinstaller
   ```

### 2. Installer Bouwen
Draai het build script:
```bash
python3 build_all_installers.py --linux
```
*Het script downloadt automatisch `appimagetool` als het niet gevonden wordt.*

### 3. Testen
- Ga naar de map `dist/`.
- Je zou een bestand moeten zien dat eindigt op `.AppImage`.
- Maak het uitvoerbaar (zou al moeten zijn, maar voor de zekerheid):
  ```bash
  chmod +x OrpheusDL_GUI-*.AppImage
  ```
- Dubbelklik erop of run `./OrpheusDL_GUI-*.AppImage` in de terminal.
- **Checklist:**
  - [ ] Start de applicatie direct op?
  - [ ] Werken de modules?

---

## 🛠 Veelvoorkomende Problemen

- **Module niet gevonden:** Zorg dat je de hele `modules/` map hebt gekopieerd naar je VM.
- **PyInstaller foutmeldingen:** Probeer `pyinstaller --clean gui.spec` handmatig te draaien om de cache te legen.
- **Ontbrekende iconen:** Controleer of `icon.ico`, `icon.png` en `icon.icns` in de root van je projectmap staan op de VM.

