import json
import secrets
import requests
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.utils.text import slugify
from django.conf import settings
from django.core.mail import send_mail
from django.utils.html import strip_tags
from django.contrib import messages

from .models import Project, ApiRoute, EmailVerification, EmailOTP


def home(request):
    return render(request, "home.html")


def send_verification_email(user, request):
    """Send email verification link to user."""
    # Delete any existing verification for this user
    EmailVerification.objects.filter(user=user).delete()
    
    # Create new verification token
    verification = EmailVerification.objects.create(user=user)
    
    # Build verification URL
    verification_url = request.build_absolute_uri(f'/verify-email/{verification.token}/')
    
    # Email content
    subject = 'Verify your email - Dummy Server'
    html_message = f'''
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333;">Welcome to Dummy Server!</h2>
        <p>Hi {user.first_name or user.username},</p>
        <p>Thank you for signing up. Please verify your email address by clicking the button below:</p>
        <p style="text-align: center; margin: 30px 0;">
            <a href="{verification_url}" 
               style="background-color: #007bff; color: white; padding: 12px 30px; 
                      text-decoration: none; border-radius: 5px; display: inline-block;">
                Verify Email
            </a>
        </p>
        <p>Or copy and paste this link in your browser:</p>
        <p style="word-break: break-all; color: #666;">{verification_url}</p>
        <p>This link will expire in 24 hours.</p>
        <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
        <p style="color: #999; font-size: 12px;">
            If you didn't create an account, you can safely ignore this email.
        </p>
    </body>
    </html>
    '''
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Email send error: {e}")
        return False


@require_http_methods(["GET", "POST"])
def login_view(request):
    """
    Custom login/signup view with Firebase Google auth option.
    """
    if request.user.is_authenticated:
        return redirect("home")

    error = None
    success = None
    
    if request.method == "POST":
        action = request.POST.get("action", "login")
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "").strip()

        if action == "login":
            # Django native login (email or username)
            try:
                # Resolve user by email or username
                if "@" in email:
                    user = User.objects.get(email=email)
                else:
                    user = User.objects.get(username=email)

                # Check verification
                try:
                    verification = user.email_verification
                    if not verification.verified:
                        messages.error(request, "Please verify your email first. Check your inbox for the verification link.")
                        context = {
                            "show_resend": True,
                            "resend_email": user.email,
                            "firebase_config": settings.FIREBASE_CONFIG,
                        }
                        return render(request, "login.html", context)
                except EmailVerification.DoesNotExist:
                    pass

                user = authenticate(request, username=user.username, password=password)
                if user is not None:
                    login(request, user)
                    return redirect("home")
                else:
                    error = "Invalid credentials. Check your password."
            except User.DoesNotExist:
                error = "Account not found. Please sign up first."

        elif action == "signup":
            # Get additional fields
            first_name = request.POST.get("first_name", "").strip()
            last_name = request.POST.get("last_name", "").strip()
            confirm_password = request.POST.get("confirm_password", "").strip()
            username = request.POST.get("username", "").strip()
            
            # Validation
            if not first_name:
                error = "First name is required."
            elif not username:
                error = "Username is required."
            elif len(username) < 3:
                error = "Username must be at least 3 characters."
            elif User.objects.filter(username=username).exists():
                error = "Username already taken."
            elif not email:
                error = "Email is required."
            elif User.objects.filter(email=email).exists():
                error = "Email already registered."
            elif not password or len(password) < 6:
                error = "Password must be at least 6 characters."
            elif password != confirm_password:
                error = "Passwords do not match."
            else:
                # Create user (inactive until email verified)
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    is_active=True  # Keep active but track verification separately
                )
                
                # Send verification email
                if send_verification_email(user, request):
                    success = "Account created! Please check your email to verify your account."
                else:
                    success = "Account created! However, we couldn't send the verification email. Please try logging in or contact support."

    if error:
        messages.error(request, error)
    if success:
        messages.success(request, success)

    context = {
        "error": error,
        "success": success,
        "firebase_config": settings.FIREBASE_CONFIG,
    }
    return render(request, "login.html", context)


