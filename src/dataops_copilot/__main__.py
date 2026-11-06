"""Command line entry point: `python -m dataops_copilot scan|serve`."""

import argparse

import uvicorn

from dataops_copilot.agent.service import ScanRequest, build_service
from dataops_copilot.config import get_settings


def main() -> None:
    """Parse arguments and run the chosen command."""
    parser = argparse.ArgumentParser(prog="dataops_copilot")
    commands = parser.add_subparsers(dest="command", required=True)

    scan = commands.add_parser("scan", help="Profile a batch and investigate its incidents.")
    scan.add_argument("--dataset", required=True)
    scan.add_argument("--batch", required=True)
    scan.add_argument("--data-uri", required=True)
    scan.add_argument("--no-investigate", action="store_true")

    serve = commands.add_parser("serve", help="Run the HTTP API.")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args()
    if args.command == "serve":
        uvicorn.run("dataops_copilot.api:app", host=args.host, port=args.port)
        return

    result = build_service(get_settings()).scan(
        ScanRequest(
            dataset_name=args.dataset,
            batch_id=args.batch,
            data_uri=args.data_uri,
            investigate=not args.no_investigate,
        )
    )
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
