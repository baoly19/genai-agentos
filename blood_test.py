from fpdf import FPDF
from datetime import date

# Sample data for a diabetic patient with some abnormal values
patient_id = "P123456789"
test_results = {
    "Fasting Blood Glucose (mg/dL)": 160,  # High (normal: <100)
    "HbA1c (%)": 8.5,                     # High (normal: <5.7)
    "Total Cholesterol (mg/dL)": 240,     # High (normal: <200)
    "LDL Cholesterol (mg/dL)": 160,       # High (normal: <100)
    "HDL Cholesterol (mg/dL)": 35,        # Low (normal: >40 for men)
    "Triglycerides (mg/dL)": 210,         # High (normal: <150)
    "Creatinine (mg/dL)": 1.1,            # Normal (approx. 0.6–1.3)
    "Blood Urea Nitrogen (BUN) (mg/dL)": 18,  # Normal (7–20)
}

# Create a PDF document
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", "B", 16)
pdf.cell(200, 10, "Blood Test Report", ln=True, align="C")

pdf.set_font("Arial", "", 12)
pdf.cell(200, 10, f"Patient ID: {patient_id}", ln=True)
pdf.cell(200, 10, f"Date: {date.today().strftime('%Y-%m-%d')}", ln=True)

pdf.ln(10)
pdf.set_font("Arial", "B", 12)
pdf.cell(120, 10, "Test", border=1)
pdf.cell(60, 10, "Result", border=1, ln=True)

pdf.set_font("Arial", "", 12)
for test, result in test_results.items():
    pdf.cell(120, 10, test, border=1)
    pdf.cell(60, 10, str(result), border=1, ln=True)

# Save the PDF
output_path = "diabetic_blood_test_report.pdf"
pdf.output(output_path)
output_path
