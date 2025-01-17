import os
from pathlib import Path
from typing import Optional

import boto3
import typer
from botocore.exceptions import ClientError
from rich.pretty import pprint

from aws_lambda import generate_lambda_resource_names
from utils import get_configuration_value
from utils.utils import Stage


def describe(
        deployment_name: str,
        config_file_path: Optional[Path] = None,
        stage: Optional[Stage] = None
):
    if not config_file_path:
        config_file_path = os.path.join(os.getcwd(), "lambda_config.json")

    if not stage:
        stage = Stage.DEV

    # get data about cf stack
    _, stack_name, repo_name = generate_lambda_resource_names(deployment_name, stage)
    lambda_config = get_configuration_value(config_file_path)
    cf_client = boto3.client("cloudformation", lambda_config["region"])
    try:
        stack_info = cf_client.describe_stacks(StackName=stack_name)
    except ClientError:
        print(f"Unable to find {deployment_name} in your cloudformation stack.")
        return

    info_json = {}
    stack_info = stack_info.get("Stacks")[0]
    keys = [
        "StackName",
        "StackId",
        "StackStatus",
    ]
    info_json = {k: v for k, v in stack_info.items() if k in keys}
    info_json["CreationTime"] = stack_info.get("CreationTime").strftime(
        "%m/%d/%Y, %H:%M:%S"
    )
    info_json["LastUpdatedTime"] = stack_info.get("LastUpdatedTime").strftime(
        "%m/%d/%Y, %H:%M:%S"
    )

    # get Endpoints
    outputs = stack_info.get("Outputs")
    outputs = {o["OutputKey"]: o["OutputValue"] for o in outputs}
    info_json.update(outputs)

    pprint(info_json)

    return info_json


if __name__ == "__main__":
    typer.run(describe)
