"""
Atlas Voice — WebSocket server for Twilio ConversationRelay.

Handles real-time voice conversations:
  POST /twiml  → Returns TwiML connecting the call to ConversationRelay
  WS   /ws     → WebSocket endpoint for ConversationRelay ↔ Claude streaming

Started by call.py, not run directly.
"""

import json
import os
import sys
from pathlib import Path

import anthropic
import yaml
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import Response

# Load config
CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "args" / "voice_config.yaml"
CONTACTS_PATH = Path(__file__).resolve().parent.parent.parent / "args" / "contacts.yaml"

with open(CONFIG_PATH) as f:
    config = yaml.safe_load(f)

with open(CONTACTS_PATH) as f:
    contacts = yaml.safe_load(f)

app = FastAPI()
claude = anthropic.Anthropic()

# Passed via environment by call.py
NGROK_DOMAIN = os.environ.get("NGROK_DOMAIN", "localhost:8001")
CALL_CONTEXT = os.environ.get("CALL_CONTEXT", "")
CALL_GREETING = os.environ.get("CALL_GREETING", "Hey, this is Atlas.")


@app.post("/twiml")
async def twiml_endpoint(request: Request):
    """Return TwiML that connects the call to ConversationRelay via WebSocket."""
    ws_url = f"wss://{NGROK_DOMAIN}/ws"

    tts_config = config.get("tts", {})
    voice = tts_config.get("voice", "en-US-Studio-O")
    language = tts_config.get("language", "en-US")
    tts_provider = tts_config.get("provider", "google")

    stt_config = config.get("stt", {})
    stt_provider = stt_config.get("provider", "google")
    stt_language = stt_config.get("language", "en-US")

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <ConversationRelay
            url="{ws_url}"
            ttsProvider="{tts_provider}"
            voice="{voice}"
            language="{language}"
            transcriptionProvider="{stt_provider}"
            speechModel="telephony"
            welcomeGreeting="{CALL_GREETING}"
        />
    </Connect>
</Response>"""

    return Response(content=twiml, media_type="application/xml")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """Handle ConversationRelay WebSocket — relay between caller and Claude."""
    await ws.accept()

    # Conversation history for Claude
    system_prompt = config.get("system_prompt", "You are Atlas, an AI assistant on a phone call.")
    if CALL_CONTEXT:
        system_prompt += f"\n\nAbout the person you're calling:\n{CALL_CONTEXT}"

    messages = []
    claude_config = config.get("claude", {})
    model = claude_config.get("model", "claude-sonnet-4-5-20250929")
    max_tokens = claude_config.get("max_tokens", 300)
    temperature = claude_config.get("temperature", 0.7)

    # Transcript for saving later
    transcript_lines = []

    print(f"[voice] WebSocket connected. Model: {model}")
    print(f"[voice] System prompt: {system_prompt[:100]}...")

    try:
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type")

            if msg_type == "setup":
                # Connection established — ConversationRelay is ready
                print(f"[voice] Setup received: {json.dumps(data, indent=2)}")
                continue

            elif msg_type == "prompt":
                # Caller spoke — transcribed text from STT
                caller_text = data.get("voicePrompt", "")
                if not caller_text.strip():
                    continue

                print(f"[voice] Caller: {caller_text}")
                transcript_lines.append(f"Caller: {caller_text}")

                messages.append({"role": "user", "content": caller_text})

                # Stream Claude's response — send each token for early TTS
                full_response = ""
                try:
                    with claude.messages.stream(
                        model=model,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        system=system_prompt,
                        messages=messages,
                    ) as stream:
                        # Collect full text — ConversationRelay expects complete response
                        for text in stream.text_stream:
                            full_response += text
                except anthropic.APIError as e:
                    print(f"[voice] Claude API error: {e}")
                    full_response = "I'm sorry, I had a brief technical issue. Could you repeat that?"

                print(f"[voice] Atlas: {full_response}")
                transcript_lines.append(f"Atlas: {full_response}")

                messages.append({"role": "assistant", "content": full_response})

                # Send response back to ConversationRelay for TTS
                # Token-level streaming: send each sentence as it completes
                # for lower latency on first audio
                response_msg = {
                    "type": "text",
                    "token": full_response,
                    "last": True,
                }
                await ws.send_text(json.dumps(response_msg))

            elif msg_type == "interrupt":
                # Caller interrupted — they spoke while TTS was playing
                utterance = data.get("utteranceUntilInterrupt", "")
                print(f"[voice] Interrupted. Heard so far: {utterance}")

                # Truncate the last assistant message if it was cut off
                if messages and messages[-1]["role"] == "assistant":
                    if utterance:
                        messages[-1]["content"] = utterance
                    else:
                        messages.pop()

            elif msg_type == "error":
                print(f"[voice] Error from ConversationRelay: {data}")

            elif msg_type == "dtmf":
                digit = data.get("digit", "")
                print(f"[voice] DTMF: {digit}")

            else:
                print(f"[voice] Unknown message type: {msg_type} — {data}")

    except WebSocketDisconnect:
        print("[voice] WebSocket disconnected — call ended")
    except Exception as e:
        print(f"[voice] Error: {e}")
    finally:
        # Save transcript
        if transcript_lines:
            _save_transcript(transcript_lines)


def _save_transcript(lines: list[str]):
    """Save call transcript to memory/transcripts/calls/."""
    from datetime import datetime

    transcript_dir = Path(__file__).resolve().parent.parent.parent / "memory" / "transcripts" / "calls"
    transcript_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    filename = now.strftime("%Y-%m-%d_%H%M") + ".md"
    filepath = transcript_dir / filename

    content = f"# Voice Call — {now.strftime('%Y-%m-%d %H:%M')}\n\n"
    for line in lines:
        content += f"{line}\n\n"

    filepath.write_text(content)
    print(f"[voice] Transcript saved: {filepath}")


if __name__ == "__main__":
    import uvicorn
    port = config.get("call", {}).get("server_port", 8001)
    uvicorn.run(app, host="0.0.0.0", port=port)
