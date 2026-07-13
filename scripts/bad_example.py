import os
import sqlite3

# VULNERABILITY 1: Hardcoded AWS Credentials
# The AI Reviewer should flag this immediately
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

def fetch_user_data(username):
    """
    VULNERABILITY 2: SQL Injection
    Using f-strings to inject user input directly into a SQL query.
    """
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # DANGEROUS: Do not do this in production
    query = f"SELECT * FROM users WHERE username = '{username}'"
    
    try:
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        print(f"Error executing query: {e}")
        return None

def ping_server(host):
    """
    VULNERABILITY 3: Command Injection
    Passing unvalidated user input directly to a system shell command.
    """
    # DANGEROUS: An attacker could pass "8.8.8.8; rm -rf /"
    command = f"ping -c 4 {host}"
    print(f"Executing: {command}")
    
    # Extremely unsafe usage of os.system
    os.system(command)

if __name__ == "__main__":
    print("This file contains intentional vulnerabilities for testing the AI PR Review Engine.")
    # Example usage that could be exploited
    fetch_user_data("admin' OR '1'='1")
    ping_server("localhost; echo 'Hacked!'")
