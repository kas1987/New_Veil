import os
import sys

# Ensure the core module can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import InteractiveNarrativeEngine


def main():
    print("\n" + "=" * 50)
    print("🗣️ NARRATIVE ENGINE HARNESS: INTERACTIVE MODE")
    print("Type your actions/dialogue. Type 'quit' to exit.")
    print("=" * 50 + "\n")

    target = input("Enter a Target Model name from the DB (e.g. 'Autumn Falls') or press Enter for generic: ").strip()
    if not target:
        target = None

    engine = InteractiveNarrativeEngine(target_model=target)

    if target:
        print(f"\n[System] Hooked into models.db. Persona set to: {target}")

    while True:
        try:
            user_input = input("\n[You]: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                break

            # Simulated Heuristic Parser
            a_mod = 10 if any(w in user_input.lower() for w in ["touch", "kiss", "pull", "hard"]) else 2
            i_mod = 10 if any(w in user_input.lower() for w in ["talk", "look", "soft"]) else 2
            inh_mod = -5 if any(w in user_input.lower() for w in ["safe", "lock", "trust"]) else -2

            print("--------------------------------------------------")
            engine.process_turn(user_input, arousal_mod=a_mod, intimacy_mod=i_mod, inhibition_mod=inh_mod)
            print("--------------------------------------------------")

        except KeyboardInterrupt:
            break

    print("\nExiting interactive harness.")


if __name__ == "__main__":
    main()
