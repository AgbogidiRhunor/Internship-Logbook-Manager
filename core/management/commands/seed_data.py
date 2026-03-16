"""
core/management/commands/seed_data.py
Seeds initial Nigerian university data.
Run: python manage.py seed_data
All seeded data remains fully editable through the admin interface.
"""
from django.core.management.base import BaseCommand
from institutions.models import University, Faculty, Department


SEED_DATA = {
    "University of Lagos": {
        "state": "Lagos",
        "abbr": "UNILAG",
        "faculties": {
            "Faculty of Engineering": [
                "Civil Engineering",
                "Electrical/Electronics Engineering",
                "Mechanical Engineering",
                "Systems Engineering",
                "Chemical Engineering",
                "Computer Engineering",
            ],
            "Faculty of Science": [
                "Computer Science",
                "Mathematics",
                "Physics",
                "Chemistry",
                "Biochemistry",
                "Microbiology",
                "Statistics",
            ],
            "Faculty of Social Sciences": [
                "Economics",
                "Political Science",
                "Sociology",
                "Mass Communication",
                "Psychology",
            ],
            "Faculty of Management Sciences": [
                "Accounting",
                "Business Administration",
                "Finance",
                "Insurance",
                "Actuarial Science",
            ],
            "Faculty of Law": [
                "Public and International Law",
                "Private and Business Law",
                "Jurisprudence and International Law",
            ],
            "Faculty of Arts": [
                "English",
                "History and Strategic Studies",
                "Philosophy",
                "Linguistics",
                "European Languages",
            ],
            "Faculty of Education": [
                "Educational Administration",
                "Educational Technology",
                "Guidance and Counselling",
                "Human Kinetics",
            ],
            "Faculty of Environmental Sciences": [
                "Architecture",
                "Urban and Regional Planning",
                "Estate Management",
                "Building",
                "Surveying and Geoinformatics",
            ],
        },
    },
    "University of Nigeria, Nsukka": {
        "state": "Enugu",
        "abbr": "UNN",
        "faculties": {
            "Faculty of Engineering": [
                "Civil Engineering",
                "Electrical Engineering",
                "Electronic Engineering",
                "Mechanical Engineering",
                "Agricultural and Bioresource Engineering",
                "Chemical Engineering",
                "Computer Engineering",
                "Metallurgical and Materials Engineering",
            ],
            "Faculty of Physical Sciences": [
                "Computer Science",
                "Mathematics",
                "Physics and Astronomy",
                "Chemistry",
                "Statistics",
            ],
            "Faculty of Social Sciences": [
                "Economics",
                "Political Science",
                "Sociology and Anthropology",
                "Mass Communication",
                "Psychology",
            ],
            "Faculty of Management Sciences": [
                "Accountancy",
                "Business Administration",
                "Banking and Finance",
                "Marketing",
                "Public Administration and Local Government",
            ],
            "Faculty of Law": [
                "Private Law",
                "Public Law and Jurisprudence",
            ],
            "Faculty of Agriculture": [
                "Animal Science",
                "Crop Science",
                "Food Science and Technology",
                "Soil Science",
                "Agricultural Economics",
            ],
            "Faculty of Veterinary Medicine": [
                "Veterinary Anatomy",
                "Veterinary Physiology",
                "Veterinary Surgery",
                "Veterinary Medicine",
            ],
            "Faculty of Education": [
                "Science Education",
                "Arts Education",
                "Educational Foundations",
                "Vocational Teacher Education",
            ],
            "Faculty of Environmental Studies": [
                "Architecture",
                "Urban and Regional Planning",
                "Estate Management",
                "Fine and Applied Arts",
            ],
            "Faculty of Pharmaceutical Sciences": [
                "Clinical Pharmacy and Pharmacy Management",
                "Pharmaceutical and Medicinal Chemistry",
                "Pharmaceutics and Pharmaceutical Technology",
                "Pharmacognosy and Environmental Medicine",
            ],
        },
    },
    "Obafemi Awolowo University": {
        "state": "Osun",
        "abbr": "OAU",
        "faculties": {
            "Faculty of Technology": [
                "Civil Engineering",
                "Electrical and Electronics Engineering",
                "Mechanical Engineering",
                "Chemical Engineering",
                "Computer Science and Engineering",
                "Agricultural and Environmental Engineering",
            ],
            "Faculty of Science": [
                "Computer Science",
                "Mathematics",
                "Physics and Engineering Physics",
                "Chemistry",
                "Zoology",
                "Botany",
                "Microbiology",
                "Biochemistry",
            ],
            "Faculty of Social Sciences": [
                "Economics",
                "Political Science",
                "Sociology and Anthropology",
                "Mass Communication",
                "Psychology",
                "Demography and Social Statistics",
            ],
            "Faculty of Administration": [
                "Accounting",
                "Business Administration",
                "Finance",
                "Public Administration",
            ],
            "Faculty of Law": [
                "Public Law",
                "Private Law",
                "International Law",
            ],
            "Faculty of Education": [
                "Teacher Education",
                "Curriculum Studies",
                "Educational Management",
                "Human Kinetics and Health Education",
            ],
            "Faculty of Environmental Design and Management": [
                "Architecture",
                "Urban and Regional Planning",
                "Estate Management",
                "Building",
            ],
            "Faculty of Pharmacy": [
                "Clinical Pharmacy",
                "Pharmaceutical Chemistry",
                "Pharmaceutics",
                "Pharmacognosy",
            ],
        },
    },
    "Ahmadu Bello University": {
        "state": "Kaduna",
        "abbr": "ABU",
        "faculties": {
            "Faculty of Engineering": [
                "Civil Engineering",
                "Electrical Engineering",
                "Mechanical Engineering",
                "Chemical Engineering",
                "Agricultural Engineering",
                "Computer Engineering",
                "Water Resources and Environmental Engineering",
            ],
            "Faculty of Science": [
                "Computer Science",
                "Mathematics",
                "Physics",
                "Chemistry",
                "Biological Sciences",
                "Statistics",
            ],
            "Faculty of Social Sciences": [
                "Economics",
                "Political Science",
                "Sociology",
                "Mass Communication",
                "Geography",
            ],
            "Faculty of Administration": [
                "Accounting",
                "Business Administration",
                "Finance",
                "Public Administration",
            ],
            "Faculty of Law": [
                "Commercial Law",
                "Constitutional Law and Jurisprudence",
                "International Law",
                "Private Law",
            ],
            "Faculty of Agriculture": [
                "Agronomy",
                "Animal Science",
                "Agricultural Economics and Rural Sociology",
                "Crop Protection",
                "Soil Science",
                "Food Science and Technology",
            ],
            "Faculty of Veterinary Medicine": [
                "Veterinary Anatomy",
                "Veterinary Medicine",
                "Veterinary Surgery",
            ],
            "Faculty of Education": [
                "Education Administration",
                "Education Arts",
                "Education Science",
                "Physical and Health Education",
            ],
            "Faculty of Environmental Design": [
                "Architecture",
                "Building",
                "Estate Management",
                "Land Surveying",
                "Urban and Regional Planning",
            ],
        },
    },
    "University of Ibadan": {
        "state": "Oyo",
        "abbr": "UI",
        "faculties": {
            "Faculty of Technology": [
                "Civil Engineering",
                "Electrical and Electronics Engineering",
                "Mechanical Engineering",
                "Chemical Engineering",
                "Computer Engineering",
                "Petroleum Engineering",
            ],
            "Faculty of Science": [
                "Computer Science",
                "Mathematics",
                "Physics",
                "Chemistry",
                "Zoology",
                "Botany",
                "Microbiology",
                "Biochemistry",
                "Statistics",
            ],
            "Faculty of Social Sciences": [
                "Economics",
                "Political Science",
                "Sociology",
                "Psychology",
            ],
            "Faculty of the Social and Management Sciences": [
                "Accounting",
                "Business Administration",
                "Human Resource Management",
            ],
            "Faculty of Law": [
                "Jurisprudence",
                "Private Law",
                "Public Law",
            ],
            "Faculty of Agriculture and Forestry": [
                "Agronomy",
                "Animal Science",
                "Food Technology",
                "Forest Resources Management",
                "Wildlife and Ecotourism Management",
                "Agricultural Economics",
            ],
            "Faculty of Veterinary Medicine": [
                "Veterinary Anatomy",
                "Veterinary Physiology, Biochemistry and Pharmacology",
                "Veterinary Public Health and Preventive Medicine",
            ],
            "Faculty of Education": [
                "Guidance and Counselling",
                "Human Kinetics and Health Education",
                "Teacher Education",
                "Institute of Education",
            ],
            "Faculty of the Arts": [
                "Communication and Language Arts",
                "English",
                "History",
                "Linguistics and African Languages",
                "Philosophy",
                "Theatre Arts",
            ],
            "Faculty of Public Health": [
                "Epidemiology and Medical Statistics",
                "Health Promotion and Education",
                "Environmental Health Sciences",
                "Community Medicine",
            ],
            "Faculty of Pharmacy": [
                "Clinical Pharmacy and Pharmacy Administration",
                "Pharmaceutical Chemistry",
                "Pharmaceutics and Industrial Pharmacy",
                "Pharmacognosy",
                "Pharmacology and Toxicology",
            ],
        },
    },
}


