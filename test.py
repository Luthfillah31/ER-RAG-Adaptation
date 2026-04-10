# test.py
from models.dummy_model import RAGModel

# Initialize your Brain
bot = RAGModel()

# Ask a question!
question = "apakah bidang projek dosen bernama Kemas rahmat berbeda dengan tulisan papernya"
print(f"User: {question}\n")

# Run the pipeline
answer = bot.generate_answer(question)

print(f"\nFinal Answer: {answer}")