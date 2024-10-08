# PlexHunter
A simple Discord bot for searching your Plex library and retrieving details about movies and TV shows.

## Features
- **Movies**: Reports movies found with embedded TMDB links in the title, along with total file size and resolution.
- **TV Shows**: Reports TV shows with embedded TMDB links in the title, along with the total number of seasons and the overall size.

## Dependencies

### Python Version
Ensure Python 3.8 or higher is installed.

### Required Packages
These packages can be installed via pip:
- `discord.py`: Library to interact with the Discord API.
- `requests`: For making HTTP requests to the Plex and TMDB APIs.

## Additional Setup

### Plex Token
Obtain your Plex Token by inspecting network requests in the Plex Web app.

### Discord Token
Create a Discord bot via the [Discord Developer Portal](https://discord.com/developers/applications) and retrieve the bot token.

### TMDB API Key
Create an account on [The Movie Database (TMDB)](https://www.themoviedb.org/) and get an API key from the TMDB API settings.

## Configuration
Update the following values in the script before running the bot:

```python
PLEX_TOKEN = 'YOUR_PLEX_TOKEN'  # Replace with your Plex token
DISCORD_TOKEN = 'YOUR_DISCORD_TOKEN'  # Replace with your Discord token
PLEX_SERVER_URL = 'http://127.0.0.1:32400'  # Replace with your Plex server URL
TMDB_API_KEY = 'YOUR_TMDB_API_KEY'  # Replace with your TMDB API key
