"""
Batch Manager - Core Module
============================

Módulo transversal para gerenciamento de uploads em lote.
Centraliza lógica de batch para reutilização em:
- Scheduler (batch schedule)
- Ingestão (batch upload)
- Factory Watcher (batch monitoring)
"""

import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum

from core.smart_logic import smart_logic
from core.scheduler import scheduler_service


class BatchStatus(Enum):
    """Status do batch job"""
    CREATED = "created"
    VALIDATING = "validating"
    VALIDATED = "validated"
    SCHEDULING = "scheduling"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchEvent:
    """Um evento dentro de um batch"""
    id: str
    profile_id: str
    video_path: str
    scheduled_time: datetime
    validation_result: Optional[Dict] = None
    event_id: Optional[str] = None  # ID após agendado
    status: str = "pending"
    metadata: Dict = field(default_factory=dict) # [SYN-39] Per-event config
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "video_path": self.video_path,
            "scheduled_time": self.scheduled_time.isoformat(),
            "validation_result": self.validation_result,
            "event_id": self.event_id,
            "status": self.status
        }


@dataclass
class BatchResult:
    """Resultado de uma operação de batch"""
    batch_id: str
    status: BatchStatus
    events: List[BatchEvent] = field(default_factory=list)
    valid_count: int = 0
    invalid_count: int = 0
    warnings_count: int = 0
    message: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "batch_id": self.batch_id,
            "status": self.status.value,
            "events": [e.to_dict() for e in self.events],
            "valid_count": self.valid_count,
            "invalid_count": self.invalid_count,
            "warnings_count": self.warnings_count,
            "message": self.message
        }


