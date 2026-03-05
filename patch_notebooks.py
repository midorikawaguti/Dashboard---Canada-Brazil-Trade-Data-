"""
patch_notebooks.py
==================
Patches all .ipynb notebooks in the project to work in both
Google Colab and local VS Code environments.

Run from project root:
  python patch_notebooks.py
"""

import json
import re
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path.cwd()

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

# The new environment detection block to inject
COLAB_HEADER = '''# ── Environment detection (Colab vs Local) ───────────────────
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

print(f'Environment : {"Colab" if IN_COLAB else "Local"}')
print(f'Base dir    : {BASE_DIR}')
print(f'Exists      : {BASE_DIR.exists()}')
'''

# Old path patterns to replace — add any variants found in notebooks
OLD_PATTERNS = [
    # Module 1-5 pattern
    (
        r"BASE_DIR\s*=\s*Path\.cwd\(\)\.parent\s*\n"
        r"EXPORTS_DIR\s*=\s*BASE_DIR\s*/\s*[\"']Dataset[\"']\s*/\s*[\"']Exports[\"']",
        "BASE_DIR = Path('/content/drive/MyDrive/Dashboard-BR-CA-Data')\n"
        "EXPORTS_DIR  = BASE_DIR / 'Exports'"
    ),
    # Module 6a pattern
    (
        r"BASE_DIR\s*=\s*Path\.cwd\(\)\s*\n"
        r"INPUT_DIR\s*=\s*BASE_DIR\s*/\s*[\"']Dataset[\"']\s*/\s*[\"']Exports[\"']",
        "BASE_DIR = Path('/content/drive/MyDrive/Dashboard-BR-CA-Data')\n"
        "INPUT_DIR    = BASE_DIR / 'Exports'"
    ),
    # Module 6b/6c pattern
    (
        r"BASE_DIR\s*=\s*Path\.cwd\(\)\s*\n"
        r"INPUT_FILE\s*=\s*BASE_DIR\s*/\s*[\"']Dataset[\"']\s*/\s*[\"']Normalised[\"']\s*/\s*[\"']prices_normalised\.csv[\"']",
        "BASE_DIR = Path('/content/drive/MyDrive/Dashboard-BR-CA-Data')\n"
        "INPUT_FILE   = BASE_DIR / 'Normalised' / 'prices_normalised.csv'"
    ),
]


# ── HELPERS ───────────────────────────────────────────────────────────────────

def patch_cell_source(source: str) -> tuple[str, bool]:
    """
    Patch a single cell's source code.
    Returns (patched_source, was_changed).
    """
    original = source
    changed = False

    # Check if this cell already has the Colab header
    if 'from google.colab import drive' in source:
        return source, False

    # Check if this cell has old path definitions
    has_old_paths = any([
        'Path.cwd().parent' in source,
        'Path.cwd()' in source and 'Dataset' in source,
        'EXPORTS_DIR' in source and 'Dataset' in source,
    ])

    if not has_old_paths:
        return source, False

    # Apply regex replacements
    for pattern, replacement in OLD_PATTERNS:
        new_source = re.sub(pattern, replacement, source)
        if new_source != source:
            source = new_source
            changed = True

    # If we found old paths but regex didn't match exactly,
    # inject the header block before the first BASE_DIR line
    if not changed and has_old_paths:
        lines = source.split('\n')
        insert_at = 0
        for i, line in enumerate(lines):
            if 'BASE_DIR' in line or 'EXPORTS_DIR' in line:
                insert_at = i
                break

        # Remove old BASE_DIR and EXPORTS_DIR lines
        new_lines = []
        skip_next = False
        for line in lines:
            if skip_next:
                skip_next = False
                continue
            if ('BASE_DIR' in line and ('Path.cwd()' in line or 'Dataset' in line)):
                continue
            if ('EXPORTS_DIR' in line and 'Dataset' in line):
                continue
            if ('INPUT_DIR' in line and 'Dataset' in line):
                continue
            if ('INPUT_FILE' in line and 'Dataset' in line):
                continue
            new_lines.append(line)

        # Insert the Colab header at the right place
        new_lines.insert(insert_at, COLAB_HEADER)
        source = '\n'.join(new_lines)
        changed = True

    return source, changed


def patch_notebook(nb_path: Path) -> bool:
    """
    Patch a single notebook file.
    Returns True if any changes were made.
    """
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    any_changed = False

    for cell in nb['cells']:
        if cell['cell_type'] != 'code':
            continue

        # Join source lines into one string
        source = ''.join(cell['source'])
        patched, changed = patch_cell_source(source)

        if changed:
            # Split back into lines preserving newlines
            lines = patched.split('\n')
            cell['source'] = [
                line + '\n' if i < len(lines) - 1 else line
                for i, line in enumerate(lines)
            ]
            any_changed = True

    if any_changed:
        with open(nb_path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1, ensure_ascii=False)

    return any_changed


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  NOTEBOOK PATCHER — Colab + Local compatibility")
    print("=" * 60)

    patched = []
    skipped = []
    not_found = []

    for nb_rel in NOTEBOOKS:
        nb_path = PROJECT_ROOT / nb_rel

        if not nb_path.exists():
            not_found.append(nb_rel)
            print(f"  ⚠️  Not found: {nb_rel}")
            continue

        changed = patch_notebook(nb_path)

        if changed:
            patched.append(nb_rel)
            print(f"  ✅ Patched : {nb_rel}")
        else:
            skipped.append(nb_rel)
            print(f"  ⏭️  Skipped : {nb_rel} (already patched or no path found)")

    print()
    print("=" * 60)
    print(f"  Patched : {len(patched)}")
    print(f"  Skipped : {len(skipped)}")
    print(f"  Missing : {len(not_found)}")
    print("=" * 60)

    if patched:
        print()
        print("  Next step — commit and push to GitHub:")
        print()
        print("  git add Modules/ Report_Data_Quality/ Report_Price_Analysis/")
        print('  git commit -m "Patch all notebooks for Colab + local compatibility"')
        print("  git push")


if __name__ == "__main__":
    main()
