import enum

import typer


class Stage(str, enum.Enum):
    PROD = "prod"
    DEV = "dev"


def check_output_command(return_code, stdout, stderr):
    if return_code != 0:
        typer.echo(stdout, )
        typer.echo(f"STDOUT: {stdout}")
        typer.echo(f"STDERR: {stderr}")
        raise typer.Exit(code=return_code)
