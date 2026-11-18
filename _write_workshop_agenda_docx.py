"""Write a simple landscape Word agenda matching workshop_agenda.md."""
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

OUT = Path(__file__).resolve().parent / "workshop_agenda.docx"

NAVY = RGBColor(0x1B, 0x3A, 0x4B)
TEAL = RGBColor(0x0F, 0x5C, 0x66)
GREY = RGBColor(0x44, 0x44, 0x44)


def set_run(run, size=11, bold=False, color=GREY, font="Calibri"):
    run.font.name = font
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font)
    run.font.size = Pt(size)
    run.bold = bold
    run.font.color.rgb = color


def shade(cell, hex_color: str) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def set_cell_text(cell, text, *, bold=False, size=10, color=GREY, center=False):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    set_run(run, size=size, bold=bold, color=color)


def add_table(doc, headers, rows, widths):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for i, w in enumerate(widths):
        for cell in table.columns[i].cells:
            cell.width = w
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        shade(cell, "0F5C66")
        set_cell_text(cell, h, bold=True, size=10, color=RGBColor(0xFF, 0xFF, 0xFF), center=True)
    for r_i, row in enumerate(rows):
        is_break = row[1] in {"—", "-"} or row[2] in {"Break", "Lunch", "Save your work", "Close"}
        for c_i, val in enumerate(row):
            cell = table.rows[r_i + 1].cells[c_i]
            if is_break:
                shade(cell, "EEF3F4")
            set_cell_text(
                cell,
                val,
                bold=(c_i == 2 and not is_break),
                size=10,
                color=NAVY if c_i == 2 else GREY,
            )
    return table


def heading(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run(text)
    set_run(run, size=16, bold=True, color=NAVY)


def body(doc, text, *, italic=False, size=11):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(8)
    run = p.add_run(text)
    set_run(run, size=size, color=GREY)
    run.italic = italic


def main() -> None:
    doc = Document()
    section = doc.sections[0]
    section.page_width = Cm(29.7)
    section.page_height = Cm(21.0)
    section.left_margin = Cm(1.4)
    section.right_margin = Cm(1.4)
    section.top_margin = Cm(1.2)
    section.bottom_margin = Cm(1.2)

    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.LEFT
    t.paragraph_format.space_after = Pt(2)
    r = t.add_run("Tier 1 workshop agenda")
    set_run(r, size=22, bold=True, color=NAVY)

    meta = doc.add_paragraph()
    meta.paragraph_format.space_after = Pt(6)
    r = meta.add_run(
        "9:00 AM–3:00 PM each day  ·  CivicDesk fiction only (no real ministry files)  ·  "
        "Written for people who need to judge AI at work, not write code."
    )
    set_run(r, size=11, color=TEAL)

    intro = doc.add_paragraph()
    intro.paragraph_format.space_after = Pt(8)
    r = intro.add_run(
        "Each block says what you will do, and why it matters. Instruction lives in the notebooks. This page is the running order."
    )
    set_run(r, size=11, color=GREY)

    headers = ["Time", "Item", "Title", "What you take away"]
    widths = [Cm(3.6), Cm(2.2), Cm(6.6), Cm(14.0)]

    heading(doc, "Day 1 — Start a small model and see what it actually does")
    body(
        doc,
        "By the end of the day you should know: this tool guesses the next words; it is not your database; and you can say what it would cost to keep it running.",
        italic=True,
    )
    add_table(
        doc,
        headers,
        [
            ["9:00–9:15 AM", "T1-00", "Opening and ground rules", "Real work files stay out of the chatbot. We agree that before anything else."],
            ["9:15–9:50 AM", "T1-01a", "Start the classroom models", "Get the box talking — or use a practice stand-in if it will not start."],
            ["9:50–10:30 AM", "T1-01", "First office question", "Send one made-up question and see a reply, so you know the setup works."],
            ["10:30–10:45 AM", "—", "Break", ""],
            ["10:45 AM–12:00 PM", "T1-02", "How it answers", "See that it is guessing the next bit of wording, not looking up your files."],
            ["12:00–12:45 PM", "—", "Lunch", ""],
            ["12:45–1:45 PM", "T1-03", "Score two small models", "Same test, two models: which is good enough, and who pays."],
            ["1:45–2:20 PM", "T1-04", "Your computer vs a company’s website", "Who holds the door, and what the licence actually allows."],
            ["2:20–2:55 PM", "T1-05", "Your job, on one page", "For your work: better wording, a filing lookup, fine-tuning, or no model at all."],
            ["2:55–3:00 PM", "—", "Save your work", ""],
        ],
        widths,
    )
    heading(doc, "Day 2 — Look it up before you guess")
    body(
        doc,
        "By the end of the day you should know: a clever instruction can still invent a rule; a quoted circular is safer; and finding a file is not the same as being allowed to see it.",
        italic=True,
    )
    add_table(
        doc,
        headers,
        [
            ["9:00–9:20 AM", "T1-06", "Put the idea in a bucket", "So we do not “AI” everything. Some jobs need a lookup, a database, or no model."],
            ["9:20–10:30 AM", "T1-07", "What may be searched", "Names, secrets, and case files stay out. Only approved pages go in."],
            ["10:30–10:45 AM", "—", "Break", ""],
            ["10:45 AM–12:00 PM", "T1-08", "Look up a page, then answer", "The reply should quote something you can point at — not a remembered rule."],
            ["", "T1-08b", "Extra if time: the same from a PDF", "A PDF is still just a file. It is not automatically a trusted source."],
            ["12:00–12:45 PM", "—", "Lunch", ""],
            ["12:45–1:45 PM", "T1-09", "Smart prompt vs looking it up", "A well-written instruction can still make up a circular. Lookup is how you get a quote."],
            ["1:45–2:20 PM", "T1-10", "Finding a file ≠ allowed to see it", "Search is not permission. The clerk and the records officer are not the same person."],
            ["2:20–2:55 PM", "T1-10b", "Quote it, or say you do not know", "The desk rule: point to the source, or stop. Do not guess."],
            ["2:55–3:00 PM", "—", "Save your work", ""],
        ],
        widths,
    )
    heading(doc, "Day 3 — Fine-tuning, and when a person must still decide")
    body(
        doc,
        "Fine-tuning means showing the model many labelled examples of one job. By the end of the day you should know: that can help a narrow task; it is not your filing cabinet; and hire, award, and password reset stay with a person.",
        italic=True,
    )
    add_table(
        doc,
        headers,
        [
            ["9:00–9:15 AM", "T1-11", "A fine-tuning job vs answers all day", "A one-off training run is a different bill from a chatbot that stays on."],
            ["9:15–10:30 AM", "T1-11", "See where a careful instruction still fails", "A good prompt is not enough. See what fine-tuning would actually teach — and what must never be taught."],
            ["10:30–10:45 AM", "—", "Break", ""],
            ["10:45 AM–12:00 PM", "T1-12", "Same test, with and without fine-tuning", "The small add-on only changes how it continues a sentence. It is not your records system."],
            ["12:00–12:45 PM", "—", "Lunch", ""],
            ["12:45–1:30 PM", "T1-12b", "If the fine-tune goes wrong", "Can we switch it off? Whose licence? Did private data sneak in?"],
            ["1:30–2:15 PM", "T1-13", "Writing a draft vs taking an action", "Drafting text is fine. Resetting a password or awarding a contract is not."],
            ["2:15–2:55 PM", "T1-14", "First safe next step — not a pilot", "One thing you can take back without going live. AI assists. People decide."],
            ["2:55–3:00 PM", "—", "Close", ""],
        ],
        widths,
    )
    doc.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
