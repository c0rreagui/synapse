"""
Smart Logic - Motor de Regras Inteligente (Plataforma-Wide)
============================================================

Sistema transversal de validação e otimização de agendamentos.

Usado em:
- Agendamento: Evitar conflitos de horário
- Batch Manager: Distribuir vídeos inteligentemente
- Ingestão: Sugerir melhor horário ao fazer upload
- Central: Validar antes de qualquer ação
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, time
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum

# Importar scheduler existente
from core.scheduler import scheduler_service


class ValidationSeverity(Enum):
    """Severidade da validação"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class ValidationIssue:
    """Um problema de validação encontrado"""
    severity: ValidationSeverity
    code: str
    message: str
    suggested_fix: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "suggested_fix": self.suggested_fix
        }


@dataclass
class ValidationResult:
    """Resultado completo de uma validação"""
    is_valid: bool
    can_proceed: bool  # True se só tem warnings, False se tem errors
    issues: List[ValidationIssue]
    suggested_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "is_valid": self.is_valid,
            "can_proceed": self.can_proceed,
            "issues": [i.to_dict() for i in self.issues],
            "suggested_time": self.suggested_time.isoformat() if self.suggested_time else None
        }


@dataclass
class OptimalTimeSlot:
    """Um slot de horário sugerido com score"""
    time: datetime
    score: float  # 0-100
    reasons: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "time": self.time.isoformat(),
            "score": self.score,
            "reasons": self.reasons
        }


