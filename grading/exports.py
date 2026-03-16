import csv
import io
from datetime import date

from django.http import HttpResponse

try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph,
        Spacer, HRFlowable,
    )
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False



def export_grades_csv(students_qs, lecturer_user):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="siwes_grades_{date.today()}.csv"'
    )

    writer = csv.writer(response)
    writer.writerow([
        'Student Name', 'Matric Number', 'University', 'Faculty', 'Department',
        'Company Name', 'Industrial Supervisor', 'Internship Duration',
        'Start Date', 'End Date', 'Days Logged', 'Score', 'Grade',
        'Lecturer Comment', 'Date Graded',
    ])

    for student in students_qs:
        grade = getattr(student, 'grade_record', None)
        writer.writerow([
            student.full_name,
            student.matric_number,
            student.university.name,
            student.faculty.name,
            student.department.name,
            student.company_name,
            student.industrial_supervisor_name,
            student.get_internship_duration_display(),
            student.internship_start_date.strftime('%Y-%m-%d'),
            student.internship_end_date.strftime('%Y-%m-%d'),
            student.days_logged,
            grade.overall_score if grade else '',
            grade.letter_grade if grade else '',
            grade.lecturer_comment if grade else '',
            grade.graded_at.strftime('%Y-%m-%d') if grade else '',
        ])

    return response



NAVY  = colors.HexColor('#0a2240')
TEAL  = colors.HexColor('#0d9488')
LIGHT = colors.HexColor('#f1f5f9')
WHITE = colors.white
GREY  = colors.HexColor('#64748b')


def export_grades_pdf(students_qs, lecturer_user):
    if not HAS_REPORTLAB:
        return HttpResponse(
            'PDF export requires the reportlab library. '
            'Install it with: pip install reportlab',
            status=501,
            content_type='text/plain',
        )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title='SIWES Grade Summary',
        author=lecturer_user.get_full_name(),
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'SIWESTitle',
        parent=styles['Heading1'],
        textColor=NAVY,
        fontSize=16,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        'SIWESSub',
        parent=styles['Normal'],
        textColor=GREY,
        fontSize=9,
    )
    cell_style = ParagraphStyle(
        'Cell',
        parent=styles['Normal'],
        fontSize=8,
        leading=10,
    )

    story = []

    # Header
    lp = getattr(lecturer_user, 'lecturer_profile', None)
    dept_info = f'{lp.department.name} · {lp.faculty.name} · {lp.university.name}' if lp else ''
    story.append(Paragraph('SIWES Logbook Manager — Grade Summary Report', title_style))
    story.append(Paragraph(
        f'Lecturer: {lecturer_user.get_full_name()} &nbsp;|&nbsp; {dept_info} &nbsp;|&nbsp; Generated: {date.today()}',
        subtitle_style,
    ))
    story.append(HRFlowable(width='100%', color=TEAL, thickness=1.5, spaceAfter=10))

    # Table header
    headers = [
        'Student Name', 'Matric No.', 'Faculty', 'Company',
        'Duration', 'Start', 'End', 'Days\nLogged',
        'Score', 'Grade', 'Comment', 'Graded On',
    ]

    data = [headers]
    for student in students_qs:
        grade = getattr(student, 'grade_record', None)
        data.append([
            Paragraph(student.full_name, cell_style),
            student.matric_number,
            student.faculty.name,
            Paragraph(student.company_name, cell_style),
            student.get_internship_duration_display(),
            str(student.internship_start_date),
            str(student.internship_end_date),
            str(student.days_logged),
            str(grade.overall_score) if grade else '—',
            grade.letter_grade if grade else '—',
            Paragraph(grade.lecturer_comment[:120] if grade and grade.lecturer_comment else '—', cell_style),
            grade.graded_at.strftime('%Y-%m-%d') if grade else '—',
        ])

    col_widths = [3.5*cm, 2.2*cm, 2.5*cm, 3*cm, 1.6*cm, 1.8*cm, 1.8*cm, 1.2*cm, 1.2*cm, 1.2*cm, 5*cm, 2*cm]

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND',   (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR',    (0, 0), (-1, 0), WHITE),
        ('FONTNAME',     (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',     (0, 0), (-1, 0), 8),
        ('TOPPADDING',   (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING',(0, 0), (-1, 0), 8),

        # Data rows
        ('FONTNAME',     (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',     (0, 1), (-1, -1), 7.5),
        ('TOPPADDING',   (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING',(0, 1), (-1, -1), 5),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [WHITE, LIGHT]),

        # Borders
        ('GRID',         (0, 0), (-1, -1), 0.3, colors.HexColor('#cbd5e1')),
        ('LINEABOVE',    (0, 1), (-1, 1), 1, TEAL),
        
        # Grade column highlight
        ('TEXTCOLOR',    (9, 1), (9, -1), TEAL),
        ('FONTNAME',     (9, 1), (9, -1), 'Helvetica-Bold'),
        ('ALIGN',        (7, 0), (9, -1), 'CENTER'),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    story.append(table)
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        f'Total students: {len(data) - 1}  |  Report generated by SIWES Logbook Manager',
        subtitle_style,
    ))

    doc.build(story)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="siwes_grades_{date.today()}.pdf"'
    )
    return response
