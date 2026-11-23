from core.sanitization_verifier import verify_sanitization


# TEST 1: Existing file
existing_result = verify_sanitization(
    target_path="evidence/test_files/document.txt",
    sanitization_method="file_deletion",
    storage_type="filesystem",
)

print("\n--- TEST 1: EXISTING FILE ---")
print(existing_result)


# TEST 2: Missing file
missing_result = verify_sanitization(
    target_path="evidence/test_files/nonexistent.txt",
    sanitization_method="file_deletion",
    storage_type="filesystem",
)

print("\n--- TEST 2: MISSING FILE ---")
print(missing_result)


# TEST 3: Residual marker detection
residual_result = verify_sanitization(
    target_path="evidence/test_files/sanitization_probe.txt",
    sanitization_method="file_deletion",
    storage_type="filesystem",
    residual_marker="VANISH_RESIDUAL_TEST_2026_ABC123",
)

print("\n--- TEST 3: RESIDUAL MARKER DETECTION ---")
print(residual_result)
# TEST 4: Marker not detected
no_marker_result = verify_sanitization(
    target_path="evidence/test_files/sanitization_probe.txt",
    sanitization_method="file_deletion",
    storage_type="filesystem",
    residual_marker="MARKER_THAT_DOES_NOT_EXIST",
)

print("\n--- TEST 4: MARKER NOT DETECTED ---")
print(no_marker_result)