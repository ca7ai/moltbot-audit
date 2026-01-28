import json
import os
import sys
import argparse
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
    print("║           Moltbot-Audit v1.0           ║")
    print("║     AI Agent Security Config Scanner   ║")
    print("╚════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")

def load_config(config_path):
    path = Path(config_path).expanduser().resolve()
    if not path.exists():
        print(f"{Colors.FAIL}[!] Config file not found at: {path}{Colors.ENDC}")
        return None
    
    try:
        with open(path, 'r') as f:
            return json.load(f), path
    except Exception as e:
        print(f"{Colors.FAIL}[!] Error reading JSON: {e}{Colors.ENDC}")
        return None, None

def check_file_permissions(path):
    print(f"{Colors.BLUE}[*] Checking File Permissions...{Colors.ENDC}")
    
    if platform.system() == "Windows":
        print(f"    {Colors.WARNING}[!] Windows detected. Permission bits (chmod) do not apply.{Colors.ENDC}")
        print(f"    {Colors.WARNING}>>> MANUAL CHECK: Right-click file -> Properties -> Security.{Colors.ENDC}")
        print(f"    Ensure only you and Administrators have read access.")
        return True

    st = os.stat(path)
    # Check if group or other has read/write (0o077)
    # Ideally should be 600 (rw-------) or 640 (rw-r-----)
    mode = st.st_mode
    if mode & stat.S_IRWXO: # Others have access
        print(f"    {Colors.FAIL}[FAIL] Config is world-accessible! (chmod {oct(mode)[-3:]}){Colors.ENDC}")
        print(f"    {Colors.WARNING}>>> FIX: Run 'chmod 600 {path}'{Colors.ENDC}")
        return False
    elif mode & stat.S_IRWXG: # Group has access
        print(f"    {Colors.WARNING}[WARN] Config is group-accessible. Ensure group members are trusted.{Colors.ENDC}")
    else:
        print(f"    {Colors.GREEN}[PASS] File permissions are secure (User-only).{Colors.ENDC}")
    return True

def check_gateway(config):
    print(f"\n{Colors.BLUE}[*] Checking Gateway (API) Security...{Colors.ENDC}")
    gateway = config.get('gateway', {})
    
    # 1. Bind Address
    bind = gateway.get('bind', 'loopback')
    port = gateway.get('port', 'unknown')
    
    if bind in ['0.0.0.0', 'all', '::']:
        print(f"    {Colors.FAIL}[FAIL] Gateway bound to '{bind}' on port {port}. Exposed to network!{Colors.ENDC}")
    elif bind in ['loopback', 'localhost', '127.0.0.1']:
        print(f"    {Colors.GREEN}[PASS] Gateway bound to local interface ({bind}).{Colors.ENDC}")
    else:
        print(f"    {Colors.WARNING}[WARN] Custom bind address '{bind}'. Verify this is intended.{Colors.ENDC}")

    # 2. Auth Mode
    auth = gateway.get('auth', {})
    mode = auth.get('mode', 'token')
    
    if mode == 'none':
        print(f"    {Colors.FAIL}[CRITICAL] Gateway authentication is DISABLED (mode='none'). Full remote control possible.{Colors.ENDC}")
    elif mode == 'token':
        token = auth.get('token', '')
        if len(token) < 16:
            print(f"    {Colors.WARNING}[WARN] Gateway token appears short/weak (<16 chars).{Colors.ENDC}")
        else:
            print(f"    {Colors.GREEN}[PASS] Gateway authentication enabled (Token mode).{Colors.ENDC}")
    else:
        print(f"    {Colors.GREEN}[PASS] Gateway auth mode: {mode}{Colors.ENDC}")

def check_channels(config):
    print(f"\n{Colors.BLUE}[*] Checking Channel Policies...{Colors.ENDC}")
    channels = config.get('channels', {})
    
    if not channels:
        print(f"    {Colors.WARNING}[INFO] No channels configured.{Colors.ENDC}")
        return

    for name, settings in channels.items():
        if not settings.get('enabled', False):
            continue
            
        print(f"    > Inspecting '{name}'...")
        
        # DM Policy
        dm_policy = settings.get('dmPolicy', 'pairing')
        if dm_policy == 'open':
            print(f"      {Colors.FAIL}[FAIL] DM Policy is 'open'. ANYONE can message this bot.{Colors.ENDC}")
        elif dm_policy == 'pairing':
            print(f"      {Colors.GREEN}[PASS] DM Policy is 'pairing' (Require Auth Code).{Colors.ENDC}")
        elif dm_policy == 'allowlist':
            print(f"      {Colors.GREEN}[PASS] DM Policy is 'allowlist' (Strict).{Colors.ENDC}")
        else:
            print(f"      {Colors.WARNING}[?] Unknown DM Policy: {dm_policy}{Colors.ENDC}")

        # Group Policy
        group_policy = settings.get('groupPolicy', 'allowlist')
        if group_policy == 'open':
             print(f"      {Colors.FAIL}[FAIL] Group Policy is 'open'. Bot will reply to anyone in groups.{Colors.ENDC}")
        else:
             print(f"      {Colors.GREEN}[PASS] Group Policy is '{group_policy}'.{Colors.ENDC}")

def check_secrets(config):
    print(f"\n{Colors.BLUE}[*] Checking for Hardcoded Secrets...{Colors.ENDC}")
    # Simple recursive search for suspicious values
    suspicious_prefixes = ['sk-', 'AIza', 'xoxb-', 'xoxp-', 'ghp_']
    
    def walk_json(node, path=""):
        if isinstance(node, dict):
            for k, v in node.items():
                walk_json(v, f"{path}.{k}" if path else k)
        elif isinstance(node, str):
            for prefix in suspicious_prefixes:
                if node.startswith(prefix):
                    masked = node[:4] + "..." + node[-4:]
                    print(f"    {Colors.WARNING}[WARN] Found potential API Key at '{path}': {masked}{Colors.ENDC}")
                    print(f"          {Colors.BOLD}RISK:{Colors.ENDC} Plaintext secrets in config files are easily leaked (git, backups, logs).")
                    print(f"          {Colors.BOLD}FIX:{Colors.ENDC}  1. Remove this key from clawdbot.json.")
                    print(f"               2. Set it as an environment variable instead (e.g. in ~/.bashrc or systemd).")
                    print(f"               Example: export {k.upper()}_KEY=\"...\" (Check plugin docs for exact variable name)")

    walk_json(config)

def main():
    print_banner()
    parser = argparse.ArgumentParser(description="Audit Moltbot/Clawdbot Configuration for Security Risks")
    parser.add_argument("--config", help="Path to clawdbot.json", default="~/.clawdbot/clawdbot.json")
    args = parser.parse_args()

    config, path = load_config(args.config)
    
    if config:
        print(f"Target: {path}\n")
        check_file_permissions(path)
        check_gateway(config)
        check_channels(config)
        check_secrets(config)
        print(f"\n{Colors.HEADER}=== Audit Complete ==={Colors.ENDC}")

if __name__ == "__main__":
    main()
