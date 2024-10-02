{\rtf1\ansi\ansicpg1252\cocoartf2639
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import discord\
from discord.ext import commands\
import requests\
import geopandas as gpd\
import matplotlib.pyplot as plt\
import io\
\
class COVIDWastewaterMap(commands.Cog):\
    def __init__(self, bot):\
        self.bot = bot\
\
    @commands.command()\
    async def covidmap(self, ctx):\
        """Send an embedded map of current COVID-19 wastewater data."""\
        \
        # Fetch the data from the CDC NWSS API (replace URL as needed)\
        data_url = "https://data.cdc.gov/resource/g653-rqe2.json"\
        response = requests.get(data_url)\
        \
        if response.status_code == 200:\
            data = response.json()\
            \
            # Extract the coordinates and case levels\
            latitudes = [float(item['latitude']) for item in data if 'latitude' in item]\
            longitudes = [float(item['longitude']) for item in data if 'longitude' in item]\
            viral_levels = [item.get('sars_cov_2_virus_normalized_concentration', 0) for item in data]\
            \
            # Load base map of the US\
            world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))\
            us = world[world.name == "United States"]\
            \
            # Plot the map\
            fig, ax = plt.subplots(figsize=(10, 8))\
            us.plot(ax=ax, color='lightgray', edgecolor='black')\
            \
            # Plot data points (wastewater sites) on the map\
            ax.scatter(longitudes, latitudes, s=20, c=viral_levels, cmap='Reds', alpha=0.6)\
            plt.title("COVID-19 Wastewater Surveillance in the US (Real Data)")\
\
            # Save the map to a BytesIO object\
            map_image = io.BytesIO()\
            plt.savefig(map_image, format='png')\
            map_image.seek(0)\
\
            # Create an embed and attach the image\
            embed = discord.Embed(\
                title="COVID-19 Wastewater Surveillance Data",\
                description="Current COVID-19 levels from wastewater monitoring.",\
                color=0x3498db\
            )\
            embed.set_image(url="attachment://covid_map.png")\
            embed.set_footer(text="Source: CDC NWSS")\
            \
            await ctx.send(embed=embed, file=discord.File(map_image, 'covid_map.png'))\
\
        else:\
            await ctx.send("Could not retrieve data from CDC.")\
\
async def setup(bot):\
    bot.add_cog(COVIDWastewaterMap(bot))}