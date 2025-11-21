from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from agent import app

load_dotenv()

def main():
    print("=== LangChain x LangGraph RAG Agent ===")
    print("Type 'exit' or 'quit' to end the conversation.\n")

    chat_history = []

    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["exit", "quit"]:
                break

            if not user_input.strip():
                continue

            message = HumanMessage(content=user_input)

            print("\n--- Agent Processing ---")

            final_state = app.invoke({"messages": chat_history + [message]})

            chat_history = final_state["messages"]

            ai_reply = chat_history[-1].content
            print(f"\nAgent: {ai_reply}\n")

        except KeyboardInterrupt:
            print("\nExiting.")
            break
        except Exception as e:
            print(f"\nError: {e}\n")
            continue


if __name__ == "__main__":
    main()
