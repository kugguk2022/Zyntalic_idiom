
from zyntalic import core
import re

print("--- Alphabet Verification ---")

# Regex for Hangul
hangul_regex = re.compile(r'[\uAC00-\uD7A3]')

errors = []
for i in range(50):
    word = core.generate_word(f"seed_{i}")
    print(f"{i}: {word}")
    if hangul_regex.search(word):
        errors.append(word)

if errors:
    print(f"FAILED: Found Hangul in {len(errors)} words: {errors}")
else:
    print("SUCCESS: No Hangul found in 50 generated words.")

# Check tail - should HAVE Hangul
tail = core.make_korean_tail("test")
print(f"Tail check: {tail}")
if not hangul_regex.search(tail):
    print("WARNING: Tail does not contain Hangul!")
else:
    print("SUCCESS: Tail contains Hangul.")
