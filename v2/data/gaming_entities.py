"""
Mobile Gaming Entities Database
Maps game names and companies to their official URLs for hyperlinking
"""

from typing import Dict, Optional

# Top mobile games with their official URLs
MOBILE_GAMES = {
    # Supercell games
    "clash royale": "https://supercell.com/en/games/clashroyale/",
    "clash of clans": "https://supercell.com/en/games/clashofclans/",
    "brawl stars": "https://supercell.com/en/games/brawlstars/",
    "hay day": "https://supercell.com/en/games/hayday/",
    "boom beach": "https://supercell.com/en/games/boombeach/",
    "squad busters": "https://supercell.com/en/games/squadbusters/",

    # King/Activision Blizzard games
    "candy crush saga": "https://king.com/game/candycrush",
    "candy crush": "https://king.com/game/candycrush",
    "farm heroes saga": "https://king.com/game/farm",
    "pet rescue saga": "https://king.com/game/petrescue",

    # Niantic games
    "pokémon go": "https://pokemongolive.com/",
    "pokemon go": "https://pokemongolive.com/",
    "ingress": "https://www.ingress.com/",
    "pikmin bloom": "https://pikminbloom.com/",

    # Riot Games
    "league of legends wild rift": "https://wildrift.leagueoflegends.com/",
    "wild rift": "https://wildrift.leagueoflegends.com/",
    "teamfight tactics": "https://teamfighttactics.leagueoflegends.com/",

    # miHoYo/HoYoverse
    "genshin impact": "https://genshin.hoyoverse.com/",
    "honkai star rail": "https://hsr.hoyoverse.com/",
    "honkai impact 3rd": "https://honkaiimpact3.hoyoverse.com/",

    # Scopely
    "monopoly go": "https://www.monopolygo.com/",
    "stumble guys": "https://www.stumbleguys.com/",
    "marvel strike force": "https://www.marvelstrikeforce.com/",

    # Tencent games
    "honor of kings": "https://www.honorofkings.com/",
    "pubg mobile": "https://www.pubgmobile.com/",
    "call of duty mobile": "https://www.callofduty.com/mobile",

    # Other major games
    "roblox": "https://www.roblox.com/",
    "minecraft": "https://www.minecraft.net/",
    "among us": "https://www.innersloth.com/games/among-us/",
    "garena free fire": "https://ff.garena.com/",
    "coin master": "https://coinmaster.com/",
    "royal match": "https://www.royalmatchgame.com/",
    "subway surfers": "https://www.subwaysurfers.com/",
    "temple run": "https://www.templerun.com/",
    "angry birds": "https://www.angrybirds.com/",
    "fruit ninja": "https://fruitninja.com/",
    "fallout shelter": "https://fallout.bethesda.net/en/games/fallout-shelter",
    "marvel snap": "https://www.marvelsnap.com/",
    "hearthstone": "https://playhearthstone.com/",
    "diablo immortal": "https://diabloimmortal.blizzard.com/",
    "raid shadow legends": "https://raidshadowlegends.com/",
    "homescapes": "https://www.playrix.com/homescapes/",
    "gardenscapes": "https://www.playrix.com/gardenscapes/",
    "township": "https://www.township.com/",
    "cookie run kingdom": "https://www.cookierun-kingdom.com/",
    "afk arena": "https://www.afkarena.com/",
    "rise of kingdoms": "https://rok.lilithgames.com/",
    "state of survival": "https://www.stateofsurvival.com/",
    "empires & puzzles": "https://www.empiresandpuzzles.com/",
    "golf clash": "https://golfclashgame.com/",
    "eight ball pool": "https://www.miniclip.com/games/8-ball-pool-multiplayer/en/",
}

# Gaming companies with their official URLs
GAMING_COMPANIES = {
    "supercell": "https://supercell.com/",
    "king": "https://king.com/",
    "activision blizzard": "https://www.activisionblizzard.com/",
    "niantic": "https://nianticlabs.com/",
    "riot games": "https://www.riotgames.com/",
    "mihoyo": "https://www.hoyoverse.com/",
    "hoyoverse": "https://www.hoyoverse.com/",
    "scopely": "https://scopely.com/",
    "tencent": "https://www.tencent.com/",
    "tencent games": "https://game.qq.com/",
    "netease": "https://www.neteasegames.com/",
    "ea": "https://www.ea.com/",
    "electronic arts": "https://www.ea.com/",
    "ubisoft": "https://www.ubisoft.com/",
    "gameloft": "https://www.gameloft.com/",
    "zynga": "https://www.zynga.com/",
    "playrix": "https://www.playrix.com/",
    "lilith games": "https://www.lilithgames.com/",
    "innersloth": "https://www.innersloth.com/",
    "halfbrick": "https://www.halfbrick.com/",
    "rovio": "https://www.rovio.com/",
    "bethesda": "https://bethesda.net/",
    "second dinner": "https://www.seconddinner.com/",
    "blizzard": "https://www.blizzard.com/",
    "plarium": "https://plarium.com/",
    "miniclip": "https://www.miniclip.com/",
    "voodoo": "https://www.voodoo.io/",
    "ketchapp": "https://www.ketchapp.com/",
    "epic games": "https://www.epicgames.com/",
    "krafton": "https://www.krafton.com/",
    "garena": "https://www.garena.com/",
    "moon active": "https://www.moonactive.com/",
    "dream games": "https://dreamgames.com/",
    "sybo games": "https://sybo.com/",
    "imangi studios": "https://imangistudios.com/",
    "devsisters": "https://www.devsisters.com/",
}


def get_game_url(game_name: str) -> Optional[str]:
    """Get official URL for a game (case-insensitive)"""
    game_key = game_name.lower().strip()
    return MOBILE_GAMES.get(game_key)


def get_company_url(company_name: str) -> Optional[str]:
    """Get official URL for a gaming company (case-insensitive)"""
    company_key = company_name.lower().strip()
    return GAMING_COMPANIES.get(company_key)


def get_entity_url(name: str) -> Optional[str]:
    """Get URL for either a game or company"""
    name_lower = name.lower().strip()

    # Try games first
    url = MOBILE_GAMES.get(name_lower)
    if url:
        return url

    # Try companies
    url = GAMING_COMPANIES.get(name_lower)
    if url:
        return url

    return None


def find_entities_in_text(text: str) -> Dict[str, str]:
    """
    Find all game/company mentions in text and return their URLs

    Returns:
        Dict mapping entity name (as it appears in text) to URL
    """
    text_lower = text.lower()
    found_entities = {}

    # Check games (prioritize longer names first to avoid partial matches)
    game_names_sorted = sorted(MOBILE_GAMES.keys(), key=len, reverse=True)
    for game_name in game_names_sorted:
        if game_name in text_lower:
            # Find the original case version in text
            start_idx = text_lower.find(game_name)
            original_name = text[start_idx:start_idx + len(game_name)]
            found_entities[original_name] = MOBILE_GAMES[game_name]

    # Check companies
    company_names_sorted = sorted(GAMING_COMPANIES.keys(), key=len, reverse=True)
    for company_name in company_names_sorted:
        if company_name in text_lower:
            start_idx = text_lower.find(company_name)
            original_name = text[start_idx:start_idx + len(company_name)]
            # Only add if not already found as a game
            if original_name not in found_entities:
                found_entities[original_name] = GAMING_COMPANIES[company_name]

    return found_entities


# Export all for easy imports
__all__ = [
    'MOBILE_GAMES',
    'GAMING_COMPANIES',
    'get_game_url',
    'get_company_url',
    'get_entity_url',
    'find_entities_in_text',
]