@require_http_methods(["GET"])
def verify_email(request, token):
    """Handle email verification link."""
    try:
        verification = EmailVerification.objects.get(token=token)
        
        if verification.verified:
            messages.info(request, "Your email is already verified. You can log in.")
            return redirect("login")
        
        if verification.is_expired():
            messages.error(request, "This verification link has expired. Please request a new one.")
            return redirect("login")
        
        # Mark as verified
        verification.verified = True
        verification.save()
        
        messages.success(request, "Email verified successfully! You can now log in.")
        return redirect("login")
        
    except EmailVerification.DoesNotExist:
        messages.error(request, "Invalid verification link.")
        return redirect("login")


@require_http_methods(["POST"])
def resend_verification(request):
    """Resend verification email."""
    email = request.POST.get("email", "").strip().lower()
    
    try:
        user = User.objects.get(email=email)
        
        # Check if already verified
        try:
            verification = user.email_verification
            if verification.verified:
                messages.info(request, "Your email is already verified.")
                return redirect("login")
        except EmailVerification.DoesNotExist:
            pass
        
        # Send new verification email
        if send_verification_email(user, request):
            messages.success(request, "Verification email sent! Please check your inbox.")
        else:
            messages.error(request, "Failed to send verification email. Please try again.")
            
    except User.DoesNotExist:
        messages.error(request, "No account found with this email.")
    
    return redirect("login")





def logout_view(request):
    """
    Logout user.
    """
    logout(request)
    return redirect("login")


@login_required
@require_http_methods(["GET", "POST"])
def profile_view(request):
    """
    User profile page - view and edit profile information.
    """
    user = request.user
    
    if request.method == "POST":
        action = request.POST.get("action", "")
        
        if action == "update_profile":
            # Update basic profile info
            first_name = request.POST.get("first_name", "").strip()
            last_name = request.POST.get("last_name", "").strip()
            username = request.POST.get("username", "").strip()
            
            errors = []
            
            # Validate username
            if username and username != user.username:
                if User.objects.filter(username=username).exclude(id=user.id).exists():
                    errors.append("Username already taken.")
                elif len(username) < 3:
                    errors.append("Username must be at least 3 characters.")
                else:
                    user.username = username
            
            if not errors:
                user.first_name = first_name
                user.last_name = last_name
                user.save()
                messages.success(request, "Profile updated successfully!")
            else:
                for error in errors:
                    messages.error(request, error)
        
        elif action == "change_password":
            current_password = request.POST.get("current_password", "")
            new_password = request.POST.get("new_password", "")
            confirm_password = request.POST.get("confirm_password", "")
            
            if not user.check_password(current_password):
                messages.error(request, "Current password is incorrect.")
            elif len(new_password) < 6:
                messages.error(request, "New password must be at least 6 characters.")
            elif new_password != confirm_password:
                messages.error(request, "New passwords do not match.")
            else:
                user.set_password(new_password)
                user.save()
                # Re-authenticate to keep user logged in
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, "Password changed successfully!")
        
        elif action == "delete_account":
            password = request.POST.get("password", "")
            if user.check_password(password):
                user.delete()
                messages.success(request, "Your account has been deleted.")
                return redirect("login")
            else:
                messages.error(request, "Incorrect password. Account deletion cancelled.")
        
        return redirect("profile")
    
    # GET request - show profile page
    # Get user's projects and routes count
    projects = Project.objects.filter(owner=user)
    routes_count = ApiRoute.objects.filter(project__owner=user).count()
    
    # Check email verification status
    try:
        email_verified = user.email_verification.verified
    except:
        email_verified = False
    
    context = {
        "projects": projects,
        "projects_count": projects.count(),
        "routes_count": routes_count,
        "email_verified": email_verified,
    }
    
    return render(request, "profile.html", context)


