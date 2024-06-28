import json
from openai import OpenAI
from tenacity import retry, wait_random_exponential, stop_after_attempt
from bson.objectid import ObjectId
import datetime

GPT_MODEL = "gpt-3.5-turbo"
EMBEDDING_MODEL = "text-embedding-ada-002"
client = OpenAI()

@retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(3))
def embedding_request(text):
    response = client.embeddings.create(input=text, model=EMBEDDING_MODEL)
    return response

@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, tools=None, tool_choice=None, model=GPT_MODEL):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e

def add_expense_from_chat(user_id, question):
    messages = []
    current_date = datetime.datetime.now().date()
    output_format = {
        "user_id": user_id,
        "date": f"date mentioned by the user, otherwise use {current_date}",
        "category": "select category based on the user input only from this: [Entertainment, Food, Utilities, Education, Travel expenses, Gifts, Rent, Subscriptions, Other]",
        "amount": "amount mentioned in the user message, if not, add 0",
        "payment_method": "select payment_method based on the user input only from this: [UPI, Cash]",
        "description": "add description about the spend based on user input."
    }
    messages.append({"role": "system", "content": f"Read user input and only return a JSON response in this format: {output_format}. If there are multiple transaction details, return an array of JSON records in the given format."})
    messages.append({"role": "user", "content": question})
    print(messages,"\n\n")
    chat_response = chat_completion_request(messages)
    assistant_message = chat_response.choices[0].message
    messages.append(assistant_message)
    x = assistant_message.content
    x = x.replace("'", '"')
    expense_list = json.loads(x)
    return expense_list
