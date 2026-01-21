"""
CAS Core - Clean architecture components for Cortana's Autonomous System.
"""

from cas_core.protocol import (
    CommandResult,
    TextResponse,
    FileUpload,
    Screenshot,
    ScreenRecord,
    PhonePhoto,
    PhoneVideo,
    DeleteFile,
    AmbientScreenshot,
    AmbientAudio,
    serialize_responses,
    deserialize_responses,
)

from cas_core.parser import parse_commands, has_commands
from cas_core.scheduler import HeartbeatScheduler, read_latest_message
from cas_core.commands import dispatch, list_commands, is_registered

__all__ = [
    # Protocol
    'CommandResult',
    'TextResponse', 
    'FileUpload',
    'Screenshot',
    'ScreenRecord',
    'PhonePhoto',
    'PhoneVideo',
    'DeleteFile',
    'AmbientScreenshot',
    'AmbientAudio',
    'serialize_responses',
    'deserialize_responses',
    
    # Parser
    'parse_commands',
    'has_commands',
    
    # Scheduler
    'HeartbeatScheduler',
    'read_latest_message',
    
    # Commands
    'dispatch',
    'list_commands',
    'is_registered',
]
