from django.db import models
from django.utils import timezone
from .course import Course
from .student import Student


class Topic(models.Model):
    course      = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='topics')
    title       = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order       = models.PositiveIntegerField(default=0)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Тема'
        verbose_name_plural = 'Темы'
        ordering            = ['order', 'created_at']

    def __str__(self):
        return f"{self.course.name} — {self.title}"

    def active_tests(self):
        return self.tests.filter(is_active=True)


class Test(models.Model):
    topic               = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='tests')
    title               = models.CharField(max_length=200)
    description         = models.TextField(blank=True)
    time_limit_minutes  = models.PositiveIntegerField(default=0, help_text='0 — без ограничения')
    passing_score       = models.PositiveIntegerField(default=60, help_text='Минимальный % для зачёта')
    max_attempts        = models.PositiveIntegerField(default=0, help_text='0 — неограниченно')
    is_active           = models.BooleanField(default=True)
    created_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Тест'
        verbose_name_plural = 'Тесты'

    def __str__(self):
        return f"{self.topic.title} — {self.title}"

    def questions_count(self):
        return self.questions.count()

    def total_points(self):
        return sum(q.points for q in self.questions.all())


class Question(models.Model):
    TYPE_SINGLE   = 'single'
    TYPE_MULTIPLE = 'multiple'
    TYPE_CHOICES  = [
        (TYPE_SINGLE,   'Один правильный ответ'),
        (TYPE_MULTIPLE, 'Несколько правильных ответов'),
    ]

    test          = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions')
    text          = models.TextField()
    question_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_SINGLE)
    order         = models.PositiveIntegerField(default=0)
    points        = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name        = 'Вопрос'
        verbose_name_plural = 'Вопросы'
        ordering            = ['order', 'id']

    def __str__(self):
        return f"[{self.test.title}] {self.text[:60]}"

    def correct_answers(self):
        return self.answers.filter(is_correct=True)


class Answer(models.Model):
    question   = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text       = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order      = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name        = 'Ответ'
        verbose_name_plural = 'Ответы'
        ordering            = ['order', 'id']

    def __str__(self):
        return f"{'✓' if self.is_correct else '✗'} {self.text[:60]}"


class TestAttempt(models.Model):
    test          = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='attempts')
    student       = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='test_attempts')
    started_at    = models.DateTimeField(auto_now_add=True)
    finished_at   = models.DateTimeField(null=True, blank=True)
    score         = models.FloatField(default=0.0)    # 0–100 %
    is_passed     = models.BooleanField(default=False)
    attempt_number = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name        = 'Попытка теста'
        verbose_name_plural = 'Попытки теста'
        ordering            = ['-started_at']

    def __str__(self):
        return f"{self.student} — {self.test.title} #{self.attempt_number} ({self.score:.0f}%)"

    def is_finished(self):
        return self.finished_at is not None

    def duration_seconds(self):
        if self.finished_at:
            return int((self.finished_at - self.started_at).total_seconds())
        return None

    def score_color(self):
        if self.score >= 85: return 'success'
        if self.score >= 70: return 'info'
        if self.score >= self.test.passing_score: return 'warning'
        return 'danger'

    def finish(self):
        """Calculate score, mark as finished, trigger KPI update."""
        questions = self.test.questions.prefetch_related('answers')
        total_points  = 0
        earned_points = 0

        for question in questions:
            total_points += question.points
            student_ans  = self.student_answers.filter(question=question).first()
            if student_ans and student_ans.is_correct:
                earned_points += question.points

        self.score      = round(earned_points / total_points * 100, 1) if total_points else 0
        self.is_passed  = self.score >= self.test.passing_score
        self.finished_at = timezone.now()
        self.save()


class StudentAnswer(models.Model):
    attempt          = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='student_answers')
    question         = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answers = models.ManyToManyField(Answer, blank=True)
    is_correct       = models.BooleanField(default=False)
    points_earned    = models.FloatField(default=0.0)

    class Meta:
        verbose_name        = 'Ответ ученика'
        verbose_name_plural = 'Ответы учеников'
        unique_together     = ('attempt', 'question')

    def evaluate(self):
        """Check if the student's selection is correct and assign points."""
        correct_ids  = set(self.question.answers.filter(is_correct=True).values_list('id', flat=True))
        selected_ids = set(self.selected_answers.values_list('id', flat=True))

        if self.question.question_type == Question.TYPE_SINGLE:
            self.is_correct = selected_ids == correct_ids
        else:
            # Multiple: full match required for full points
            self.is_correct = selected_ids == correct_ids

        self.points_earned = self.question.points if self.is_correct else 0.0
        self.save()
