#!/usr/bin/env python3
"""
Tracker de progression pour NBA-15
Affiche barre de progression et statistiques temps réel
"""

import time
from datetime import datetime, timedelta
from typing import Optional

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


class ProgressTracker:
    """Track progression avec barre visuelle"""
    
    def __init__(self, total_steps: int, desc: str = "NBA-15"):
        self.total_steps = total_steps
        self.current_step = 0
        self.desc = desc
        self.start_time = datetime.now()
        self.step_start_time = None
        
        if TQDM_AVAILABLE:
            self.pbar = tqdm(total=total_steps, desc=desc, unit="step")
        else:
            self.pbar = None
            print(f"[NBA-15] {desc}")
    
    def start_step(self, step_name: str, total_items: int = 0):
        """Démarre une nouvelle étape"""
        self.step_start_time = datetime.now()
        self.step_name = step_name
        self.step_total = total_items
        self.step_current = 0
        
        if self.pbar:
            self.pbar.set_description(f"{self.desc} - {step_name}")
        else:
            print(f"\n📋 {step_name}")
    
    def update(self, n: int = 1):
        """Met à jour la progression"""
        self.step_current += n
        
        if self.pbar:
            self.pbar.update(0)  # Force refresh
            
        if self.step_total > 0:
            pct = (self.step_current / self.step_total) * 100
            if not self.pbar:
                print(f"  Progress: {self.step_current}/{self.step_total} ({pct:.1f}%)", end="\r")
    
    def complete_step(self, items_count: int = 0, details: str = ""):
        """Marque l'étape comme terminée"""
        self.current_step += 1
        elapsed = datetime.now() - self.step_start_time if self.step_start_time else timedelta(0)
        
        if self.pbar:
            self.pbar.update(1)
            if items_count > 0:
                self.pbar.set_postfix({"items": items_count})
        else:
            status = f"[OK] {self.step_name}"
            if items_count > 0:
                status += f" ({items_count} items)"
            if details:
                status += f" - {details}"
            status += f" [{elapsed.seconds}s]"
            print(f"  {status}")
    
    def get_elapsed(self) -> str:
        """Retourne le temps écoulé formaté"""
        elapsed = datetime.now() - self.start_time
        minutes, seconds = divmod(elapsed.seconds, 60)
        return f"{minutes}m {seconds}s"
    
    def get_eta(self, remaining_steps: int) -> str:
        """Estime le temps restant"""
        if self.current_step == 0:
            return "N/A"
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        avg_per_step = elapsed / self.current_step
        eta_seconds = avg_per_step * remaining_steps
        
        minutes, seconds = divmod(int(eta_seconds), 60)
        return f"{minutes}m {seconds}s"
    
    def print_summary(self):
        """Affiche le résumé final"""
        elapsed = self.get_elapsed()
        
        if self.pbar:
            self.pbar.close()
        
        print(f"\n{'='*60}")
        print(f"[OK] NBA-15 COMPLETE")
        print(f"{'='*60}")
        print(f"⏱️  Temps total: {elapsed}")
        print(f"📊 Étapes complétées: {self.current_step}/{self.total_steps}")
        print(f"{'='*60}")
    
    def close(self):
        """Ferme le tracker"""
        if self.pbar:
            self.pbar.close()


class SimpleProgress:
    """Version simplifiée sans tqdm"""
    
    def __init__(self, total: int, desc: str = "Progress"):
        self.total = total
        self.current = 0
        self.desc = desc
        self.start = time.time()
    
    def update(self, n: int = 1):
        self.current += n
        pct = (self.current / self.total) * 100
        bar = "█" * int(pct / 2) + "░" * (50 - int(pct / 2))
        print(f"\r{self.desc}: |{bar}| {pct:.1f}% ({self.current}/{self.total})", end="")
    
    def close(self):
        elapsed = time.time() - self.start
        print(f"\n✅ Terminé en {elapsed:.1f}s")
