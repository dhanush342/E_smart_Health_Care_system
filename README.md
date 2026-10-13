# E-Health-Care: Smart AI Healthcare & Teleconsultation Platform

An intelligent, AI-powered healthcare web platform built with **Django**, **Machine Learning**, and **Deep Learning** (CNN & ANN). The platform bridges the gap between patients and medical professionals by providing automated disease symptom prediction, chest X-ray image diagnostics, appointment scheduling, real-time doctor-patient messaging, and a comprehensive hospital administration portal.

---

## Key Highlights

- **AI-Powered Diagnostics**:
  - **Pneumonia Detection**: Deep Convolutional Neural Network (CNN) trained on chest X-ray images.
  - **Medical Image Validator**: Automated CNN-based image block verification ensuring uploaded images are valid chest radiographs.
  - **Heart Disease Risk Classifier**: Machine Learning model analyzing clinical indicators (BP, cholesterol, ECG, ST depression, etc.).
  - **Diabetes Predictor**: ML predictive model evaluating glucose, BMI, insulin, and age factors.
  - **Multi-Symptom Disease Predictor**: Natural-language and symptom-based decision tree matching over 130+ symptoms to relevant conditions.
- **100+ Verified Specialists & Schedules**: Pre-seeded with **106+ doctors** across 20 distinct medical specialties with **369+ appointment slots** across morning, afternoon, and evening shifts.
- **Real-Time Interactive Chat**: Dynamic messaging system connecting patients and doctors directly with active presence indicators and conversation history.
- **Appointment Management & PDF Export**: Instant appointment booking, slot cancellation, and printable PDF prescription receipts.
- **Multi-Role Portals**: Dedicated, secure portals for **Patients**, **Doctors**, and **System Administrators**.

---

## System Architecture & Portals

### 1. Patient Portal (`/patient/`)
- User registration, authentication, and personalized profile management.
- Multi-disease self-checkup tools (Heart Disease, Diabetes, Pneumonia X-Ray scan, General Symptoms).
- Doctor search engine filterable by Doctor Name, Specialty/Department, Clinic Location, or Disease/Condition.
- Appointment slot booking and appointment history with PDF export.
- Real-time chat with doctors.
- Feedback submission system.

### 2. Doctor Portal (`/doctor/`)
- Doctor dashboard with daily schedule and upcoming patient consultations.
- Appointment management and patient status tracking.
- Direct teleconsultation communication via live chat.
- Disease precautions and health advisory tools.

### 3. Roleadmin Portal (`/roleadmin/`)
- Global hospital analytics: total patients, verified doctors, symptom predictions, and feedback ratings.
- Doctor roster management: onboarding, credential editing, and removal.
- Patient record oversight and disease-to-specialist mapping configuration.

### 4. Live Chat System (`/chat/` & `/patient/chat/`)
- Real-time conversation exchange between patients and doctors.
- Contact presence indicators (Online / Offline status).
- Auto-scroll, message timestamps, and unread notification tracking.

---

## Quick Reference URLs

