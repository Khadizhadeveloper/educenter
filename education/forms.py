from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models.user import User
from .models.mentor import Mentor
from .models.student import Student
from .models.lesson import Lesson
from .models.schedule import Schedule
from .models.course import Course
from .models.homework import Homework, HomeworkSubmission
from .models.grade import Grade
from .models.attendance import Attendance
from .models.announcement import Announcement
from .models.enrollment import Enrollment
import re




def validate_phone(value):
    """Принимает форматы: +996700123456 / 0700123456 / 996700123456"""
    cleaned = re.sub(r'[\s\-\(\)]', '', value)
    if not re.match(r'^\+?[1-9]\d{9,14}$', cleaned):
        raise ValidationError(
            'Введите корректный номер телефона. Пример: +996700123456'
        )
    return value




class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(required=True, label='Имя')
    last_name = forms.CharField(required=True, label='Фамилия')
    phone = forms.CharField(
        required=False,
        label='Телефон',
        help_text='Формат: +996700123456'
    )
    role = forms.ChoiceField(
        choices=[('parent', 'Родитель'), ('student', 'Ученик')],
        label='Роль'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'role', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже зарегистрирован.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            return phone
        phone = validate_phone(phone)  # проверка формата
        if User.objects.filter(phone=phone).exists():
            raise ValidationError('Пользователь с таким номером уже зарегистрирован.')
        return phone

    def clean_role(self):
        """Запрещаем самостоятельную регистрацию ментора и админа"""
        role = self.cleaned_data.get('role')
        if role not in ('parent', 'student'):
            raise ValidationError('Недопустимая роль для самостоятельной регистрации.')
        return role




class AdminCreateUserForm(UserCreationForm):

    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(required=True, label='Имя')
    last_name = forms.CharField(required=True, label='Фамилия')
    phone = forms.CharField(
        required=False,
        label='Телефон',
        help_text='Формат: +996700123456'
    )
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        label='Роль'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'role', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = User.ROLE_CHOICES
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            return phone
        phone = validate_phone(phone)
        if User.objects.filter(phone=phone).exists():
            raise ValidationError('Пользователь с таким номером уже существует.')
        return phone



class AssignRoleForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('role',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].widget.attrs.update({'class': 'form-control'})




class MentorProfileForm(forms.ModelForm):
    class Meta:
        model = Mentor
        fields = ('specialization', 'bio', 'experience_years', 'education', 'photo')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})




class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'address', 'avatar')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not phone:
            return phone
        phone = validate_phone(phone)
        # При редактировании исключаем текущего пользователя
        qs = User.objects.filter(phone=phone)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('Этот номер уже используется другим пользователем.')
        return phone


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ('grade', 'enrollment_date', 'medical_info')
        widgets = {
            'enrollment_date': forms.DateInput(attrs={'type': 'date'}),
            'medical_info': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ('name', 'description', 'mentor', 'duration_weeks', 'max_students', 'start_date', 'end_date', 'is_active')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'is_active':
                self.fields[field].widget.attrs.update({'class': 'form-control'})


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ('course', 'title', 'description', 'date', 'start_time', 'end_time', 'room', 'notes')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ('course', 'weekday', 'start_time', 'end_time', 'room')
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class HomeworkForm(forms.ModelForm):
    class Meta:
        model = Homework
        fields = ('lesson', 'title', 'description', 'due_date', 'file')
        widgets = {
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'file':
                self.fields[field].widget.attrs.update({'class': 'form-control'})


class HomeworkSubmissionForm(forms.ModelForm):
    class Meta:
        model = HomeworkSubmission
        fields = ('content', 'file')
        widgets = {
            'content': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Опишите выполненное задание...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].widget.attrs.update({'class': 'form-control'})


class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ('student', 'course', 'lesson', 'grade', 'comment')
        widgets = {
            'grade': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ('lesson', 'student', 'status', 'notes')
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ('title', 'content', 'target_audience', 'course', 'is_pinned')
        widgets = {
            'content': forms.Textarea(attrs={'rows': 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field not in ['is_pinned']:
                self.fields[field].widget.attrs.update({'class': 'form-control'})