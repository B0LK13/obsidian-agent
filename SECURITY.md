# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of Obsidian Agent seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

**Please DO NOT open a public issue for security vulnerabilities.**

Instead, please email the maintainer directly or use GitHub's private vulnerability reporting feature:

1. Go to the [Security tab](https://github.com/B0LK13/obsidian-agent/security)
2. Click "Report a vulnerability"
3. Provide detailed information about the vulnerability

### What to Include

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Suggested fix (if any)
- Your contact information for follow-up

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity, typically 14-30 days for critical issues

## Security Considerations

### API Key Storage

- API keys are stored locally in your Obsidian vault's plugin data
- Keys are never transmitted except to your chosen AI provider
- We recommend protecting your vault with encryption if it contains sensitive API keys

### Data Privacy

- **No Third-Party Tracking**: This plugin does not send data to any analytics services
- **Direct API Calls**: All AI requests go directly from your machine to your chosen provider
- **Context Control**: You control what context is shared with AI via settings
- **Local Processing**: All plugin logic runs locally in Obsidian

### Network Security

- API calls use HTTPS for encryption in transit
- API keys are sent in headers (not URL parameters)
- No credential caching or logging

### Recommended Practices

1. **Protect Your Vault**
   - Use Obsidian's built-in encryption if your vault contains sensitive data
   - Don't commit your vault to public repositories

2. **API Key Management**
   - Use environment-specific API keys (not your master key)
   - Rotate keys periodically
   - Revoke keys if compromised
   - Monitor API usage on provider dashboards

3. **Sensitive Content**
   - Be mindful of what content you send to AI providers
   - Review your AI provider's data retention policies
   - Consider using custom/local models for highly sensitive data

4. **Keep Updated**
   - Update to the latest plugin version for security fixes
   - Check release notes for security-related changes

## Known Security Limitations

1. **API Key Visibility**: API keys are stored in plain text in plugin settings (standard for Obsidian plugins)
2. **Third-Party Dependencies**: Plugin relies on external AI services which have their own security policies
3. **Note Content Transmission**: When using AI features, selected note content is sent to external AI providers

## Security Features

- ✅ No code execution from untrusted sources
- ✅ Input validation on all API interactions
- ✅ Error handling to prevent sensitive data leakage
- ✅ No external dependencies beyond Obsidian API and standard libraries
- ✅ Open source code for community review

## Vulnerability Disclosure Policy

Once a vulnerability is fixed:

1. We will credit the reporter (unless they prefer anonymity)
2. A security advisory will be published on GitHub
3. Users will be notified through release notes
4. A new version will be released with the fix

## Contact

For security concerns, please contact the maintainers through:
- GitHub Security Advisory (preferred)
- GitHub Issues (for non-sensitive security discussions)

## Acknowledgments

We appreciate the security research community and will acknowledge all reporters who help us improve security.

---

**Last Updated**: January 16, 2026
