import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QComboBox,
    QLineEdit, QFormLayout, QPushButton, QMessageBox, QInputDialog
)
from PyQt6.QtGui import QFont
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

class DesignChecker(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Osdag FOSSE - Custom LaTeX File Generation")
        self.widgets = {}
        self.design_checked = False
        self.results = "Haven't been checked yet"

        self.input = {
            "Axial Load (kN)": ["Custom Input (Typical: 50 - 500 kN)"],
            "Length (mm)": ["Custom Input (Typical: 500 - 5000 mm)"],
            "Section Profiles": ["Angles", "Channels", "Beams", "Pipes", "RHS", "CHS"],
            "Section Size": ["40 x 40 x 5", "50 x 50 x 6", "60 x 60 x 6", "75 x 75 x 8", "100 x 100 x 10"],
            "Material": ["E 250", "E 300", "E 350", "E 410"],
            "Ultimate Strength, Fu (MPa)": ["410", "450", "500", "550", "600"],
            "Yield Strength, Fy (MPa)": ["250", "300", "350", "410", "450", "500"],
        }

        self.bolt = {
            "Number of Bolts": ["Custom Input (Typical: 2 - 20)"],
            "Bolt Diameter (mm)": ["8", "10", "12", "16", "20"],
            "Bolt Property Class": ["4.6", "5.6", "8.8", "10.9"],
            "Bolt Type": ["Bearing Bolt", "Friction Grip Bolt"],
            "Hole Type": ["Standard", "Oversized", "Slotted", "Long Slotted"],
        }

        self.detail = {
            "Edge Preparation": ["Sheared Cut", "Machine Cut", "Saw Cut"],
            "Corrosive Influence": ["Yes", "No"],
        }

        self.plate = {
            "Thickness (mm)": ["Custom Input (Typical: 8 - 120 mm)"],
            "Plate Material": ["E 250", "E 300", "E 350", "E 410"],
        }

        layout = QVBoxLayout()

        self.title1 = QLabel("General Input Parameters: ")
        layout.addWidget(self.title1)
        layout.addLayout(self.create_form_layout(self.input))

        self.title2 = QLabel("Bolt Details - Input and Design Preference: ")
        layout.addWidget(self.title2)
        layout.addLayout(self.create_form_layout(self.bolt))

        self.title3 = QLabel("Detailing - Design Preference: ")
        layout.addWidget(self.title3)
        layout.addLayout(self.create_form_layout(self.detail))

        self.title4 = QLabel("Plate Details - Input and Design Preference:")
        layout.addWidget(self.title4)
        layout.addLayout(self.create_form_layout(self.plate))

        self.title5 = QLabel("Preview of Selected Parameters: ")
        layout.addWidget(self.title5)

        for label in [self.title1, self.title2, self.title3, self.title4, self.title5]:
            label.setProperty("class", "title")

        self.check_button = QPushButton("Check Design")
        self.check_button.clicked.connect(self.check_design)
        layout.addWidget(self.check_button)

        self.preview_button = QPushButton("Preview")
        self.preview_button.clicked.connect(self.show_preview)
        layout.addWidget(self.preview_button)

        self.setLayout(layout)

    def create_form_layout(self, data_dict):
        form_layout = QFormLayout()
        for category, values in data_dict.items():
            if "Custom Input" in values[0]:
                widget = QLineEdit()
            else:
                widget = QComboBox()
                widget.addItem("Select")
                widget.addItems(values)

            self.widgets[category] = widget
            form_layout.addRow(QLabel(category + ":"), widget)
        return form_layout

    def check_design(self):
        try:
            d0_text = self.widgets["Bolt Diameter (mm)"].currentText()
            bolts_text = self.widgets["Number of Bolts"].text().strip()
            length_text = self.widgets["Length (mm)"].text().strip()
            fy_text = self.widgets["Yield Strength, Fy (MPa)"].currentText()

            if not bolts_text or not length_text:
                raise ValueError("Missing input")

            d0 = int(d0_text)
            rl = int(bolts_text)
            length = int(length_text)
            fy = int(fy_text)

            emin = 1.5 * d0
            edge_pass = "Pass" if emin < 15 else "Fail"

            e = 15
            g = 20
            depth = 2 * e + (rl - 1) * g
            spacing_pass = "Pass" if depth <= 29.5 else "Fail"

            slenderness = length / 7.8
            slenderness_pass = "Pass" if slenderness <= 400 else "Fail"

            tdg = (381.0 * fy) / 1100
            tension_pass = "Pass" if tdg >= 86.59 else "Fail"

            self.results = f"""
            Edge Distance Check: {edge_pass}
            Spacing Check: {spacing_pass}
            Slenderness Check: {slenderness_pass}
            Tension Member Check: {tension_pass}
            """
            self.design_checked = True
            QMessageBox.information(self, "Design Check Results", self.results)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter valid values for Bolt diameter, Number of bolts, Length, and Yield strength.")

    def show_preview(self):
        preview_text = "Selected Design Parameters:\n"
        for category, widget in self.widgets.items():
            value = widget.text().strip() if isinstance(widget, QLineEdit) else widget.currentText().strip()
            if value and value != "Select":
                preview_text += f"{category}: {value}\n"
        preview_text += "\nDesign Check Results:\n" + (self.results if self.design_checked else "Haven't been checked yet")

        reply = QMessageBox.question(
            self,
            "Preview",
            preview_text + "\n\nDo you want to generate a PDF?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.generate_pdf(preview_text)

    def generate_pdf(self, text):
        filename, ok = QInputDialog.getText(self, "Save PDF", "Enter a filename (without .pdf):")

        if ok and filename.strip():
            pdf_filename = filename.strip() + ".pdf"
            c = canvas.Canvas(pdf_filename, pagesize=A4)
            y_position = 800

            for line in text.split("\n"):
                line = line.strip()

                if "Selected Design Parameters:" in line or "Design Check Results:" in line:
                    c.setFont("Helvetica-Bold", 14)
                else:
                    c.setFont("Helvetica", 12)

                c.drawString(50, y_position, line)
                y_position -= 20

                if "Selected Design Parameters:" in line or "Design Check Results:" in line:
                    y_position -= 5

            c.save()
            QMessageBox.information(self, "PDF Generated", f"PDF saved as {pdf_filename}")
        else:
            QMessageBox.information(self, "Canceled", "PDF generation was canceled.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    with open("style.qss", "r") as file:
        app.setStyleSheet(file.read())
    window = DesignChecker()
    window.show()
    sys.exit(app.exec())