@csrf_exempt
@require_http_methods(["POST"])
def validate_email(request):
    """
    HTMX endpoint: Check if email exists.
    """
    email = request.POST.get("email", "").strip()
    exists = User.objects.filter(email=email).exists()
    
    if exists:
        return HttpResponse(
            '<div class="alert alert-warning">Email already registered.</div>',
            status=400
        )
    else:
        return HttpResponse(
            '<div class="alert alert-success">Email available.</div>'
        )


@csrf_exempt
@require_http_methods(["POST"])
def validate_username(request):
    """
    HTMX endpoint: Check if username exists and meets basic length requirements.
    """
    username = request.POST.get("username", "").strip()
    
    if not username:
        return HttpResponse(
            '<div class="alert alert-warning">Username is required.</div>',
            status=400
        )
    
    if len(username) < 3:
        return HttpResponse(
            '<div class="alert alert-warning">Username must be at least 3 characters.</div>',
            status=400
        )
    
    exists = User.objects.filter(username=username).exists()
    
    if exists:
        return HttpResponse(
            '<div class="alert alert-warning">Username already taken.</div>',
            status=400
        )
    
    return HttpResponse(
        '<div class="alert alert-success">Username available.</div>'
    )


@csrf_exempt
@require_http_methods(["POST"])
def validate_json(request):
    """
    HTMX endpoint: Validate JSON input.
    """
    json_input = request.POST.get("response_json", request.POST.get("json_input", "")).strip()
    
    if not json_input:
        return HttpResponse('')
    
    try:
        json.loads(json_input)
        return HttpResponse(
            '<div class="flex items-center gap-3 px-4 py-3 bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/20 rounded-xl text-emerald-600 dark:text-emerald-400"><i class="bi bi-check-circle-fill text-lg"></i><span class="text-sm font-medium">Valid JSON - Ready to use</span></div>'
        )
    except json.JSONDecodeError as e:
        return HttpResponse(
            f'<div class="flex items-start gap-3 px-4 py-3 bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-xl text-red-600 dark:text-red-400"><i class="bi bi-exclamation-triangle-fill text-lg mt-0.5"></i><div class="text-sm"><div class="font-medium mb-1">Invalid JSON</div><div class="text-xs opacity-90">{str(e)}</div></div></div>'
        )


@csrf_exempt
@require_http_methods(["POST"])
def generate_slug(request):
    """
    HTMX endpoint: Auto-generate slug from project name.
    """
    name = request.POST.get("name", "").strip()
    
    if not name:
        return HttpResponse("")
    
    slug = slugify(name)
    
    # Check if slug already exists for this user
    if request.user.is_authenticated:
        exists = Project.objects.filter(owner=request.user, slug=slug).exists()
        if exists:
            return HttpResponse(
                f'<div class="alert alert-warning">Slug "{slug}" already exists. Try another name.</div>',
                status=400
            )
    
    return HttpResponse(f'<input type="text" name="slug" id="slug" class="form-control" value="{slug}">')


@login_required
@require_http_methods(["GET"])
def routes_list_fragment(request, project_id):
    """
    HTMX endpoint: Return only the routes table fragment for the given project.
    """
    project = get_object_or_404(Project, id=project_id, owner=request.user)
    routes = project.routes.all()
    
    html = """
    <table class="table table-striped table-sm">
        <thead>
            <tr>
                <th>Method</th>
                <th>Path</th>
                <th>Status</th>
                <th>Content-Type</th>
                <th>Active</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
    """
    
    if routes.exists():
        for route in routes:
            status_badge = '<span class="badge badge-success">Yes</span>' if route.is_active else '<span class="badge badge-secondary">No</span>'
            html += f"""
            <tr>
                <td><strong>{route.method}</strong></td>
                <td><code>{route.path}</code></td>
                <td>{route.status_code}</td>
                <td><small>{route.content_type}</small></td>
                <td>{status_badge}</td>
                <td>
                    <a href="/{request.user.username}/{project.slug}{route.path}" target="_blank" class="btn btn-sm btn-info">Test</a>
                </td>
            </tr>
            """
    else:
        html += '<tr><td colspan="6" class="text-muted text-center">No routes yet.</td></tr>'
    
    html += """
        </tbody>
    </table>
    """
    
    return HttpResponse(html)




