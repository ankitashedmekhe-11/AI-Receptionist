from __future__ import annotations

from services.nlu import extract, init_nlu


def main() -> None:
    init_nlu()
    tests = [
        "I would like to book an appointment for next Tuesday at 3pm",
        "Can you cancel my appointment on July 5th?",
        "I need to reschedule my appointment from Friday to Monday morning",
        "Do you have any availability next week for a consultation?",
        # messy ASR-like
        "uh I wanna book uh a haircut at ten am",
        "please cancel my appointment two zero two three",  # misheard numbers
        "move my dentist appointment from 5pm to 6pm",
        "what time is my checkup on the 12th",
        "i'd like to book a therapy session with Dr Smith",
        "hey, can you resched my appointment?",
        # additional tests
        "Book an appointment for John Mehta on March 15th at 3 PM",
        "I'd like to move my appointment from 2pm to 4pm tomorrow",
        "Please cancel my appointment on the fifteenth of April",
    ]

    for i, s in enumerate(tests, 1):
        result = extract(s)
        print(f"{i:02d}. {s}")
        print("   ->", result)


if __name__ == "__main__":
    main()
