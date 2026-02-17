"""Tests for Atlas Voice tools."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TOOLS_DIR = Path(__file__).resolve().parent.parent / "tools" / "voice"
ARGS_DIR = Path(__file__).resolve().parent.parent / "args"


class TestConfig:
    """Test config files load correctly."""

    def test_voice_config_loads(self):
        with open(ARGS_DIR / "voice_config.yaml") as f:
            config = yaml.safe_load(f)
        assert config["tts"]["provider"] == "ElevenLabs"
        assert "voice" in config["tts"]
        assert config["claude"]["model"] == "claude-sonnet-4-5-20250929"
        assert config["call"]["server_port"] == 8001
        assert "system_prompt" in config

    def test_contacts_loads(self):
        with open(ARGS_DIR / "contacts.yaml") as f:
            contacts = yaml.safe_load(f)
        assert "contacts" in contacts
        assert "norm" in contacts["contacts"]
        assert "austin" in contacts["contacts"]
        assert "phone" in contacts["contacts"]["norm"]
        assert "context" in contacts["contacts"]["norm"]


class TestContactResolution:
    """Test contact name → phone resolution."""

    def test_resolve_known_contact(self):
        # Import after path setup
        from tools.voice.call import resolve_contact, contacts_data

        # Temporarily set a real-looking phone number
        contacts_data["contacts"]["norm"]["phone"] = "+19105551234"
        phone, name, context = resolve_contact("norm")
        assert phone == "+19105551234"
        assert name == "norm"
        # Restore
        contacts_data["contacts"]["norm"]["phone"] = "+1REPLACEME"

    def test_resolve_raw_number(self):
        from tools.voice.call import resolve_contact
        phone, name, context = resolve_contact("+19105551234")
        assert phone == "+19105551234"
        assert name == "Unknown"

    def test_resolve_unknown_contact(self):
        from tools.voice.call import resolve_contact
        with pytest.raises(SystemExit):
            resolve_contact("nobody")

    def test_resolve_unconfigured_contact(self):
        from tools.voice.call import resolve_contact
        with pytest.raises(SystemExit):
            resolve_contact("norm")  # phone is REPLACEME


class TestTwiML:
    """Test the TwiML endpoint."""

    def test_twiml_returns_valid_xml(self):
        # Set required env vars before importing
        os.environ["NGROK_DOMAIN"] = "test.ngrok.io"
        os.environ["CALL_GREETING"] = "Hello test"
        os.environ["CALL_CONTEXT"] = ""

        from tools.voice.server import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.post("/twiml")
        assert response.status_code == 200
        assert "application/xml" in response.headers["content-type"]

        body = response.text
        assert "<Response>" in body
        assert "<ConversationRelay" in body
        assert "wss://test.ngrok.io/ws" in body
        assert 'ttsProvider="ElevenLabs"' in body
        assert "elevenlabsTextNormalization" in body
        assert "Hello test" in body


class TestWebSocket:
    """Test WebSocket message handling."""

    def test_websocket_accepts_connection(self):
        os.environ["NGROK_DOMAIN"] = "test.ngrok.io"
        os.environ["CALL_GREETING"] = "Hello test"
        os.environ["CALL_CONTEXT"] = ""

        from tools.voice.server import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        with client.websocket_connect("/ws") as ws:
            # Send setup message
            ws.send_text(json.dumps({"type": "setup", "callSid": "CA123"}))
            # Connection should stay open — no response expected for setup

    @patch("tools.voice.server.claude")
    def test_websocket_handles_prompt(self, mock_claude):
        os.environ["NGROK_DOMAIN"] = "test.ngrok.io"
        os.environ["CALL_GREETING"] = "Hello"
        os.environ["CALL_CONTEXT"] = ""

        # Mock the streaming response
        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=False)
        mock_stream.text_stream = iter(["Hello ", "there!"])
        mock_claude.messages.stream.return_value = mock_stream

        from tools.voice.server import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        with client.websocket_connect("/ws") as ws:
            # Send setup
            ws.send_text(json.dumps({"type": "setup"}))
            # Send a prompt (caller spoke)
            ws.send_text(json.dumps({
                "type": "prompt",
                "voicePrompt": "Hey, who is this?"
            }))
            # Should get a response
            response = ws.receive_text()
            data = json.loads(response)
            assert data["type"] == "text"
            assert "Hello there!" in data["token"]
            assert data["last"] is True
