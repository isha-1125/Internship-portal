from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now


class custom_user(AbstractUser):

    ROLE_CHOICES = (
        ('student', 'Student'),
        ('company', 'Company'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='student'
    )

    email = models.EmailField(unique=True)
    date_joined = models.DateTimeField(default=now)

    groups = models.ManyToManyField(
        "auth.Group",
        related_name="custom_user_set",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        related_name="custom_user_permissions_set",
        blank=True
    )

    def __str__(self):
        return self.username


class user_profile(models.Model):
    user = models.OneToOneField(custom_user, on_delete=models.CASCADE, related_name='profile')

    full_name = models.CharField(max_length=255, blank=True, null=True)

    contact_number = models.CharField(
        max_length=10,
        validators=[RegexValidator(regex=r'^\d{10}$', message="Contact number must be exactly 10 digits.")],
        blank=True,
        null=True
    )

    gender = models.CharField(
        max_length=10,
        choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')],
        blank=True,
        null=True
    )

    age = models.IntegerField(blank=True, null=True)

    date_of_birth = models.DateField(blank=True, null=True)

    qualifications = models.TextField(blank=True, null=True)

    # ✅ MULTIPLE SKILLS SAVE HO SAKTI HAIN
    skills = models.CharField(max_length=255, blank=True, null=True)

    certificates = models.FileField(upload_to='certificates/', blank=True, null=True)

    area_of_interest = models.TextField(blank=True, null=True)

    profile_picture = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.jpg')

    def __str__(self):
        return self.full_name if self.full_name else self.user.username

class InternshipPost(models.Model):
    company_name = models.CharField(max_length=100, blank=True, null=True)
    company = models.ForeignKey(
    custom_user,
    on_delete=models.CASCADE,
    related_name='internships',
    null=True,      # ✅ add this
    blank=True      # ✅ add this
    )

    internship_title = models.CharField(max_length=100, blank=True, null=True)

    description = models.TextField(blank=True, null=True)

    apply_url = models.URLField(blank=True, null=True)

    posted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company_name} - {self.internship_title}"


class Application(models.Model):

    STATUS_CHOICES = [
        ('Under Review', 'Under Review'),
        ('Shortlisted', 'Shortlisted'),
        ('Interview Scheduled', 'Interview Scheduled'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected')
    ]

    user = models.ForeignKey(custom_user, on_delete=models.CASCADE, related_name='applications')
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(
        max_length=10,
        validators=[RegexValidator(regex=r'^\d{10}$', message="Phone number must be exactly 10 digits.")],
        blank=True,
        null=True
    )
    address = models.TextField()
    skills = models.CharField(max_length=255)
    experience = models.IntegerField()
    preferred_technology = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    github = models.URLField(blank=True, null=True)
    freshers = models.CharField(max_length=255)
    internship_role = models.CharField(max_length=255)

    internship = models.ForeignKey(
    InternshipPost, 
    on_delete=models.CASCADE, 
    related_name='applications',
    null=True,  # allow null for existing rows
    blank=True
    )

    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    certificates = models.FileField(upload_to='certificates/', blank=True, null=True)
    applied_on = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Under Review')
    test_taken = models.BooleanField(default=False)
    passed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} - {self.internship_role}"

    @classmethod
    def can_apply(cls, user):
        return user.applications.filter(
            status__in=['Under Review', 'Shortlisted', 'Interview Scheduled', 'Accepted']
        ).count() < 4


        # ===============================
# Assessment Test Models
# ===============================

class Question(models.Model):
    DOMAIN_CHOICES = [
        ('Python', 'Python'),
        ('Web', 'Web Development'),
        ('DS', 'Data Science'),
        ('AI', 'AI/ML'),
    ]

    QUESTION_TYPE = (
        ('MCQ', 'MCQ'),
        ('CODE', 'Coding'),
    )

    number = models.PositiveIntegerField(default=1)  # question numbering
    question = models.CharField(max_length=255)
    domain = models.CharField(max_length=50, choices=DOMAIN_CHOICES, default='Python')
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPE, default='MCQ')

    # MCQ options
    option1 = models.CharField(max_length=200, blank=True, null=True)
    option2 = models.CharField(max_length=200, blank=True, null=True)
    option3 = models.CharField(max_length=200, blank=True, null=True)
    option4 = models.CharField(max_length=200, blank=True, null=True)
    correct_answer = models.CharField(max_length=200, blank=True, null=True)

    # Coding starter code
    starter_code_python = models.TextField(blank=True, null=True)
    starter_code_cpp = models.TextField(blank=True, null=True)
    starter_code_java = models.TextField(blank=True, null=True)
    starter_code_web = models.TextField(blank=True, null=True)

    # Test cases
    test_cases = models.JSONField(blank=True, null=True)
    hidden_test_cases = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"[{self.domain}] {self.number}. {self.question}"


class TestResult(models.Model):
    user = models.ForeignKey(custom_user, on_delete=models.CASCADE)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, null=True, blank=True)

    # ✅ Total score
    score = models.IntegerField()
    total_questions = models.IntegerField()

    # ✅ MCQ + Coding breakdown
    mcq_score = models.IntegerField(default=0)
    mcq_total = models.IntegerField(default=0)
    coding_score = models.IntegerField(default=0)
    coding_total = models.IntegerField(default=0)

    submitted_at = models.DateTimeField(auto_now_add=True)
    passed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - Score: {self.score}"

class CompanyProfile(models.Model):
    user = models.OneToOneField(custom_user, on_delete=models.CASCADE, related_name='company_profile')
    company_name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    contact_number = models.CharField(max_length=15, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)

    def __str__(self):
        return self.company_name

