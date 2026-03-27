#!/usr/bin/env python3
import sys
import os
import shutil

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_file = os.path.join(project_root, ".env")
    example_file = os.path.join(project_root, ".env.example")
    
    if not os.path.exists(example_file):
        print(f"Erreur: Le fichier {example_file} n'existe pas.")
        sys.exit(1)
        
    old_values = {}
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    old_values[key.strip()] = val.strip()

        # Création d'une sauvegarde de précaution
        backup_file = env_file + ".bak"
        shutil.copy2(env_file, backup_file)
        print(f"Sauvegarde créée : {backup_file}")

    new_content = []
    with open(example_file, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            # On cherche les définitions de variables
            if stripped and not stripped.startswith('#') and '=' in stripped:
                key, _ = stripped.split('=', 1)
                key = key.strip()
                if key in old_values:
                    # On remplace par la clé existante
                    new_content.append(f"{key}={old_values[key]}\n")
                else:
                    # On garde la valeur/template du fichier example
                    new_content.append(line)
            else:
                # Commentaires, lignes vides, etc.
                new_content.append(line)

    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(new_content)

    print(f"Succès: {env_file} a été mis à jour en conservant vos valeurs précédentes.")

if __name__ == "__main__":
    main()