class BatchManager:
    """
    Gerenciador de Batch - Centraliza operações de upload em lote.
    
    Uso:
        batch_id = batch_manager.create_batch(files, profiles, start_time, 60)
        result = batch_manager.validate_batch(batch_id)
        if result.invalid_count == 0:
            result = batch_manager.execute_batch(batch_id)
    """
    
    def __init__(self):
        self._batches: Dict[str, Dict] = {}
    
    def create_batch(
        self, 
        files: List[str], 
        profiles: List[str], 
        start_time: datetime, 
        interval_minutes: int = 60,
        viral_music_enabled: bool = False,
        sound_id: Optional[str] = None,
        sound_title: Optional[str] = None,
        mix_viral_sounds: bool = False  # [SYN-39] New Flag
    ) -> str:
        """
        Cria um novo batch e retorna batch_id.
        """
        batch_id = f"batch_{uuid.uuid4().hex[:8]}"
        
        # [SYN-39] Load Trends for Auto-Mix if enabled
        viral_sounds_pool = []
        if viral_music_enabled and mix_viral_sounds:
            try:
                from core.oracle.trend_checker import trend_checker
                trends = trend_checker.get_cached_trends().get("trends", [])
                # Filter for sounds (assuming trend objects have a type or we just take all)
                # Ideally we check category or type, but here we take top 20 whatever they are
                viral_sounds_pool = trends[:20]
                print(f"🎵 Auto-Mix: Loaded {len(viral_sounds_pool)} sounds for rotation.")
            except Exception as e:
                print(f"⚠️ Auto-Mix Error: {e}")
        
        # Gerar eventos
        events: List[BatchEvent] = []
        cursor = start_time
        
        sound_idx = 0
        
        for i, video_path in enumerate(files):
            for profile_id in profiles:
                # Determine Sound for this specific event
                event_sound_id = sound_id
                event_sound_title = sound_title
                
                # Apply Auto-Mix
                if viral_sounds_pool:
                    track = viral_sounds_pool[sound_idx % len(viral_sounds_pool)]
                    event_sound_id = track["id"]
                    event_sound_title = track["title"]
                    sound_idx += 1
                
                # Store per-event config (overrides batch config if needed)
                # But BatchEvent struct doesn't have metadata field?
                # We need to pass this config to execute_batch or store it in event.
                # Currently BatchEvent is simple.
                # Let's add a `metadata` field to BatchEvent or just rely on the fact that
                # we need to persist this choice.
                # Wait, execute_batch uses `batch["config"]`.
                # If we want per-event sound, we MUST modify BatchEvent to hold it.
                # Let's add `config_override` dict to BatchEvent.
                
                events.append(BatchEvent(
                    id=f"{batch_id}_{i}_{profile_id}",
                    profile_id=profile_id,
                    video_path=video_path,
                    scheduled_time=cursor,
                    # We will attach the sound info here. 
                    # See BatchEvent definition update below.
                    metadata={
                        "viral_music_enabled": viral_music_enabled,
                        "sound_id": event_sound_id,
                        "sound_title": event_sound_title
                    }
                ))
            cursor += timedelta(minutes=interval_minutes)
        
        try:
            from zoneinfo import ZoneInfo
        except ImportError:
            from backports.zoneinfo import ZoneInfo
            
        self._batches[batch_id] = {
            "batch_id": batch_id,
            "status": BatchStatus.CREATED,
            "events": events,
            "created_at": datetime.now(ZoneInfo("America/Sao_Paulo")),
            "config": {
                "interval_minutes": interval_minutes,
                "viral_music_enabled": viral_music_enabled,
                "sound_id": sound_id,
                "sound_title": sound_title,
                "mix_viral_sounds": mix_viral_sounds
            }
        }
        
        return batch_id
    
    def validate_batch(self, batch_id: str) -> BatchResult:
        """
        Valida todos os eventos do batch com Smart Logic.
        
        Args:
            batch_id: ID do batch
            
        Returns:
            BatchResult com contagem de válidos/inválidos
        """
        if batch_id not in self._batches:
            return BatchResult(
                batch_id=batch_id,
                status=BatchStatus.FAILED,
                message="Batch not found"
            )
        
        batch = self._batches[batch_id]
        batch["status"] = BatchStatus.VALIDATING
        
        valid = 0
        invalid = 0
        warnings = 0
        
        for event in batch["events"]:
            result = smart_logic.check_conflict(
                event.profile_id,
                event.scheduled_time
            )
            
            event.validation_result = result.to_dict()
            
            if result.is_valid:
                valid += 1
                event.status = "valid"
                if any(i.severity.value == "warning" for i in result.issues):
                    warnings += 1
            else:
                invalid += 1
                event.status = "invalid"
        
        batch["status"] = BatchStatus.VALIDATED
        
        return BatchResult(
            batch_id=batch_id,
            status=BatchStatus.VALIDATED,
            events=batch["events"],
            valid_count=valid,
            invalid_count=invalid,
            warnings_count=warnings,
            message=f"Validated {len(batch['events'])} events"
        )
    
    def execute_batch(
        self, 
        batch_id: str, 
        force: bool = False
    ) -> BatchResult:
        """
        Executa o batch, agendando todos os eventos.
        
        Args:
            batch_id: ID do batch
            force: Se True, ignora eventos inválidos
            
        Returns:
            BatchResult com eventos agendados
        """
        if batch_id not in self._batches:
            return BatchResult(
                batch_id=batch_id,
                status=BatchStatus.FAILED,
                message="Batch not found"
            )
        
        batch = self._batches[batch_id]
        config = batch["config"]
        
        # Verificar se foi validado
        if batch["status"] != BatchStatus.VALIDATED:
            # Validar primeiro
            self.validate_batch(batch_id)
        
        batch["status"] = BatchStatus.SCHEDULING
        scheduled = 0
        skipped = 0
        
        for event in batch["events"]:
            # Pular inválidos se não forçar
            if event.status == "invalid" and not force:
                skipped += 1
                continue
            
            # Encontrar slot seguro
            safe_time = scheduler_service.find_next_available_slot(
                event.profile_id,
                event.scheduled_time
            )
            
            # Agendar
            try:
                # [SYN-39] Prefer event metadata for sound config if present (Auto-Mix)
                evt_meta = event.metadata or {}
                
                use_sound_id = evt_meta.get("sound_id") or config.get("sound_id")
                use_sound_title = evt_meta.get("sound_title") or config.get("sound_title")
                
                scheduled_event = scheduler_service.add_event(
                    profile_id=event.profile_id,
                    video_path=event.video_path,
                    scheduled_time=safe_time,
                    viral_music_enabled=config.get("viral_music_enabled", False),
                    sound_id=use_sound_id,
                    sound_title=use_sound_title
                )
                event.event_id = scheduled_event.get("id")
                event.status = "scheduled"
                scheduled += 1
            except Exception as e:
                event.status = f"error: {str(e)}"
        
        batch["status"] = BatchStatus.COMPLETED
        
        return BatchResult(
            batch_id=batch_id,
            status=BatchStatus.COMPLETED,
            events=batch["events"],
            valid_count=scheduled,
            invalid_count=skipped,
            message=f"Scheduled {scheduled} events, skipped {skipped}"
        )
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict]:
        """
        Retorna status atual do batch.
        """
        if batch_id not in self._batches:
            return None
        
        batch = self._batches[batch_id]
        return {
            "batch_id": batch_id,
            "status": batch["status"].value,
            "events_count": len(batch["events"]),
            "created_at": batch["created_at"].isoformat()
        }
    
    def cancel_batch(self, batch_id: str) -> bool:
        """
        Cancela um batch em andamento.
        """
        if batch_id not in self._batches:
            return False
        
        batch = self._batches[batch_id]
        if batch["status"] in [BatchStatus.COMPLETED, BatchStatus.CANCELLED]:
            return False
        
        batch["status"] = BatchStatus.CANCELLED
        return True
    
    def list_batches(self, limit: int = 20) -> List[Dict]:
        """
        Lista batches recentes.
        """
        batches = sorted(
            self._batches.values(),
            key=lambda b: b["created_at"],
            reverse=True
        )[:limit]
        
        return [self.get_batch_status(b["batch_id"]) for b in batches]


# Instância singleton
batch_manager = BatchManager()
