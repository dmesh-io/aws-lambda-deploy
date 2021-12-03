import os
from pathlib import Path
from typing import Optional

import typer

from deploy import deploy
from utils import console
from utils.utils import Stage


def update(
        bento_bundle_path: Path,
        deployment_name: str,
        config_json: Optional[Path] = None,
        stage: Optional[Stage] = None
):
    if not config_json:
        config_json = os.path.join(os.getcwd(), "lambda_config.json")

    if not stage:
        stage = Stage.DEV

    """
    in the case of AWS Lambda deployments, since we are using SAM cli for deploying
    the updation and deployment process is identical, hence you can just call the
    deploy functionality for updation also.
    """
    deploy(
        bento_bundle_path=bento_bundle_path,
        deployment_name=deployment_name,
        config_json=config_json,
        stage=stage
    )
    console.print("[bold green]Deployment (Update) Complete!")


if __name__ == "__main__":
    typer.run(deploy)
