# OpenClaw Audit

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-PolyForm%20Noncommercial-red)
![Security](https://img.shields.io/badge/security-hardened-success)

**OpenClaw Audit** is a security configuration scanner for OpenClaw AI agents. It analyzes your `openclaw.json` configuration file to identify security misconfigurations that could leave your agent vulnerable to unauthorized access or remote control.

> ⚠️ **DISCLAIMER**: This tool modifies system-level configurations and file permissions. Use at your own risk. The author is not responsible for any data loss, system instability, or locked-out accounts. Always test in a non-production environment first.

## Supported Platforms

*   **Linux** (Ubuntu, Debian, Fedora, CentOS, etc.) - ✅ Full Support
*   **macOS** - ✅ Full Support
*   **Windows** (10/11) - ⚠️ Partial Support
    *   *Note: File permission automation (`chmod 600`) is not available on Windows. The tool will skip this check and provide instructions for manual verification via File Explorer.*

## Tools Included

### 1. `audit.py` - Security Scanner
Non-destructive scanner that reports vulnerabilities.

### 2. `harden.py` - Automated Hardening
Interactive script that fixes vulnerabilities found by the auditor.
*   Backs up your config (`.json.bak.security`) before touching it.
*   Locks down file permissions (`chmod 600`) (Linux/macOS).
*   Binds Gateway to localhost.
*   Enables Token Authentication (and generates strong tokens).
*   Sets Channel Policies to `pairing` (prevents random DM access).

## Installation

To get started, clone the repository and navigate into the project directory.

```bash
# Clone the repository
git clone https://github.com/ca7ai/openclaw-audit.git

# Enter the directory
cd openclaw-audit

## Usage

No external dependencies required. Runs with standard Python 3.

### Audit Mode (Check Only)
```bash
python3 audit.py
```

### Hardening Mode (Fix Issues)
```bash
python3 harden.py
```
*Follow the interactive prompts to apply fixes.*

## Example Output

<img width="653" height="422" alt="openclaw-audit" src="https://github.com/user-attachments/assets/fe4042a2-ba03-479f-8e72-b98287e7c706" />


## Security Recommendations

*   **Gateway Binding:** Never bind to `0.0.0.0` unless you are behind a VPN.
*   **Authentication:** Ensure the Gateway has a strong token.
*   **Channel Policy:** Use `pairing` or `allowlist`. `open` policies allow strangers to use your bot.
*   **API Keys:** Use environment variables, not hardcoded keys in `openclaw.json`.

### ⚠️ A Note on `exec` (Shell Access)
This tool audits your *configuration*, not your *capabilities*.
If your bot has the `exec` tool enabled (which allows running shell commands), you **must** ensure your Channel Policies are strict (`allowlist`).
*   **Risk:** If `exec` is on + Channel is `open` = Anyone can delete your files.
*   **Check:** Look in your `tools/` directory. If `exec` is present, be extra careful.

## Acknowledgments

This tool is designed to support the [OpenClaw](https://github.com/openclaw/openclaw) Project. Special thanks to the OpenClaw contributors for creating a powerful, MIT-licensed framework for AI agents.

## License

This project is Source Available under the PolyForm Noncommercial License 1.0.0.

    ✅ Permitted: Personal use, research, hobby projects, and non-commercial organizations.

    ❌ Prohibited: Any use with an anticipated commercial application without explicit permission from the author.
