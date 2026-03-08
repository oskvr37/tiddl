# Contributing

## Development Setup

Clone the repository

```bash
git clone https://github.com/oskvr37/tiddl
cd tiddl
```

Create virtual environment and activate it

```bash
uv venv
source .venv/Scripts/activate
```

Install package with `--editable` flag

```bash
uv pip install -e .
```

## Debugging

The Rich `Live` display used during downloads can interfere with interactive debuggers like `breakpoint()` / `pdb`. To disable it, add the following to your `config.toml` under `[download]`:

```toml
[download]
disable_live = true
```

This will disable the live progress display and allow `breakpoint()` to work normally.

> [!NOTE]
> The `config.toml` file normally lives in your app directory (`~/.tiddl` on Linux, `C:/Users/<your_username>/.tiddl` on Windows). You can override this path with the `TIDDL_PATH` environment variable. See [config.example.toml](/docs/config.example.toml) for all available options.
