import click

banner ="""
Porekit CLI
Copyright (C) 2016 by Andreas Klostermann

"""


@click.group()
def main():
    pass


@main.command()
@click.argument('path', type=click.Path(exists=True))
@click.argument('output', type=click.Path())
@click.option('--workers', nargs=1, type=int, default=1)
def collect(path, output, workers):
    import porekit
    import feather
    click.echo("Collecting metadata")
    df = porekit.gather_metadata(path, workers=workers)
    click.echo("Writing Metadata to file")
    feather.write_dataframe(df, output)
    click.echo("\nDone.")
