"""
Utilitaires de transformation de données NBA - VERSION CORRIGÉE.

Corrections P0:
- Meilleure détection cm vs feet-inches
- Meilleure détection kg vs lbs
- Gestion des unités explicites
"""

import re
from typing import Optional
from datetime import datetime


def convert_height_to_cm(height_str: str) -> Optional[int]:
    """
    Convertit une taille en centimètres.
    
    CORRECTION P0: Détecte automatiquement le format.
    
    Args:
        height_str: Taille au format 'feet-inches', 'cm', ou nombre
        
    Returns:
        Taille en cm (int) ou None
    """
    if not height_str:
        return None
    
    height_clean = str(height_str).strip()
    
    try:
        # CORRECTION 1: Format feet-inches (ex: "6-8", "6-11")
        match = re.match(r'^(\d+)-(\d+)$', height_clean)
        if match:
            feet = int(match.group(1))
            inches = int(match.group(2))
            # 1 foot = 30.48 cm, 1 inch = 2.54 cm
            return round((feet * 30.48) + (inches * 2.54))
        
        # CORRECTION 2: Nombre à 3 chiffres = probablement cm
        if height_clean.isdigit() and len(height_clean) == 3:
            val = int(height_clean)
            if 160 <= val <= 240:
                return val
        
        # CORRECTION 3: Nombre à 1-2 chiffres = probablement feet (ex: "6")
        if height_clean.isdigit() and len(height_clean) <= 2:
            val = int(height_clean)
            if 5 <= val <= 8:  # 5-8 feet
                return round(val * 30.48)
        
        # CORRECTION 4: Nombre décimal = peut être inches ou cm
        try:
            val = float(height_clean)
            if 160 <= val <= 240:
                return round(val)
            elif 60 <= val <= 100:
                return round(val * 2.54)
        except:
            pass
                
    except (ValueError, TypeError):
        pass
    
    return None


def convert_weight_to_kg(weight_val) -> Optional[int]:
    """
    Convertit un poids en kilogrammes.
    
    CORRECTION P0: Détecte automatiquement kg vs lbs.
    
    Args:
        weight_val: Poids avec ou sans unité
        
    Returns:
        Poids en kg (int) ou None
    """
    if not weight_val:
        return None
    
    weight_str = str(weight_val).strip().lower()
    
    try:
        # CORRECTION 1: Unité explicite KG
        if 'kg' in weight_str:
            val = float(weight_str.replace('kg', '').strip())
            if 50 <= val <= 160:  # Plage réaliste NBA
                return int(val)
        
        # CORRECTION 2: Unité explicite LBS
        if 'lbs' in weight_str or 'lb' in weight_str:
            val = float(weight_str.replace('lbs', '').replace('lb', '').strip())
            if 100 <= val <= 350:  # Plage réaliste NBA
                return int(val * 0.453592)
        
        # CORRECTION 3: Sans unité - inférence par plage
        val = float(weight_str)
        
        # Si entre 50-160, probablement kg
        if 50 <= val <= 160:
            return int(val)
        
        # Si entre 100-350, probablement lbs
        if 100 <= val <= 350:
            return round(val * 0.453592)
        
        # Si entre 160-200, ambigu - vérifier si plausible
        if 160 <= val <= 200:
            # Si proche de 160, probablement lbs (73kg)
            if val < 180:
                return int(val * 0.453592)
            # Si proche de 200, probablement kg
            else:
                return int(val)
                
    except (ValueError, TypeError):
        pass
    
    return None


def standardize_position(position: str) -> str:
    """Standardise le code position NBA."""
    if not position:
        return 'Unknown'
    
    position_map = {
        'guard': 'G',
        'forward': 'F',
        'center': 'C',
        'g': 'G',
        'f': 'F',
        'c': 'C',
        'g-f': 'G-F',
        'f-g': 'F-G',
        'f-c': 'F-C',
        'c-f': 'C-F',
        'c-g': 'C-G',
        'g-c': 'G-C',
    }
    
    pos_clean = str(position).strip().lower()
    
    # Gérer les positions composées
    if '-' in pos_clean or '/' in pos_clean:
        parts = re.split(r'[-/]', pos_clean)
        std_parts = [position_map.get(p.strip(), p.strip().upper()) for p in parts]
        return '-'.join(std_parts)
    
    return position_map.get(pos_clean, position.strip().upper())


def standardize_date(date_str: str) -> Optional[str]:
    """Standardise une date en format ISO."""
    if not date_str:
        return None
    
    formats = [
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%d/%m/%Y',
        '%B %d, %Y',
        '%b %d, %Y',
    ]
    
    date_clean = str(date_str).strip()
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_clean, fmt)
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    return None


def calculate_age(birth_date: str) -> Optional[int]:
    """Calcule l'âge à partir de la date de naissance."""
    if not birth_date:
        return None
    
    try:
        birth = datetime.strptime(str(birth_date)[:10], '%Y-%m-%d')
        today = datetime.now()
        return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    except:
        return None


def convert_to_int_safe(val, default=None):
    """Convertit une valeur en int de manière sécurisée."""
    if val is None:
        return default
    
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return default


if __name__ == "__main__":
    # Tests des corrections
    print("Tests conversions corrigées:")
    
    # Tests hauteur
    test_heights = ['218', '6-8', '203', '6-11', '200', '5']
    for h in test_heights:
        result = convert_height_to_cm(h)
        print(f"  {h:6} -> {result} cm")
    
    print()
    
    # Tests poids
    test_weights = ['102', '225', '102kg', '250lbs', '115', '200']
    for w in test_weights:
        result = convert_weight_to_kg(w)
        print(f"  {w:8} -> {result} kg")
