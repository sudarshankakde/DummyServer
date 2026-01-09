# Dummy Server - Mock API Generator

A Django-based mock API server that allows users to create dynamic routes and serve JSON responses instantly. Users can upload JSON files or paste JSON directly, and routes are accessible via custom URLs.

## Features

✅ **Firebase Google OAuth** - One-click Google login  
✅ **Custom Email/Password Auth** - Traditional login/signup  
✅ **Project Management** - Organize routes by project  
✅ **Dynamic Route Serving** - `/username/project-slug/route` URL pattern  
✅ **JSON Upload & Paste** - Create routes with inline JSON or uploaded files  
✅ **HTMX Integration** - Real-time validation without page reloads  
✅ **Auto-slug Generation** - Automatic URL-friendly project names  
✅ **Live JSON Validation** - Instant feedback on JSON syntax  
✅ **Admin Panel** - Full CRUD management of projects and routes  

## Architecture

### Models

**Project**
- `owner` (ForeignKey: User)
- `name` (CharField)
- `slug` (SlugField, unique per owner)
- `description` (TextField)
- `created_at`, `updated_at` (Timestamps)

**ApiRoute**
- `project` (ForeignKey: Project)
- `method` (CharField: GET, POST, PUT, PATCH, DELETE)
- `path` (CharField, must start with `/`)
- `status_code` (PositiveSmallIntegerField, default: 200)
- `content_type` (CharField, default: `application/json`)
- `response_json` (JSONField, nullable)
- `response_file` (FileField for `.json` files, nullable)
- `is_active` (BooleanField)
- Constraint: Exactly one of `response_json` or `response_file` must be set
- Unique constraint on `(project, method, path)`

## URLs

### Authentication
- `GET /login/` - Login/signup page
- `POST /login/` - Submit credentials
- `GET /logout/` - Logout
- `POST /auth/firebase/` - Firebase authentication callback

### Projects & Routes
- `GET /create-project/` - Create project form
- `POST /create-project/` - Submit new project
- `GET /create-route/` - Create route (uses first project)
- `POST /create-route/` - Submit new route
- `GET /create-route/<project_id>/` - Create route for specific project

### HTMX Endpoints
- `POST /htmx/validate-email/` - Check if email exists
- `POST /htmx/validate-json/` - Validate JSON syntax
- `POST /htmx/generate-slug/` - Auto-generate slug from name
- `GET /htmx/routes-list/<project_id>/` - Load routes table fragment

### Dynamic Routes
- `GET /<username>/<project_slug>/<rest_of_path>` - Serve mock JSON

## Usage

### Setup

1. **Configure Python Environment**
   ```bash
   cd E:\Coding\DummyServer\server
   py -m venv venv
   venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install django
   ```

3. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

4. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

5. **Start Server**
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

### Access Points

| Route | Purpose |
|-------|---------|
| `http://localhost:8000/` | Home |
| `http://localhost:8000/login/` | Login/Signup |
| `http://localhost:8000/create-project/` | Create project |
| `http://localhost:8000/create-route/` | Create route |
| `http://localhost:8000/admin/` | Admin panel |

### Example Flow

1. **Login**
   - Click "Continue with Google" or use email/password
   - Google: Instant login if you have a Google account
   - Email: Create account with email and password (auto-generates username)

2. **Create Project**
   - Navigate to "Create Project"
   - Enter project name (slug auto-generated)
   - Add optional description

3. **Create Route**
   - Go to "Create Route" or select project
   - Set HTTP method (GET, POST, etc.)
   - Set path (e.g., `/users`, `/api/data`)
   - Set status code (default: 200)
   - Paste JSON or upload `.json` file

4. **Test Route**
   - URL format: `http://localhost:8000/username/project-slug/path`
   - Example: `http://localhost:8000/john/myproject/users`
   - Returns stored JSON with specified status code and content-type

## HTMX Features

### Real-Time Email Validation
- As users type email on login form, checks if already registered
- Shows "Email available" or "Email already registered"

### Auto-Slug Generation
- When creating a project, typing the name auto-generates a slug
- 500ms debounce prevents excessive requests
- Checks for slug uniqueness per user

### Live JSON Validation
- When pasting JSON in route form, validates syntax in real-time
- 1s debounce
- Shows "Valid JSON!" or error message

### Dynamic Routes Table
- Routes list loads without page refresh
- Table updates after route creation

## Firebase Configuration

Firebase credentials are embedded in the template:
- **API Key**: `AIzaSyDsmuDbiXKtFjQnrKf7SUrAYd1aQ49NBjM`
- **Auth Domain**: `sudarshankakde-5d03b.firebaseapp.com`
- **Project ID**: `sudarshankakde-5d03b`

Google Sign-In button appears on login page. Clicking it opens Google auth popup.

## File Structure

```
server/
├── manage.py
├── db.sqlite3
├── server/
│   ├── __init__.py
│   ├── settings.py (Django config + Firebase)
│   ├── urls.py (All routes)
│   ├── views.py (Auth, projects, routes, HTMX endpoints)
│   ├── models.py (Project, ApiRoute)
│   ├── admin.py (Admin configuration)
│   ├── asgi.py
│   ├── wsgi.py
│   └── __pycache__/
├── migrations/
│   └── 0001_initial.py
├── templates/
│   ├── Base.html (HTMX + Bootstrap)
│   ├── home.html
│   ├── login.html (Firebase + custom auth)
│   ├── create_project.html (Auto-slug via HTMX)
│   ├── create_route.html (JSON validation via HTMX)
└── media/
    └── routes/ (Uploaded JSON files)
```

## API Response Format

### Success
```json
GET /johndoe/myapi/users
```
Returns:
```
HTTP/1.1 200 OK
Content-Type: application/json

{"users": [{"id": 1, "name": "John"}]}
```

### Error (Route not found)
```
HTTP/1.1 404 Not Found
Content-Type: application/json

{"error": "Route 'GET /users' not found in project 'myapi'"}
```

## Admin Features

Visit `/admin/` to:
- Create/edit/delete projects
- Create/edit/delete routes
- Set route status codes and content types
- Enable/disable routes
- View user projects and routes

## Development Notes

- Django 4.2.5 with SQLite database
- Bootstrap 4.6 for styling
- HTMX 1.9.10 for dynamic interactions
- Firebase JS SDK 12.7.0 for Google auth
- Auto-reload enabled during development

## Future Enhancements

- [ ] Response headers customization
- [ ] Route versioning
- [ ] Rate limiting per route
- [ ] Request logging
- [ ] Custom middleware support
- [ ] Route templates/placeholders
- [ ] API documentation generation

## Troubleshooting

**Firebase Google login not working?**
- Ensure Firebase credentials are correct
- Check browser console for errors
- Verify Google account is logged in

**Slug conflict?**
- Each user can have unique slugs
- System auto-appends random suffix if duplicate

**JSON file upload fails?**
- Only `.json` files are allowed
- File must be valid JSON
- Maximum file size depends on server config

**Routes not showing?**
- Ensure route `is_active` is enabled
- Check project slug matches URL
- Verify HTTP method matches (GET vs POST)

---

Created: January 8, 2026  
Django Version: 4.2.5  
Python: 3.13
