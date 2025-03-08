import lmstudio as lms

model = lms.llm("hermes-3-llama-3.2-3b")
result = model.respond("I want to add fertilizer in my 100 ekor field where I am cultivating rice. How much fertilizer would I need?")

print(result)
