# "I know what I did last summer" Langflow agent.

> **Keywords:** #langflow #p20250620a #agent #llm #pipeline #workflow #whatsapp #twilio #whisper #openai #mistral #mcp #voice-assistant #speech-to-text #webhook #python #docker #hackathon #poc #project-management #personal-assistant #audio-processing #nlp #chatbot #automation #ngrok #ai-agent #voice-commands #project-tracker #eleven-labs #custom-components #langflow-components

Langflow-based agent that keeps track of my personal projects.

Implemented as a project for "Hacking Agents" Hackathon, sponsored by Langflow, Twilio, Mistral, Eleven Labs (London, Jun 2025).

**IT IS A POC. NOT FOR PRODUCTION USE**

The workflow is triggered by WhatsApp voice message.

It can:

- **Find projects and notes** by verbal description, e.g. "What have I done to get driving license?" returns list of actions with dates.
- **Create new projects.** E.g. "I'm about to find a good present for my uncle's birthday" will create project folder with README.md file in it, containing concise and accurate title and applicable keywords.

## System Architecture

```mermaid
sequenceDiagram
    participant U as User
    participant WA as WhatsApp
    participant T as Twilio
    participant WH as Webhook<br/>(whatsapp_audio_link_recever.py)
    participant LF as Langflow Pipeline
    participant W as Whisper Component<br/>(Speech-to-Text)
    participant LLM as LLM Agent
    participant MCP as MCP Projector<br/>(mcp_projector.py)
    participant TS as Twilio Send Component<br/>(WhatsApp Response)

    U->>WA: Voice message with prompt
    WA->>T: Audio message
    T->>WH: POST webhook with audio URL
    Note right of T: Twilio webhook configured<br/>to point to ngrok tunnel

    WH->>LF: Trigger Langflow pipeline<br/>with audio URL parameter

    LF->>W: Pass audio URL
    W->>W: Download audio file
    W->>W: Whisper API<br/>(Speech-to-Text)
    W->>LLM: Text prompt

    LLM->>MCP: Request project details
    Note right of MCP: Custom MCP server<br/>provides project information

    MCP->>LLM: Project data
    LLM->>LLM: Process request<br/>with project context
    LLM->>TS: Generated response text

    TS->>T: Send WhatsApp message
    T->>WA: Text response
    WA->>U: Answer delivered

    Note over WH, MCP: All components run locally<br/>except Twilio/WhatsApp services
```

This project uses Langflow running in the Docker:

```bash
docker run -d --name langflow-app -p 7860:7860 langflowai/langflow:latest
```

## Implementation details

- MCP for searching and creating projects
- Custom component for turning audio into text and processing via LLM (Whisper-based)
- Custom component for returning text responses via WhatsApp (Twilio-based)
- Versions for OpenAI and Mistral LLMs are available