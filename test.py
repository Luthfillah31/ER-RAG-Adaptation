# test.py
from models.dummy_model import RAGModel

# Initialize your Brain
bot = RAGModel()

# Ask a question!
question = "apa saya project yang selama ini dikerjakan pak kemas"
print(f"User: {question}\n")

# Run the pipeline
answer = bot.generate_answer(question)

print(f"\nFinal Answer: {answer}")