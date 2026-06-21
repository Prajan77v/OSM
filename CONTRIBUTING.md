# 🤝 Contributing to OMS Sentinel

We welcome contributions from open-source developers, AI engineers, UI/UX designers, and security specialists! Thank you for helping build the future of autonomous smart surveillance.

Please read this document carefully to maintain the design aesthetics and engineering quality of the platform.

---

## 📖 Code of Conduct
By participating in this project, you agree to abide by our Code of Conduct (standard open-source behaviors: respectful communication, prioritizing system safety, and protecting privacy rights).

---

## 🛠️ Development Setup

1. **Fork & Clone**
   ```bash
   git clone https://github.com/Prajan77v/OSM.git
   cd OSM
   ```

2. **Backend Setup**
   * Create a virtual environment using Python 3.10 or 3.11:
     ```bash
     python -m venv venv
     source venv/bin/activate
     pip install -r requirements.txt
     ```
   * Run the AI surveillance core:
     ```bash
     python main.py
     ```

3. **Frontend Setup**
   * Install Node.js v18+.
   * Go to the `frontend/` directory and start the dev server:
     ```bash
     cd frontend
     npm install
     npm run dev
     ```
   * Open [http://localhost:3000](http://localhost:3000).

---

## 🎨 Visual & Code Design Rules

### 1. Maintain the "Black & Gold" OLED Aesthetic
* All new frontend components must utilize the predefined CSS variables from [globals.css](file:///C:/Users/Prajan/.gemini/antigravity/scratch/smart_surveillance/frontend/src/app/globals.css):
  - Card backgrounds: `var(--card-bg)` (`#161A22`)
  - Accent colors: `var(--gold-accent)` (`#D4AF37`)
  - Base background: `var(--bg-color)` (`#0D0F12`)
* Avoid using generic colors (like basic Bootstrap green or red badges). Use the custom themed palettes.

### 2. Thread Safety is Paramount
* The camera capture thread must **never block**. 
* Any new ML inferences, file outputs, or network network requests (like Telegram alerts) must be executed:
  - Through non-blocking queue queues (`NotificationQueue`).
  - Or submitted to an asynchronous thread executor (`face_pool`, `haae_pool`) via `concurrent.futures`.

### 3. Graceful Fallbacks & Optional Modules
* The app must build and execute successfully even if optional packages (like `deepface`, `fer`, or `pynvml`) fail to load.
* Wrap imports and initializations in try/except blocks and set status booleans (e.g. `DEEPFACE_AVAILABLE = False`).

---

## 📬 Pull Request Protocol

1. **Branch Naming**: Use clear prefixes:
   - `feat/feature-name` (new features)
   - `fix/bug-description` (bug fixes)
   - `docs/documentation-update` (documentation)
2. **Unit Tests**: Run tests inside the `/tests` folder prior to submitting.
3. **Document Your Work**: Update `walkthrough.md` or add notes in your PR detailing what was tested and how to verify it.
