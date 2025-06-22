# "I know what I did last summer" Langflow agent.

Langflow-based agent that keeps track of my personal projects.

Implemented as a project for "Hacking Agents" Hackathon, sponsored by Langflow, Twilio, Mistral, Eleven Labs (London, Jun 2025).

**IT IS A POC. NOT FOR PRODUCTION USE**

The workflow is triggered by WhatsApp voice message.

It can:

- **Find projects and notes** by verbal description, e.g. "What have I done to get driving license?" returns list of actions with dates.
- **Create new projects.** E.g. "I'm about to find a good present for my uncle's birthday" will create project folder with README.md file in it, containing concise and accurate title and applicable keywords.

## System Architecture

```plantuml
@startuml WhatsApp Voice Agent Flow

!theme plain

actor User as U
participant "WhatsApp" as WA
participant "Twilio" as T
participant "Webhook\n(whatsapp_audio_link_recever.py)" as WH
participant "Langflow Pipeline" as LF
participant "Whisper Component\n(Speech-to-Text)" as W
participant "LLM Agent" as LLM
participant "MCP Projector\n(mcp_projector.py)" as MCP
participant "Twilio Send Component\n(WhatsApp Response)" as TS

U -> WA: Voice message with prompt
WA -> T: Audio message
T -> WH: POST webhook with audio URL
note right of T: Twilio webhook configured\nto point to ngrok tunnel

WH -> LF: Trigger Langflow pipeline\nwith audio URL parameter

LF -> W: Pass audio URL
W -> W: Download audio file
W -> W: Whisper API\n(Speech-to-Text)
W -> LLM: Text prompt

LLM -> MCP: Request project details
note right of MCP: Custom MCP server\nprovides project information

MCP -> LLM: Project data
LLM -> LLM: Process request\nwith project context
LLM -> TS: Generated response text

TS -> T: Send WhatsApp message
T -> WA: Text response
WA -> U: Answer delivered

note over WH, MCP: All components run locally\nexcept Twilio/WhatsApp services

@enduml
```

Next steps:

- Return details from project notes.
- Download and search archived projects.

## Implementation details

- MCP for searching and creating projects
- Custom component for turning audio into text and processing via LLM (Whisper-based)
- Custom component for returning text responses via WhatsApp (Twilio-based)
- Versions for OpenAI and Mistral LLMs are available