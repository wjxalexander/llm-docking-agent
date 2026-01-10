## 1. Implementation
- [x] 1.1 Add `ProDy` to `pyproject.toml` dependencies.
- [x] 1.2 Create `app/tools/receptor_preparation.py` with `download_pdb` and `prepare_receptor` functions.
- [x] 1.3 Implement `download_pdb` using `requests` or `curl`.
- [x] 1.4 Implement `prepare_receptor` logic using `ProDy`, `reduce2` (if available via meeko/external), and `meeko`.
- [x] 1.5 Register new tools in `app/agent.py`.
- [x] 1.6 Add unit tests for receptor preparation tools.
