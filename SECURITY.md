# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability within GroqChatbot, please send an email to the maintainer or create a private security advisory on GitHub. All security vulnerabilities will be promptly addressed.

### What to include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline:
- We will acknowledge your report within 48 hours
- We will provide a detailed response within 7 days
- We will work on a fix and release it as soon as possible

## Security Best Practices

### For Users
- **API Keys**: Never share your Groq API key. Store it securely.
- **Local Storage**: API keys are stored locally on your device. Keep your device secure.
- **Updates**: Keep the app updated to get latest security patches.
- **Network**: Only use trusted networks when possible.

### For Developers
- Never commit API keys or secrets to the repository
- Use environment variables for sensitive data
- Validate all user inputs
- Keep dependencies updated
- Follow secure coding practices

## Known Security Considerations

- **API Key Storage**: Desktop stores in `.env` file (plain text). Android stores in app-private localStorage.
- **Direct API Calls**: The app makes direct calls to Groq API from client - this is by design for privacy but means your API key is used from your device.
- **Local Database**: Memory database is stored locally without encryption. Ensure device security.
- **Tool Execution**: Some tools like `execute_python` have limited sandboxing - use with caution.

## Disclaimer

GroqChatbot is provided "as is" without warranty. Use at your own risk.
