
import discord
from discord.ext import commands, tasks
import random
import asyncio
import os
import json
from flask import Flask
from threading import Thread

# --- CONFIGURACIÓN DE FLASK PARA RENDER (KEEP ALIVE) ---
app = Flask('')
@app.route('/')
def home(): return "Bot Vivo"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- LÓGICA DEL BOT ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True # Necesario para cambiar apodos
bot = commands.Bot(command_prefix='!', intents=intents)

DB_FILE = 'caos_db.json'

def cargar_puntos():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f: return json.load(f)
    return {}

def guardar_puntos(data):
    with open(DB_FILE, 'w') as f: json.dump(data, f)

@bot.event
async def on_ready():
    print(f'Conectado como {bot.user}')
    bomba_aleatoria.start() # Inicia el ciclo de bombas

# --- COMANDO: LA BOMBA (EVENTO ALEATORIO) ---
@tasks.loop(minutes=20) # Lanza una bomba cada 20 min
async def bomba_aleatoria():
    # Solo actúa en un canal específico o el primero que encuentre
    channel = bot.get_channel(ID_DE_TU_CANAL) 
    if channel:
        await channel.send("💣 **¡ATENCIÓN! Una bomba ha aparecido. Escribe `DESACTIVAR` rápido!**")
        def check(m): return m.content.upper() == 'DESACTIVAR' and m.channel == channel
        
        try:
            msg = await bot.wait_for('message', check=check, timeout=10.0)
            puntos = cargar_puntos()
            uid = str(msg.author.id)
            puntos[uid] = puntos.get(uid, 0) + 100
            guardar_puntos(puntos)
            await channel.send(f"✅ {msg.author.mention} fue el más rápido. +100 de Poder de Caos. ⚡")
        except asyncio.TimeoutError:
            await channel.send("💥 **¡BOOM! Nadie la desactivó. Qué lentos...**")

# --- COMANDOS DE PODER (DOPAMINA) ---
@bot.command()
async def puntos(ctx):
    p = cargar_puntos().get(str(ctx.author.id), 0)
    await ctx.send(f"🪙 Tienes **{p}** puntos de Poder de Caos.")

@bot.command()
async def humillar(ctx, oponente: discord.Member):
    """Cuesta 150 puntos: Cambia el nombre a alguien por 1 min"""
    puntos = cargar_puntos()
    uid = str(ctx.author.id)
    if puntos.get(uid, 0) < 150:
        return await ctx.send("❌ No tienes suficiente poder (150 pts).")
    
    puntos[uid] -= 150
    guardar_puntos(puntos)
    
    old_nick = oponente.display_name
    await oponente.edit(nick="🤡 Payaso de " + ctx.author.name)
    await ctx.send(f"⚡ {oponente.mention} ha sido humillado por {ctx.author.name}.")
    
    await asyncio.sleep(60) # Espera 1 minuto
    await oponente.edit(nick=old_nick)

@bot.command()
async def ruleta(ctx, apuesta: int):
    """Apuesta tus puntos: Duplica o pierde todo"""
    puntos = cargar_puntos()
    uid = str(ctx.author.id)
    if puntos.get(uid, 0) < apuesta:
        return await ctx.send("❌ No tienes tantos puntos.")
    
    if random.random() > 0.5:
        puntos[uid] += apuesta
        await ctx.send(f"🎰 ¡GANASTE! Ahora tienes {puntos[uid]} puntos.")
    else:
        puntos[uid] -= apuesta
        await ctx.send(f"💀 PERDISTE. La casa gana.")
    guardar_puntos(puntos)

keep_alive()
bot.run(os.getenv('DISCORD_TOKEN'))

