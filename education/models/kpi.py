from django.db import models
from django.db.models import Avg, Count, Q
from django.utils import timezone
from .student import Student
from .mentor import Mentor


class StudentKPI(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='kpi')

    attendance_score     = models.FloatField(default=0.0)
    homework_score       = models.FloatField(default=0.0)
    grade_score          = models.FloatField(default=0.0)
    test_score           = models.FloatField(default=0.0)
    total_kpi            = models.FloatField(default=0.0)

    # Raw counters (handy for UI)
    total_lessons        = models.IntegerField(default=0)
    attended_lessons     = models.IntegerField(default=0)
    total_homeworks      = models.IntegerField(default=0)
    submitted_homeworks  = models.IntegerField(default=0)
    grades_count         = models.IntegerField(default=0)
    tests_taken          = models.IntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'KPI ученика'
        verbose_name_plural = 'KPI учеников'

    # ------------------------------------------------------------------
    def recalculate(self):
        from .attendance import Attendance
        from .homework import Homework, HomeworkSubmission
        from .grade import Grade
        from .enrollment import Enrollment
        from .lesson import Lesson

        today      = timezone.now().date()
        course_ids = list(
            Enrollment.objects.filter(student=self.student, is_active=True)
                              .values_list('course_id', flat=True)
        )

        # ── 1. Attendance ──────────────────────────────────────────────
        past_lessons = Lesson.objects.filter(
            course_id__in=course_ids, date__lte=today, is_cancelled=False
        )
        total_lessons = past_lessons.count()

        if total_lessons > 0:
            agg = Attendance.objects.filter(
                student=self.student, lesson__in=past_lessons
            ).aggregate(
                present=Count('id', filter=Q(status='present')),
                late=Count('id', filter=Q(status='late')),
                excused=Count('id', filter=Q(status='excused')),
            )
            effective = agg['present'] + agg['late'] * 0.5 + agg['excused'] * 0.8
            attendance_score = min(100.0, effective / total_lessons * 100)
            attended_count   = agg['present'] + agg['late'] + agg['excused']
        else:
            attendance_score = None
            attended_count   = 0

        # ── 2. Homework ────────────────────────────────────────────────
        due_hw = Homework.objects.filter(
            lesson__course_id__in=course_ids, due_date__lte=timezone.now()
        )
        total_hw = due_hw.count()

        if total_hw > 0:
            submitted = HomeworkSubmission.objects.filter(
                student=self.student, homework__in=due_hw
            ).count()
            submission_rate = submitted / total_hw * 100

            graded_qs = HomeworkSubmission.objects.filter(
                student=self.student, homework__in=due_hw,
                status='checked', grade__isnull=False
            )
            if graded_qs.exists():
                avg_hw_grade = graded_qs.aggregate(avg=Avg('grade'))['avg'] or 0
                grade_factor = min(100.0, avg_hw_grade / 10 * 100)
                homework_score = submission_rate * 0.7 + grade_factor * 0.3
            else:
                homework_score = submission_rate
        else:
            homework_score = None
            submitted      = 0

        # ── 3. Grades ──────────────────────────────────────────────────
        grades_qs = Grade.objects.filter(student=self.student, course_id__in=course_ids)
        grades_count = grades_qs.count()

        if grades_count > 0:
            avg_grade  = grades_qs.aggregate(avg=Avg('grade'))['avg'] or 0
            grade_score = min(100.0, avg_grade / 10 * 100)
        else:
            grade_score = None

        # ── 4. Tests ───────────────────────────────────────────────────
        from .test_system import TestAttempt, Topic
        finished_attempts = TestAttempt.objects.filter(
            student=self.student,
            finished_at__isnull=False,
            test__topic__course_id__in=course_ids,
        )
        tests_taken = finished_attempts.values('test_id').distinct().count()

        if tests_taken > 0:
            # Best score per test, then average
            best_scores = []
            for test_id in finished_attempts.values_list('test_id', flat=True).distinct():
                best = finished_attempts.filter(test_id=test_id).order_by('-score').first()
                if best:
                    best_scores.append(best.score)
            test_score = round(sum(best_scores) / len(best_scores), 1) if best_scores else 0
        else:
            test_score = None

        # ── Weighted total (exclude components with no data) ───────────
        # Weights: attendance 35%, homework 30%, grade 15%, test 20%
        components = [
            (attendance_score, 0.35),
            (homework_score,   0.30),
            (grade_score,      0.15),
            (test_score,       0.20),
        ]
        total_weight = sum(w for s, w in components if s is not None)
        if total_weight > 0:
            total_kpi = sum(s * w for s, w in components if s is not None) / total_weight
        else:
            total_kpi = 0.0

        self.attendance_score    = round(attendance_score or 0, 1)
        self.homework_score      = round(homework_score   or 0, 1)
        self.grade_score         = round(grade_score      or 0, 1)
        self.test_score          = round(test_score       or 0, 1)
        self.total_kpi           = round(total_kpi,             1)
        self.total_lessons       = total_lessons
        self.attended_lessons    = attended_count
        self.total_homeworks     = total_hw
        self.submitted_homeworks = submitted
        self.grades_count        = grades_count
        self.tests_taken         = tests_taken
        self.save()

    def kpi_label(self):
        if self.total_kpi >= 85:
            return 'Отлично'
        if self.total_kpi >= 70:
            return 'Хорошо'
        if self.total_kpi >= 50:
            return 'Удовлетворительно'
        return 'Требует внимания'

    def kpi_color(self):
        if self.total_kpi >= 85:
            return 'success'
        if self.total_kpi >= 70:
            return 'info'
        if self.total_kpi >= 50:
            return 'warning'
        return 'danger'

    def __str__(self):
        return f"KPI {self.student}: {self.total_kpi}%"