| Portal / Feature | URL |
| :--- | :--- |
| **Landing Page** | [http://127.0.0.1:8000/](http://127.0.0.1:8000/) |
| **Patient Portal** | [http://127.0.0.1:8000/patient/patient_login/](http://127.0.0.1:8000/patient/patient_login/) |
| **Doctor Portal** | [http://127.0.0.1:8000/doctor/doctor_login/](http://127.0.0.1:8000/doctor/doctor_login/) |
| **Roleadmin Dashboard** | [http://127.0.0.1:8000/roleadmin/roleadmin_login/](http://127.0.0.1:8000/roleadmin/roleadmin_login/) |
| **Live Chat Console** | [http://127.0.0.1:8000/patient/chat/](http://127.0.0.1:8000/patient/chat/) |
| **Django Administration** | [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) |

## Machine Learning & Deep Learning Models

| Model | File / Artifact | Architecture | Purpose |
| :--- | :--- | :--- | :--- |
| **Pneumonia Detection** | `datasets/model_check.json` + `datasets/model_check.h5` | Deep Convolutional Neural Network (CNN) | Predicts presence of Pneumonia from chest X-Ray scans |
| **X-Ray Image Validator** | `patient/image_block.py` | CNN Image Verification Pipeline | Rejects non-medical or invalid image uploads |
| **Heart Disease** | `datasets/pickle_model_heart.pkl` | Random Forest Classifier | Evaluates cardiovascular risk factors |
| **Diabetes** | `datasets/pickle_model_diabetes.pkl` | Supervised ML Classifier | Assesses type-2 diabetes probability |
| **General Disease** | `datasets/pickle_model_disease.pkl` | Multi-class Classification Tree | Diagnoses conditions from 130+ symptoms |

---

## Technology Stack

- **Backend**: Python 3.10+, Django 2.2 / Django REST Framework
- **Machine Learning**: TensorFlow / Keras 3, Scikit-Learn, NumPy, Pandas, Pillow
- **Frontend**: HTML5, CSS3, JavaScript, jQuery, Bootstrap, Materialize CSS
- **Database**: SQLite (Development) / PostgreSQL compatible
- **Document Generation**: WeasyPrint / ReportLab (PDF export)
- **Package Management**: UV / Pip

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher installed on your system.
- Git installed.

### 1. Clone the Repository
```bash
git clone https://github.com/dhanush342/E_smart_Health_Care_system.git
cd E_smart_Health_Care_system
```

### 2. Set Up Virtual Environment

**Using UV (Recommended):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
uv sync
```

**Using Standard Python venv:**
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Database Migrations & Setup
```bash
python manage.py migrate
```

*(Optional) Seed 100+ doctors, schedules, and disease mappings:*
```bash
python seed_doctors.py
```

### 4. Start the Application
```bash
python manage.py runserver
```
Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

---

## Medical Specialties Covered

The database includes certified medical specialists across 20 distinct departments:

1. **Cardiology** (Heart Diseases, Arrhythmia, Hypertension)
2. **Neurology** (Migraine, Stroke, Epilepsy)
3. **Pediatrics** (Childhood Healthcare, Pediatric Fevers)
4. **Orthopedics** (Bone Fractures, Arthritis, Joint Care)
5. **Dermatology** (Skin Allergies, Acne, Eczema)
6. **Oncology** (Tumors, Cancer Care)
7. **Gastroenterology** (GERD, Liver Health, Digestive Disorders)
8. **Pulmonology** (Pneumonia, Asthma, Respiratory Health)
9. **Nephrology** (Kidney Stones, Renal Care)
10. **Endocrinology** (Diabetes, Thyroid Disorders)
11. **Gynecology & Obstetrics** (Women's Health & Maternity)
12. **Ophthalmology** (Vision Care, Cataract, Glaucoma)
13. **ENT** (Ear, Nose & Throat Disorders)
14. **Psychiatry** (Mental Health, Anxiety, Depression)
15. **General Medicine** (Primary Care & Viral Fevers)
16. **Rheumatology** (Autoimmune & Joint Disorders)
17. **Urology** (Urinary Tract & Bladder Care)
18. **Infectious Disease** (Viral, Bacterial & Epidemic Care)
19. **Dental Surgery** (Oral Health & Dental Procedures)
20. **Radiology** (Diagnostic Imaging & Scan Reviews)

---

## Contact & Location

- **Address**: No. 1, Ramachandra Nagar, Porur, Chennai - 600116, Tamil Nadu, India
- **Email**: [dhanushnaginane@gmail.com](mailto:dhanushnaginane@gmail.com)
- **Phone**: +91 9490357006
- **LinkedIn**: [Dhanush Nagineni](https://www.linkedin.com/in/dhanush-nagineni/)

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