@login_required
@require_http_methods(["GET", "POST"])
def create_project(request):
    """
    Form view to create a new project.
    """
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        slug = request.POST.get("slug", "").strip()
        description = request.POST.get("description", "").strip()

        # Auto-generate slug if not provided
        if not slug:
            slug = slugify(name)

        # Validate
        if not name:
            return render(
                request,
                "create_project.html",
                {"error": "Project name is required."},
            )

        # Check if project slug already exists for this user
        if Project.objects.filter(owner=request.user, slug=slug).exists():
            return render(
                request,
                "create_project.html",
                {"error": f"Project with slug '{slug}' already exists for you.", "form_data": request.POST},
            )

        # Create project
        project = Project.objects.create(
            owner=request.user,
            name=name,
            slug=slug,
            description=description,
        )

        return redirect("create_route_for_project", project_id=project.id)

    # GET request: show form
    user_projects = Project.objects.filter(owner=request.user)
    return render(
        request,
        "create_project.html",
        {"projects": user_projects},
    )



@csrf_exempt
@require_http_methods(["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
def dynamic_route_handler(request, username, project_slug, rest_of_path):
    """
    Dynamic route handler that serves JSON responses based on Project/ApiRoute.
    URL: /<username>/<project_slug>/<rest_of_path>
    """
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return HttpResponseNotFound(json.dumps({"error": "User not found"}), content_type="application/json")

    try:
        project = Project.objects.get(owner=user, slug=project_slug)
    except Project.DoesNotExist:
        return HttpResponseNotFound(
            json.dumps({"error": f"Project '{project_slug}' not found for user '{username}'"}),
            content_type="application/json",
        )

    # Build the full path with leading slash
    path = "/" + rest_of_path if rest_of_path else "/"

    try:
        route = ApiRoute.objects.get(project=project, method=request.method, path=path, is_active=True)
    except ApiRoute.DoesNotExist:
        # Check if route exists but is inactive
        try:
            inactive_route = ApiRoute.objects.get(project=project, method=request.method, path=path)
            return HttpResponseNotFound(
                json.dumps({"error": f"Route '{request.method} {path}' is inactive. Enable it to use.", "hint": "Go to route settings to activate it."}),
                content_type="application/json",
            )
        except ApiRoute.DoesNotExist:
            # List available routes for debugging
            available_routes = ApiRoute.objects.filter(project=project, is_active=True).values_list('method', 'path')
            route_list = [f"{m} {p}" for m, p in available_routes] if available_routes else []
            
            return HttpResponseNotFound(
                json.dumps({
                    "error": f"Route '{request.method} {path}' not found in project '{project_slug}'",
                    "available_routes": route_list if route_list else "No active routes found"
                }),
                content_type="application/json",
            )

    # Handle Email OTP routes
    if route.route_type == 'EMAIL_OTP':
        # Handle GET list action
        if request.method == 'GET':
            # Get all verified emails for this route
            verified_otps = EmailOTP.objects.filter(route=route, verified=True).values_list('email', flat=True).distinct()
            verified_emails = sorted(list(verified_otps))
            
            return HttpResponse(
                json.dumps({
                    "success": True,
                    "verified_emails": verified_emails,
                    "total_verified": len(verified_emails)
                }),
                status=200,
                content_type="application/json",
            )
        
        # Handle POST for send/verify actions
        try:
            request_data = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            return HttpResponse(
                json.dumps({"error": "Invalid JSON in request body"}),
                status=400,
                content_type="application/json",
            )
        
        action = request_data.get('action', 'send')
        email = request_data.get('email', '').strip()
        
        if not email:
            return HttpResponse(
                json.dumps({"error": "Email is required"}),
                status=400,
                content_type="application/json",
            )
        
        if action == 'send':
            # Generate and send OTP
            otp_instance = EmailOTP.objects.create(route=route, email=email)
            
            # Send email
            try:
                from django.core.mail import send_mail
                from django.utils.html import strip_tags
                
                subject = 'Your OTP Code'
                html_message = f'''
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #333;">Your OTP Code</h2>
                    <p>Your verification code is:</p>
                    <h1 style="color: #007bff; letter-spacing: 8px; font-size: 36px;">{otp_instance.otp}</h1>
                    <p>This code will expire in 10 minutes.</p>
                    <p style="color: #999; font-size: 12px;">If you didn't request this code, please ignore this email.</p>
                </body>
                </html>
                '''
                plain_message = strip_tags(html_message)
                
                send_mail(
                    subject,
                    plain_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                return HttpResponse(
                    json.dumps({"success": True, "message": "OTP sent to email"}),
                    status=200,
                    content_type="application/json",
                )
            except Exception as e:
                return HttpResponse(
                    json.dumps({"error": f"Failed to send OTP: {str(e)}"}),
                    status=500,
                    content_type="application/json",
                )
        
        elif action == 'verify':
            otp_code = request_data.get('otp', '').strip()
            
            if not otp_code:
                return HttpResponse(
                    json.dumps({"error": "OTP code is required"}),
                    status=400,
                    content_type="application/json",
                )
            
            # Find the latest OTP for this email and route
            try:
                otp_instance = EmailOTP.objects.filter(
                    route=route,
                    email=email,
                    verified=False
                ).latest('created_at')
                
                if otp_instance.is_expired():
                    return HttpResponse(
                        json.dumps({"error": "OTP has expired. Please request a new one."}),
                        status=400,
                        content_type="application/json",
                    )
                
                if otp_instance.attempts >= 3:
                    return HttpResponse(
                        json.dumps({"error": "Too many attempts. Please request a new OTP."}),
                        status=400,
                        content_type="application/json",
                    )
                
                otp_instance.attempts += 1
                otp_instance.save()
                
                if otp_instance.otp == otp_code:
                    otp_instance.verified = True
                    otp_instance.save()
                    return HttpResponse(
                        json.dumps({"success": True, "message": "OTP verified successfully", "email": email}),
                        status=200,
                        content_type="application/json",
                    )
                else:
                    return HttpResponse(
                        json.dumps({"error": "Invalid OTP code"}),
                        status=400,
                        content_type="application/json",
                    )
            except EmailOTP.DoesNotExist:
                return HttpResponse(
                    json.dumps({"error": "No OTP found. Please request one first."}),
                    status=400,
                    content_type="application/json",
                )
        
        elif action == 'list':
            # Get all verified emails for this route
            verified_otps = EmailOTP.objects.filter(route=route, verified=True).values_list('email', flat=True).distinct()
            verified_emails = sorted(list(verified_otps))
            
            return HttpResponse(
                json.dumps({
                    "success": True,
                    "verified_emails": verified_emails,
                    "total_verified": len(verified_emails)
                }),
                status=200,
                content_type="application/json",
            )
        else:
            return HttpResponse(
                json.dumps({"error": "Invalid action. Use 'send', 'verify', or 'list'"}),
                status=400,
                content_type="application/json",
            )

    # Validate request body if specified
    if route.request_body and request.method in ['POST', 'PUT', 'PATCH']:
        try:
            request_data = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            return HttpResponse(
                json.dumps({"error": "Invalid JSON in request body"}),
                status=400,
                content_type="application/json",
            )
        
        # Check if request body matches expected structure
        if request_data != route.request_body:
            return HttpResponse(
                json.dumps({
                    "error": "Request body does not match expected format",
                    "expected": route.request_body,
                    "received": request_data
                }),
                status=400,
                content_type="application/json",
            )

    # Prepare response data
    if route.response_json:
        response_data = route.response_json
    elif route.response_file:
        try:
            with route.response_file.open("r") as f:
                response_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            return HttpResponse(
                json.dumps({"error": f"Failed to read JSON file: {str(e)}"}),
                status=500,
                content_type="application/json",
            )
    else:
        return HttpResponse(
            json.dumps({"error": "No response configured for this route"}),
            status=500,
            content_type="application/json",
        )

    # Serialize and return response
    response_body = json.dumps(response_data)
    return HttpResponse(
        response_body,
        status=route.status_code,
        content_type=route.content_type,
    )


@login_required
@require_http_methods(["GET"])
def check_route_exists(request):
    """
    HTMX endpoint to check if a route with the same method and path already exists.
    """
    project_id = request.GET.get("project")
    method = request.GET.get("method", "GET").upper()
    path = request.GET.get("path", "").strip()
    
    if not project_id or not path:
        return HttpResponse("")
    
    # Add leading slash if not present
    if path and not path.startswith("/"):
        path = "/" + path
    
    try:
        project = get_object_or_404(Project, id=project_id, owner=request.user)
        route_exists = ApiRoute.objects.filter(
            project=project,
            method=method,
            path=path
        ).exists()
        
        if route_exists:
            return HttpResponse(
                f'<div class="flex items-start gap-3 px-4 py-3 bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/20 rounded-xl text-amber-600 dark:text-amber-400"><i class="bi bi-exclamation-circle-fill text-lg mt-0.5"></i><div class="text-sm"><div class="font-medium mb-1">Route Already Exists</div><div class="text-xs opacity-90">A {method} {path} route already exists in this project.</div></div></div>'
            )
        else:
            return HttpResponse("")
    except Exception:
        return HttpResponse("")


@login_required
@require_http_methods(["GET", "POST"])
def create_route(request, project_id=None):
    """
    Form view to create or edit API routes.
    Users can either paste JSON or upload a JSON file.
    """
    if project_id:
        project = get_object_or_404(Project, id=project_id, owner=request.user)
    else:
        # Default to user's first project or redirect to create one
        projects = Project.objects.filter(owner=request.user)
        if not projects.exists():
            return render(
                request,
                "create_route.html",
                {"error": "Please create a project first.", "projects": []},
            )
        project = projects.first()

    if request.method == "POST":
        method = request.POST.get("method", "POST").upper()
        path = request.POST.get("path", "").strip()
        route_type = request.POST.get("route_type", "STANDARD")
        status_code = int(request.POST.get("status_code", "200"))
        content_type = request.POST.get("content_type", "application/json")
        request_body_input = request.POST.get("request_body", "").strip()
        json_input = request.POST.get("response_json", "").strip()
        json_file = request.FILES.get("response_file")

        # Add leading slash if not present
        if path and not path.startswith("/"):
            path = "/" + path

        # Validate path
        if not path or path == "/":
            return render(
                request,
                "create_route.html",
                {
                    "error": "Path cannot be empty. Example: /users or /data/123",
                    "project": project,
                    "form_data": request.POST,
                },
            )

        # Parse request body if provided
        request_body = None
        if request_body_input:
            try:
                request_body = json.loads(request_body_input)
            except json.JSONDecodeError as e:
                return render(
                    request,
                    "create_route.html",
                    {
                        "error": f"Invalid request body JSON: {str(e)}",
                        "project": project,
                        "form_data": request.POST,
                    },
                )

        # For EMAIL_OTP routes, skip response validation
        if route_type == "EMAIL_OTP":
            response_json = {"type": "email_otp", "message": "Use action: send/verify with email and otp fields"}
            response_file = None
        else:
            # Validate exactly one of json_input or json_file is provided
            if not json_input and not json_file:
                return render(
                    request,
                    "create_route.html",
                    {
                        "error": "Provide either JSON input or upload a JSON file for the response.",
                        "project": project,
                        "form_data": request.POST,
                    },
                )
            
            if json_input and json_file:
                return render(
                    request,
                    "create_route.html",
                    {
                        "error": "Provide either JSON input or upload a JSON file, not both.",
                        "project": project,
                        "form_data": request.POST,
                    },
                )

            # Parse and validate JSON
            try:
                if json_input:
                    response_json = json.loads(json_input)
                    response_file = None
                else:
                    if not json_file.name.lower().endswith(".json"):
                        raise ValidationError("File must be a .json file.")
                    file_content = json_file.read().decode("utf-8")
                    json.loads(file_content)  # Validate it's valid JSON
                    response_json = None
                    response_file = json_file
            except json.JSONDecodeError as e:
                return render(
                    request,
                    "create_route.html",
                    {
                        "error": f"Invalid JSON: {str(e)}",
                        "project": project,
                        "form_data": request.POST,
                    },
                )
            except ValidationError as e:
                return render(
                    request,
                    "create_route.html",
                    {
                        "error": str(e),
                        "project": project,
                        "form_data": request.POST,
                    },
                )

        # Create or update route
        route, created = ApiRoute.objects.update_or_create(
            project=project,
            method=method,
            path=path,
            defaults={
                "route_type": route_type,
                "status_code": status_code,
                "content_type": content_type,
                "request_body": request_body,
                "response_json": response_json,
                "response_file": response_file,
            },
        )

        # Always create/update the GET /list route for EMAIL_OTP
        if route_type == "EMAIL_OTP":
            list_path = path + "/list" if path != "/" else "/list"
            ApiRoute.objects.update_or_create(
                project=project,
                method="GET",
                path=list_path,
                defaults={
                    "route_type": "EMAIL_OTP",
                    "status_code": 200,
                    "content_type": "application/json",
                    "response_json": {"type": "email_otp_list", "message": "Returns list of verified emails"},
                    "is_active": True,
                },
            )

        if created:
            messages.success(request, f"Route created: {method} {path}")
        else:
            messages.info(request, f"Route updated: {method} {path}")
        
        return redirect('route_detail', route_id=route.id)

    # GET request: show form
    return render(
        request,
        "create_route.html",
        {
            "project": project,
            "projects": Project.objects.filter(owner=request.user),
            "routes": project.routes.all(),
        },
    )
  

@login_required
def project_detail(request, project_id):
    # ""View project details and all routes.""
    project = get_object_or_404(Project, id=project_id, owner=request.user)
    routes = project.routes.all().order_by('-created_at')
    
    return render(request, "project_detail.html", {
        "project": project,
        "routes": routes,
    })


@login_required
def route_detail(request, route_id):
    # ""View route details.""
    route = get_object_or_404(ApiRoute, id=route_id, project__owner=request.user)
    
    # Format JSON for display
    if route.response_json:
        route.response_json = json.dumps(route.response_json, indent=2)
    
    return render(request, "route_detail.html", {
        "route": route,
    })


@login_required
def edit_route(request, route_id):
    # ""Edit an existing route - uses the same create_route form.""
    route = get_object_or_404(ApiRoute, id=route_id, project__owner=request.user)
    
    # Redirect to create_route with route_id as query parameter to indicate editing
    return redirect('edit_route', route_id=route_id)


@login_required
@require_http_methods(["GET", "POST"])
def edit_route_form(request, route_id):
    """
    Form view to edit an existing route.
    Similar to create_route but prefilled with existing data.
    """
    route = get_object_or_404(ApiRoute, id=route_id, project__owner=request.user)
    project = route.project

    if request.method == "POST":
        method = request.POST.get("method", "POST").upper()
        path = request.POST.get("path", "").strip()
        route_type = request.POST.get("route_type", route.route_type)
        status_code = int(request.POST.get("status_code", "200"))
        content_type = request.POST.get("content_type", "application/json")
        request_body_input = request.POST.get("request_body", "").strip()
        json_input = request.POST.get("response_json", "").strip()
        json_file = request.FILES.get("response_file")

        # Add leading slash if not present
        if path and not path.startswith("/"):
            path = "/" + path

        # Validate path
        if not path or path == "/":
            return render(
                request,
                "edit_route.html",
                {
                    "error": "Path cannot be empty. Example: /users or /data/123",
                    "project": project,
                    "route": route,
                    "form_data": request.POST,
                },
            )

        # Parse request body if provided
        request_body = None
        if request_body_input:
            try:
                request_body = json.loads(request_body_input)
            except json.JSONDecodeError as e:
                return render(
                    request,
                    "edit_route.html",
                    {
                        "error": f"Invalid request body JSON: {str(e)}",
                        "project": project,
                        "route": route,
                        "form_data": request.POST,
                    },
                )

        # For EMAIL_OTP routes, use default response and always create/update GET /list
        if route_type == "EMAIL_OTP":
            response_json = {"type": "email_otp", "message": "Use action: send/verify with email and otp fields"}
            response_file = None
            list_path = path + "/list" if path != "/" else "/list"
            ApiRoute.objects.update_or_create(
                project=project,
                method="GET",
                path=list_path,
                defaults={
                    "route_type": "EMAIL_OTP",
                    "status_code": 200,
                    "content_type": "application/json",
                    "response_json": {"type": "email_otp_list", "message": "Returns list of verified emails"},
                    "is_active": True,
                },
            )
        else:
            # Validate exactly one of json_input or json_file is provided
            if not json_input and not json_file:
                return render(
                    request,
                    "edit_route.html",
                    {
                        "error": "Provide either JSON input or upload a JSON file for the response.",
                        "project": project,
                        "route": route,
                        "form_data": request.POST,
                    },
                )
            
            if json_input and json_file:
                return render(
                    request,
                    "edit_route.html",
                    {
                        "error": "Provide either JSON input or upload a JSON file, not both.",
                        "project": project,
                        "route": route,
                        "form_data": request.POST,
                    },
                )

            # Parse and validate JSON
            try:
                if json_input:
                    response_json = json.loads(json_input)
                    response_file = None
                else:
                    if not json_file.name.lower().endswith(".json"):
                        raise ValidationError("File must be a .json file.")
                    file_content = json_file.read().decode("utf-8")
                    json.loads(file_content)  # Validate it's valid JSON
                    response_json = None
                    response_file = json_file
            except json.JSONDecodeError as e:
                return render(
                    request,
                    "edit_route.html",
                    {
                        "error": f"Invalid JSON: {str(e)}",
                        "project": project,
                        "route": route,
                        "form_data": request.POST,
                    },
                )
            except ValidationError as e:
                return render(
                    request,
                    "edit_route.html",
                    {
                        "error": str(e),
                        "project": project,
                        "route": route,
                        "form_data": request.POST,
                    },
                )

        # Update route
        route.method = method
        route.path = path
        route.route_type = route_type
        route.status_code = status_code
        route.content_type = content_type
        route.request_body = request_body
        route.response_json = response_json
        if response_file:
            route.response_file = response_file
        route.save()

        messages.success(request, f"Route updated: {method} {path}")
        return redirect('route_detail', route_id=route.id)

    # GET request: show form with prefilled data
    return render(
        request,
        "edit_route.html",
        {
            "project": project,
            "route": route,
            "projects": Project.objects.filter(owner=request.user),
        },
    )


@login_required
@require_http_methods(["POST"])
def delete_project(request, project_id):
    # ""Delete a project and all its routes.""
    project = get_object_or_404(Project, id=project_id, owner=request.user)
    project_name = project.name
    project.delete()
    messages.success(request, f'Project "{project_name}" deleted successfully.')
    return redirect('home')


@login_required
@require_http_methods(["POST"])
def delete_route(request, route_id):
    # ""Delete a route.""
    route = get_object_or_404(ApiRoute, id=route_id, project__owner=request.user)
    project_id = route.project.id
    route.delete()
    messages.success(request, 'Route deleted successfully.')
    return redirect('project_detail', project_id=project_id)
