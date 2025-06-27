#!/usr/bin/env python3
"""Claude CLI with session continuity - follows bin/docs/CONVENTION.yaml"""
import subprocess
import sys
from session import (
    parse_json, add_to_history, build_context, 
    extract_assistant_text, SessionHistory
)

def run_claude_command(prompt: str, continue_session: bool = False) -> subprocess.Popen:
    """Create Claude subprocess with proper arguments"""
    base_cmd = ["claude", "--output-format", "stream-json", "--verbose", "--print", prompt]
    if continue_session:
        base_cmd.append("--continue")
    return subprocess.Popen(base_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def process_stream(process: subprocess.Popen, history: SessionHistory) -> SessionHistory:
    """Process streaming output and update history"""
    updated_history = history
    
    for line in process.stdout:
        print(line.strip())  # Echo the stream
        
        result = parse_json(line.strip())
        if result["ok"]:
            data = result["data"]
            # Extract assistant responses
            if data.get("type") == "assistant":
                if text := extract_assistant_text(data):
                    updated_history = add_to_history(updated_history, "assistant", text)
                    
    return updated_history

def create_session_loop():
    """Create interactive session loop"""
    history: SessionHistory = []
    
    print("Claude session (type 'exit' to quit)")
    
    while True:
        try:
            user_input = input("> ")
            if user_input.lower() == "exit":
                break
                
            # Build prompt with context
            if history:
                context = build_context(history)
                full_prompt = f"{context}\n\nUser: {user_input}"
            else:
                full_prompt = user_input
                
            # Run command
            process = run_claude_command(full_prompt, continue_session=bool(history))
            
            # Process response
            history = add_to_history(history, "user", user_input)
            history = process_stream(process, history)
            
            # Wait for completion
            process.wait()
            
        except KeyboardInterrupt:
            print("\nInterrupted")
            break
        except Exception as e:
            print(f"Error: {e}")

# In-source tests
def test_run_claude_command_basic():
    proc = run_claude_command("test", continue_session=False)
    assert proc.args[-1] == "test"
    assert "--continue" not in proc.args
    proc.terminate()

def test_run_claude_command_continue():
    proc = run_claude_command("test", continue_session=True)
    assert "--continue" in proc.args
    proc.terminate()

if __name__ == "__main__":
    create_session_loop()