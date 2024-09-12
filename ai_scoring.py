import os
from openai import OpenAI

api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

def evaluate_essay(essay_text, prompt):
    if not client:
        return "AI scoring is currently unavailable. Please try again later."
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert essay evaluator. Provide a score from 1 to 10 and brief feedback for the given essay."},
                {"role": "user", "content": f"Prompt: {prompt}\n\nEssay: {essay_text}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in AI evaluation: {str(e)}")
        return "Error in AI evaluation. Please try again later."

def parse_ai_response(ai_response):
    if ai_response == "AI scoring is currently unavailable. Please try again later.":
        return 0, ai_response
    
    try:
        lines = ai_response.split('\n')
        score = int(lines[0].split(':')[1].strip())
        feedback = '\n'.join(lines[1:]).strip()
        return score, feedback
    except Exception as e:
        print(f"Error parsing AI response: {str(e)}")
        return 0, "Error parsing AI response. Please review manually."
