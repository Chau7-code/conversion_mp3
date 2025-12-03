"""Test script for timecode parser - comprehensive test"""
import sys
sys.path.insert(0, '.')
import downloader

# Test cases from user's example: 19.30;36.30;40.30;49.03;52.36;1.00.00;1.07.00;1.09.00;1h11.30;1h13;1h16.11;1h21
test_cases = [
    # Basic formats
    ("90", 90),                          # Secondes
    ("1.30", 90),                        # MM.SS
    ("1:30", 90),                        # MM:SS
    
    # Hour formats
    ("1h", 3600),                        # 1 heure
    ("1H", 3600),                        # 1 heure (majuscule)
    ("1h07", 4020),                      # 1h + 7 minutes = 3600 + 420
    ("2H30", 9000),                      # 2h + 30 minutes = 7200 + 1800
    
    # HH:MM:SS format
    ("1:30:45", 5445),                   # 1h + 30m + 45s = 3600 + 1800 + 45
    
    # User's specific examples
    ("19.30", 1170),                     # 19m + 30s = 1140 + 30
    ("36.30", 2190),                     # 36m + 30s = 2160 + 30
    ("40.30", 2430),                     # 40m + 30s = 2400 + 30
    ("49.03", 2943),                     # 49m + 3s = 2940 + 3
    ("52.36", 3156),                     # 52m + 36s = 3120 + 36
    ("1.00.00", 3600),                   # 1h + 0m + 0s = 3600
    ("1.07.00", 4020),                   # 1h + 7m + 0s = 3600 + 420
    ("1.09.00", 4140),                   # 1h + 9m + 0s = 3600 + 540
    ("1h11.30", 4290),                   # 1h + 11m + 30s = 3600 + 660 + 30
    ("1h13", 4380),                      # 1h + 13m = 3600 + 780
    ("1h16.11", 4571),                   # 1h + 16m + 11s = 3600 + 960 + 11
    ("1h21", 4860),                      # 1h + 21m = 3600 + 1260
]

print("Testing timecode parser with user's examples...\n")
all_passed = True

for timecode_str, expected in test_cases:
    try:
        result = downloader.parse_timecode(timecode_str)
        if result == expected:
            print(f"[OK] '{timecode_str}' -> {result}s (expected {expected}s)")
        else:
            print(f"[FAIL] '{timecode_str}' -> {result}s (expected {expected}s)")
            all_passed = False
    except Exception as e:
        print(f"[ERROR] '{timecode_str}' -> {e}")
        all_passed = False

print("\n" + ("="*60))
if all_passed:
    print("[SUCCESS] All tests passed!")
else:
    print("[FAILED] Some tests failed!")

# Test the exact user's input
print("\n" + ("="*60))
print("Testing user's exact input string:")
user_input = "19.30;36.30;40.30;49.03;52.36;1.00.00;1.07.00;1.09.00;1h11.30;1h13;1h16.11;1h21"
timecode_parts = user_input.split(';')
print(f"Input: {user_input}\n")

try:
    timecodes = [downloader.parse_timecode(tc.strip()) for tc in timecode_parts]
    print(f"[SUCCESS] Parsed {len(timecodes)} timecodes:")
    for i, (tc_str, tc_val) in enumerate(zip(timecode_parts, timecodes)):
        print(f"  {i+1}. '{tc_str}' -> {tc_val}s")
except Exception as e:
    print(f"[ERROR] Failed to parse: {e}")
