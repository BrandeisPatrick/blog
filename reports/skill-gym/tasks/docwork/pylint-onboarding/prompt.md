You are in a checkout of pylint-dev/pylint. Write a contributor
onboarding document (ONBOARDING.md is NOT to be created — reply in chat only)
explaining, for a new contributor:

1. How a lint run flows end to end: entry point, how PyLinter is constructed,
   how checkers are registered and invoked, and how messages are emitted.
2. The role of these specific pieces: pylint/lint/pylinter.py, the checkers/
   package, message definitions and message IDs, and the functional test
   framework under tests/functional.
3. How to add a brand-new checker with one new message, step by step.

Ground every claim in the actual code you read. Reply in chat with the
document; do not write files.
