from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import authenticate, logout, login as auth_login
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError

from .forms import RegisterForm, LoginForm, ProfileUpdateForm, ApplicationForm, UsernameUpdateForm
from .models import user_profile, custom_user, Application, Question, TestResult
from .forms import CompanyProfileForm
from .models import CompanyProfile

# --------------------------
# Role → Domain Mapping
# --------------------------
ROLE_DOMAIN_MAP = {
    'Frontend Developer': 'Web',
    'Backend Developer': 'Python',
    'Full Stack Developer': 'Web',
    'Software Developer': 'Web',
    'Data Analyst': 'DS',
    'AI Engineer': 'AI',
}

# Reverse mapping (Domain → Role)
DOMAIN_ROLE_MAP = {v: k for k, v in ROLE_DOMAIN_MAP.items()}

# -------------------------------
# Public Views
# -------------------------------

def index(request):
    return render(request, "index.html")

def home(request):
    return render(request, "home.html")

def home1(request):
    return render(request, "home1.html")

def aplit(request):
    return render(request, "aplit.html")

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, "Account created successfully!")
            return redirect('login')
        else:
            messages.error(request, "Registration failed! Please check your details.")
    else:
        form = RegisterForm()
    return render(request, "registration.html", {"form": form})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['username']
            password = form.cleaned_data['password']

            try:
                user = custom_user.objects.get(email=username_or_email)
                username = user.username
            except custom_user.DoesNotExist:
                username = username_or_email

            user = authenticate(request, username=username, password=password)
            if user:
                auth_login(request, user)
                messages.success(request, "Login Successful!")

                # -------------------------
                # Role-based redirect
                # -------------------------
                if user.role == 'student':
                    return redirect('student_dashboard')   # Student dashboard
                elif user.role == 'company':
                    return redirect('company_dashboard')   # Company dashboard
                else:
                    return redirect('profile')             # fallback

            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

# -------------------------------
# Authenticated Views
# -------------------------------

