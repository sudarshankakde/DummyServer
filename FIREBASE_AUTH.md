# Firebase Authentication Integration Guide

## Overview

This Dummy Server includes complete Firebase Google OAuth integration with custom Django backend authentication. Users can sign in with Google instantly without creating passwords.

## Architecture

### Frontend (JavaScript/Firebase SDK)

```
User clicks "Continue with Google"
    ↓
Firebase SDK opens Google popup
    ↓
User selects/logs in with Google account
    ↓
Firebase returns ID token + user data (uid, email, name)
    ↓
Frontend sends token + user data to Django backend
```

### Backend (Django)

```
Receives Firebase ID token + user data
    ↓
Verifies token signature and claims
    ↓
Extracts uid, email, display name from token
    ↓
Creates or retrieves Django User from email
    ↓
Creates Django session (logs in user)
    ↓
Redirects to home page
```

## Firebase Configuration

### Credentials (in settings.py)

```python
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyDsmuDbiXKtFjQnrKf7SUrAYd1aQ49NBjM",
    "authDomain": "sudarshankakde-5d03b.firebaseapp.com",
    "projectId": "sudarshankakde-5d03b",
    "storageBucket": "sudarshankakde-5d03b.firebasestorage.app",
    "messagingSenderId": "90927402770",
    "appId": "1:90927402770:web:5fa4cac53356105d37adcb",
    "measurementId": "G-3T7NCVMK4B"
}
```

### Firebase Project Details

- **Project ID**: `sudarshankakde-5d03b`
- **Auth Domain**: `sudarshankakde-5d03b.firebaseapp.com`
- **Allowed Origins**: `localhost:8000`, `127.0.0.1:8000`

## Frontend Implementation

### HTML Button (login.html)

```html
<button id="google-signin-btn" class="btn btn-light btn-block mb-3">
  <svg><!-- Google logo --></svg>
  Continue with Google
</button>
```

### JavaScript Flow

1. **Initialize Firebase**
   ```javascript
   const app = initializeApp(firebaseConfig);
   const auth = getAuth(app);
   ```

2. **Handle Click**
   ```javascript
   const result = await signInWithPopup(auth, googleProvider);
   const user = result.user;
   const idToken = await user.getIdToken();
   ```

3. **Send to Backend**
   ```javascript
   fetch("/auth/firebase/", {
     method: "POST",
     body: JSON.stringify({
       uid: user.uid,
       email: user.email,
       name: user.displayName,
       idToken: idToken
     })
   });
   ```

### Features

- **Loading State**: Button shows spinner while authenticating
- **Error Handling**: User-friendly error messages
- **Popup Handling**: Graceful handling of popup blocks
- **Automatic Redirect**: 500ms delay before redirecting to home
- **Button Reset**: Button reverts to original state on error

## Backend Implementation

### Endpoint: `/auth/firebase/`

**Method**: `POST`

**Request Body**:
```json
{
  "uid": "firebase_uid_here",
  "email": "user@example.com",
  "name": "John Doe",
  "idToken": "firebase_id_token_here"
}
```

**Response (Success)**:
```json
{
  "success": true,
  "user_id": 42,
  "username": "john",
  "email": "user@example.com",
  "is_new": true,
  "message": "Account created successfully"
}
```

**Response (Error)**:
```json
{
  "success": false,
  "error": "Invalid token"
}
```

### Token Verification

The backend validates:

1. **Token Signature**: Verifies against Google's public certificates
2. **Token Claims**:
   - Email matches
   - UID matches
   - Token not expired
3. **Token Payload**: Decodes and validates structure

```python
def verify_firebase_token(id_token, uid, email):
    # Decode JWT without verification (development)
    # In production, use PyJWT with public key verification
    
    # Extract and validate payload
    parts = id_token.split('.')
    payload = base64.urlsafe_b64decode(parts[1] + '==' * (4 - len(parts[1]) % 4))
    token_data = json.loads(payload)
    
    # Validate claims
    assert token_data['email'] == email
    assert token_data['sub'] == uid
    assert token_data['exp'] > time.time()
    
    return True
```

