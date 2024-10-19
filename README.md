# UK Biobank Query App

This Streamlit application allows users to query the UK Biobank database using natural language. It converts natural language questions to SQL queries, executes them, and provides an analysis of the results using AI agents.

## Features

- Natural language to SQL query conversion
- Database setup from CSV files
- Interactive query interface
- AI-powered data analysis and report generation

## Prerequisites

- Python 3.7+
- Anthropic API key

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/your-username/uk-biobank-query-app.git
   cd uk-biobank-query-app
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up your Anthropic API key:
   - Rename `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`
   - Replace `your_api_key_here` with your actual Anthropic API key

## Usage

1. Prepare your UK Biobank CSV files.

2. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

3. In the app:
   - Enter the paths to your CSV files (comma-separated)
   - Wait for the database to be set up
   - Enter your question about the UK Biobank data
   - View the generated SQL query, analysis, and report

## Project Structure

- `app.py`: Main Streamlit application
- `database_utils.py`: Database setup and utility functions
- `nlp_utils.py`: Natural language processing and SQL conversion functions
- `crewai_components.py`: CrewAI agents, tasks, and tools
- `requirements.txt`: List of required Python packages
- `.streamlit/secrets.toml`: Configuration file for API keys

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