@login_required
def Ulogout(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('login')

@login_required
def pro(request):
    profile, created = user_profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            if not form.cleaned_data.get("contact_number"):
                form.instance.contact_number = None
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('student_dashboard')
        else:
            messages.error(request, "Error updating profile. Please check the details.")
    else:
        form = ProfileUpdateForm(instance=profile)

    return render(request, 'pro.html', {'form': form, 'profile': profile})

@login_required
def profile_view(request):

    # 🔥 ADMIN → admin panel
    if request.user.is_superuser:
        return redirect('admin_panel')

    # 🔥 COMPANY → company profile
    if request.user.role == "company":
        return redirect('company_profile')

    # 👇 STUDENT → normal profile
    profile, created = user_profile.objects.get_or_create(user=request.user)

    if created:
        messages.info(request, "Your profile has been created. Please update your details.")

    applications = Application.objects.filter(user=request.user)

    # 📸 Profile picture upload
    if request.method == 'POST' and 'profile_picture' in request.FILES:
        profile.profile_picture = request.FILES['profile_picture']
        profile.save()
        messages.success(request, "Profile picture updated successfully! Reload the page")
        return redirect('student_dashboard')

    if not applications:
        messages.info(request, "You have not applied for any internships yet.")

    return render(request, 'student_dashboard.html', {
        'profile': profile,
        'applications': applications
    })

@login_required
def update_username(request):
    if request.method == "POST":
        form = UsernameUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Username updated successfully!")
            return redirect("student_dashboard")
    else:
        form = UsernameUpdateForm(instance=request.user)
    return render(request, "update_username.html", {"form": form})

@login_required
def apply_internship(request, internship_id):

    internship = InternshipPost.objects.get(id=internship_id)

    if request.method == "POST":
        form = ApplicationForm(request.POST, request.FILES)

        if form.is_valid():

            if request.user.applications.count() >= 4:
                messages.error(request, "Single user can only apply for 4 internships.")
                return redirect('student_dashboard')

            application = form.save(commit=False)

            application.user = request.user

            # ✅ MOST IMPORTANT LINE
            application.internship = internship

            # optional but useful
            application.company_name = internship.company_name
            application.internship_role = internship.internship_title

            application.save()

            messages.success(request, "Application submitted successfully!")
            return redirect('student_dashboard')

        else:
            messages.error(request, "Please correct the errors below.")

    else:
        form = ApplicationForm()

    return render(request, 'aplit.html', {
        "form": form,
        "internship": internship
    })

@login_required
def quit_application(request, application_id):
    try:
        application = Application.objects.get(id=application_id, user=request.user)
        application.delete()
        messages.success(request, "You have successfully quit the application. Reload the page")
    except Application.DoesNotExist:
        messages.error(request, "Application not found.")
    except Exception as e:
        messages.error(request, f"Error quitting application: {str(e)}")
    return redirect("student_dashboard")

from .models import InternshipPost

@login_required
def intern_list(request):
    internships = InternshipPost.objects.all().order_by('-posted_at')
    return render(request, "list.html", {'internships': internships})
# -------------------------------
# Assessment Test Views
# -------------------------------

# Role to domain mapping

@login_required
def start_assessment(request, application_id):

    application = get_object_or_404(Application, id=application_id, user=request.user)

    if application.status != "Shortlisted":
        messages.error(request, "You are not shortlisted for this test.")
        return redirect('student_dashboard')

    # ✅ FIXED LINE
    domain = ROLE_DOMAIN_MAP.get(application.internship_role, "Web")
    print("DOMAIN:", domain)

    mcq_questions = Question.objects.filter(
    domain__iexact=domain,
    question_type__iexact="MCQ"
).order_by('number')[:10]

    coding_questions = Question.objects.filter(
    domain__iexact=domain,
    question_type__iexact="CODE"
).order_by('number')[:2]
    return render(request, "test.html", {
        "mcqs": mcq_questions,
        "codings": coding_questions,
        "application": application
    })
       
       
       

   
#submit test

import subprocess
import tempfile
import os

@login_required
def submit_test(request):
    if request.method != "POST":
        return redirect("student_dashboard")

    application_id = request.POST.get("application_id")
    application = get_object_or_404(Application, id=application_id, user=request.user)

    # 🔐 Prevent multiple attempts
    if application.test_taken:
        messages.warning(request, "You have already submitted the test.")
        return redirect("student_dashboard")

    # 🔁 Role → Domain mapping
    domain = ROLE_DOMAIN_MAP.get(application.internship_role, "Web")
    # ---------------- MCQ ----------------
    mcqs = Question.objects.filter(
    domain__iexact=domain,
    question_type__iexact="MCQ"
)[:10]

    # ---------------- Coding ----------------
    coding_questions = Question.objects.filter(
    domain__iexact=domain,
    question_type__iexact="CODE"
)[:2]

    # ✅ Initialize scores
    mcq_score = 0
    mcq_total = len(mcqs)

    coding_score = 0
    coding_total = 0

    # --------- MCQ Evaluation ---------
    for q in mcqs:
        selected = request.POST.get(str(q.id))
        if selected == q.correct_answer:
            mcq_score += 1

    # --------- Coding Evaluation ---------
    for q in coding_questions:
        user_code = request.POST.get(f"code_{q.id}", "").strip()

        test_cases = q.test_cases or []
        hidden_cases = q.hidden_test_cases or []

        all_cases = test_cases + hidden_cases

        for case in all_cases:
            try:
                # ✅ Create temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
                    f.write(user_code.encode())
                    file_name = f.name

                # ✅ Run code
                result = subprocess.run(
                    ["python", file_name],
                    input=case.get("input", ""),
                    text=True,
                    capture_output=True,
                    timeout=5
                )

                output = result.stdout.strip()
                expected_output = case.get("output", "").strip()

                if output == expected_output:
                    coding_score += 1

            except Exception:
                pass

            finally:
                # ✅ Cleanup temp file
                if os.path.exists(file_name):
                    os.remove(file_name)

            coding_total += 1

    # --------- Final Score ---------
    total_score = mcq_score + coding_score
    total_questions = mcq_total + coding_total

    percentage = (total_score / total_questions) * 100 if total_questions > 0 else 0

    # --------- Pass/Fail ---------
    passed = (mcq_score >= 7) and (coding_score >= 1)
    # --------- Save Result ---------
    TestResult.objects.update_or_create(
    application=application,
    defaults={
        "user": request.user,
        "score": total_score,
        "total_questions": total_questions,
        "mcq_score": mcq_score,
        "mcq_total": mcq_total,
        "coding_score": coding_score,
        "coding_total": coding_total,
        "passed": passed
    }
)

    # --------- Update Application ---------
    application.test_taken = True
    application.passed = passed   # ✅ IMPORTANT LINE
    application.status = "Selected" if passed else "Rejected"
    application.save()

    # --------- Render Result ---------
    return render(request, "result.html", {
        "score": total_score,
        "total": total_questions,
        "passed": passed,
        "percentage": percentage,
        "mcq_score": mcq_score,
        "mcq_total": mcq_total,
        "coding_score": coding_score,
        "coding_total": coding_total,
    })

#run code

from django.http import JsonResponse
import subprocess
import tempfile
import os

@login_required
def run_code(request):

    if request.method == "POST":
        code = request.POST.get("code", "")
        language = request.POST.get("language", "python")

        file_name = None

        try:
            # ✅ PYTHON
            if language == "python":
                with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
                    f.write(code.encode())
                    file_name = f.name

                result = subprocess.run(
                    ["python", file_name],
                    text=True,
                    capture_output=True,
                    timeout=5
                )

                output = result.stdout or result.stderr

            # ❌ C++ (placeholder)
            elif language == "cpp":
                output = "⚠️ C++ execution not supported yet"

            # ❌ Java (placeholder)
            elif language == "java":
                output = "⚠️ Java execution not supported yet"

            # 🌐 Web
            elif language == "web":
                output = "✅ Rendered below (preview)"

            else:
                output = "Invalid language selected"

        except Exception as e:
            output = str(e)

        finally:
            if file_name and os.path.exists(file_name):
                os.remove(file_name)

        return JsonResponse({"output": output})

    return JsonResponse({"output": "Error"})

       


# ================================
# Admin Panel Views
# ================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Application
from .models import Application, TestResult  # ✅ Import TestResult
from .models import Application, TestResult, InternshipPost


# -------------------------------
# Admin Panel Views
# -------------------------------

@login_required
def admin_panel(request):

    if not request.user.is_superuser:
        messages.error(request, "You are not authorized to access admin panel.")
        return redirect("home")

    # Base queryset
    applications = Application.objects.all().order_by('-applied_on')

    # 🔎 Search
    search_query = request.GET.get('search')
    if search_query:
        applications = applications.filter(
            Q(full_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(internship_role__icontains=search_query)
        )

    # 📊 Status Filter
    status_filter = request.GET.get('status')
    if status_filter:
        applications = applications.filter(status=status_filter)

    filtered_applications = applications

    total_applications = filtered_applications.count()
    shortlisted = filtered_applications.filter(status="Shortlisted").count()
    rejected = filtered_applications.filter(status="Rejected").count()
    under_review = filtered_applications.filter(status="Under Review").count()

    # ✅ Initialize counts
    passed_count = 0
    failed_count = 0

    # ✅ Loop for counts
    for app in filtered_applications:
        result = TestResult.objects.filter(application=app).first()

        if result:
            passed = (result.mcq_score >= 7) and (result.coding_score >= 1)
            if passed:
                passed_count += 1
            else:
                failed_count += 1

    # ✅ Attach result for table
    for app in filtered_applications:
        result = TestResult.objects.filter(application=app).first()

        if not app.test_taken:
            app.result_status = "Not Attempted"
            app.score = None

        elif result:
            passed = (result.mcq_score >= 7) and (result.coding_score >= 1)
            app.result_status = "Pass" if passed else "Fail"
            app.score = f"{result.score}/{result.total_questions}"

        else:
            app.result_status = "Not Attempted"
            app.score = None
    # ✅ AI SCORE ADD KARNA (YAHI PERFECT PLACE HAI)
    for app in filtered_applications:
        app.ai_score = calculate_score(app)

    # 🔥 ADD THIS (INTERNSHIP LIST)
    # ===============================
    internships = InternshipPost.objects.all().order_by('-posted_at')

    # ✅ Context (IMPORTANT: inside function)
    context = {
        "applications": filtered_applications,
        "internships": internships,   # ✅ IMPORTANT LINE
        "total_applications": total_applications,
        "shortlisted": shortlisted,
        "rejected": rejected,
        "under_review": under_review,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "search_query": search_query,
        "status_filter": status_filter
    }

    return render(request, "admin1.html", context)

    
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required

@login_required
def view_application(request, app_id):

    # ✅ सबसे पहले application fetch करो
    application = get_object_or_404(Application, id=app_id)

    # ✅ Admin OR company owner OR unauthorized check
    if request.user.is_superuser:
        pass
    elif request.user.role == "company":
        if application.company_name != request.user.company_profile.company_name:
            messages.error(request, "Unauthorized ❌")
            return redirect("company_dashboard")
    else:
        messages.error(request, "Unauthorized ❌")
        return redirect("home")

    # ✅ AI SCORE CALCULATE
    ai_score = calculate_score(application)

    # ✅ Breakdown
    skills_score = 30 if application.skills else 0
    exp_score = min(application.experience * 10, 30) if application.experience else 0
    resume_score = 20 if application.resume else 0
    tech_score = 20 if application.preferred_technology else 0

    application.ai_score = ai_score  # temporary attach

    # ✅ Correct way to fetch latest test result
    from .models import TestResult
    test_result = TestResult.objects.filter(application=application).order_by('-id').first() 
    role_name = DOMAIN_ROLE_MAP.get(application.internship_role, application.internship_role)

    context = {
        "application": application,
        "test_result": test_result,
        "role_name": role_name,  
        "skills_score": skills_score,
        "exp_score": exp_score,
        "resume_score": resume_score,
        "tech_score": tech_score,
    }

    return render(request, "view_application.html", context)


@login_required
def update_status(request, id, status):

    application = get_object_or_404(Application, id=id)

    # ✅ Allow admin OR company (owner only)
    if request.user.is_superuser:
        pass
    elif request.user.role == 'company':
        if application.company_name != request.user.company_profile.company_name:
            messages.error(request, "Unauthorized ❌")
            return redirect("company_dashboard")
    else:
        messages.error(request, "Unauthorized ❌")
        return redirect("home")

    application.status = status
    application.save()

    messages.success(request, "Application status updated!")

    if request.user.role == "company":
        return redirect("company_dashboard")
    return redirect("admin_panel")



from datetime import date
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Application, TestResult, user_profile

@login_required
def certificate_view(request, application_id):

    application = get_object_or_404(Application, id=application_id, user=request.user)

    test_result = TestResult.objects.filter(application=application).first()

    if not test_result or not test_result.passed:
        messages.error(request, "You are not eligible for a certificate yet.")
        return render(request, 'certificate_not_available.html')

    # ✅ FULL NAME FIX
    profile = user_profile.objects.filter(user=request.user).first()
    if profile and profile.full_name:
        full_name = profile.full_name
    else:
        full_name = request.user.username

    # ✅ ROLE (reverse mapping)
    role_name = DOMAIN_ROLE_MAP.get(application.internship_role, application.internship_role)

    # ✅ PERCENTAGE
    percentage = (test_result.score / test_result.total_questions) * 100 if test_result.total_questions else 0

    context = {
        'full_name': full_name,
        'role_name': role_name,
        'percentage': round(percentage, 2),
        'today': date.today(),
    }

    return render(request, 'certificate.html', context)

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import InternshipPostForm

@login_required
def add_internship(request):

    # ✅ Allow only admin + company
    if not (request.user.is_superuser or request.user.role == 'company'):
        messages.error(request, "You are not authorized to add internship.")
        return redirect('home')

    if request.method == 'POST':
        form = InternshipPostForm(request.POST)

        if form.is_valid():
            internship = form.save(commit=False)
            # ✅ ADD THIS LINE (MOST IMPORTANT)
            internship.company = request.user

            if request.user.role == "company":
                name = (
                    request.user.company_profile.company_name
                    or form.cleaned_data.get('company_name')
                )
                internship.company_name = name.strip()
            else:
                internship.company_name = form.cleaned_data.get('company_name')

            internship.save()

            messages.success(request, "Internship posted successfully ✅")

            if request.user.role == "company":
                return redirect('company_dashboard')
            else:
                return redirect('admin_panel')

        else:
            messages.error(request, "Something went wrong ❌")

    else:
        form = InternshipPostForm()

    return render(request, 'add_internship.html', {'form': form})


def calculate_score(application):
    score = 0

    # Skills
    if application.skills:
        score += 30

    # Experience
    if application.experience:
        score += min(application.experience * 10, 30)

    # Resume uploaded
    if application.resume:
        score += 20

    # Preferred Tech
    if application.preferred_technology:
        score += 20

    return score

@login_required
def delete_internship(request, id):

    internship = get_object_or_404(InternshipPost, id=id)

    # ✅ Admin OR company owner
    if request.user.is_superuser:
        pass
    elif request.user.role == "company":
        if internship.company_name != request.user.company_profile.company_name:
            messages.error(request, "Unauthorized ❌")
            return redirect("company_dashboard")
    else:
        return redirect("home")

    internship.delete()
    messages.success(request, "Deleted successfully ✅")

    if request.user.role == "company":
        return redirect("company_dashboard")
    return redirect("admin_panel")

@login_required
def edit_internship(request, id):

    internship = get_object_or_404(InternshipPost, id=id)

    # ✅ Admin OR company owner
    if request.user.is_superuser:
        pass
    elif request.user.role == "company":
        if internship.company_name != request.user.company_profile.company_name:
            messages.error(request, "Unauthorized ❌")
            return redirect("company_dashboard")
    else:
        return redirect("home")

    if request.method == 'POST':
        form = InternshipPostForm(request.POST, instance=internship)
        if form.is_valid():
            form.save()
            messages.success(request, "Internship updated ✅")

            if request.user.role == "company":
                return redirect("company_dashboard")
            return redirect("admin_panel")
    else:
        form = InternshipPostForm(instance=internship)

    return render(request, 'add_internship.html', {'form': form})

@login_required
def company_profile_update(request):
    if request.user.role != 'company':
        messages.error(request, "Unauthorized access")
        return redirect('home')

    profile, created = CompanyProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = CompanyProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('company_dashboard')
    else:
        form = CompanyProfileForm(instance=profile)

    return render(request, "company_profile.html", {"form": form})

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import InternshipPost, Application, CompanyProfile
from .models import TestResult


@login_required
def company_dashboard(request):
    if request.user.role != 'company':
        messages.error(request, "Unauthorized access")
        return redirect('home')

    profile = getattr(request.user, 'company_profile', None)
    if not profile:
        messages.error(request, "Please complete your company profile first")
        return redirect('company_profile')

    internships = InternshipPost.objects.filter(company=request.user)  # sirf is company ke posts
    all_apps = Application.objects.filter(internship__company=request.user)  # sirf is company ke applications
    search = request.GET.get('search')
    if search:
        all_apps = all_apps.filter(full_name__icontains=search)

    status = request.GET.get('status')
    if status:
        all_apps = all_apps.filter(status=status)

    passed_count = 0
    failed_count = 0

    for app in all_apps:
        # Test Result
        result = TestResult.objects.filter(application=app).order_by('-id').first()

        if not app.test_taken:
            app.result_status = "Not Attempted"
            app.score = None
        elif result:
            if result.passed:
                app.result_status = "Pass"
                passed_count += 1
            else:
                app.result_status = "Fail"
                failed_count += 1
            app.score = f"{result.score}/{result.total_questions}"
        else:
            app.result_status = "Not Attempted"
            app.score = None

        # AI Score Calculation
        try:
            app.ai_score = calculate_score(app)
        except:
            app.ai_score = 0

        # Progress bars calculation
        app.progress = {
            "skills": 30 if getattr(app, "skills", None) else 0,
            "projects": 20 if getattr(app, "projects", None) else 0,
            "experience": min(getattr(app, "experience", 0)*10, 30),
            "technology": 20 if getattr(app, "preferred_technology", None) else 0,
        }

    context = {
        "profile": profile,
        "internships": internships,
        "applications": all_apps,
        "total_applications": all_apps.count(),
        "under_review": all_apps.filter(status="Under Review").count(),
        "shortlisted": all_apps.filter(status="Shortlisted").count(),
        "rejected": all_apps.filter(status="Rejected").count(),
        "passed_count": passed_count,
        "failed_count": failed_count,
    }

    return render(request, "company_dashboard.html", context)