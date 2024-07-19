from fpdf import FPDF

# Crear una clase que hereda de FPDF
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Reunión Bratex', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(10)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

# Crear el objeto PDF
pdf = PDF()
pdf.add_page()

# Leer el archivo .txt y agregarlo al PDF
with open('transcript.txt', 'r', encoding='utf-8') as file:
    content = file.read()
    pdf.chapter_body(content)

# Guardar el PDF
pdf.output('archivo.pdf')
