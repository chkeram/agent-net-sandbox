"""Simple CLI client for testing the Hello World Agent using direct HTTP calls."""

import json
import sys
from typing import Optional
import click
import httpx


@click.group()
@click.option('--host', default='localhost', help='Agent host')
@click.option('--port', default=8000, help='Agent port')
@click.option('--base-url', help='Base URL (overrides host/port)')
@click.pass_context
def cli(ctx, host: str, port: int, base_url: Optional[str]):
    """Simple CLI client for Hello World Agent."""
    if base_url:
        agent_url = base_url
    else:
        agent_url = f"http://{host}:{port}"
    
    ctx.ensure_object(dict)
    ctx.obj['agent_url'] = agent_url


@cli.command()
@click.pass_context
def info(ctx):
    """Get agent information and capabilities."""
    agent_url = ctx.obj['agent_url']
    
    try:
        with httpx.Client() as client:
            # Get basic info
            response = client.get(f"{agent_url}/")
            if response.status_code == 200:
                info_data = response.json()
                click.echo(f"🤖 Agent Information")
                click.echo(f"URL: {agent_url}")
                click.echo(f"Agent: {info_data.get('agent', 'N/A')}")
                click.echo(f"Version: {info_data.get('version', 'N/A')}")
                click.echo(f"Description: {info_data.get('description', 'N/A')}")
                click.echo(f"Protocol: {info_data.get('protocol', 'N/A')}")
            
            # Get capabilities
            response = client.get(f"{agent_url}/capabilities")
            if response.status_code == 200:
                capabilities = response.json()
                click.echo(f"\n📋 Capabilities:")
                for cap in capabilities.get('capabilities', []):
                    click.echo(f"  • {cap.get('name', 'N/A')}: {cap.get('description', 'N/A')}")
                
                if 'supported_languages' in capabilities:
                    click.echo(f"\n🌍 Supported Languages: {', '.join(capabilities['supported_languages'])}")
                    
    except Exception as e:
        click.echo(f"❌ Error getting agent info: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def auth(ctx):
    """Get authentication information."""
    agent_url = ctx.obj['agent_url']
    
    try:
        with httpx.Client() as client:
            response = client.get(f"{agent_url}/auth")
            if response.status_code == 200:
                auth_info = response.json()
                click.echo("🔒 Authentication Information:")
                click.echo(json.dumps(auth_info, indent=2))
            else:
                click.echo(f"❌ Error: HTTP {response.status_code}")
                sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error getting auth info: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def schema(ctx):
    """Get agent schemas (input, output, config)."""
    agent_url = ctx.obj['agent_url']
    
    try:
        with httpx.Client() as client:
            response = client.get(f"{agent_url}/schema")
            if response.status_code == 200:
                schemas = response.json()
                click.echo("📋 Agent Schemas:")
                click.echo(json.dumps(schemas, indent=2))
            else:
                click.echo(f"❌ Error: HTTP {response.status_code}")
                sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error getting schemas: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--name', default='World', help='Name to greet')
@click.option('--language', default='en', help='Language for greeting (en, es, fr, de, it)')
@click.option('--message', help='Custom greeting message')
@click.option('--stream', is_flag=True, help='Use streaming response')
@click.pass_context
def hello(ctx, name: str, language: str, message: Optional[str], stream: bool):
    """Send a hello request to the agent."""
    agent_url = ctx.obj['agent_url']
    
    # Prepare input
    input_data = {
        "name": name,
        "language": language
    }
    if message:
        input_data["message"] = message
    
    try:
        with httpx.Client() as client:
            if stream:
                click.echo(f"🌊 Streaming hello to {name} in {language}...")
                invoke_request = {
                    "input": input_data,
                    "stream": True
                }
                
                with client.stream('POST', f"{agent_url}/invoke", 
                                 json=invoke_request) as response:
                    if response.status_code == 200:
                        for line in response.iter_lines():
                            if line.strip():
                                if line.startswith('data: '):
                                    data = line[6:]  # Remove 'data: ' prefix
                                    if data == '[DONE]':
                                        break
                                    try:
                                        chunk_data = json.loads(data)
                                        click.echo(f"📦 {chunk_data}")
                                    except json.JSONDecodeError:
                                        click.echo(f"📦 {data}")
                    else:
                        click.echo(f"❌ Error: HTTP {response.status_code}")
                        sys.exit(1)
            else:
                click.echo(f"👋 Saying hello to {name} in {language}...")
                
                # Try ACP invoke endpoint first
                invoke_request = {
                    "input": input_data,
                    "stream": False
                }
                
                response = client.post(f"{agent_url}/invoke", json=invoke_request)
                if response.status_code == 200:
                    result = response.json()
                    if 'output' in result:
                        output = result['output']
                        click.echo(f"✨ {output.get('greeting', 'No greeting returned')}")
                        click.echo(f"🕐 Generated at: {output.get('timestamp', 'N/A')}")
                        click.echo(f"🤖 By agent: {output.get('agent_id', 'N/A')}")
                    else:
                        click.echo("📝 Response:")
                        click.echo(json.dumps(result, indent=2))
                else:
                    # Fallback to simple hello endpoint
                    response = client.post(f"{agent_url}/hello", json=input_data)
                    if response.status_code == 200:
                        result = response.json()
                        click.echo(f"✨ {result.get('greeting', 'No greeting returned')}")
                        click.echo(f"🕐 Generated at: {result.get('timestamp', 'N/A')}")
                        click.echo(f"🤖 By agent: {result.get('agent_id', 'N/A')}")
                    else:
                        click.echo(f"❌ Error: HTTP {response.status_code}")
                        if response.text:
                            click.echo(response.text)
                        sys.exit(1)
                    
    except Exception as e:
        click.echo(f"❌ Error invoking agent: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--agent-name', help='Custom agent name')
@click.option('--default-language', help='Default language')
@click.option('--custom-greeting', multiple=True, help='Custom greeting in format lang:greeting')
@click.pass_context
def config(ctx, agent_name: Optional[str], default_language: Optional[str], custom_greeting: tuple):
    """Create and store agent configuration."""
    agent_url = ctx.obj['agent_url']
    
    # Build configuration
    config_data = {}
    if agent_name:
        config_data["agent_name"] = agent_name
    if default_language:
        config_data["default_language"] = default_language
    
    if custom_greeting:
        custom_greetings = {}
        for greeting in custom_greeting:
            if ':' in greeting:
                lang, msg = greeting.split(':', 1)
                custom_greetings[lang] = msg
        if custom_greetings:
            config_data["custom_greetings"] = custom_greetings
    
    if not config_data:
        click.echo("❌ No configuration provided. Use --help for options.", err=True)
        sys.exit(1)
    
    config_request = {"config": config_data}
    
    try:
        with httpx.Client() as client:
            response = client.post(f"{agent_url}/config", json=config_request)
            if response.status_code == 200:
                result = response.json()
                click.echo("✅ Configuration created:")
                click.echo(f"Config ID: {result.get('config_id', 'N/A')}")
                click.echo(f"Created at: {result.get('created_at', 'N/A')}")
                click.echo("Configuration:")
                click.echo(json.dumps(result.get('config', {}), indent=2))
            else:
                click.echo(f"❌ Error: HTTP {response.status_code}")
                if response.text:
                    click.echo(response.text)
                sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error creating configuration: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def health(ctx):
    """Check agent health status."""
    agent_url = ctx.obj['agent_url']
    
    try:
        with httpx.Client() as client:
            response = client.get(f"{agent_url}/health", timeout=5.0)
            if response.status_code == 200:
                click.echo("✅ Agent is healthy")
                health_data = response.json()
                click.echo(f"Status: {health_data.get('status', 'N/A')}")
                click.echo(f"Timestamp: {health_data.get('timestamp', 'N/A')}")
            else:
                click.echo(f"⚠️ Agent health check failed: HTTP {response.status_code}")
                sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Cannot reach agent: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def test(ctx):
    """Run a comprehensive test of the agent."""
    agent_url = ctx.obj['agent_url']
    
    click.echo(f"🧪 Testing Hello World Agent at {agent_url}")
    click.echo("=" * 50)
    
    tests = [
        ("Health Check", lambda: ctx.invoke(health)),
        ("Agent Info", lambda: ctx.invoke(info)),
        ("Authentication", lambda: ctx.invoke(auth)),
        ("Schemas", lambda: ctx.invoke(schema)),
        ("Simple Hello", lambda: ctx.invoke(hello, name="Test", language="en")),
        ("Spanish Hello", lambda: ctx.invoke(hello, name="Mundo", language="es")),
        ("French Hello", lambda: ctx.invoke(hello, name="Monde", language="fr")),
        ("Custom Message", lambda: ctx.invoke(hello, name="AGNTCY", message="Welcome")),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        click.echo(f"\n🔍 Running: {test_name}")
        try:
            test_func()
            click.echo(f"✅ {test_name} - PASSED")
            passed += 1
        except SystemExit:
            click.echo(f"❌ {test_name} - FAILED")
        except Exception as e:
            click.echo(f"❌ {test_name} - ERROR: {e}")
    
    click.echo("\n" + "=" * 50)
    click.echo(f"📊 Test Results: {passed}/{total} tests passed")
    if passed == total:
        click.echo("🎉 All tests passed!")
    else:
        click.echo("⚠️ Some tests failed.")
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()