"""Module for parsing email messages using LLMs to extract transaction data."""

import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Determine the project root directory dynamically
# This will be /path/to/finbot
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_directory = os.path.join(project_root, "logfiles")

# Ensure the log directory exists
if not os.path.exists(log_directory):
    os.makedirs(log_directory)


# Configure logging
logging.basicConfig(
    filename="logfiles/llm_operations.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client()


class Transaction(BaseModel):
    """Pydantic model for a transaction."""

    date: str = Field(description="Transaction date in DD/MM/YYYY format")
    amount: float = Field(description="Transaction amount")
    merchant: str = Field(description="Name of the merchant")
    details: str = Field(description="Transaction details or description")
    account: str = Field(description="Account number or identifier")


def parse_mail_message(message):
    """Parses an email message to extract transaction data using a Gemini model with structured output.

    Args:
        message (str): The content of the email message.

    Returns:
        str: The parsed transaction data in JSON format.
    """
    system_instruction = Path("prompts/mail_parser_system.md").read_text(
        encoding="utf-8"
    )

    user_message = (
        Path("prompts/mail_parser_user.md")
        .read_text(encoding="utf-8")
        .format(message=message, format="JSON")
    )

    # Define the JSON schema using Pydantic
    json_schema = Transaction.model_json_schema()

    # Log the system and user messages
    logging.info("System Instruction: %s", system_instruction)
    logging.info("User Message: %s", user_message)

    parsed_message = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_json_schema=json_schema,
        ),
        contents=user_message,
    )

    # Log the output from the LLM
    logging.info("LLM Output: %s", parsed_message.text)

    return parsed_message.text.lower()
