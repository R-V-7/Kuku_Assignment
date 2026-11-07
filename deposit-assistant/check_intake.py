"""Interactive test for the intake step; do not enter real sensitive information."""

from intake import IntakeError, extract_case
from llm_client import ModelError, create_client


def main() -> int:
    print("Enter a fictional case in one line. It will be sent to the model provider.")
    story = input("> ")
    try:
        case = extract_case(story, create_client())
    except (IntakeError, ModelError) as exc:
        print(f"Intake failed: {exc}")
        return 1
    print("\nProposed facts (unverified; user confirmation will be added next):")
    print(case.model_dump_json(indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