class Command(BaseCommand):
    help = 'Seeds initial Nigerian university, faculty, and department data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing seed data before seeding (dangerous in production).',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing institution data...'))
            Department.objects.all().delete()
            Faculty.objects.all().delete()
            University.objects.all().delete()

        created_unis = 0
        created_facs = 0
        created_depts = 0

        for uni_name, uni_data in SEED_DATA.items():
            uni, created = University.objects.get_or_create(
                name=uni_name,
                defaults={
                    'abbreviation': uni_data['abbr'],
                    'state': uni_data['state'],
                    'is_active': True,
                },
            )
            if created:
                created_unis += 1
                self.stdout.write(f'  ✓ University: {uni_name}')

            for fac_name, dept_list in uni_data['faculties'].items():
                fac, fac_created = Faculty.objects.get_or_create(
                    university=uni,
                    name=fac_name,
                    defaults={'is_active': True},
                )
                if fac_created:
                    created_facs += 1

                for dept_name in dept_list:
                    _, dept_created = Department.objects.get_or_create(
                        faculty=fac,
                        name=dept_name,
                        defaults={'is_active': True},
                    )
                    if dept_created:
                        created_depts += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nSeed complete: {created_unis} universities, '
            f'{created_facs} faculties, {created_depts} departments created.'
        ))
        self.stdout.write(
            'All data is fully editable through the Django admin at /admin/'
        )
