#!/usr/bin/env python3
import sys
import os
import shutil
import re


ASSIGNMENT_RE = re.compile(r'^(\s*(?:export\s+)?)([A-Za-z_][A-Za-z0-9_]*)(\s*=\s*)(.*?)(\r?\n?)$')


def split_value_and_inline_comment(rhs):
    """Split a RHS value into value + inline comment suffix.

    The suffix preserves its original leading spaces and starts at the first
    unquoted '#'. Quoted '#' characters are treated as part of the value.
    """
    in_single = False
    in_double = False
    escaped = False

    for i, ch in enumerate(rhs):
        if escaped:
            escaped = False
            continue

        if ch == '\\' and in_double:
            escaped = True
            continue

        if ch == "'" and not in_double:
            in_single = not in_single
            continue

        if ch == '"' and not in_single:
            in_double = not in_double
            continue

        if ch == '#' and not in_single and not in_double:
            return rhs[:i], rhs[i:]

    return rhs, ""


def parse_existing_values(env_path):
    old_values = {}
    if not os.path.exists(env_path):
        return old_values

    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = ASSIGNMENT_RE.match(line)
            if not match:
                continue

            key = match.group(2)
            rhs = match.group(4)
            value_part, _ = split_value_and_inline_comment(rhs)
            old_values[key] = value_part.strip()

    return old_values


def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_file = os.path.join(project_root, ".env")
    example_file = os.path.join(project_root, ".env.example")
    
    if not os.path.exists(example_file):
        print(f"Erreur: Le fichier {example_file} n'existe pas.")
        sys.exit(1)

    old_values = parse_existing_values(env_file)

    if os.path.exists(env_file):
        # Création d'une sauvegarde de précaution
        backup_file = env_file + ".bak"
        shutil.copy2(env_file, backup_file)
        print(f"Sauvegarde créée : {backup_file}")

    new_content = []
    with open(example_file, 'r', encoding='utf-8') as f:
        for line in f:
            match = ASSIGNMENT_RE.match(line)
            if not match:
                # Commentaires, lignes vides, etc.
                new_content.append(line)
                continue

            prefix, key, sep, rhs, newline = match.groups()
            if key not in old_values:
                new_content.append(line)
                continue

            _, inline_comment = split_value_and_inline_comment(rhs)
            new_value = old_values[key]
            new_content.append(f"{prefix}{key}{sep}{new_value}{inline_comment}{newline}")

    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(new_content)

    print(f"Succès: {env_file} a été mis à jour en conservant vos valeurs précédentes.")

if __name__ == "__main__":
    main()
