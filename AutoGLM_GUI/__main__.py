"""CLI entry point for AutoGLM-GUI."""

import argparse
import sys

# Default configuration
DEFAULT_MODEL_NAME = "autoglm-phone-9b"


def main() -> None:
    """Start the AutoGLM-GUI server."""
    parser = argparse.ArgumentParser(
        description="AutoGLM-GUI - Web GUI for AutoGLM Phone Agent"
    )
    parser.add_argument(
        "--base-url",
        required=True,
        help="Base URL of the model API (required, e.g., http://localhost:8080/v1)",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL_NAME,
        help=f"Model name to use (default: {DEFAULT_MODEL_NAME})",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )

    # If no arguments provided, print help and exit
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    import uvicorn

    from AutoGLM_GUI import server

    # Set model configuration for the server
    server.DEFAULT_BASE_URL = args.base_url
    server.DEFAULT_MODEL_NAME = args.model

    # Display startup banner
    print()
    print("=" * 50)
    print("  AutoGLM-GUI - Phone Agent Web Interface")
    print("=" * 50)
    print()
    print(f"  Server:     http://{args.host}:{args.port}")
    if args.host == "0.0.0.0":
        print(f"  Local:      http://127.0.0.1:{args.port}")
    print()
    print("  Model Configuration:")
    print(f"    Base URL: {args.base_url}")
    print(f"    Model:    {args.model}")
    print()
    print("=" * 50)
    print("  Press Ctrl+C to stop")
    print("=" * 50)
    print()

    uvicorn.run(
        server.app if not args.reload else "AutoGLM_GUI.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