# ──────────────────────────────────────────────────────────────────────────────

class MentorKPI(models.Model):
    mentor = models.OneToOneField(Mentor, on_delete=models.CASCADE, related_name='kpi')

    avg_student_kpi          = models.FloatField(default=0.0)
    avg_attendance           = models.FloatField(default=0.0)
    homework_completion_rate = models.FloatField(default=0.0)
    total_kpi                = models.FloatField(default=0.0)

    students_count = models.IntegerField(default=0)
    courses_count  = models.IntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = 'KPI тренера'
        verbose_name_plural = 'KPI тренеров'

    # ------------------------------------------------------------------
    def recalculate(self):
        from .course import Course
        from .enrollment import Enrollment
        from .attendance import Attendance
        from .homework import Homework, HomeworkSubmission
        from .lesson import Lesson

        today   = timezone.now().date()
        courses = Course.objects.filter(mentor=self.mentor, is_active=True)

        if not courses.exists():
            self.avg_student_kpi = self.avg_attendance = 0
            self.homework_completion_rate = self.total_kpi = 0
            self.students_count = self.courses_count = 0
            self.save()
            return

        self.courses_count = courses.count()

        # ── 1. Average Student KPI ─────────────────────────────────────
        student_ids = list(
            Enrollment.objects.filter(course__in=courses, is_active=True)
                              .values_list('student_id', flat=True).distinct()
        )
        self.students_count = len(student_ids)

        student_kpis = StudentKPI.objects.filter(student_id__in=student_ids)
        if student_kpis.exists():
            avg_student_kpi = student_kpis.aggregate(avg=Avg('total_kpi'))['avg'] or 0
        else:
            avg_student_kpi = None

        # ── 2. Average Attendance across groups ────────────────────────
        past_lessons = Lesson.objects.filter(
            course__in=courses, date__lte=today, is_cancelled=False
        )
        total_slots   = 0
        attended_slots = 0
        for lesson in past_lessons:
            enrolled = Enrollment.objects.filter(
                course=lesson.course, is_active=True
            ).count()
            if enrolled:
                present = Attendance.objects.filter(
                    lesson=lesson,
                    status__in=['present', 'late', 'excused']
                ).count()
                total_slots   += enrolled
                attended_slots += present

        avg_attendance = (attended_slots / total_slots * 100) if total_slots > 0 else None

        # ── 3. Homework Completion Rate ────────────────────────────────
        due_hw = Homework.objects.filter(
            lesson__course__in=courses, due_date__lte=timezone.now()
        )
        total_hw_slots = 0
        submitted_slots = 0
        for hw in due_hw:
            enrolled = Enrollment.objects.filter(
                course=hw.lesson.course, is_active=True
            ).count()
            submitted = HomeworkSubmission.objects.filter(homework=hw).count()
            total_hw_slots  += enrolled
            submitted_slots += submitted

        homework_completion_rate = (
            min(100.0, submitted_slots / total_hw_slots * 100)
            if total_hw_slots > 0 else None
        )

        # ── Weighted total ─────────────────────────────────────────────
        components = [
            (avg_student_kpi,         0.40),
            (avg_attendance,          0.30),
            (homework_completion_rate, 0.30),
        ]
        total_weight = sum(w for s, w in components if s is not None)
        if total_weight > 0:
            total_kpi = sum(s * w for s, w in components if s is not None) / total_weight
        else:
            total_kpi = 0.0

        self.avg_student_kpi          = round(avg_student_kpi          or 0, 1)
        self.avg_attendance           = round(avg_attendance            or 0, 1)
        self.homework_completion_rate = round(homework_completion_rate  or 0, 1)
        self.total_kpi                = round(total_kpi,                    1)
        self.save()

    def kpi_label(self):
        if self.total_kpi >= 85:
            return 'Отлично'
        if self.total_kpi >= 70:
            return 'Хорошо'
        if self.total_kpi >= 50:
            return 'Удовлетворительно'
        return 'Требует внимания'

    def kpi_color(self):
        if self.total_kpi >= 85:
            return 'success'
        if self.total_kpi >= 70:
            return 'info'
        if self.total_kpi >= 50:
            return 'warning'
        return 'danger'

    def __str__(self):
        return f"KPI {self.mentor}: {self.total_kpi}%"
