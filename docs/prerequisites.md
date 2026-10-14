# Prerequisites

| Tool | Needed by | Why |
|---|---|---|
| Node.js 18+ | all skills | Runs Playwright (headless Chromium) |
| ffmpeg | `video-tutorial` | Encodes the MP4 and the preview contact sheet |
| Python 3.8+ | `user-manual` | Builds the DOCX (standard library only, no pip packages) |
| LibreOffice **or** Microsoft Word (Windows) | `user-manual` | Refreshes the table of contents and exports the PDF |
| Poppler (`pdftoppm`) | `user-manual` | Renders PDF pages so the agent can review them |

If you only need `/visual-check`, Node.js is enough.

Chromium itself is downloaded once (about 150 MB) by the installer, or by the
agent the first time a skill runs.

## Linux (Debian/Ubuntu)

```bash
sudo apt install nodejs npm ffmpeg python3 libreoffice-writer python3-uno poppler-utils
```

On other distributions install the same packages with your package manager.
`python3-uno` is what lets the scripts drive LibreOffice; without it the PDF
cannot be produced.

## macOS (Homebrew)

```bash
brew install node ffmpeg python poppler
brew install --cask libreoffice
```

`to_pdf.py` uses the Python bundled with LibreOffice automatically.

## Windows 10/11

```powershell
winget install OpenJS.NodeJS.LTS
winget install Gyan.FFmpeg
winget install Python.Python.3.12
winget install oschwartz10612.Poppler
winget install TheDocumentFoundation.LibreOffice   # optional if Microsoft Word is installed
```

Close and reopen the terminal so `PATH` is refreshed, then check:

```powershell
node --version; ffmpeg -version | Select-Object -First 1; python --version; pdftoppm -v
```

- If `python` opens the Microsoft Store, turn off the *App execution aliases*
  for `python.exe` and `python3.exe` in *Settings → Apps → Advanced app settings*.
- If winget cannot find Poppler, download it from
  <https://github.com/oschwartz10612/poppler-windows/releases>, unzip it (for
  example to `C:\poppler`) and add `C:\poppler\Library\bin` to your user `PATH`.
- Without LibreOffice, `to_pdf.py` drives Microsoft Word through COM.
- Claude Code on Windows needs Git for Windows (`winget install Git.Git`).

## WSL2

You can also run everything inside WSL following the Linux instructions, with
the agent running in WSL too. If the app under test runs on Windows, enable
`networkingMode=mirrored` in `%USERPROFILE%\.wslconfig` so `localhost` reaches it.

## Test credentials

Every role you check or document needs a **test** user, never a real one.
Keep the credentials outside any repository, in one file per project:

Linux / macOS / Git Bash:

```bash
mkdir -p ~/.config/webapp-docs-kit && chmod 700 ~/.config/webapp-docs-kit
cat > ~/.config/webapp-docs-kit/acme-orders.env <<'EOF'
export ACME_CLERK_USER='clerk@test.example.com'
export ACME_CLERK_PASS='test-user-password'
EOF
chmod 600 ~/.config/webapp-docs-kit/acme-orders.env
source ~/.config/webapp-docs-kit/acme-orders.env && claude   # or codex, gemini...
```

Inside a Claude Code session that is already open: `! source ~/.config/webapp-docs-kit/acme-orders.env`
(this works on Windows too, where Claude Code runs Git Bash).

PowerShell (for agents started from PowerShell):

```powershell
New-Item -ItemType Directory -Force $HOME\.config\webapp-docs-kit | Out-Null
icacls $HOME\.config\webapp-docs-kit /inheritance:r /grant:r "${env:USERNAME}:(OI)(CI)F"
# $HOME\.config\webapp-docs-kit\acme-orders.ps1:
#   $env:ACME_CLERK_USER = 'clerk@test.example.com'
#   $env:ACME_CLERK_PASS = 'test-user-password'
. $HOME\.config\webapp-docs-kit\acme-orders.ps1; codex
```

The variable names are the ones you put in `credentialsEnv` in `docs/webapp-docs.json`.
