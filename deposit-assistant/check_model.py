"""Verify model configuration using a fixed, non-sensitive prompt."""

from llm_client import ModelError, create_client


def main() -> int:
    try:
        response = create_client().generate_text("Reply with exactly: Connection successful.")
    except ModelError as exc:
        print(f"Model check failed: {exc}")
        return 1
    print(f"Model: {response.model}\nResponse: {response.text}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
