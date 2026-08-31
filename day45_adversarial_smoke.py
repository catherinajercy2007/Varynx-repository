from app.adaptive_response import calculate_adaptive_response
from tests.test_adversarial_security import (
    build_adversarial_scenarios,
)


def main():
    scenarios = build_adversarial_scenarios()

    print("=" * 70)
    print("VARYNX DAY 45 ADVERSARIAL SECURITY SMOKE TEST")
    print("=" * 70)

    for scenario in scenarios:
        final_event = scenario.events[-1]

        result = calculate_adaptive_response(
            final_event
        )

        print()
        print(f"Scenario : {scenario.name}")
        print(f"Category : {scenario.category}")
        print(
            f"Ground truth threat : "
            f"{scenario.expected_threat}"
        )
        print(
            f"Adaptive action     : "
            f"{result.get('action')}"
        )
        print(
            f"Severity            : "
            f"{result.get('severity')}"
        )
        print(
            f"Score               : "
            f"{result.get('score')}"
        )
        print(
            f"Reasons             : "
            f"{result.get('reasons')}"
        )


if __name__ == "__main__":
    main()