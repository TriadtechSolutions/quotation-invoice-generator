# Win Spares Document Management System — VRF Quotation Module (Version 1)

Production-ready web application built for **Win Spares** to generate, preview, save, and download professional **VRF Quotations**.

Designed with a modular architecture so an **Invoice module can be added seamlessly in future versions without rebuilding the application**.

---

## 🌟 Key Features

1. **Exact Visual Reproduction of Reference PDF**:
   - Matches the layout, structure, font hierarchy, borders, and spacing of `VRF_Quotation.pdf`.
   - Side-by-side bordered `FROM` and `CUSTOMER` boxes.
   - Dark Navy Blue (`#1c3b68`) header table with solid 1.5px grid cell borders.
   - Exact text formatting for Subtotal, SGST (9%), CGST (9%), and Grand Total (`₹17,700/-`).
   - Bulleted Scope of Service checklist.
   - Centered Win Spares greeting and footer branding.

2. **Automated Calculations**:
   - Dynamic Item rows with instant client-side calculation (`Qty × Rate`).
   - Authoritative server-side recalculation to prevent tampering or client discrepancies.
   - Indian currency standard formatting (`₹15,000/-`, `₹1,350/-`, `₹17,700/-`).

3. **Firebase Firestore Integration**:
   - Stores settings, customer profiles, service templates, and quotations in separate Firestore collections.
   - Embeds a snapshot of company details in each quotation for historical immutability.
   - Sequential quotation number generator (`QTN-YYYY-001`, `QTN-YYYY-002`) with Firestore transaction handling.
   - Out-of-the-box local storage fallback when Firebase credentials are not yet configured.

4. **High-Fidelity Server-Side PDF Generation**:
   - Compiles searchable, selectable PDFs from clean HTML/CSS templates using **WeasyPrint**.
   - Automatic sanitized PDF filenames: `QTN-2026-001_Visesha-Silk-Sarees-LLP.pdf`.

5. **Customer Autocomplete & Scope Manager**:
   - Customer lookup from existing database records.
   - Dynamic scope checklist editor with add, remove, and reordering capabilities.

6. **Quotation History & Search**:
   - Full history table listing generated quotations.
   - Real-time search filter by Quotation Number or Customer Name.
   - Quick View, PDF Download, and Duplicate Quotation into a new draft.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.12, Flask 3.1.3
- **Database**: Firebase Firestore (`firebase-admin` SDK) + `LocalJSONFirestore` fallback
- **PDF Engine**: WeasyPrint 69.0 (HTML5/CSS3 → PDF)
- **Frontend**: Vanilla JavaScript (ES6+), HTML5, Vanilla CSS3 + Bootstrap 5 layout

---

## 📁 Project Structure

```text
├── app.py                      # Main Flask application entry point
├── requirements.txt            # Python dependency manifest
├── README.md                   # Setup documentation & guide
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
│
├── firebase/
│   └── firebase_config.py      # Firebase Admin SDK & LocalJSONFirestore setup
│
├── services/
│   ├── firebase_service.py     # Firestore CRUD, seeding, and sequence generator
│   ├── quotation_service.py    # Quotation business logic & calculations
│   └── pdf_service.py          # WeasyPrint PDF compiler
│
├── utils/
│   ├── calculations.py         # Subtotal, tax, and grand total logic
│   ├── formatting.py           # Indian currency & date formatters
│   └── validators.py           # Server-side payload validation
│
├── routes/
│   ├── dashboard_routes.py     # Dashboard blueprint (/)
│   └── quotation_routes.py     # Quotation routes & API endpoints
│
├── templates/
│   ├── base.html               # Main navbar layout
│   ├── dashboard.html          # Application dashboard
│   ├── quotation_form.html     # Create/edit quotation form
│   ├── quotation_preview.html  # Centered A4 visual document preview
│   ├── quotation_pdf.html      # Printable HTML template for WeasyPrint
│   ├── quotation_history.html  # Quotation history list & search
│   └── quotation_view.html     # Saved quotation view
│
├── static/
│   ├── css/
│   │   ├── main.css            # Web UI styles & cards
│   │   └── quotation.css       # Paper document styles matching VRF_Quotation.pdf
│   └── js/
│       ├── common.js           # Currency formatters & toasts
│       └── quotation.js        # Dynamic row calculation & scope manager
│
└── tests/
    ├── test_calculations.py    # Unit tests for calculations & formatting
    ├── test_pdf.py             # Integration test for WeasyPrint PDF output
    └── test_routes.py          # Flask route integration tests
```

---

## ⚡ Quick Start & Setup

### 1. Prerequisites
Ensure Python 3.10+ is installed on your system.

### 2. Clone / Open Directory
```bash
cd "VRF Quotation Invoice Generator"
```

### 3. Create & Activate Virtual Environment
```bash
python3 -m venv venv

# On Linux / macOS:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. (Optional) Configure Firebase Admin SDK Credentials
If you have a live Firebase Firestore project:
1. Go to Firebase Console → Project Settings → Service accounts.
2. Click **Generate new private key** and download `serviceAccountKey.json`.
3. Place `serviceAccountKey.json` in the root folder of this project.

*Note: If no service account key is present, the app automatically runs in out-of-the-box local testing mode using file-backed storage in `data_store/`.*

### 6. Run the Application
```bash
python app.py
```

Access the application in your browser at:
`http://127.0.0.1:5000`

---

## 🧪 Running Automated Tests

Run the test suite to verify calculations, WeasyPrint PDF compilation, and web routes:

```bash
source venv/bin/activate
python -m unittest discover -s tests
```

---

## 📝 License
© 2026 Win Spares. All rights reserved.
