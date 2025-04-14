# Slack Kanban Bot

This Slack bot integrates with Trello to help manage tasks in a Kanban board directly from Slack. It uses natural language processing (NLP) to create, update, complete, and delete tasks in Trello based on messages received in Slack.

## Features

- **Create Tasks**: Add new tasks to a Trello board with specific priority.
- **Complete Tasks**: Mark tasks as complete in the Trello board.
- **Update Tasks**: Update the name or priority of an existing task.
- **Delete Tasks**: Remove tasks from the Kanban board.
- **View Tasks**: List all current tasks and their status.
- **Natural Language Processing**: Uses an LLM (Large Language Model) to extract task actions from Slack messages.
  
## Technologies Used

- **Slack Bolt**: Framework to build Slack apps.
- **Trello API**: For managing tasks in a Trello board.
- **Groq (LLM)**: For natural language understanding and task extraction.
- **Python**: Programming language used for bot logic.
- **dotenv**: For loading environment variables.
- **requests**: For making HTTP requests to Trello.

## Prerequisites

Before setting up the project, ensure you have the following:

1. **Python 3.7+**: Make sure Python is installed on your machine.
2. **Slack App**: You'll need a Slack app with the appropriate permissions.
3. **Trello Account**: A Trello account with a board to manage.
4. **Groq API Key**: For LLM interaction.

### Dependencies

Install the necessary dependencies by running the following:

```bash
pip install -r requirements.txt