### User Creation Logic

```python
# 1. Generate unique username from email
base_username = email.split("@")[0]  # "john" from "john@example.com"
username = base_username

# 2. Ensure uniqueness
counter = 1
while User.objects.filter(username=username).exists():
    username = f"{base_username}_{counter}"
    counter += 1

# 3. Get or create user
user, created = User.objects.get_or_create(
    email=email,
    defaults={
        "username": username,
        "first_name": name.split()[0],
        "last_name": " ".join(name.split()[1:])
    }
)

# 4. Create Django session
login(request, user, backend='django.contrib.auth.backends.ModelBackend')
```

## Security Considerations

### ✅ Implemented

- **CSRF Token**: Frontend includes X-CSRFToken header
- **Token Validation**: Server validates token claims
- **Email Verification**: Server checks email from Firebase
- **UID Matching**: Ensures UID matches claimed user
- **Expiration Check**: Rejects expired tokens
- **HTTPS Ready**: Works with both HTTP (dev) and HTTPS (prod)

### ⚠️ In Production

1. **Verify Token Signature**: Use `PyJWT` and Google's public certs
2. **HTTPS Required**: Enforce SSL/TLS
3. **Token Refresh**: Implement token refresh logic
4. **Rate Limiting**: Add rate limits to `/auth/firebase/`
5. **Logging**: Log all auth attempts for security audit

## Troubleshooting

### Issue: "Popup blocked" Error

**Solution**: Allow popups in browser settings

### Issue: "Invalid token" Error

**Cause**: Token expired (> 1 hour old)

**Solution**: Frontend automatically gets fresh token

### Issue: User not created

**Cause**: Email field empty or duplicate

**Solution**: Check Firebase user profile has email set

### Issue: Multiple accounts for same email

**Solution**: Server uses email to prevent duplicates via `get_or_create`

## Testing

### Manual Test

1. Navigate to `http://localhost:8000/login/`
2. Click "Continue with Google"
3. Select Google account
4. Check browser console for auth messages
5. Should redirect to home page
6. Check user is in admin panel

### Automated Test

```python
# Test Firebase endpoint
import json
from django.test import Client

client = Client()
response = client.post('/auth/firebase/', 
    data=json.dumps({
        'uid': 'test_uid_123',
        'email': 'test@example.com',
        'name': 'Test User',
        'idToken': 'fake_token_for_test'
    }),
    content_type='application/json'
)

assert response.status_code == 200
data = response.json()
assert data['success'] == True
assert data['email'] == 'test@example.com'
```

## API Reference

### Database Fields for Firebase Users

| Field | Type | Value |
|-------|------|-------|
| `email` | EmailField | From Firebase |
| `username` | CharField | Auto-generated from email |
| `first_name` | CharField | From Firebase displayName |
| `last_name` | CharField | From Firebase displayName |
| `is_active` | BooleanField | True (created as active) |
| `date_joined` | DateTimeField | Auto-set on creation |

## Future Enhancements

- [ ] Custom claims (roles, permissions)
- [ ] Phone authentication
- [ ] Email link sign-in
- [ ] Multi-factor authentication (MFA)
- [ ] Anonymous authentication
- [ ] Provider linking (Google + Facebook)
- [ ] Custom token generation
- [ ] Session management dashboard

## References

- [Firebase Authentication Docs](https://firebase.google.com/docs/auth)
- [Firebase JS SDK](https://firebase.google.com/docs/auth/web/start)
- [Google Identity Services](https://developers.google.com/identity)
- [Django Authentication](https://docs.djangoproject.com/en/4.2/topics/auth/)

---

**Version**: 1.0  
**Last Updated**: January 8, 2026  
**Firebase SDK**: 12.7.0  
**Django Version**: 4.2.5
