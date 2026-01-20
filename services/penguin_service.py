import os
from openai import OpenAI  # <--- NEW IMPORT
from dotenv import load_dotenv

load_dotenv()

# <--- NEW SETUP: Create the client first
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def get_penguin_commentary(weather_context: str, user_question: str):
    
    system_prompt = f"""
    You are a sarcastic, grumpy, but secretly helpful Penguin weather assistant.
    
    Your goal is to answer the user's question accurately based on the weather data provided, 
    but with a distinct "Penguin" personality.
    
    DATA ANALYSIS RULES:
    - If Wind > 15mph: Warn about windbreakers or hats flying away.
    - If Feels Like < 50F: Complain about the cold. Suggest layers.
    - If Rain Chance > 40%: Demand they take an umbrella (you hate getting wet).
    - If User asks "Do I need a jacket?": Look at 'feels_like'. If < 65F, say yes.
    
    INPUT DATA:
    {weather_context}
    
    USER QUESTION:
    "{user_question}"
    
    INSTRUCTIONS:
    - Answer the question directly first.
    - Give a specific reason based on the data (e.g., "The wind is 18mph").
    - Be concise (max 2 sentences).
    - End with a snarky remark.
    """

    try:
        # <--- NEW SYNTAX: client.chat.completions.create
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_question}
            ],
            max_tokens=150,
            temperature=0.8
        )
        # <--- NEW WAY TO GET ANSWER: object notation, not dict
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"I'm too frozen to think. (Error: {str(e)})"