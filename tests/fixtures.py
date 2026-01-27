"""Test fixtures for detection tests."""

# Known positive examples (should trigger warnings)
POSITIVE_EXAMPLES = [
    "As an AI language model, I cannot provide that information.",
    "Certainly! Here is the requested code implementation.",
    "I hope this helps! Let me know if you need anything else.",
    "Below is a comprehensive solution to your problem.",
    "I cannot assist with that request. I encourage you to seek professional help.",
    "To summarize, the main points are as follows...",
    "In conclusion, we have demonstrated that...",
]

# Known negative examples (should NOT trigger warnings)
NEGATIVE_EXAMPLES = [
    "This is just a regular paragraph of text without any AI markers.",
    "The function returns true if the condition is met, otherwise false.",
    "Please review the pull request when you have time.",
    "Meeting scheduled for tomorrow at 2 PM.",
]

# Examples with quotes (should have suppression applied)
QUOTED_EXAMPLES = [
    """> As an AI language model, I cannot help
> Here is the information
> Below is the code""",
    """> Certainly! I hope this helps.
> Let me know if you need more.
> Feel free to ask questions.""",
]

# Examples with code fences (should have suppression applied)
CODE_FENCE_EXAMPLES = [
    """Here is the code:
```python
def hello():
    print("As an AI, this is in code")
```
Certainly! I hope this helps.""",
    """```javascript
// Below is the implementation
function test() {
    return true;
}
```""",
]
