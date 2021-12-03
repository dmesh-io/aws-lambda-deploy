import os
from pathlib import Path
from typing import Optional

import typer as typer
from bentoml.saved_bundle import load_bento_service_metadata

from aws_lambda import (
    generate_lambda_deployable,
    generate_lambda_resource_names,
    generate_aws_lambda_cloudformation_template_file,
    call_sam_command,
)
from utils import (
    get_configuration_value,
    create_ecr_repository_if_not_exists,
    console
)
from utils.utils import Stage


def deploy(
        bento_bundle_path: Path,
        deployment_name: str,
        config_json: Optional[Path] = None,
        stage: Optional[Stage] = None
):
    if not config_json:
        config_json = os.path.join(os.getcwd(), "lambda_config.json")

    if not stage:
        stage = Stage.DEV

    bento_metadata = load_bento_service_metadata(str(bento_bundle_path))
    lambda_config = get_configuration_value(config_json)
    deployable_path = os.path.join(
        os.path.curdir,
        f"{bento_metadata.name}-{bento_metadata.version}-lambda-deployable",
    )

    generate_lambda_deployable(bento_bundle_path, deployable_path, lambda_config)
    (
        template_name,
        stack_name,
        repo_name,
    ) = generate_lambda_resource_names(deployment_name, stage)
    console.print(f"Created AWS Lambda deployable [b][{deployable_path}][/b]")

    api_names = [api.name for api in bento_metadata.apis]
    template_file_path = generate_aws_lambda_cloudformation_template_file(
        deployment_name=deployment_name,
        project_dir=deployable_path,
        api_names=api_names,
        bento_service_name=bento_metadata.name,
        docker_context=deployable_path,
        docker_file="Dockerfile-lambda",
        docker_tag=repo_name,
        memory_size=lambda_config["memory_size"],
        timeout=lambda_config["timeout"],
    )
    console.print(f"Built SAM template [b][{template_file_path}][/b]")

    with console.status("Building image"):
        return_code, stdout, stderr = call_sam_command(
            [
                "build",
                "--template-file",
                template_file_path.split("/")[-1],
                "--build-dir",
                os.path.join(deployable_path, "build"),
            ],
            project_dir=deployable_path,
            region=lambda_config["region"],
        )
        # print(return_code, stdout, stderr)

    with console.status("Pushing image to ECR"):
        repository_id, registry_url = create_ecr_repository_if_not_exists(
            lambda_config["region"], repo_name
        )
        return_code, stdout, stderr = call_sam_command(
            [
                "package",
                "--template-file",
                os.path.join(deployable_path, "build", "template.yaml"),
                "--output-template-file",
                "package-template.yaml",
                "--image-repository",
                registry_url,
            ],
            project_dir=deployable_path,
            region=lambda_config["region"],
        )
        # print(return_code, stdout, stderr)
    console.print(f"Image built and pushed [b][{registry_url}][/b]")

    with console.status("Deploying to Lambda"):
        return_code, stdout, stderr = call_sam_command(
            [
                "deploy",
                "-t",
                "package-template.yaml",
                "--stack-name",
                stack_name,
                "--image-repository",
                registry_url,
                "--capabilities",
                "CAPABILITY_IAM",
                "--region",
                lambda_config["region"],
                "--no-confirm-changeset",
            ],
            project_dir=deployable_path,
            region=lambda_config["region"],
        )
        # print(return_code, stdout, stderr)

    print("### Deployment Complete! ###")


if __name__ == "__main__":
    typer.run(deploy)
