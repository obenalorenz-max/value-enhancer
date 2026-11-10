# 🛰️ Value-Enhancer

> **High-Performance Unified OSINT & Digital Reconnaissance Suite**  
> *Engineered for fast, lightweight, on-premise security auditing, digital footprint discovery, and defensive intelligence gathering.*

---

## ⚡ Overview

**Value-Enhancer** is a modular, high-speed reconnaissance and digital exposure audit framework. Inspired by tools like **Maigret**, **PhoneInfoga**, **theHarvester**, and **TruffleHog**, it integrates multi-vector OSINT capabilities into a single, low-overhead engine with both a sleek terminal CLI and an interactive local web dashboard.

Optimized to run seamlessly on low-spec hardware (including low-spec Windows 11 machines and lightweight Linux containers) with minimal memory footprint (<60MB RAM) and zero heavy GPU dependencies.

---

## 🛠️ Reconnaissance Vectors

```mermaid
flowchart TD
    Target["Target Entity"]
    
    subgraph Engine["Value-Enhancer Modular Engine"]
        ID["👤 Identity Hunter\n(Maigret / Sherlock style)"]
        PH["📱 Phone & Carrier Recon\n(PhoneInfoga style)"]
        DM["🌐 Domain & DNS Intel\n(theHarvester style)"]
        SC["🔑 Secrets & Leaks Auditor\n(TruffleHog style)"]
        EX["🗺️ EXIF & GPS Harvester\n(Geolocation extractor)"]
    end
    
    Target --> Engine
    Engine --> Output["Console Tables / Structured JSON / Interactive WebUI"]
```

1. **👤 Identity Hunter (`identity`)**:
   - Asynchronous multi-platform username scanner querying dozens of developer, social, publishing, and messaging platforms in parallel.
   - Calculates exposure score based on active digital footprints.

2. **📱 Carrier & Phone Recon (`phone`)**:
   - Parses international telephone numbers using Google's libphonenumber standard.
   - Detects telecom carriers, country locations, and line types (e.g., Mobile, Fixed Line, or VOIP/burner numbers).
   - Generates targeted Google OSINT dorks for web presence correlation.

3. **🌐 Domain & Infrastructure Intel (`domain`)**:
   - Maps IPv4 (A), IPv6 (AAAA), Mail Exchangers (MX), and Name Servers (NS).
   - Analyzes **SPF** and **DMARC** records to identify critical email spoofability risks.
   - Fast asynchronous subdomain probing.

4. **🔑 Secrets & Leaks Auditor (`secrets`)**:
   - Shannon Entropy analysis to detect high-entropy keys, passwords, and tokens.
   - Pattern matching for AWS keys, GitHub PATs, private certificates, Google API keys, Slack tokens, and JWTs.
   - Automatic secret masking to avoid plaintext terminal leaks.

5. **🗺️ EXIF & GPS Harvester (`metadata`)**:
   - Extracts camera hardware makes, models, software versions, and creation timestamps.
   - Decodes DMS GPS tags into decimal latitude/longitude with direct Google Maps links.

---

## 🚀 Quickstart

### 1. Installation

Clone the repository and install dependencies using `pip` or `uv`:

```bash
git clone https://github.com/obenalorenz-max/value-enhancer.git
cd value-enhancer

# Create and activate virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On Linux/macOS:
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

---

### 2. Command Line Usage (CLI)

#### 👤 Scan Digital Footprint (Username)
```bash
python -m value_enhancer.cli identity torvalds
```

#### 📱 Analyze Phone Number
```bash
python -m value_enhancer.cli phone "+639171234567"
```

#### 🌐 Audit Domain & DNS Security
```bash
python -m value_enhancer.cli domain github.com
```

#### 🔑 Audit Code / Files for Leaked Credentials
```bash
python -m value_enhancer.cli secrets ./src
```

#### 🗺️ Extract GPS & Camera Metadata from Image
```bash
python -m value_enhancer.cli metadata photo.jpg
```

*Tip: Pass `--json-out` to any command for pipeline scripting and machine-readable output.*

---

### 3. Local Web Dashboard

Launch the embedded web dashboard:

```bash
python -m value_enhancer.cli web --port 8000
```

Open `http://localhost:8000` in your browser to access the tactical cyber console with drag-and-drop file uploads, live scan progress bars, and instant risk scoring.

---

## 🧪 Running Automated Tests

Run the test suite using `pytest`:

```bash
PYTHONPATH=src pytest -v tests/
```

---

## ⚖️ Ethical & Legal Disclaimer

*Value-Enhancer is built strictly for educational, defensive security auditing, and authorized open-source intelligence research. All queries utilize public endpoints and open records. Users are responsible for complying with all applicable local, national, and international laws.*

---

## 📄 License

MIT License. Developed for open security research.
