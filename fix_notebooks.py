"""
fix_notebooks.py
================
Rewrites the environment/path config block in all notebooks
to include the full Drive mount + warm-up pattern.

Run from project root:
  python fix_notebooks.py
"""

import json
from pathlib import Path

NOTEBOOKS = [
    "Modules/Module1.ipynb",
    "Modules/Module2.ipynb",
    "Modules/Module3.ipynb",
    "Modules/Module4.ipynb",
    "Modules/Module5.ipynb",
    "Modules/Module6a.ipynb",
    "Modules/Module6b.ipynb",
    "Modules/Module6c.ipynb",
    "Report_Data_Quality/Data_Quality.ipynb",
    "Report_Data_Quality/Report_zero_qty_diag.ipynb",
    "Report_Price_Analysis/Price_Analysis.ipynb",
]

# Full correct block — inserted before any BASE_DIR / EXPORTS_DIR line
COLAB_BLOCK = """\
# ── Environment detection (Colab vs Local) ────────────────────
try:
    from google.colab import drive
    drive.mount('/content/drive', force_remount=True)
    import os as _os
    _os.listdir('/content/drive/MyDrive')
    _os.listdir('/content/drive/MyDrive/Dashboard-BR-CA-Data')
    _os.listdir('/content/drive/MyDrive/Dashboard-BR-CA-Data/Exports')
    BASE_DIR = Path('/content/drive/MyDrive/Dashboard-BR-CA-Data')
    IN_COLAB = True
except Exception:
    BASE_DIR = Path.cwd().parent / 'Dataset'
    IN_COLAB = False

EXPORTS_DIR  = BASE_DIR / 'Exports'
NORM_FILE    = BASE_DIR / 'Normalised' / 'prices_normalised.csv'
REPORTS_DIR  = BASE_DIR / 'Reports'
LOOKER_DIR   = BASE_DIR / 'Looker'

print(f'Environment : {\"Colab\" if IN_COLAB else \"Local\"}')
print(f'Base dir    : {BASE_DIR}')
print(f'Exists      : {BASE_DIR.exists()}')
"""

# Lines to remove from config cells (old or partial path definitions)
REMOVE_PATTERNS = [
    "BASE_DIR        = Path.cwd",
    "BASE_DIR    = Path.cwd",
    "BASE_DIR = Path.cwd",
    "BASE_DIR = Path('/content/drive",
    "BASE_DIR    = Path('/content/drive",
    "EXPORTS_DIR     = BASE_DIR",
    "EXPORTS_DIR  = BASE_DIR",
    "EXPORTS_DIR = BASE_DIR",
    "INPUT_DIR    = BASE_DIR",
    "INPUT_DIR = BASE_DIR",
    "INPUT_FILE   = BASE_DIR",
    "INPUT_FILE = BASE_DIR",
    "NORM_FILE    = BASE_DIR",
    "NORM_FILE = BASE_DIR",
    "REPORTS_DIR  = BASE_DIR",
    "REPORTS_DIR = BASE_DIR",
    "LOOKER_DIR   = BASE_DIR",
    "LOOKER_DIR = BASE_DIR",
    "IN_COLAB = True",
    "IN_COLAB = False",
    "from google.colab import drive",
    "drive.mount(",
    "_os.listdir(",
    "import os as _os",
    "print(f'Environment",
    "print(f'Base dir",
    "print(f'Exists",
    "# ── Environment detection",
    "# Environment detection",
    "except Exception:",
    "except ImportError:",
    "except:",
    "try:",
]


def is_config_cell(source: str) -> bool:
    """Detect if this cell contains path configuration."""
    return any(p in source for p in [
        "Path.cwd()",
        "Path('/content/drive",
        "EXPORTS_DIR",
        "BASE_DIR",
        "Dashboard-BR-CA-Data",
    ])


def clean_cell(source: str) -> str:
    """Remove old path/env lines from a cell."""
    lines = source.split('\n')
    cleaned = []
    skip_block = False

    for line in lines:
        stripped = line.strip()

        # Skip blank lines that follow removed lines (avoid double spacing)
        if skip_block and stripped == '':
            continue
        skip_block = False

        # Check if this line should be removed
        should_remove = any(stripped.startswith(p.strip()) or p.strip() in stripped
                           for p in REMOVE_PATTERNS)

        if should_remove:
            skip_block = True
            continue

        cleaned.append(line)

    return '\n'.join(cleaned).strip()


def patch_notebook(nb_path: Path) -> bool:
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    changed = False

    for cell in nb['cells']:
        if cell['cell_type'] != 'code':
            continue

        source = ''.join(cell['source'])

        if not is_config_cell(source):
            continue

        # Already correctly patched — has mount + warmup
        if "drive.mount(" in source and "_os.listdir('/content/drive/MyDrive')" in source:
            continue

        # Clean out old/partial path lines
        cleaned = clean_cell(source)

        # Find where to insert the Colab block
        # Insert after the last import line in the cell
        lines = cleaned.split('\n')
        insert_at = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('import ') or stripped.startswith('from '):
                insert_at = i + 1

        lines.insert(insert_at, '\n' + COLAB_BLOCK)
        new_source = '\n'.join(lines)

        # Write back as list of strings
        source_lines = new_source.split('\n')
        cell['source'] = [
            line + '\n' if i < len(source_lines) - 1 else line
            for i, line in enumerate(source_lines)
        ]
        changed = True

    if changed:
        with open(nb_path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1, ensure_ascii=False)

    return changed


def main():
    print("=" * 60)
    print("  NOTEBOOK FIX — Full Colab Drive mount + warm-up")
    print("=" * 60)

    project_root = Path.cwd()
    patched, skipped, missing = [], [], []

    for nb_rel in NOTEBOOKS:
        nb_path = project_root / nb_rel
        if not nb_path.exists():
            missing.append(nb_rel)
            print(f"  ⚠️  Missing  : {nb_rel}")
            continue

        changed = patch_notebook(nb_path)
        if changed:
            patched.append(nb_rel)
            print(f"  ✅ Fixed    : {nb_rel}")
        else:
            skipped.append(nb_rel)
            print(f"  ⏭️  Skipped  : {nb_rel} (already correct)")

    print()
    print("=" * 60)
    print(f"  Fixed   : {len(patched)}")
    print(f"  Skipped : {len(skipped)}")
    print(f"  Missing : {len(missing)}")
    print("=" * 60)

    if patched:
        print()
        print("  Next — commit and push:")
        print()
        print("  git add Modules/ Report_Data_Quality/ Report_Price_Analysis/")
        print('  git commit -m "Fix all notebooks: full Colab Drive mount and warm-up"')
        print("  git push")


if __name__ == "__main__":
    main()
