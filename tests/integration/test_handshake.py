import pytest
import asyncio
from unittest.mock import MagicMock, patch
from simco_agent.core.handshake import handshake_service, ControllerVendor, ProtocolEnum

@pytest.mark.asyncio
async def test_probe_opcua():
    # Mock _check_port to return True for 4840
    with patch.object(handshake_service, "_check_port", side_effect=lambda ip, port, t=1.0: port == 4840):
        result = await handshake_service.probe("192.168.1.10")
        assert result is not None
        assert result.controller_vendor == ControllerVendor.SIEMENS
        assert result.protocol == ProtocolEnum.OPCUA

@pytest.mark.asyncio
async def test_probe_fanuc():
    with patch.object(handshake_service, "_check_port", side_effect=lambda ip, port, t=1.0: port == 8193):
        result = await handshake_service.probe("192.168.1.11")
        assert result is not None
        assert result.controller_vendor == ControllerVendor.FANUC
        assert result.protocol == ProtocolEnum.FOCAS

@pytest.mark.asyncio
async def test_probe_fail():
    with patch.object(handshake_service, "_check_port", return_value=False):
        result = await handshake_service.probe("192.168.1.99")
        assert result is None
