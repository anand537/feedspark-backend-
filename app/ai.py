#Encapsulates  AI logic (OpenAI API interaction, NLP processing)
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def generate_feedback(rubric, performance, instructions=None):
    """
    Generate feedback using OpenAI.
    rubric: The template text or rubric description.
    performance: A list of dictionaries containing criterion details and scores.
    """
    # Format performance data into a readable string
    performance_str = ""
    if isinstance(performance, list):
        for item in performance:
            performance_str += f"- {item.get('criterion', 'Unknown')}: {item.get('score')}/{item.get('max_score', 10)} (Remarks: {item.get('remarks', 'None')})\n"
    else:
        performance_str = str(performance)

    prompt = f"Template/Style Guide: {rubric}\n\nStudent Performance:\n{performance_str}\n"
    if instructions:
        prompt += f"\nAdditional Instructions: {instructions}\n"
    prompt += "\nGenerate constructive feedback for the student based on the template and performance above."
    
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=150,
        temperature=0.7
    )
    return response.choices[0].text.strip()
