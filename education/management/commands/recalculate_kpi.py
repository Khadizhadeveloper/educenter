from django.core.management.base import BaseCommand
from education.models import Student, Mentor
from education.models.kpi import StudentKPI, MentorKPI


class Command(BaseCommand):
    help = 'Пересчитать KPI для всех учеников и тренеров'

    def handle(self, *args, **kwargs):
        students = Student.objects.filter(is_active=True)
        self.stdout.write(f'Пересчёт KPI для {students.count()} учеников...')
        for student in students:
            kpi, _ = StudentKPI.objects.get_or_create(student=student)
            kpi.recalculate()
            self.stdout.write(f'  {student}: {kpi.total_kpi}%')

        mentors = Mentor.objects.all()
        self.stdout.write(f'Пересчёт KPI для {mentors.count()} тренеров...')
        for mentor in mentors:
            kpi, _ = MentorKPI.objects.get_or_create(mentor=mentor)
            kpi.recalculate()
            self.stdout.write(f'  {mentor}: {kpi.total_kpi}%')

        self.stdout.write(self.style.SUCCESS('KPI успешно пересчитаны.'))