class SmartLogic:
    """
    Motor de Regras Inteligente para validação e otimização de agendamentos.
    
    Regras de Negócio:
    - Intervalo mínimo: 2 horas entre posts do mesmo perfil
    - Máximo posts/dia: 3 por perfil
    - Horário bloqueado: 02:00 - 06:00 (madrugada)
    - Prioridade: Posts mais antigos primeiro
    """
    
    # Configurações de Regras
    MIN_INTERVAL_HOURS = 2
    MAX_POSTS_PER_DAY = 3
    BLOCKED_START_HOUR = 2
    BLOCKED_END_HOUR = 6
    
    # Horários considerados "prime time" para TikTok
    PRIME_TIME_SLOTS = [
        (7, 9),    # Manhã
        (12, 14),  # Almoço
        (19, 23),  # Noite (melhor)
    ]
    
    def __init__(self):
        self.scheduler = scheduler_service
    
    def get_rules(self) -> Dict[str, Any]:
        """Retorna as regras de negócio configuradas"""
        return {
            "min_interval_hours": self.MIN_INTERVAL_HOURS,
            "max_posts_per_day": self.MAX_POSTS_PER_DAY,
            "blocked_hours": {
                "start": self.BLOCKED_START_HOUR,
                "end": self.BLOCKED_END_HOUR
            },
            "prime_time_slots": [
                {"start": s, "end": e} for s, e in self.PRIME_TIME_SLOTS
            ]
        }
    
    def _is_in_blocked_hours(self, dt: datetime) -> bool:
        """Verifica se o horário está no período bloqueado (02:00 - 06:00)"""
        hour = dt.hour
        return self.BLOCKED_START_HOUR <= hour < self.BLOCKED_END_HOUR
    
    def _is_in_prime_time(self, dt: datetime) -> Tuple[bool, str]:
        """Verifica se o horário está em prime time"""
        hour = dt.hour
        for start, end in self.PRIME_TIME_SLOTS:
            if start <= hour < end:
                if start == 19:
                    return True, "🌙 Horário nobre noturno"
                elif start == 12:
                    return True, "🍽️ Horário do almoço"
                else:
                    return True, "🌅 Horário da manhã"
        return False, ""
    
    def _get_posts_count_for_day(self, profile_id: str, target_date: datetime) -> int:
        """Conta quantos posts um perfil tem agendados para um dia"""
        events = self.scheduler.load_schedule()
        count = 0
        
        target_day_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        target_day_end = target_day_start + timedelta(days=1)
        
        for event in events:
            if event.get('profile_id') != profile_id:
                continue
            if event.get('status') in ['completed', 'failed', 'cancelled']:
                continue
                
            try:
                event_time = datetime.fromisoformat(event['scheduled_time'])
                if target_day_start <= event_time < target_day_end:
                    count += 1
            except (KeyError, ValueError):
                continue
                
        return count
    
    def _get_nearest_event(self, profile_id: str, target_time: datetime) -> Optional[Tuple[datetime, float]]:
        """Encontra o evento mais próximo do horário alvo e retorna a distância em horas"""
        events = self.scheduler.load_schedule()
        nearest = None
        min_distance = float('inf')
        
        for event in events:
            if event.get('profile_id') != profile_id:
                continue
            if event.get('status') in ['completed', 'failed', 'cancelled']:
                continue
                
            try:
                event_time = datetime.fromisoformat(event['scheduled_time'])
                distance = abs((event_time - target_time).total_seconds() / 3600)
                
                if distance < min_distance:
                    min_distance = distance
                    nearest = event_time
            except (KeyError, ValueError):
                continue
        
        if nearest:
            return nearest, min_distance
        return None
    
    def check_conflict(
        self, 
        profile_id: str, 
        proposed_time: datetime,
        exclude_event_id: Optional[str] = None
    ) -> ValidationResult:
        """
        Verifica se um horário proposto tem conflitos.
        
        Args:
            profile_id: ID do perfil TikTok
            proposed_time: Horário proposto para o post
            exclude_event_id: ID de evento a excluir da verificação (para edições)
            
        Returns:
            ValidationResult com status e issues encontradas
        """
        issues: List[ValidationIssue] = []
        suggested_time = None
        
        # 1. Verificar horário bloqueado
        if self._is_in_blocked_hours(proposed_time):
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="BLOCKED_HOURS",
                message=f"Horário {proposed_time.strftime('%H:%M')} está no período bloqueado (02:00-06:00)",
                suggested_fix="Agende para após as 06:00"
            ))
        
        # 2. Verificar máximo de posts por dia
        posts_today = self._get_posts_count_for_day(profile_id, proposed_time)
        if posts_today >= self.MAX_POSTS_PER_DAY:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="MAX_POSTS_EXCEEDED",
                message=f"Limite de {self.MAX_POSTS_PER_DAY} posts/dia atingido para este perfil",
                suggested_fix="Agende para outro dia"
            ))
        elif posts_today == self.MAX_POSTS_PER_DAY - 1:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="APPROACHING_LIMIT",
                message=f"Este será o último post permitido hoje ({posts_today + 1}/{self.MAX_POSTS_PER_DAY})",
                suggested_fix=None
            ))
        
        # 3. Verificar intervalo mínimo
        nearest = self._get_nearest_event(profile_id, proposed_time)
        if nearest:
            nearest_time, distance_hours = nearest
            if distance_hours < self.MIN_INTERVAL_HOURS:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="MIN_INTERVAL_VIOLATED",
                    message=f"Intervalo de {distance_hours:.1f}h é menor que o mínimo de {self.MIN_INTERVAL_HOURS}h",
                    suggested_fix=f"Post mais próximo: {nearest_time.strftime('%d/%m às %H:%M')}"
                ))
                
                # Calcular sugestão
                if proposed_time > nearest_time:
                    suggested_time = nearest_time + timedelta(hours=self.MIN_INTERVAL_HOURS)
                else:
                    suggested_time = nearest_time - timedelta(hours=self.MIN_INTERVAL_HOURS)
        
        # 4. Verificar prime time (info)
        is_prime, prime_reason = self._is_in_prime_time(proposed_time)
        if is_prime:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                code="PRIME_TIME",
                message=prime_reason,
                suggested_fix=None
            ))
        
        # Determinar resultado
        has_errors = any(i.severity == ValidationSeverity.ERROR for i in issues)
        has_warnings = any(i.severity == ValidationSeverity.WARNING for i in issues)
        
        return ValidationResult(
            is_valid=not has_errors,
            can_proceed=not has_errors,
            issues=issues,
            suggested_time=suggested_time
        )
    
    def suggest_slot(
        self, 
        profile_id: str, 
        preferred_time: Optional[datetime] = None,
        prefer_prime_time: bool = True
    ) -> Optional[OptimalTimeSlot]:
        """
        Sugere o melhor slot disponível para um perfil.
        
        Args:
            profile_id: ID do perfil
            preferred_time: Horário preferido (opcional)
            prefer_prime_time: Se deve priorizar horários de prime time
            
        Returns:
            OptimalTimeSlot com o horário sugerido
        """
        if preferred_time is None:
            preferred_time = datetime.now()
        
        # Começar a busca a partir do horário preferido
        current = preferred_time
        best_slot = None
        best_score = -1
        
        # Buscar nos próximos 7 dias
        max_attempts = 7 * 24 * 4  # 4 slots por hora
        
        for _ in range(max_attempts):
            # Pular horários bloqueados
            if self._is_in_blocked_hours(current):
                current += timedelta(minutes=15)
                continue
            
            # Verificar se é válido
            result = self.check_conflict(profile_id, current)
            
            if result.is_valid:
                # Calcular score
                score = 50  # Base
                reasons = []
                
                # Bonus para prime time
                is_prime, prime_reason = self._is_in_prime_time(current)
                if is_prime:
                    score += 30
                    reasons.append(prime_reason)
                
                # Bonus para horários próximos ao preferido
                time_diff = abs((current - preferred_time).total_seconds() / 3600)
                if time_diff < 1:
                    score += 20
                    reasons.append("⏰ Próximo ao horário desejado")
                elif time_diff < 3:
                    score += 10
                
                # Verificar se é o melhor até agora
                if score > best_score:
                    best_score = score
                    best_slot = OptimalTimeSlot(
                        time=current,
                        score=score,
                        reasons=reasons if reasons else ["✅ Slot disponível"]
                    )
                
                # Se encontrou um slot perfeito (prime time + próximo), retornar
                if score >= 90:
                    return best_slot
            
            current += timedelta(minutes=15)
        
        return best_slot
    
    def get_optimal_times(
        self, 
        profile_id: str,
        target_date: Optional[datetime] = None,
        count: int = 5
    ) -> List[OptimalTimeSlot]:
        """
        Retorna os melhores horários disponíveis para um perfil.
        
        Args:
            profile_id: ID do perfil
            target_date: Data alvo (default: hoje)
            count: Quantidade de sugestões
            
        Returns:
            Lista de OptimalTimeSlot ordenada por score
        """
        if target_date is None:
            target_date = datetime.now()
        
        slots: List[OptimalTimeSlot] = []
        
        # Começar do início do dia alvo
        day_start = target_date.replace(hour=6, minute=0, second=0, microsecond=0)
        
        # Se o dia é hoje e já passou das 6h, começar de agora
        if target_date.date() == datetime.now().date():
            day_start = max(day_start, datetime.now())
        
        current = day_start
        day_end = day_start.replace(hour=23, minute=59)
        
        while current < day_end and len(slots) < count * 3:  # Buscar mais para ter opções
            if not self._is_in_blocked_hours(current):
                result = self.check_conflict(profile_id, current)
                
                if result.is_valid:
                    score = 50
                    reasons = []
                    
                    is_prime, prime_reason = self._is_in_prime_time(current)
                    if is_prime:
                        score += 40
                        reasons.append(prime_reason)
                    
                    slots.append(OptimalTimeSlot(
                        time=current,
                        score=score,
                        reasons=reasons if reasons else ["✅ Disponível"]
                    ))
            
            current += timedelta(minutes=30)  # Intervalos de 30 min
        
        # Ordenar por score e retornar top N
        slots.sort(key=lambda x: x.score, reverse=True)
        return slots[:count]
    
    def validate_batch(
        self, 
        events: List[Dict]
    ) -> Dict[str, ValidationResult]:
        """
        Valida um batch de eventos.
        
        Args:
            events: Lista de dicts com {profile_id, scheduled_time}
            
        Returns:
            Dict mapeando event_id/index para ValidationResult
        """
        results = {}
        
        for i, event in enumerate(events):
            event_id = event.get('id', str(i))
            profile_id = event.get('profile_id')
            scheduled_time_str = event.get('scheduled_time')
            
            if not profile_id or not scheduled_time_str:
                results[event_id] = ValidationResult(
                    is_valid=False,
                    can_proceed=False,
                    issues=[ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        code="MISSING_DATA",
                        message="profile_id e scheduled_time são obrigatórios"
                    )]
                )
                continue
            
            try:
                scheduled_time = datetime.fromisoformat(scheduled_time_str)
            except ValueError:
                results[event_id] = ValidationResult(
                    is_valid=False,
                    can_proceed=False,
                    issues=[ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        code="INVALID_TIME_FORMAT",
                        message="Formato de data inválido. Use ISO 8601."
                    )]
                )
                continue
            
            results[event_id] = self.check_conflict(
                profile_id, 
                scheduled_time,
                exclude_event_id=event_id if event.get('id') else None
            )
        
        return results


# Instância singleton
smart_logic = SmartLogic()
