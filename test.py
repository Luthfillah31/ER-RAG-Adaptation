# test.py
from models.dummy_model import RAGModel

# Initialize your Brain
bot = RAGModel()

# Ask a question!
question = "apakah ada dosen yang bidang projek berbeda dengan tulisan papernya"
print(f"User: {question}\n")

# Run the pipeline
answer = bot.generate_answer(question)

print(f"\nFinal Answer: {answer}")