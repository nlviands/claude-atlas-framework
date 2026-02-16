**Upgrade me to Claude Opus 4.6. Follow these steps exactly:**

1. Find the model catalog file:

find /opt/homebrew/lib/node\_modules/clawdbot \-name "models.generated.js" \-path "\*pi-ai\*"

(On Linux, check `/usr/lib/node_modules/clawdbot` instead)

1. In that file, find `"claude-opus-4-5"`. There are **two** entries (one with `provider: "anthropic"`, one with `provider: "opencode"`). Add this block **above each one**, matching the provider field to whatever the 4.5 entry below it uses:

"claude-opus-4-6": {  
    id: "claude-opus-4-6",  
    name: "Claude Opus 4.6 (latest)",  
    api: "anthropic-messages",  
    provider: "anthropic",  
    baseUrl: "\<https://api.anthropic.com\>",  
    reasoning: true,  
    input: \["text", "image"\],  
    cost: { input: 5, output: 25, cacheRead: 0.5, cacheWrite: 6.25 },  
    contextWindow: 200000,  
    maxTokens: 64000,  
},

1. Patch the config:

    Use `gateway config.patch` with: `{"agents":{"defaults":{"model":{"primary":"anthropic/claude-opus-4-6"},"models":{"anthropic/claude-opus-4-6":{"alias":"opus"}}}}}`

2. **IMPORTANT:** The config patch does a hot reload which won't pick up the catalog change. You need a full cold restart. Run: `clawdbot gateway stop && clawdbot gateway start`

3. After restart, verify with `session_status` that you're running on `claude-opus-4-6`.

