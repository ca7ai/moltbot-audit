import json
import os
import sys
import argparse
import shutil
import secrets
import stat
import platform
from pathlib import Path

# --- Visual Styling ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("╔════════════════════════════════════════╗")
    print("║          OpenClaw Hardener v1.0         ║")
    print("║      Automated Security Remediation    ║")
    print("╚════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")

def load_config(config_path):
    path = Path(config_path).expanduser().resolve()
    if not path.exists():
        print(f"{Colors.FAIL}[!] Config file not found at: {path}{Colors.ENDC}")
        return None, None
    
    try:
        with open(path, 'r') as f:
            return json.load(f), path
    except Exception as e:
        print(f"{Colors.FAIL}[!] Error reading JSON: {e}{Colors.ENDC}")
        return None, None

def save_config(config, path):
    try:
        with open(path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"{Colors.GREEN}[+] Configuration saved successfully.{Colors.ENDC}")
        return True
    except Exception as e:
        print(f"{Colors.FAIL}[!] Error saving configuration: {e}{Colors.ENDC}")
        return False

def backup_config(path):
    backup_path = path.with_suffix('.json.bak.security')
    try:
        shutil.copy2(path, backup_path)
        print(f"{Colors.BLUE}[*] Created backup at: {backup_path}{Colors.ENDC}")
        return True
    except Exception as e:
        print(f"{Colors.FAIL}[!] Failed to create backup: {e}{Colors.ENDC}")
        return False

def fix_permissions(path):
    print(f"\n{Colors.BLUE}[*] Checking File Permissions...{Colors.ENDC}")
    
    if platform.system() == "Windows":
        print(f"    {Colors.WARNING}[!] Windows detected. Skipping chmod.{Colors.ENDC}")
        print(f"    {Colors.WARNING}>>> Please restrict file permissions via Windows Explorer.{Colors.ENDC}")
        return False

    st = os.stat(path)
    mode = st.st_mode
    
    if (mode & stat.S_IRWXO) or (mode & stat.S_IRWXG):
        print(f"    {Colors.WARNING}[!] Config is too permissive.{Colors.ENDC}")
        choice = input(f"    >>> Fix permissions to 600 (User-only)? [Y/n] ").strip().lower()
        if choice != 'n':
            os.chmod(path, 0o600)
            print(f"    {Colors.GREEN}[+] Permissions updated to 600.{Colors.ENDC}")
            return True
    else:
        print(f"    {Colors.GREEN}[PASS] Permissions are already secure.{Colors.ENDC}")
    return False

def fix_gateway(config):
    changed = False
    print(f"\n{Colors.BLUE}[*] Checking Gateway Security...{Colors.ENDC}")
    gateway = config.get('gateway', {})
    
    # 1. Bind Address
    bind = gateway.get('bind', 'loopback')
    if bind in ['0.0.0.0', 'all', '::']:
        print(f"    {Colors.FAIL}[!] Gateway bound to '{bind}' (Exposed).{Colors.ENDC}")
        choice = input(f"    >>> Change bind to 'loopback' (Localhost only)? [Y/n] ").strip().lower()
        if choice != 'n':
            gateway['bind'] = 'loopback'
            changed = True
            print(f"    {Colors.GREEN}[+] Gateway bind set to 'loopback'.{Colors.ENDC}")

    # 2. Auth Mode
    auth = gateway.get('auth', {})
    mode = auth.get('mode', 'token')
    
    if mode == 'none':
        print(f"    {Colors.FAIL}[!] Gateway authentication is DISABLED.{Colors.ENDC}")
        choice = input(f"    >>> Enable token authentication? [Y/n] ").strip().lower()
        if choice != 'n':
            new_token = secrets.token_hex(32)
            auth['mode'] = 'token'
            auth['token'] = new_token
            gateway['auth'] = auth
            changed = True
            print(f"    {Colors.GREEN}[+] Auth mode enabled.{Colors.ENDC}")
            print(f"    {Colors.GREEN}[+] Generated strong token: {new_token}{Colors.ENDC}")
    
    # Check weak token
    elif mode == 'token':
        token = auth.get('token', '')
        if len(token) < 16:
            print(f"    {Colors.WARNING}[!] Gateway token is weak (<16 chars).{Colors.ENDC}")
            choice = input(f"    >>> Rotate to a new strong token? [Y/n] ").strip().lower()
            if choice != 'n':
                new_token = secrets.token_hex(32)
                auth['token'] = new_token
                gateway['auth'] = auth
                changed = True
                print(f"    {Colors.GREEN}[+] Token rotated: {new_token}{Colors.ENDC}")

    if changed:
        config['gateway'] = gateway
    
    return changed

def fix_channels(config):
    changed = False
    print(f"\n{Colors.BLUE}[*] Checking Channel Policies...{Colors.ENDC}")
    channels = config.get('channels', {})
    
    if not channels:
        return False

    for name, settings in channels.items():
        if not settings.get('enabled', False):
            continue
            
        # DM Policy
        dm_policy = settings.get('dmPolicy', 'pairing')
        if dm_policy == 'open':
            print(f"    {Colors.FAIL}[!] '{name}' DM Policy is 'open'.{Colors.ENDC}")
            choice = input(f"    >>> Change '{name}' DM Policy to 'pairing'? [Y/n] ").strip().lower()
            if choice != 'n':
                settings['dmPolicy'] = 'pairing'
                channels[name] = settings
                changed = True
                print(f"    {Colors.GREEN}[+] '{name}' DM Policy set to 'pairing'.{Colors.ENDC}")
    
    if changed:
        config['channels'] = channels
    
    return changed

def main():
    print_banner()
    parser = argparse.ArgumentParser(description="Harden OpenClaw Configuration")
    parser.add_argument("--config", help="Path to openclaw.json", default="~/.openclaw/openclaw.json")
    parser.add_argument("--dry-run", action="store_true", help="Don't write changes to disk")
    args = parser.parse_args()

    config, path = load_config(args.config)
    
    if not config:
        return

    print(f"Target: {path}\n")

    # Backup first
    if not args.dry_run:
        if not backup_config(path):
            print(f"{Colors.FAIL}Aborting due to backup failure.{Colors.ENDC}")
            return

    changes_made = False
    
    # Run Fixes
    if fix_permissions(path) and not args.dry_run:
        # Permissions are OS level, not JSON level, so we don't set changes_made=True for save_config
        pass
        
    if fix_gateway(config):
        changes_made = True
        
    if fix_channels(config):
        changes_made = True
        
    # Save if modified
    if changes_made:
        print(f"\n{Colors.BLUE}[*] Applying Changes...{Colors.ENDC}")
        if args.dry_run:
            print(f"{Colors.WARNING}[DRY RUN] Config would be saved now.{Colors.ENDC}")
        else:
            save_config(config, path)
            print(f"{Colors.WARNING}>>> NOTE: You must restart OpenClaw for changes to take effect.{Colors.ENDC}")
            print(f"    Run: openclaw gateway restart")
    else:
        print(f"\n{Colors.GREEN}[+] No configuration changes were needed or applied.{Colors.ENDC}")

if __name__ == "__main__":
    main()
