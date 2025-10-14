"""
Migration script to transfer data from JSON files to PostgreSQL database.
Run this once after setting up the database to preserve existing data.
"""
import asyncio
import json
import os
from database import db


async def migrate_user_stats():
    """Migrate user stats from userphone_stats.json to database."""
    stats_file = 'userphone_stats.json'
    
    if not os.path.exists(stats_file):
        print(f"✅ {stats_file} not found - nothing to migrate")
        return
    
    print(f"📂 Loading {stats_file}...")
    with open(stats_file, 'r') as f:
        data = json.load(f)
    
    messages = data.get('messages', {})
    started = data.get('started', {})
    wins_ttt = data.get('wins_ttt', {})
    wins_c4 = data.get('wins_c4', {})
    wins_rps = data.get('wins_rps', {})
    wins_hangman = data.get('wins_hangman', {})
    
    # Collect all user IDs
    all_user_ids = set()
    all_user_ids.update(messages.keys())
    all_user_ids.update(started.keys())
    all_user_ids.update(wins_ttt.keys())
    all_user_ids.update(wins_c4.keys())
    all_user_ids.update(wins_rps.keys())
    all_user_ids.update(wins_hangman.keys())
    
    print(f"📊 Found {len(all_user_ids)} users with stats")
    
    migrated = 0
    for user_id_str in all_user_ids:
        user_id = int(user_id_str)
        
        # Increment each stat
        if user_id_str in messages:
            await db.increment_stat(user_id, 'userphone_messages', messages[user_id_str])
        if user_id_str in started:
            await db.increment_stat(user_id, 'userphone_started', started[user_id_str])
        if user_id_str in wins_ttt:
            await db.increment_stat(user_id, 'wins_tictactoe', wins_ttt[user_id_str])
        if user_id_str in wins_c4:
            await db.increment_stat(user_id, 'wins_connectfour', wins_c4[user_id_str])
        if user_id_str in wins_rps:
            await db.increment_stat(user_id, 'wins_rps', wins_rps[user_id_str])
        if user_id_str in wins_hangman:
            await db.increment_stat(user_id, 'wins_hangman', wins_hangman[user_id_str])
        
        migrated += 1
    
    print(f"✅ Migrated stats for {migrated} users")


async def migrate_warnings():
    """Migrate warnings from warnings.json to database."""
    warnings_file = 'warnings.json'
    
    if not os.path.exists(warnings_file):
        print(f"✅ {warnings_file} not found - nothing to migrate")
        return
    
    print(f"📂 Loading {warnings_file}...")
    with open(warnings_file, 'r') as f:
        data = json.load(f)
    
    total_warnings = 0
    for guild_id_str, users in data.items():
        guild_id = int(guild_id_str)
        for user_id_str, warnings_list in users.items():
            user_id = int(user_id_str)
            for warning in warnings_list:
                await db.add_warning(
                    guild_id,
                    user_id,
                    warning['moderator_id'],
                    warning['reason']
                )
                total_warnings += 1
    
    print(f"✅ Migrated {total_warnings} warnings")


async def migrate_configs():
    """Migrate config JSON files to database."""
    config_files = [
        'giveaway_config.json',
        'timechannel_config.json',
        'welcomer_config.json'
    ]
    
    for config_file in config_files:
        if not os.path.exists(config_file):
            continue
        
        print(f"📂 Loading {config_file}...")
        with open(config_file, 'r') as f:
            data = json.load(f)
        
        # Use filename without extension as the config key
        key = config_file.replace('.json', '')
        await db.set_config(key, data)
        print(f"✅ Migrated {key}")


async def main():
    print("🚀 Starting database migration...")
    print("=" * 50)
    
    # Connect to database
    try:
        await db.connect()
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        print("Make sure DATABASE_URL environment variable is set!")
        return
    
    print()
    
    # Migrate data
    try:
        await migrate_user_stats()
        print()
        await migrate_warnings()
        print()
        await migrate_configs()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return
    finally:
        await db.close()
    
    print()
    print("=" * 50)
    print("✅ Migration complete!")
    print()
    print("You can now safely delete the old JSON files:")
    print("  - userphone_stats.json")
    print("  - warnings.json")
    print("  - giveaway_config.json")
    print("  - timechannel_config.json")
    print("  - welcomer_config.json")


if __name__ == '__main__':
    asyncio.run(main())
