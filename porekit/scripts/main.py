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
def gather(path, output, workers):
    import porekit
    import feather
    def progress(files_read, files_total, bar):
        if files_read % 30==0:
            #bar.length=files_total
            #bar.update(files_read)
            pass

    bar = click.progressbar(label="Parsing Fast5 files", length=1)

    bar.render_finish()
    bar = None
    df = porekit.gather_metadata(path, workers=workers, progress_callback=lambda a,b: progress(a,b,bar))
    click.echo("Writing Metadata to file")
    feather.write_dataframe(df, output)
    click.echo("\nDone.")
    


