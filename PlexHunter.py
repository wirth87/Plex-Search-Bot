import discord
from discord.ext import commands
import requests
from xml.etree import ElementTree as ET

# Replace these with your actual tokens
PLEX_TOKEN = 'YOUR PLEX TOKEN'  # Replace with your Plex token
DISCORD_TOKEN = 'YOUR DISCORD TOKEN'  # Replace with your Discord token
PLEX_SERVER_URL = 'http://127.0.0.1:32400'  # Replace with your Plex server address
TMDB_API_KEY = 'YOUR TMDB API'  # Replace with your TMDB API key

# Set up the bot with the necessary intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

def create_summary_embed(query, movies_count, shows_count):
    return discord.Embed(
        title=f"Search Results for: {query}",
        description=f"**Total Movies**: {movies_count}\n**Total TV Shows**: {shows_count}",
        color=discord.Color.blue()
    )

def create_movies_embed(movies):
    if not movies:
        return None
    description = "\n\n".join([
        f"[**{movie['title']}**]({movie['tmdb_link']})\n**Size**: {movie['size']} | **Resolution**: {movie['resolution']}" 
        for movie in movies
    ])
    return discord.Embed(
        title="Movies",
        description=description,
        color=discord.Color.blue()
    )

def create_shows_embed(tv_shows):
    if not tv_shows:
        return None
    description = "\n\n".join([
        f"[**{show}**]({details['tmdb_link']})\n**Seasons**: {details['seasons']} | **Total Size**: {details['total_size']:.2f}GB" 
        for show, details in tv_shows.items()
    ])
    return discord.Embed(
        title="TV Shows",
        description=description,
        color=discord.Color.blue()
    )

@bot.command()
async def search(ctx, *, query):
    # Get library sections dynamically
    sources_url = f"{PLEX_SERVER_URL}/library/sections"
    headers = {'X-Plex-Token': PLEX_TOKEN}
    
    sources_response = requests.get(sources_url, headers=headers)
    
    if sources_response.status_code == 200:
        sources_xml = sources_response.text
        sources_root = ET.fromstring(sources_xml)
        
        # Extract source IDs and types from the XML data
        sources = [(source.get('key'), source.get('type')) for source in sources_root.findall(".//Directory")]
    else:
        await ctx.send(f"Error retrieving library sources: {sources_response.status_code}")
        return

    movies = []
    tv_shows = {}

    for source_id, source_type in sources:
        # Search movies, shows, etc., in all types of libraries
        search_url = f"{PLEX_SERVER_URL}/library/sections/{source_id}/all?query={query}"
        
        response = requests.get(search_url, headers=headers)
        
        if response.status_code == 200:
            xml_data = response.text
            
            # Parse XML data
            root = ET.fromstring(xml_data)
            
            # Extract titles and sizes from the XML data for both movies and TV shows
            if source_type == 'movie':
                for element in root.findall(".//Video[@type='movie']"):
                    title = element.get('title')
                    if title and query.lower() in title.lower():
                        # Get size and resolution
                        size = 0
                        resolution = "Unknown"
                        tmdb_link = None
                        
                        for part in element.findall(".//Part"):
                            size += int(part.get('size', 0))
                        
                        # Get video resolution from the Media element
                        media_element = element.find(".//Media")
                        if media_element is not None:
                            video_resolution = media_element.get('videoResolution')
                            if video_resolution == '1080':
                                resolution = '1080p'
                            elif video_resolution == '720':
                                resolution = '720p'
                            elif video_resolution == '4k':
                                resolution = '4K'
                        
                        # Get TMDB link
                        guid_element = element.find(".//Guid[@id]")
                        if guid_element is not None:
                            guid_id = guid_element.get('id')
                            if guid_id and 'tmdb://' in guid_id:
                                tmdb_id = guid_id.split('tmdb://')[1]
                                tmdb_link = f"https://www.themoviedb.org/movie/{tmdb_id}"
                        else:
                            # If no TMDB link is found in metadata, search TMDB API for the movie
                            search_tmdb_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}"
                            tmdb_response = requests.get(search_tmdb_url)
                            if tmdb_response.status_code == 200:
                                tmdb_data = tmdb_response.json()
                                if tmdb_data['results']:
                                    tmdb_id = tmdb_data['results'][0]['id']
                                    tmdb_link = f"https://www.themoviedb.org/movie/{tmdb_id}"
                        
                        size_gb = size / (1024 ** 3)  # Convert bytes to GB
                        size_str = f"{size_gb:.2f}GB"
                        movies.append({
                            'title': title,
                            'size': size_str,
                            'resolution': resolution,
                            'tmdb_link': tmdb_link or "No TMDB link available"
                        })
            
            elif source_type == 'show':
                for element in root.findall(".//Directory[@type='show']"):
                    title = element.get('title')
                    rating_key = element.get('ratingKey')
                    if title and query.lower() in title.lower():
                        tv_shows[title] = {'rating_key': rating_key, 'total_size': 0}

    # Fetch and count seasons for each TV show
    for show, details in tv_shows.items():
        show_url = f"{PLEX_SERVER_URL}/library/metadata/{details['rating_key']}/children"
        show_response = requests.get(show_url, headers=headers)
        
        if show_response.status_code == 200:
            show_xml = show_response.text
            show_root = ET.fromstring(show_xml)
            
            # Count seasons and total size for the TV show
            seasons = show_root.findall(".//Directory[@type='season']")
            details['seasons'] = len(seasons)
            
            # Calculate total size for the TV show
            total_size = 0
            for season in seasons:
                season_url = f"{PLEX_SERVER_URL}/library/metadata/{season.get('ratingKey')}/children"
                season_response = requests.get(season_url, headers=headers)
                
                if season_response.status_code == 200:
                    season_xml = season_response.text
                    season_root = ET.fromstring(season_xml)
                    
                    for part in season_root.findall(".//Part"):
                        total_size += int(part.get('size', 0))
            
            details['total_size'] = total_size / (1024 ** 3)  # Convert bytes to GB

            # Fetch TMDB link for the TV show
            search_tmdb_url = f"https://api.themoviedb.org/3/search/tv?api_key={TMDB_API_KEY}&query={show}"
            tmdb_response = requests.get(search_tmdb_url)
            if tmdb_response.status_code == 200:
                tmdb_data = tmdb_response.json()
                if tmdb_data['results']:
                    tmdb_id = tmdb_data['results'][0]['id']
                    details['tmdb_link'] = f"https://www.themoviedb.org/tv/{tmdb_id}"
                else:
                    details['tmdb_link'] = "No TMDB link available"
            else:
                details['tmdb_link'] = "TMDB API error"

    # Create and send the embed responses
    embed_sections = []

    # Section 1: Summary
    summary_embed = create_summary_embed(query, len(movies), len(tv_shows))
    embed_sections.append(summary_embed)

    # Section 2: Movies
    movies_per_message = 10  # Adjust as needed
    for i in range(0, len(movies), movies_per_message):
        movie_slice = movies[i:i + movies_per_message]
        movies_embed = create_movies_embed(movie_slice)
        if movies_embed:
            embed_sections.append(movies_embed)

    # Section 3: TV Shows
    tv_shows_per_message = 10  # Adjust as needed
    for i in range(0, len(tv_shows), tv_shows_per_message):
        shows_slice = dict(list(tv_shows.items())[i:i + tv_shows_per_message])
        shows_embed = create_shows_embed(shows_slice)
        if shows_embed:
            embed_sections.append(shows_embed)

    # Send all embed messages
    for embed in embed_sections:
        await ctx.send(embed=embed)

# Run the bot
bot.run(DISCORD_TOKEN)
