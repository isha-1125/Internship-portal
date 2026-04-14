from django.urls import path
from user_auth import views
from .views import update_username, apply_internship
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Home / Index
    path("", views.index, name='index'),
    path("home/", views.home1, name='home'),

    # Authentication
    path("register/", views.register, name="register"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.Ulogout, name="logout"),

    # Profile
    path("student-dashboard/", views.profile_view, name="student_dashboard"),
    path('update_profile/', views.pro, name='update_profile'),
    path("pro/", views.pro, name="pro"),
    path("update-username/", update_username, name="update_username"),

    # Internships
    path("list/", views.intern_list, name="list"),
    path("apply/<int:internship_id>/", apply_internship, name="apply_internship"),
    path('quit_application/<int:application_id>/', views.quit_application, name='quit_application'),

    # Assessment Test
    path('start-assessment/<int:application_id>/', views.start_assessment, name='start_assessment'),
    path('submit-test/', views.submit_test, name='submit_test'),
    path('run-code/', views.run_code, name='run_code'),
    
     # -------------------------------
    # Admin Panel
    # -------------------------------
    path('logout/', views.Ulogout, name='ulogout'),  # view function Ulogout
    path('admin-panel/', views.admin_panel, name='admin_panel'),

    path('update-status/<int:id>/<str:status>/', views.update_status, name='update_status'),
    # ✅ Add this line for viewing single application
    path('application/<int:app_id>/', views.view_application, name='view_application'),
    # Certificate view URL
    path('certificate/<int:application_id>/', views.certificate_view, name='certificate_view'),

    path('add-internship/', views.add_internship, name='add_internship'),
    path('delete-internship/<int:id>/', views.delete_internship, name='delete_internship'),
    path('edit-internship/<int:id>/', views.edit_internship, name='edit_internship'),

    # Company URLs
    path("company/profile/", views.company_profile_update, name="company_profile"),
    path("company/dashboard/", views.company_dashboard, name="company_dashboard"),
    # 🔥 FORGOT PASSWORD (FINAL FIX)
    path(
      'password-reset/',
       auth_views.PasswordResetView.as_view(
       template_name='registration/password_reset_form.html'
       ),
       name='password_reset'
    ),

    path(
      'password-reset/done/',
      auth_views.PasswordResetDoneView.as_view(
      template_name='registration/password_reset_done.html'
      ),
      name='password_reset_done'
    ),

    path(
      'reset/<uidb64>/<token>/',
       auth_views.PasswordResetConfirmView.as_view(
       template_name='registration/password_reset_confirm.html'
       ),
       name='password_reset_confirm'
    ),

    path(
     'reset/done/',
      auth_views.PasswordResetCompleteView.as_view(
      template_name='registration/password_reset_complete.html'
      ),
      name='password_reset_complete'
    )
   ]

if settings.DEBUG:
     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

