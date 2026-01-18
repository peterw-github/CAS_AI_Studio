"""
Protocol definitions for CAS brain↔bridge communication.

Instead of parsing strings like "UPLOAD|||path|||message", we use
typed dataclasses that are serialized/deserialized cleanly.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import json


# --- RESPONSE TYPES (Brain → Bridge) ---

@dataclass
class TextResponse:
    """Plain text to send to chat."""
    text: str
    
    def to_dict(self):
        return {"type": "text", "text": self.text}


@dataclass
class FileUpload:
    """Upload a file from disk."""
    path: str
    message: str
    
    def to_dict(self):
        return {"type": "file_upload", "path": self.path, "message": self.message}


@dataclass
class Screenshot:
    """Take and send a screenshot."""
    message: str
    
    def to_dict(self):
        return {"type": "screenshot", "message": self.message}


@dataclass
class ScreenRecord:
    """Screen recording (already in clipboard from OBS)."""
    message: str
    
    def to_dict(self):
        return {"type": "screen_record", "message": self.message}


@dataclass
class PhonePhoto:
    """Photo from phone camera."""
    message: str
    
    def to_dict(self):
        return {"type": "phone_photo", "message": self.message}


@dataclass
class PhoneVideo:
    """Video from phone camera (already in clipboard)."""
    message: str
    
    def to_dict(self):
        return {"type": "phone_video", "message": self.message}


@dataclass
class DeleteFile:
    """Delete a file from the chat by filename."""
    filename: str
    
    def to_dict(self):
        return {"type": "delete_file", "filename": self.filename}


# --- COMMAND RESULT (Wrapper) ---

@dataclass
class CommandResult:
    """Result of executing a command."""
    responses: List = field(default_factory=list)  # List of response objects
    new_interval: Optional[int] = None  # New interval in seconds, if changed
    should_stop: bool = False  # Whether to stop the brain loop
    
    def add(self, response):
        """Add a response to the list."""
        self.responses.append(response)
        return self
    
    def add_text(self, text: str):
        """Convenience: add a plain text response."""
        self.responses.append(TextResponse(text))
        return self


# --- SERIALIZATION ---

def serialize_responses(responses: List) -> str:
    """Convert response objects to JSON for the command queue file."""
    return json.dumps([r.to_dict() for r in responses])


def deserialize_responses(json_str: str) -> List[dict]:
    """Parse JSON back into response dicts."""
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return []
