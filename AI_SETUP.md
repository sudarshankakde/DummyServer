# AI JSON Generator Setup

## Get Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key

## Configure Environment Variable

### Windows (PowerShell):
```powershell
$env:GEMINI_API_KEY="your_api_key_here"
```

### Windows (Command Prompt):
```cmd
set GEMINI_API_KEY=your_api_key_here
```

### Linux/Mac:
```bash
export GEMINI_API_KEY="your_api_key_here"
```

## Using the AI Generator

1. Go to Create Route page
2. Under "Response Body" in the JSON tab, click "Generate with AI"
3. Describe the JSON you want (e.g., "Create a user profile with name, email, age, and hobbies")
4. Click "Generate JSON"
5. The AI will generate and populate the textarea with formatted JSON

## Example Prompts

- "User profile with name, email, address, and phone"
- "Product listing with id, name, price, description, and images array"
- "Blog post with title, content, author, date, and tags"
- "API error response with status code, message, and details"
