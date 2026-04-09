# test.py
from models.dummy_model import RAGModel

# Initialize your Brain
bot = RAGModel()

# Ask a question!
question = "how many lecturers with doctoral degrees are active"
print(f"User: {question}\n")

# Run the pipeline
answer = bot.generate_answer(question)

print(f"\nFinal Answer: {answer}")