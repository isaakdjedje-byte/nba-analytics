"""
Utilitaires de transformation de données NBA.

Fonctions pures pour convertir et standardiser les données joueurs.
Aucun effet de bord - facilement testables unitairement.
"""

import re
from typing import Optional
from datetime import datetime


def convert_height_to_cm(height_str: str) -> Optional[int]:
    """
    Convertit une taille du format 'feet-inches' en centimètres.
    Gère aussi les valeurs déjà en cm (3 chiffres sans tiret).
    
    Args:
        height_str: Taille au format '6-8' (pieds-pouces) ou '218' (cm)
        
    Returns:
        Taille en cm (int) ou None si format invalide
        
    Examples:
        >>> convert_height_to_cm('6-8')
        203
        >>> convert_height_to_cm('218')
        218
        >>> convert_height_to_cm('5-9')
        175
    """
    if not height_str:
        return None
    
    height_clean = str(height_str).strip()
    
    try:
        # Cas 1: Déjà en cm (3 chiffres sans tiret, ex: "218")
        if height_clean.isdigit() and len(height_clean) == 3 and 160 <= int(height_clean) <= 240:
            return int(height_clean)
        
        # Cas 2: Format pieds-pouces (ex: "6-8" ou "6-10")
        match = re.match(r'^(\d+)-(\d+)$', height_clean)
        if match:
            feet = int(match.group(1))
            inches = int(match.group(2))
            # 1 foot = 30.48 cm, 1 inch = 2.54 cm
            return int((feet * 30.48) + (inches * 2.54))
        
        # Cas 3: Nombre simple qui pourrait être cm (ex: "206")
        if height_clean.isdigit():
            val = int(height_clean)
            if 160 <= val <= 240:  # Plage réaliste NBA
                return val
                
    except (ValueError, TypeError):
        pass
    
    return None


def convert_weight_to_kg(weight_val) -> Optional[int]:
    """
    Convertit un poids de livres (lbs) en kilogrammes.
    Gère aussi les valeurs déjà en kg (valeurs < 150).
    
    Args:
        weight_val: Poids en livres (int, float, ou string avec 'lbs') ou déjà en kg
        
    Returns:
        Poids en kg (int) ou None si invalide
        
    Examples:
        >>> convert_weight_to_kg(225)
        102
        >>> convert_weight_to_kg('250 lbs')
        113
        >>> convert_weight_to_kg(102)
        102
    """
    if not weight_val:
        return None
    
    try:
        # Nettoyer la valeur (enlever 'lbs' si présent)
        weight_str = str(weight_val).replace('lbs', '').replace('kg', '').strip()
        lbs = float(weight_str)
        
        # Cas 1: Déjà en kg (valeur < 150, car NBA max ~160kg)
        # Note: 150 lbs = 68 kg, donc si > 70 et < 150, probablement déjà kg
        if 50 <= lbs <= 160:
            # Vérifier si c'est plausible comme kg (joueurs NBA entre 70-160kg)
            return int(lbs)
        
        # Cas 2: En livres (valeurs typiques NBA: 180-300 lbs)
        if lbs > 160:
            # 1 lb = 0.453592 kg
            return int(lbs * 0.453592)
                
    except (ValueError, TypeError):
        pass
    
    return None


def standardize_position(position: str) -> str:
    """
    Standardise le code position NBA.
    
    Args:
        position: Position au format long ('Guard', 'Forward', etc.)
        
    Returns:
        Code position standardisé ('G', 'F', 'C', etc.)
        
    Examples:
        >>> standardize_position('Guard')
        'G'
        >>> standardize_position('Forward-Center')
        'F-C'
    """
    if not position:
        return 'Unknown'
    
    position = str(position).strip().upper()
    
    mapping = {
        'GUARD': 'G',
        'FORWARD': 'F',
        'CENTER': 'C',
        'GUARD-FORWARD': 'G-F',
        'FORWARD-GUARD': 'F-G',
        'FORWARD-CENTER': 'F-C',
        'CENTER-FORWARD': 'C-F',
        'G-FORWARD': 'G-F',
        'F-GUARD': 'F-G',
        'F-CENTER': 'F-C',
        'C-FORWARD': 'C-F',
    }
    
    return mapping.get(position, position)


def standardize_date(date_str: str) -> Optional[str]:
    """
    Standardise une date au format ISO (YYYY-MM-DD).
    
    Args:
        date_str: Date dans divers formats possibles
        
    Returns:
        Date au format 'YYYY-MM-DD' ou None si invalide
    """
    if not date_str:
        return None
    
    # Déjà au format ISO
    if isinstance(date_str, str) and len(date_str) >= 10 and date_str[4] == '-':
        return date_str[:10]
    
    # Format 'DEC 18, 2001'
    try:
        dt = datetime.strptime(str(date_str), '%b %d, %Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        pass
    
    # Format '2001-12-18T00:00:00'
    try:
        dt = datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        pass
    
    return None


def calculate_age(birth_date: str) -> Optional[int]:
    """
    Calcule l'âge depuis la date de naissance.
    
    Args:
        birth_date: Date de naissance au format ISO 'YYYY-MM-DD'
        
    Returns:
        Âge en années (int) ou None si invalide
    """
    if not birth_date:
        return None
    
    try:
        birth = datetime.strptime(birth_date[:10], '%Y-%m-%d')
        today = datetime.now()
        age = today.year - birth.year
        
        # Ajuster si l'anniversaire n'est pas encore passé cette année
        if (today.month, today.day) < (birth.month, birth.day):
            age -= 1
        
        return age
    except (ValueError, TypeError):
        pass
    
    return None


def convert_to_int_safe(value, default: Optional[int] = None) -> Optional[int]:
    """
    Convertit une valeur en int de manière sécurisée.
    
    Gère : int, float, string, numpy types
    
    Args:
        value: Valeur à convertir
        default: Valeur par défaut si conversion impossible
        
    Returns:
        int ou default si impossible
    """
    if value is None:
        return default
    
    try:
        # Gérer numpy types
        if hasattr(value, 'item'):  # numpy scalar
            value = value.item()
        
        if isinstance(value, (int, float)):
            return int(value)
        elif isinstance(value, str):
            return int(float(value))
        else:
            return int(value)
    except (ValueError, TypeError, OverflowError):
        return default


def convert_to_float_safe(value, default: Optional[float] = None) -> Optional[float]:
    """
    Convertit une valeur en float de manière sécurisée.
    
    Args:
        value: Valeur à convertir
        default: Valeur par défaut si conversion impossible
        
    Returns:
        float ou default si impossible
    """
    if value is None:
        return default
    
    try:
        if hasattr(value, 'item'):  # numpy scalar
            value = value.item()
        return float(value)
    except (ValueError, TypeError, OverflowError):
        return default


if __name__ == "__main__":
    # Tests rapides
    print("Tests transformations:")
    print(f"Height '6-8' -> {convert_height_to_cm('6-8')} cm")
    print(f"Weight 225 -> {convert_weight_to_kg(225)} kg")
    print(f"Position 'Guard' -> {standardize_position('Guard')}")
    print(f"Date 'DEC 18, 2001' -> {standardize_date('DEC 18, 2001')}")
    print(f"Age from '1984-12-30' -> {calculate_age('1984-12-30')} ans")
