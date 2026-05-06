# test.py
from models.dummy_model import RAGModel

# Initialize your Brain
bot = RAGModel()

# Ask a question!
question = "who are the co-authors of Kemas Rahmat Saleh Wiharja"
print(f"User: {question}\n")

# Run the pipeline
answer = bot.generate_answer(question)

print(f"\nFinal Answer: {answer}")