# Contributing to GroqChatbot

We love your input! We want to make contributing to GroqChatbot as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

1. Fork the repo and create your branch from `main`
2. If you add behaviour, describe how you verified it in the PR
3. If you've changed APIs, update the documentation
4. Run the syntax checks below
5. Make sure your code follows the existing style
6. Issue that pull request!

## Setting Up Development Environment

```bash
git clone https://github.com/rhasan2026g-cell/GroqChatbot.git
cd GroqChatbot
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Testing

There is no pytest suite in the repository yet; use these checks before opening
a pull request:

```bash
# Python syntax for every module
python -m py_compile "My Chatbot.py" app.py app_paths.py memory_system.py \
  rag_system.py agent_tools.py generation.py ui_theme.py ui_widgets.py ui_dialogs.py

# Optional smoke script (memory + tools, no network)
python test_agent.py

# JavaScript syntax for the Android UI
node --check android-app/www/app.js

# Launch the desktop app and exercise chat, memory and a tool
python "My Chatbot.py"
```

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions small and focused

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update the CHANGELOG.md with your changes
3. The PR will be merged once you have the sign-off of maintainers

## Any contributions you make will be under the MIT Software License

In short, when you submit code changes, your submissions are understood to be under the same [MIT License](http://choosealicense.com/licenses/mit/) that covers the project. Feel free to contact the maintainers if that's a different concern.

## Report bugs using GitHub's [issues](https://github.com/rhasan2026g-cell/GroqChatbot/issues)

We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/rhasan2026g-cell/GroqChatbot/issues/new).

## License

By contributing, you agree that your contributions will be licensed under its MIT License.
