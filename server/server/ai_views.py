import json
import time
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.conf import settings

@login_required
@require_http_methods(["POST"])
def generate_json_ai(request):
    """Generate JSON using Gemini AI based on user prompt."""
    try:
        data = json.loads(request.body)
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return JsonResponse({'error': 'Prompt is required'}, status=400)
        
        # Configure Gemini API
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            return JsonResponse({'error': 'Gemini API key not configured. Please set GEMINI_API_KEY environment variable.'}, status=500)
        
        genai.configure(api_key=api_key)
        
        # Try different models
        models_to_try = ["gemini-2.5-flash","gemini-2.0-flash", 'gemini-pro', 'gemini-1.5-pro', 'gemini-1.5-flash']
        model = None
        last_error = None
        
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                break
            except Exception as e:
                last_error = str(e)
                continue
        
        if not model:
            return JsonResponse({'error': f'No available models. Last error: {last_error}'}, status=500)
        
        # Enhanced prompt for better JSON generation
        full_prompt = f"""Generate a valid JSON response based on this description: {prompt}

Requirements:
- Output ONLY the JSON, no explanations or markdown
- Use proper JSON formatting with correct indentation
- Include realistic sample data
- Ensure all keys and string values use double quotes
- Make the response practical and usable for an API

Generate the JSON:"""
        
        # Generate content with retry logic
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = model.generate_content(full_prompt)
                generated_text = response.text.strip()
                break
            except ResourceExhausted as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    return JsonResponse({
                        'error': 'API quota exceeded. The free tier has rate limits. Please try again later or upgrade your plan at https://ai.google.dev/pricing'
                    }, status=429)
            except Exception as e:
                error_msg = str(e)
                if '429' in error_msg or 'quota' in error_msg.lower():
                    return JsonResponse({
                        'error': 'API quota exceeded. The free tier has rate limits. Please try again later or upgrade your plan at https://ai.google.dev/pricing'
                    }, status=429)
                raise
        
        # Clean up the response (remove markdown code blocks if present)
        if generated_text.startswith('```json'):
            generated_text = generated_text[7:]
        if generated_text.startswith('```'):
            generated_text = generated_text[3:]
        if generated_text.endswith('```'):
            generated_text = generated_text[:-3]
        generated_text = generated_text.strip()
        
        # Validate it's valid JSON
        try:
            parsed = json.loads(generated_text)

            # Pretty print the JSON
            formatted_json = json.dumps(parsed, indent=2)
            return JsonResponse({'json': formatted_json})
        except json.JSONDecodeError:
            return JsonResponse({'error': 'AI generated invalid JSON. Please try rephrasing your prompt.'}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': f'Error generating JSON: {str(e)}'}, status=500)
