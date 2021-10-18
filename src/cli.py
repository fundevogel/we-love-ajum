import click

from .ajum import Ajum


###
# TASKS (START)
#

@click.group()
@click.pass_context
@click.version_option('0.4.0')
@click.option('-i', '--index-file', default='index.json', type=click.Path(False), help='Index file.')
@click.option('-d', '--db-file', default='database.json', type=click.Path(False), help='Database file.')
@click.option('-c', '--cache-dir', default='.db', type=click.Path(False), help='Cache directory.')
@click.option('-t', '--timer', default=3.0, help='Waiting time after each request.')
@click.option('-f', '--is_from', help='"From" header.')
@click.option('-u', '--user-agent', help='User agent.')
def cli(ctx, index_file: str, db_file: str, cache_dir: str, timer: float, is_from: str, user_agent: str) -> None:
    """
    Tools for interacting with the 'AJuM' database.
    """

    # Ensure context object exists & is dictionary
    ctx.ensure_object(dict)

    # Initialize object
    ajum = Ajum(index_file, db_file)

    # Configure options
    # (1) Cache directory
    ajum.cache_dir = cache_dir

    # (2) Waiting time after each request
    ajum.timer = timer

    # (3) 'From' header
    if is_from:
        ajum.headers['From'] = is_from

    # (4) User agent
    if user_agent:
        ajum.headers['User-Agent'] = user_agent

    # Assign verbose mode
    ctx.obj['ajum'] = ajum


@cli.command()
@click.pass_context
@click.option('-f', '--force', is_flag=True, help='Force cache reload.')
@click.option('-a', '--all', is_flag=True, help='Include all reviews.')
def backup(ctx, force: bool, all: bool) -> None:
    """
    Backs up remote database
    """

    # Create backup
    ctx.obj['ajum'].backup_db(force, all)


@cli.command()
def index() -> None:
    """
    Indexes reviews per ISBN
    """

    # Indexes reviews
    ctx.obj['ajum'].build_index()


@cli.command()
@click.pass_context
def build(ctx) -> None:
    """
    Builds local database
    """

    # Build database
    ctx.obj['ajum'].build_db()


@cli.command()
@click.pass_context
def clear(ctx) -> None:
    """
    Removes cached files
    """

    # Flush cache
    ctx.obj['ajum'].clear_cache()



@cli.command()
@click.pass_context
@click.argument('review')
def show(ctx, review: str) -> None:
    """
    Shows data of given REVIEW
    """

    # Fetch review
    data = ctx.obj['ajum'].get_review(review)

    # If review exists ..
    if data:
        # .. print its data
        for key, value in data.items():
            click.echo('{}: {}'.format(key, value))

    else:
        click.echo('No review found for given ID, please try again.')


@cli.command()
@click.pass_context
@click.option('-s', '--search-term', default='', help='Force cache reload.')
@click.option('-t', '--title', default='', help='Include all reviews.')
@click.option('-f', '--first-name', default='', help='Include all reviews.')
@click.option('-l', '--last-name', default='', help='Include all reviews.')
@click.option('-l', '--last-name', default='', help='Include all reviews.')
@click.option('-i', '--illustrator', default='', help='Include all reviews.')
@click.option('-a', '--all-reviews', is_flag=True, help='Include all reviews.')
@click.option('-w', '--wolgast', is_flag=True, help='Include all reviews.')
def query(ctx, search_term: str, title: str, first_name: str, last_name: str, illustrator: str, all_reviews: bool, wolgast: bool) -> None:
    """
    Queries remote database
    """

    # Query database
    reviews = ctx.obj['ajum'].query(
        search_term=search_term,
        title=title,
        first_name=first_name,
        last_name=last_name,
        illustrator=illustrator,
        archive=all_reviews,
        wolgast=wolgast
    )

    if reviews:
        # Count reviews
        count = len(reviews)

        click.echo('We found {} reviews.'.format(count))

        # If confirmed ..
        if click.confirm('Show results?'):
            # .. loop over reviews ..
            for i, review in enumerate(reviews):
                # Increase by one for human-readable numbering
                i += 1

                # Let user know where we are
                click.echo('Review {} of {}:'.format(str(i), count))

                # Print review data
                for key, value in ajum.get_review(review).items():
                    click.echo('{}: {}'.format(key, value))

                # Add newline for improved spacing
                click.echo('\n')

                # Exit script upon last entry
                if i == count:
                    click.echo('No more entries, exiting ..')

                    # Goodbye!
                    break

                # Always remember this: If told to ..
                if not click.confirm('Continue?'):
                    # .. stop!
                    break

    else:
        click.echo('Your query did not match any review, please try again.')

#
# TASKS (END)
###


if __name__ == '__main__':
    cli()
