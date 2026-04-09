from django.contrib import admin
from .models import (
    custom_user,
    user_profile,
    Application,
    InternshipPost,
    Question,
    TestResult
)

# =========================
# Custom User Admin
# =========================
@admin.register(custom_user)
class custom_userAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_active', 'date_joined')
    search_fields = ('username', 'email')
    list_filter = ('is_active',)
    ordering = ('date_joined',)

# =========================
# Application Admin
# =========================
@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'internship_role', 'status', 'applied_on', 'user')
    list_filter = ('status', 'internship_role')
    search_fields = ('full_name', 'internship_role', 'email')
    ordering = ('-applied_on',)
    list_editable = ('status',)

    def save_model(self, request, obj, form, change):
        if change:
            obj.save()
        else:
            obj.user = request.user
            obj.save()

# =========================
# User Profile
# =========================
admin.site.register(user_profile)

# =========================
# Internship Post Admin
# =========================
@admin.register(InternshipPost)
class InternshipPostAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'internship_title', 'posted_at')
    search_fields = ('company_name', 'internship_title')

# =========================
# Assessment Test Admin
# =========================
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question', 'domain', 'question_type')
    list_filter = ('domain', 'question_type')
    search_fields = ('question',)

    fieldsets = (
        ('Basic Info', {
            'fields': ('domain', 'question_type', 'question')
        }),

        ('MCQ Section', {
            'fields': (
                'option1',
                'option2',
                'option3',
                'option4',
                'correct_answer'
            )
        }),

        ('Coding Section', {
            'fields': (
                'starter_code_python',
                'starter_code_cpp',
                'starter_code_java',
                'test_cases',
                'hidden_test_cases'
            )
        }),
    )
        

@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('user', 'application', 'score', 'total_questions', 'submitted_at')

    search_fields = ('user__username', 'application__internship_role')

    list_filter = ('submitted_at',)

    ordering = ('-submitted_at',)