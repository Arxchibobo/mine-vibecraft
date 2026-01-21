"""
Build Claude Code Visualization Control Room in Minecraft
Simplified version using only block commands (no armor stands)
"""

import sys
import math
import time
sys.path.insert(0, 'src')

from vibecraft.config import load_config
from vibecraft.client_bridge import ClientBridge

def main():
    config = load_config()
    bridge = ClientBridge(config)

    print('Connecting to Minecraft...')
    if not bridge.test_connection():
        print('ERROR: Could not connect to Minecraft')
        print('Please make sure you are in a Minecraft world.')
        sys.exit(1)

    # Get player position
    try:
        context = bridge.get_player_context()
        pos = context['position']
        cx, cy, cz = int(pos['block_x']), int(pos['block_y']), int(pos['block_z'])
        print(f'Player position: ({cx}, {cy}, {cz})')
    except Exception as e:
        print(f'Could not get player position: {e}')
        print('Please make sure you are in a Minecraft world.')
        sys.exit(1)

    print()
    commands = []

    print('=' * 60)
    print('Building Claude Code Visualization Control Room')
    print('(Simplified version - blocks only)')
    print('=' * 60)
    print()

    # ===== 1. CENTRAL HUB (at player position) =====
    print('1/5 Building Central Hub...')
    hub_start = len(commands)

    # Circular platform (radius 8)
    for dx in range(-8, 9):
        for dz in range(-8, 9):
            dist_sq = dx * dx + dz * dz
            if dist_sq <= 64:  # radius = 8
                if dist_sq <= 4:
                    block = 'cyan_concrete'
                elif dist_sq <= 25:
                    block = 'light_blue_concrete'
                else:
                    block = 'black_concrete'
                commands.append(f'/setblock {cx + dx} {cy - 1} {cz + dz} {block}')

    # Border pillars at 8 positions
    for angle_deg in [0, 45, 90, 135, 180, 225, 270, 315]:
        rad = math.radians(angle_deg)
        px = int(7 * math.cos(rad))
        pz = int(7 * math.sin(rad))
        for dy in range(5):
            if angle_deg % 90 == 45:
                commands.append(f'/setblock {cx + px} {cy + dy} {cz + pz} sea_lantern')
            else:
                commands.append(f'/setblock {cx + px} {cy + dy} {cz + pz} cyan_terracotta')

    # Central beacon pillar
    for dy in range(3):
        commands.append(f'/setblock {cx} {cy + dy} {cz} diamond_block')
    commands.append(f'/setblock {cx} {cy + 3} {cz} beacon')

    print(f'   Hub: {len(commands) - hub_start} commands')

    # ===== 2. SKILLS MATRIX (North, z-40) =====
    print('2/5 Building Skills Matrix (North)...')
    skills_start = len(commands)
    skill_z = cz - 40

    # 9x9 grid representing 81 skills
    for row in range(9):
        for col in range(9):
            skill_x = cx - 4 + col
            skill_y = cy + row
            # Pattern: mostly available (sea_lantern), some recent (diamond), some unavailable (gray)
            idx = row * 9 + col
            if idx % 11 == 0:
                block = 'gray_concrete'  # unavailable
            elif idx % 7 == 0:
                block = 'diamond_block'  # recent
            elif idx % 13 == 0:
                block = 'glowstone'  # active
            else:
                block = 'sea_lantern'  # available
            commands.append(f'/setblock {skill_x} {skill_y} {skill_z} {block}')

    # Frame around matrix
    commands.append(f'/fill {cx - 5} {cy - 1} {skill_z - 1} {cx + 5} {cy - 1} {skill_z + 1} black_concrete')
    commands.append(f'/fill {cx - 5} {cy + 9} {skill_z - 1} {cx + 5} {cy + 9} {skill_z + 1} black_concrete')
    commands.append(f'/fill {cx - 5} {cy - 1} {skill_z - 1} {cx - 5} {cy + 9} {skill_z + 1} black_concrete')
    commands.append(f'/fill {cx + 5} {cy - 1} {skill_z - 1} {cx + 5} {cy + 9} {skill_z + 1} black_concrete')

    print(f'   Skills Matrix: {len(commands) - skills_start} commands')

    # ===== 3. MCP TOWER (East, x+40) =====
    print('3/5 Building MCP Tower (East)...')
    mcp_start = len(commands)
    tower_x = cx + 40

    # Tower base
    commands.append(f'/fill {tower_x - 2} {cy - 1} {cz - 2} {tower_x + 2} {cy - 1} {cz + 2} obsidian')

    # 8 MCP server floors (representing 8 MCP servers)
    mcp_servers = ['supabase', 'stripe', 'honeycomb', 'bytebase', 'chart', 'asana', 'playwright', 'context7']
    for floor, server in enumerate(mcp_servers):
        floor_y = cy + floor * 4
        # Core block (server status) - first 6 online, last 2 offline
        core = 'emerald_block' if floor < 6 else 'redstone_block'
        commands.append(f'/setblock {tower_x} {floor_y} {cz} {core}')

        # Tools ring (4 iron blocks around core)
        for dx, dz in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            commands.append(f'/setblock {tower_x + dx} {floor_y} {cz + dz} iron_block')

        # Platform under each floor
        commands.append(f'/fill {tower_x - 2} {floor_y - 1} {cz - 2} {tower_x + 2} {floor_y - 1} {cz + 2} smooth_quartz')

    # Tower tip
    commands.append(f'/setblock {tower_x} {cy + 32} {cz} gold_block')
    commands.append(f'/setblock {tower_x} {cy + 33} {cz} beacon')

    print(f'   MCP Tower: {len(commands) - mcp_start} commands')

    # ===== 4. PLUGINS GARDEN (West, x-40) =====
    print('4/5 Building Plugins Garden (West)...')
    plugins_start = len(commands)
    garden_x = cx - 40

    # Ground platform
    commands.append(f'/fill {garden_x - 12} {cy - 1} {cz - 12} {garden_x + 12} {cy - 1} {cz + 12} grass_block')

    # 9 trees representing different plugin categories
    tree_configs = [
        (0, 0, 'oak', 6),       # Central - development
        (6, 0, 'birch', 5),     # E - documentation
        (-6, 0, 'spruce', 7),   # W - security
        (0, 6, 'jungle', 6),    # S - infrastructure
        (0, -6, 'acacia', 5),   # N - AI/ML
        (5, 5, 'oak', 4),
        (-5, 5, 'birch', 5),
        (5, -5, 'spruce', 6),
        (-5, -5, 'jungle', 5),
    ]

    for dx, dz, tree_type, height in tree_configs:
        tx = garden_x + dx
        tz = cz + dz

        # Trunk
        for dy in range(height):
            commands.append(f'/setblock {tx} {cy + dy} {tz} {tree_type}_log')

        # Leaves (simplified - just top and sides)
        for lx in range(-2, 3):
            for lz in range(-2, 3):
                if abs(lx) + abs(lz) <= 3:
                    commands.append(f'/setblock {tx + lx} {cy + height} {tz + lz} {tree_type}_leaves')
                    commands.append(f'/setblock {tx + lx} {cy + height + 1} {tz + lz} {tree_type}_leaves')

    print(f'   Plugins Garden: {len(commands) - plugins_start} commands')

    # ===== 5. AGENT TIMELINE (South, z+30) =====
    print('5/5 Building Agent Timeline (South)...')
    timeline_start = len(commands)
    timeline_z = cz + 30

    # Rail track base (21 blocks long)
    for i in range(-10, 11):
        track_x = cx + i
        commands.append(f'/setblock {track_x} {cy - 1} {timeline_z} stone_bricks')
        commands.append(f'/setblock {track_x} {cy} {timeline_z} powered_rail')

    # Task markers (5 tasks) representing todo items
    tasks = [
        (-8, 'emerald_block'),   # completed
        (-4, 'emerald_block'),   # completed
        (0, 'gold_block'),       # in_progress (current)
        (4, 'iron_block'),       # pending
        (8, 'iron_block'),       # pending
    ]
    for pos_offset, block in tasks:
        commands.append(f'/setblock {cx + pos_offset} {cy + 1} {timeline_z} {block}')
        commands.append(f'/setblock {cx + pos_offset} {cy + 2} {timeline_z} glass')

    # Start and End markers
    commands.append(f'/setblock {cx - 10} {cy + 2} {timeline_z} emerald_block')
    commands.append(f'/setblock {cx - 10} {cy + 3} {timeline_z} sea_lantern')
    commands.append(f'/setblock {cx + 10} {cy + 2} {timeline_z} diamond_block')
    commands.append(f'/setblock {cx + 10} {cy + 3} {timeline_z} sea_lantern')

    print(f'   Agent Timeline: {len(commands) - timeline_start} commands')

    print()
    print(f'Total commands: {len(commands)}')
    print()

    # Execute commands
    print('Executing commands...')
    success_count = 0
    error_count = 0

    for i, cmd in enumerate(commands):
        try:
            bridge.execute_command(cmd)
            success_count += 1
            if (i + 1) % 100 == 0:
                print(f'   Progress: {i + 1}/{len(commands)}')
        except Exception as e:
            error_count += 1
            if error_count <= 3:
                print(f'   Error: {str(e)[:60]}')

    print()
    print('=' * 60)
    print('VISUALIZATION COMPLETE!')
    print('=' * 60)
    print(f'Success: {success_count} | Errors: {error_count}')
    print()
    print('Module locations:')
    print(f'  Central Hub: ({cx}, {cy}, {cz})')
    print(f'  Skills Matrix: ({cx}, {cy}, {cz - 40}) - North')
    print(f'  MCP Tower: ({cx + 40}, {cy}, {cz}) - East')
    print(f'  Plugins Garden: ({cx - 40}, {cy}, {cz}) - West')
    print(f'  Agent Timeline: ({cx}, {cy}, {cz + 30}) - South')
    print()
    print('Fly to each location to see the visualization!')

    bridge.close()


if __name__ == '__main__':
    main()
