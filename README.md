# "I know what you did last summer" Langflow agent.

Langflow-based agent that keeps track of my personal projects.

The workflow is triggered by WhatsApp voice message.

It can:

- **Find projects and notes** by verbal description, e.g. "What have I done to get driving license?" returns list of actions with dates.
- **Create new projects.** E.g. "I'm about to find a good present for my uncle's birthday" will create project folder with README.md file in it, containing concise and accurate title and applicable keywords.

Next steps:

- Return details from project notes.
- Download and search archived projects.

## Implementation details

- MCP for searching and creating projects
- Custom component for turning audio into text and processing via LLM (Whisper-based)
- Custom component for returning text responses via WhatsApp (Twilio-based)