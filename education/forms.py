from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import *


class RegistrationForm(UserCreationForm):

    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(required=True, label='Имя')
    last_name = forms.CharField(required=True, label='Фамилия')
    phone = forms.CharField(required=False, label='Телефон')
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
        fields = ('name', 'description', 'mentor', 'duration_weeks', 'max_students', 'start_date', 'end_date',
                  'is_active')
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