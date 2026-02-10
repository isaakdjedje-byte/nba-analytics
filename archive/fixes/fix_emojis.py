#!/usr/bin/env python3
"""Script pour remplacer les emojis par des équivalents ASCII"""
import os
import re

# Mapping emoji -> ASCII
emoji_map = {
    '📂': '[FILE]',
    '✅': '[OK]',
    '🔍': '[SCAN]',
    '🎯': '[TARGET]',
    '💾': '[SAVE]',
    '✨': '[DONE]',
    '📁': '[FOLDER]',
    '📊': '[STATS]',
    '👥': '[USERS]',
    '🏀': '[NBA]',
    '🚀': '[START]',
    '⛔': '[STOP]',
    '⚠️': '[WARN]',
    '❌': '[FAIL]',
    '🗑️': '[DELETE]',
    '🔄': '[RESUME]',
    '🚨': '[ALERT]',
    '📈': '[UP]',
}

def fix_file(filepath):
    """Remplacer les emojis dans un fichier"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    for emoji, replacement in emoji_map.items():
        content = content.replace(emoji, replacement)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {filepath}")
        return True
    return False

def main():
    directory = "src/ingestion/nba19/ultimate_discovery"
    
    fixed_count = 0
    for filename in os.listdir(directory):
        if filename.endswith('.py'):
            filepath = os.path.join(directory, filename)
            if fix_file(filepath):
                fixed_count += 1
    
    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == "__main__":
    main()
