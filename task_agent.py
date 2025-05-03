import os
import json
import subprocess
import requests
from datetime import datetime
from time import sleep
from config import API_KEY, MODEL, ENDPOINT

HISTORY_FILE = "history.json"

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def append_to_history(role, content):
    history = load_history()
    history.append({
        "timestamp": get_timestamp(),
        "role": role,
        "content": content
    })
    save_history(history)

def show_history():
    history = load_history()
    if not history:
        print("📭 No history found.")
        return
    print("\n📜 Command History:\n")
    for entry in history:
        print(f"[{entry['timestamp']}] {entry['role'].capitalize()}: {entry['content']}\n")

def get_ai_response(messages):
    response = requests.post(
        ENDPOINT,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "HTTP-Referer": "http://localhost",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": messages
        }
    )
    return response.json()["choices"][0]["message"]["content"]

def execute_commands(commands):
    for cmd in commands:
        print(f"⚙️ Running: {cmd}")
        try:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error:\n{e.stderr}")
            return False
    return True

def main():
    print("🤖 AI Agent with Mistral 7B via OpenRouter")
    print("Type your task in natural language.")
    print("Type 'history' to see previous commands or 'exit' to quit.\n")

    messages = [{
        "role": "system",
        "content": "You are an AI agent that returns shell commands to perform the user's task on their local computer."
    }]

    while True:
        task = input("💡 Task: ").strip()

        if task.lower() in ["exit", "quit"]:
            break
        if task.lower() == "history":
            show_history()
            continue

        messages.append({"role": "user", "content": f"My task is: {task}"})
        append_to_history("user", task)

        while True:
            print("🧠 Thinking...\n")
            plan = get_ai_response(messages)
            sleep(0.5)
            print("📋 AI PLAN:\n")
            sleep(0.3)
            for line in plan.split("\n"):
                print(line)
                sleep(0.15)
            append_to_history("assistant", plan)

            approve = input("\n✅ Approve and run? (y/n): ").strip().lower()
            if approve != "y":
                print("❌ Task canceled.")
                break

            commands = [line.strip("- ").strip("`") for line in plan.split("\n") if line.strip().startswith("-") or line.strip().startswith("`")]
            success = execute_commands(commands)

            if success:
                print("\n✅ Task completed successfully.\n")
                while True:
                    follow_up = input("❓ Did the code run perfectly? (y/n): ").strip().lower()
                    if follow_up == "y":
                        break  # Move to next task
                    elif follow_up == "n":
                        reason = input("💬 Why not? Tell the AI to retry and fix it: ").strip()
                        messages.append({
                            "role": "user",
                            "content": f"The command executed but did not behave as expected. Reason: {reason}. Fix and retry."
                        })
                        append_to_history("user", reason)

                        print("🔁 Retrying...\n")
                        plan = get_ai_response(messages)
                        sleep(0.5)
                        print("📋 NEW PLAN:\n")
                        sleep(0.3)
                        for line in plan.split("\n"):
                            print(line)
                            sleep(0.15)
                        append_to_history("assistant", plan)

                        approve = input("\n✅ Approve new plan? (y/n): ").strip().lower()
                        if approve != "y":
                            print("🔄 Not approved. Let's retry again.")
                            continue

                        commands = [line.strip("- ").strip("`") for line in plan.split("\n") if line.strip().startswith("-") or line.strip().startswith("`")]
                        success = execute_commands(commands)
                        if not success:
                            continue
                    else:
                        print("Please enter 'y' or 'n'.")
                break  # Exit inner while-loop after confirmation

            else:
                while not success:
                    reason = input("\n❌ Why did it fail? Tell the AI: ")
                    messages.append({
                        "role": "user",
                        "content": f"The last command failed because: {reason}. Retry and fix it."
                    })
                    append_to_history("user", reason)

                    print("🔁 Retrying...\n")
                    plan = get_ai_response(messages)
                    sleep(0.5)
                    print("📋 NEW PLAN:\n")
                    sleep(0.3)
                    for line in plan.split("\n"):
                        print(line)
                        sleep(0.15)
                    append_to_history("assistant", plan)

                    approve = input("\n✅ Approve new plan? (y/n): ").strip().lower()
                    if approve != "y":
                        print("🔄 Not approved. Let's retry again.")
                        continue

                    commands = [line.strip("- ").strip("`") for line in plan.split("\n") if line.strip().startswith("-") or line.strip().startswith("`")]
                    success = execute_commands(commands)

                break

if __name__ == "__main__":
    main()
