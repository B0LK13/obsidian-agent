# Created ssh-keygen-tui.py - a complete TUI utility for generating SSH keys.
## Features:
- Key type selection: ED25519 (recommended), RSA, or ECDSA
- Configurable key sizes: For RSA (2048/3072/4096) and ECDSA (256/384/521)
- Custom filename: With sensible defaults
- Optional passphrase: With confirmation and masked input
- Comment field: Defaults to user@hostname
- Summary screen: Review all settings before generation
- Key preview: Displays the generated public key content

## Usage:
```
python ssh-keygen-tui.py
```
## Navigation:
```
- ↑/↓ - Navigate options
- Enter - Select
- q - Quit
```

After generating a key, you can update your Dockerfile with the actual key path:
```
ADD id_ed25519.pub /root/.ssh/authorized_keys
```
