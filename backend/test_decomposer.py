from app.services.query_decomposer import decompose_claim_for_wikipedia

# Test claim (use this EXACT one)
claim = "The Amazon rainforest, which spans several countries in South America, is the largest tropical rainforest in the world and plays a crucial role in regulating the Earth's climate."

result = decompose_claim_for_wikipedia(claim)

print("\n=== DECOMPOSER OUTPUT ===\n")
print(result)
