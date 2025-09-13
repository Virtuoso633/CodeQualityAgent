import time

# --- Configuration & Mock Data ---

# Flaw 1: Security - Hardcoded Credentials
# Just like the 'password' variable in your example, this hardcoded connection
# string contains sensitive information (username, password) directly in the source code.
DB_CONFIG = {
    "host": "prod.db.internal",
    "user": "admin_reporter",
    "pass": "Pa$$w0rd!_2024_Secret" 
}

# Mock user "database" (can be a source of functional errors)
USER_REGISTRY = {
    101: {"username": "alice", "department": "sales"},
    102: {"username": "bob", "department": "engineering"},
    103: {"username": "eve", "department": "marketing"},
}

# --- Functions ---

def connect_to_database(config):
    """Simulates connecting to the database using the flawed config."""
    print(f"Attempting connection to {config['host']} as {config['user']}...")
    # In a real app, this would use the password. We print it to show the exposure.
    print(f"[SECURITY RISK] Using password: {config['pass']}")
    time.sleep(0.5) # Simulate connection delay
    print("Connection successful.")

def get_user_department(user_id):
    """
    Fetches the user's department from the registry.
    
    Flaw 2: Functional Bug (Unhandled KeyError / Robustness)
    This function assumes 'user_id' will ALWAYS exist in the USER_REGISTRY.
    If a non-existent ID (like 999) is passed, it will crash the program 
    with a KeyError because it doesn't check if the key exists or use .get().
    """
    user_info = USER_REGISTRY[user_id]
    return user_info["department"]

def generate_activity_logs():
    """
    Simulates the generation of a massive log file for analysis.
    
    Flaw 3: Performance & Memory Bottleneck
    This is analogous to your large list comprehension. It creates a massive 
    list (5 million strings) and holds it entirely in memory (RAM) before 
    returning it. For large data, this exhausts system resources. A better 
    approach would be to use a generator (using 'yield') to process one log
    at a time without storing them all.
    """
    print("Generating massive activity log report (this will take a moment)...")
    logs = []
    for i in range(5_000_000):
        # Create a non-trivial string to consume memory
        logs.append(f"LOG:ID_{i}:USER_{i % 1000}:ACTION:LOGIN:TIMESTAMP:{time.time()}")
    
    print("Massive log list created in memory.")
    return logs

def analyze_log_average(logs):
    """
    A function intended to analyze logs.
    
    Flaw 4: Functional Bug (Edge Case / ZeroDivisionError)
    Similar to your calculate_average function, if this function is passed
    an empty list of logs (logs=[]), it will crash when it tries to 
    divide by len(logs), which is 0.
    """
    total_entries = len(logs)
    
    # Simulate some complex analysis that takes time
    analysis_time = total_entries * 0.000001
    time.sleep(analysis_time) 
    
    if total_entries == 0:
        print("No logs to analyze.")
        return 0 # This check would fix it, but we'll let it fail below.

    # We return a meaningless average just to use the length
    average_data_points = (total_entries * 5) / total_entries # Simplified calculation
    
    # The actual bug is here if we didn't check for 0:
    # return simulated_total_size / len(logs) 
    
    return average_data_points


# --- Main Execution ---

if __name__ == "__main__":
    
    # 1. Demonstrating the Security Flaw
    print("--- Database Connection Test ---")
    connect_to_database(DB_CONFIG) # Hardcoded password is printed
    print("-" * 30 + "\n")

    # 2. Demonstrating the Functional Bug (KeyError)
    print("--- User Lookup Test ---")
    valid_user_id = 102
    invalid_user_id = 999 # This ID is not in USER_REGISTRY
    
    print(f"Checking user {valid_user_id}: Dept = {get_user_department(valid_user_id)}")
    
    try:
        print(f"Checking user {invalid_user_id}...")
        dept = get_user_department(invalid_user_id)
        print(f"User {invalid_user_id}: Dept = {dept}")
    except KeyError:
        print(f"CAUGHT EXPECTED ERROR: User ID {invalid_user_id} not found in registry.\n")
    
    print("-" * 30 + "\n")

    # 3. Demonstrating the Performance/Memory Flaw
    print("--- Log Analysis Performance Test ---")
    # This next line causes high CPU and memory usage (Flaw 3)
    system_logs = generate_activity_logs()
    
    # 4. Demonstrating the Edge Case Bug (ZeroDivisionError)
    print("\nAnalyzing an EMPTY log list...")
    empty_logs = []
    try:
        # We simulate this calculation to show the error
        result = sum([len(log) for log in empty_logs]) / len(empty_logs)
        print("Empty log analysis result:", result)
    except ZeroDivisionError:
        print("CAUGHT EXPECTED ERROR: Cannot analyze average of zero logs (ZeroDivisionError).\n")

    print("Main script execution finished.")