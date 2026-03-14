"""
Environment Setup Helper

This script helps you create and configure your .env file for the CoreInventory application.
"""

import os
import sys
from pathlib import Path


def print_header():
    """Print header."""
    print("\n" + "=" * 70)
    print("  🔧 CoreInventory Environment Setup Helper")
    print("=" * 70 + "\n")


def check_env_file():
    """Check if .env file exists."""
    env_file = Path(".env")

    if env_file.exists():
        print("✅ .env file exists")
        with open(env_file, 'r') as f:
            content = f.read().strip()
            if content:
                print("✅ .env file is not empty\n")
                return True
            else:
                print("❌ .env file is empty - needs configuration\n")
                return False
    else:
        print("❌ .env file does not exist\n")
        return False


def create_env_from_example():
    """Create .env from .env.example."""
    example_file = Path(".env.example")
    env_file = Path(".env")

    if not example_file.exists():
        print("❌ .env.example not found!")
        return False

    print(f"Creating {Colors.OKBLUE}.env{Colors.ENDC} from {Colors.OKBLUE}.env.example{Colors.ENDC}...\n")

    with open(example_file, 'r') as f:
        example_content = f.read()

    with open(env_file, 'w') as f:
        f.write(example_content)

    print(f"✅ Created {Colors.OKGREEN}.env{Colors.ENDC} file\n")
    return True


def configure_env():
    """Guide user through .env configuration."""
    env_file = Path(".env")

    print(f"{Colors.BOLD}📝 Configure Your Credentials{Colors.ENDC}\n")
    print("You need to fill in the following in your .env file:\n")

    # Read current .env
    with open(env_file, 'r') as f:
        lines = f.readlines()

    # Configuration prompts
    config = {}

    print(f"{Colors.WARNING}1. DATABASE_URL{Colors.ENDC}")
    print("   Format: postgresql+asyncpg://username:password@host:port/database")
    print("   Example: postgresql+asyncpg://postgres:mypassword@localhost:5432/core_inventory")
    db_url = input(f"   {Colors.OKCYAN}Enter your DATABASE_URL: {Colors.ENDC}").strip()
    if db_url:
        config['DATABASE_URL'] = db_url
    else:
        print(f"   {Colors.FAIL}Using default from .env.example{Colors.ENDC}")

    print(f"\n{Colors.WARNING}2. JWT_SECRET_KEY{Colors.ENDC}")
    print("   Generate a random secret key (minimum 32 characters)")
    print(f"   {Colors.OKCYAN}Run this to generate: python -c \"import secrets; print(secrets.token_urlsafe(32))\"{Colors.ENDC}")
    jwt_secret = input(f"   {Colors.OKCYAN}Enter your JWT_SECRET_KEY: {Colors.ENDC}").strip()
    if jwt_secret:
        config['JWT_SECRET_KEY'] = jwt_secret
    else:
        print(f"   {Colors.FAIL}Using default from .env.example{Colors.ENDC}")

    print(f"\n{Colors.WARNING}3. GROQ_API_KEY{Colors.ENDC}")
    print("   Get from: https://console.groq.com")
    groq_key = input(f"   {Colors.OKCYAN}Enter your GROQ_API_KEY (or press Enter to skip): {Colors.ENDC}").strip()
    if groq_key:
        config['GROQ_API_KEY'] = groq_key
    else:
        print(f"   {Colors.FAIL}Skipped - you can add this later{Colors.ENDC}")

    # Update .env file
    new_lines = []
    for line in lines:
        key = line.split('=')[0] if '=' in line else None
        if key and key in config:
            new_lines.append(f"{key}={config[key]}\n")
        else:
            new_lines.append(line)

    with open(env_file, 'w') as f:
        f.writelines(new_lines)

    print(f"\n✅ {Colors.OKGREEN}.env file updated!{Colors.ENDC}\n")


def verify_env():
    """Verify .env has all required fields."""
    env_file = Path(".env")

    if not env_file.exists():
        return False, ".env file not found"

    with open(env_file, 'r') as f:
        env_vars = {}
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value

    required = ['DATABASE_URL', 'JWT_SECRET_KEY']
    missing = [k for k in required if not env_vars.get(k) or env_vars.get(k).startswith('your-')]

    if missing:
        return False, f"Missing or unconfigured: {', '.join(missing)}"

    return True, "All required fields configured"


class Colors:
    """ANSI colors."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def main():
    """Main setup flow."""
    print_header()

    # Step 1: Check if .env exists
    if not check_env_file():
        print(f"Creating .env file...\n")
        if not create_env_from_example():
            print(f"{Colors.FAIL}❌ Could not create .env file{Colors.ENDC}")
            sys.exit(1)

    # Step 2: Configure .env
    response = input(f"{Colors.BOLD}Do you want to configure .env now? (y/n): {Colors.ENDC}").strip().lower()
    if response == 'y':
        configure_env()

    # Step 3: Verify configuration
    is_valid, message = verify_env()
    print(f"\n{Colors.BOLD}Verification Results:{Colors.ENDC}")
    if is_valid:
        print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}\n")
        print(f"{Colors.OKGREEN}Your .env is ready! You can now run:{Colors.ENDC}")
        print(f"  {Colors.OKCYAN}python app.py{Colors.ENDC}\n")
    else:
        print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")
        print(f"\n{Colors.WARNING}Please edit .env manually:{Colors.ENDC}")
        print(f"  nano .env  # or use your favorite editor\n")
        print(f"{Colors.BOLD}Required fields:{Colors.ENDC}")
        print(f"  - DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/core_inventory")
        print(f"  - JWT_SECRET_KEY=your-secret-key-here")
        print(f"  - GROQ_API_KEY=gsk_your_key_here (optional but needed for chatbot)\n")


if __name__ == "__main__":
    main()
