from fpdf import FPDF
import os


class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Lawgorithm Project Report", 0, 1, "C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, "Page " + str(self.page_no()) + "/{nb}", 0, 0, "C")


def create_pdf(input_file, output_file):
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line:
            pdf.ln(2)
            continue

        # Basic Markdown Parsing
        if line.startswith("# "):  # H1
            pdf.set_font("Arial", "B", 16)
            pdf.cell(
                0,
                10,
                line.replace("# ", "").encode("latin-1", "replace").decode("latin-1"),
                0,
                1,
                "L",
            )
            pdf.ln(2)
        elif line.startswith("## "):  # H2
            pdf.set_font("Arial", "B", 14)
            pdf.cell(
                0,
                10,
                line.replace("## ", "").encode("latin-1", "replace").decode("latin-1"),
                0,
                1,
                "L",
            )
            pdf.ln(2)
        elif line.startswith("### "):  # H3
            pdf.set_font("Arial", "B", 12)
            pdf.cell(
                0,
                10,
                line.replace("### ", "").encode("latin-1", "replace").decode("latin-1"),
                0,
                1,
                "L",
            )
            pdf.ln(1)
        elif line.startswith("#### "):  # H4
            pdf.set_font("Arial", "B", 11)
            pdf.cell(
                0,
                10,
                line.replace("#### ", "")
                .encode("latin-1", "replace")
                .decode("latin-1"),
                0,
                1,
                "L",
            )
        elif line.startswith("- ") or line.startswith("* "):  # Bullet
            pdf.set_font("Arial", "", 11)
            text = line[2:]
            pdf.cell(5)  # Indent
            pdf.multi_cell(
                0,
                6,
                chr(149) + " " + text.encode("latin-1", "replace").decode("latin-1"),
            )
        else:  # Normal Text
            pdf.set_font("Arial", "", 11)
            pdf.multi_cell(0, 6, line.encode("latin-1", "replace").decode("latin-1"))

    pdf.output(output_file, "F")
    print(f"PDF Generated Successfully: {output_file}")


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    md_path = os.path.join(base_dir, "Project_Report.md")
    pdf_path = os.path.join(base_dir, "Lawgorithm_Project_Report.pdf")

    if not os.path.exists(md_path):
        print(f"Error: Usage file not found at {md_path}")
    else:
        create_pdf(md_path, pdf_path)
