import sys
import os

# Ensure backend directory is in path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from utils import load_all_laws, get_relevant_sections, LAWS_DATA

print("--- Testing Load Laws ---")
load_all_laws()

print("\n--- Testing Search (Query: 'driving without license') ---")
results = get_relevant_sections("driving without license", limit=3)
print(results)

print("\n--- Testing Search (Query: 'murder') ---")
results_ipc = get_relevant_sections("murder", limit=3)
print(results_ipc)

print("\n--- Verification Complete ---")
