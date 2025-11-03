# multiai/agents/human_approval_agent.py
from __future__ import annotations
import time
import json
import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger("human_approval")


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ApprovalPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ApprovalRequest:
    """Onay isteği detayları"""
    request_id: str
    context: Dict[str, Any]
    priority: ApprovalPriority
    requested_by: str
    requested_at: str
    timeout_seconds: int
    status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ApprovalResult:
    """Onay sonucu"""
    request_id: str
    status: ApprovalStatus
    approved: bool
    message: str
    approved_by: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class EnhancedHumanApprovalAgent:
    """
    V5.0 Enhanced Human Approval Agent
    Gelişmiş insan onay süreçleri ve çoklu entegrasyon desteği
    """

    def __init__(self, mode: str = "cli", n8n_webhook_url: Optional[str] = None):
        self.mode = mode
        self.n8n_webhook_url = n8n_webhook_url
        self.pending_requests: Dict[str, ApprovalRequest] = {}
        self.approval_history: List[ApprovalRequest] = []
        self.callbacks: Dict[str, List[Callable]] = {}  # event -> callbacks

        # Onay politikaları
        self.auto_approve_low_risk = True
        self.require_multi_approval_high_risk = True
        self.default_timeout = 3600  # 1 hour

        # n8n entegrasyonu
        self.n8n_integration = n8n_webhook_url is not None

        logger.info(f"HumanApprovalAgent initialized in {mode} mode")

    async def request_approval(self, context: Dict[str, Any],
                               priority: ApprovalPriority = ApprovalPriority.MEDIUM,
                               timeout_seconds: Optional[int] = None,
                               metadata: Optional[Dict[str, Any]] = None) -> ApprovalResult:
        """
        Gelişmiş onay isteği oluştur
        """
        try:
            # Request ID oluştur
            request_id = str(uuid.uuid4())

            # Timeout belirle
            timeout = timeout_seconds or self._calculate_timeout(priority)

            # Onay isteği oluştur
            request = ApprovalRequest(
                request_id=request_id,
                context=context,
                priority=priority,
                requested_by=context.get("requested_by", "system"),
                requested_at=datetime.now().isoformat(),
                timeout_seconds=timeout,
                metadata=metadata or {}
            )

            # Otomatik onay kontrolü
            auto_approve_result = await self._check_auto_approval(request)
            if auto_approve_result:
                return auto_approve_result

            # Onay isteğini kaydet
            self.pending_requests[request_id] = request

            # Onay sürecini başlat
            approval_result = await self._initiate_approval_process(request)

            # Geçmişe kaydet
            self.approval_history.append(request)

            logger.info(f"Approval request {request_id} - Status: {approval_result.status}")

            return approval_result

        except Exception as e:
            logger.error(f"Approval request failed: {e}")
            return ApprovalResult(
                request_id=request_id if 'request_id' in locals() else "unknown",
                status=ApprovalStatus.REJECTED,
                approved=False,
                message=f"Approval request failed: {str(e)}"
            )

    async def _check_auto_approval(self, request: ApprovalRequest) -> Optional[ApprovalResult]:
        """Otomatik onay kontrolü"""

        # Düşük riskli işlemler için otomatik onay
        if (self.auto_approve_low_risk and
                request.priority == ApprovalPriority.LOW and
                request.context.get("risk_level") in ["low", "none"]):
            logger.info(f"Auto-approved low risk request: {request.request_id}")

            request.status = ApprovalStatus.APPROVED
            request.approved_by = "auto_approval_system"
            request.approved_at = datetime.now().isoformat()

            return ApprovalResult(
                request_id=request.request_id,
                status=ApprovalStatus.APPROVED,
                approved=True,
                message="Auto-approved: Low risk operation",
                approved_by="auto_approval_system"
            )

        # Kritik bütçe aşımı - otomatik red
        if (request.context.get("type") == "budget_exceeded" and
                request.context.get("amount", 0) > 1000):  # $1000+ bütçe aşımı

            logger.warning(f"Auto-rejected critical budget exceed: {request.request_id}")

            request.status = ApprovalStatus.REJECTED
            request.rejection_reason = "Critical budget exceedance requires manual review"

            return ApprovalResult(
                request_id=request.request_id,
                status=ApprovalStatus.REJECTED,
                approved=False,
                message="Auto-rejected: Critical budget exceedance"
            )

        return None

    async def _initiate_approval_process(self, request: ApprovalRequest) -> ApprovalResult:
        """Onay sürecini başlat"""

        if self.mode == "cli":
            return await self._handle_cli_approval(request)
        elif self.mode == "n8n":
            return await self._handle_n8n_approval(request)
        elif self.mode == "api":
            return await self._handle_api_approval(request)
        else:
            raise ValueError(f"Unsupported approval mode: {self.mode}")

    async def _handle_cli_approval(self, request: ApprovalRequest) -> ApprovalResult:
        """CLI tabanlı onay süreci"""

        # Onay detaylarını göster
        self._display_approval_request(request)

        # Timeout ile input bek