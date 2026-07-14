# 🤖 Termi

**AI-powered multi-LLM terminal assistant that converts natural language into executable shell commands.**

---

## 📖 Project Description

**Termi** lets you describe what you want to do in plain English and get back a real, executable shell command — no more digging through `man` pages or half-remembered `find` flags.

It works across **Windows, Linux, and macOS**, automatically detects your operating system and shell, and supports **five different LLM providers** so you're never locked into one vendor. Termi remembers what you've asked in the current session. It can explain what a command does before you run it, diagnose *why* a command failed after you run it and like any responsible assistant sitting in front of your terminal, it always asks before executing anything.

---

## 🎥 Demo

https://github.com/user-attachments/assets/778762da-46b0-4f7a-b4ab-8d96ec2c46a3




---

## ✨ Features

| | Feature | Description |
|---|---|---|
| ✅ | **Natural language → shell commands** | Describe a task in plain English, get back a real, runnable command |
| ✅ | **Multiple LLM providers** | Groq, OpenAI, Gemini, Anthropic, and Ollama (local) |
| ✅ | **Runtime provider switching** | Swap providers mid-session with `/provider set <name>` |
| ✅ | **Automatic OS detection** | Detects Windows, Linux, or macOS automatically |
| ✅ | **Automatic shell detection** | Detects bash, zsh, fish, PowerShell, or cmd automatically |
| ✅ | **Persistent command history** | Every prompt, command, and result is logged to SQLite |
| ✅ | **Command explanation** | Ask Termi to explain any shell command in plain English |
| ✅ | **AI-powered error explanation** | When a command fails, Termi diagnoses why and suggests a fix |
| ✅ | **Confirmation before execution** | Nothing runs without your explicit go-ahead |
| ✅ | **Cross-platform** | Windows, Linux, and macOS |
| ✅ | **Installable CLI package** | `pip install -e .` and run `termi` from anywhere |

---


## 📦 Installation

### From source

```bash
git clone https://github.com/<shreya-ramesh>/termi.git
cd termi

python3 -m venv .venv
source .venv/bin/activate      

pip install -e ".[dev]"

cp .env.example .env
# add your API key(s) to .env

termi
```

### Via pip 

```bash
pip install termi-ai
termi
```

---

## ⚙️ Configuration

Termi reads its configuration from a `.env` file at the project root so fill in the keys for whichever provider(s) you plan to use — you only need the ones you'll actually use.

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | API key for Groq |
| `OPENAI_API_KEY` | API key for OpenAI |
| `GEMINI_API_KEY` | API key for Google Gemini |
| `ANTHROPIC_API_KEY` | API key for Anthropic Claude |
| `OLLAMA_BASE_URL` | URL of a locally running Ollama server (default: `http://localhost:11434`) |

---


## 📁 Project Structure

```
termi/
├── termi/
│   ├── __init__.py
│   ├── cli.py                     # Typer + Rich CLI entrypoint
│   ├── core/
│   │   ├── agent.py                # Orchestrates generation, safety, execution
│   │   ├── provider_manager.py     # Single entry point to LLM providers
│   │   ├── conversation.py         # Conversational memory
│   │   ├── executor.py             # Shell command execution
│   │   ├── settings.py             # Persistent user settings
│   │   ├── system.py               # OS / shell / cwd / user detection
│   │   ├── system_query.py         # Local (LLM-free) system-info queries
│   │   ├── explainer.py            # Command explanation
│   │   ├── error_explainer.py      # AI-powered failure diagnosis
│   │   └── intent.py               # LLM output → clean shell command
│   ├── providers/
│   │   ├── base.py                 # Abstract BaseProvider interface
│   │   ├── factory.py              # ProviderFactory
│   │   ├── groq_provider.py
│   │   ├── openai_provider.py
│   │   ├── gemini_provider.py
│   │   ├── anthropic_provider.py
│   │   └── ollama_provider.py
│   ├── database/
│   │   ├── database.py             # SQLite connection + schema
│   │   └── history_repository.py   # History CRUD
│   └── utils/
│       ├── logger.py
│       ├── exceptions.py
│       └── dangerous_commands.py   # Destructive-command heuristics
├── tests/                          # pytest suite
├── settings.json
├── pyproject.toml
├── requirements.txt
├── .env.example
├── .gitignore
└── LICENSE

```

---

## 🤝 Contributing

Contributions are welcome! If you'd like to help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes, following the existing style (`black`, `isort`, `ruff`)
4. Run the test suite (`pytest`)
5. Open a pull request describing what changed and why

> 📋 Please keep pull requests focused on one feature or fix per PR makes review much faster.

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

Termi is built on top of a great open-source ecosystem, including [Typer](https://typer.tiangolo.com/), [Rich](https://github.com/Textualize/rich), and [python-dotenv](https://github.com/theskumar/python-dotenv), along with the official SDKs for Groq, OpenAI, Google Gemini, and Anthropic, plus [Ollama](https://ollama.com/) for local inference.
