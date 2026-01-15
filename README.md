# 🚀 Dummy Server

**Dummy Server** is a lightweight web app that lets you create mock APIs in seconds.  
Paste JSON, define routes, and instantly get shareable endpoints — no backend setup required.

Built to unblock frontend devs, test edge cases, and demo product flows without touching real APIs.

🔗 **Live Demo:** https://sudarshankakde.pythonanywhere.com/

---

## ✨ Features

- 📄 Paste or upload JSON → instantly turn it into a mock API
- 🛣️ Create custom routes with:
  - HTTP methods (GET, POST, PUT, DELETE)
  - Custom status codes
  - Custom responses
- 🔐 **Email OTP send & verify routes** (useful for auth flows)
- 🤖 **AI-generated JSON responses** for routes
- ⏱️ Test edge cases:
  - 404 / 500 errors
  - Slow or delayed responses
- 🔗 Share clean URLs with teammates for demos & testing
- 🧭 Simple dashboard to manage all routes
- 🌗 Light / Dark mode support

---

## 🧠 Use Cases

- Frontend development while backend is still in progress
- Testing error states without modifying real APIs
- Demoing realistic product flows with mock data
- Rapid API prototyping before finalizing contracts
- Mobile app testing without setting up servers

---

## 🛠️ Tech Stack

- **Backend:** Django
- **Frontend:** HTMX + Tailwind CSS
- **Database:** SQLite (easy to swap)
- **Auth & Utilities:** Django built-ins
- **AI:** JSON response generation (LLM-powered)

---

## 🚀 Getting Started (Local Setup)

### 1️⃣ Clone the repository
```bash
git clone https://github.com/your-username/dummy-server.git
cd dummy-server
```

### 2️⃣ Create & activate virtual environment
```bash
python -m venv venv
source venv/bin/activate   # macOS / Linux
venv\Scripts\activate      # Windows
```

### 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Run migrations
```bash
python manage.py migrate
```

### 5️⃣ Start the server
```bash
python manage.py runserver
```

#### Open:
👉 http://127.0.0.1:8000/

## 📦 Project Structure (Simplified)
```bash
dummy-server/
├── core/              # Core app logic
├── routes/            # Mock API routes & responses
├── templates/         # HTMX templates
├── static/            # Tailwind / assets
├── manage.py
└── requirements.txt
```
--- 
## 🧪 Example

Create a route like:

#### POST /api/login


Response:
```json
{
  "success": true,
  "token": "dummy_jwt_token"
}
```

And instantly use it in your frontend or mobile app.

---

### 🤝 Contributing

- Contributions are welcome!

1. Fork the repo

2. Create a feature branch

3. Submit a PR

#### Ideas, issues, and feedback are appreciated 🙌

----

### 📄 License

MIT License — do whatever you want, just don’t sue 😄

-----

### 🧑‍💻 Author

Sudarshan Kakde
Building in public & shipping small dev tools 🚀

If this tool helped you, a ⭐ on GitHub would mean a lot!


