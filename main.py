import click

from src.ajum import Ajum


###
# UTILITIES (START)
#

def init():
    # Initialize object
    ajum = Ajum(get_var('index_file', 'index.json'), get_var('db_file', 'database.json'))

    # Configure options
    # (1) Cache directory
    ajum.cache_dir = get_var('cache_dir', '.db')

    # (2) Waiting time after each request
    ajum.timer = get_var('timer', 3.0)

    # (3) 'From' header
    is_from = get_var('is_from', '')

    if is_from:
        ajum.headers['From'] = is_from

    # (4) User agent
    user_agent = get_var('user_agent', '')

    if user_agent:
        ajum.headers['User-Agent'] = user_agent

    return ajum

#
# UTILITIES (END)
###


###
# TASKS (START)
#

@click.group()
@click.pass_context
@click.version_option('1.4.2')
@click.option('--verbose', '-v', count=True, help='Enable verbose mode.')
def cli(ctx, verbose: int) -> None:
    """
    Tools for interacting with the 'AJuM' database.
    """

    # Ensure context object exists & is dictionary
    ctx.ensure_object(dict)

    # Assign verbose mode
    ctx.obj['verbose'] = verbose


@cli.command()
@click.option('-f', '--force', is_flag=True, help='Force cache reload.')
@click.option('-a', '--all', is_flag=True, help='Include all reviews.')
def backup(force: bool, all: bool) -> None:
    """
    Backs up remote database
    """

    # Initialize object
    ajum = Ajum()

    # Create backup
    ajum.backup_db(force, all)


if __name__ == '__main__':
    cli()



def task_build_index():
    """
    Builds index of reviews per ISBN
    """

    def build_index():
        # Initialize object
        ajum = init()

        # Build index
        ajum.build_index()

    return {
        'actions': [build_index],
    }


def task_build_db():
    """
    Builds local database
    """

    def build_db():
        # Initialize object
        ajum = init()

        # Build database
        ajum.build_db()

    return {
        'actions': [build_db],
    }


def task_clear_cache():
    """
    Removes cached index files
    """

    def clear_cache():
        # Initialize object
        ajum = init()

        # Build database
        ajum.clear_cache()

    return {
        'actions': [clear_cache],
    }


def task_fetch():
    """
    Fetches review data from remote database
    """

    def fetch():
        # Initialize object
        ajum = init()

        # Determine review ID
        data = ajum.get_review(get_var('id', ''))

        # If review for given ID exists ..
        if data:
            # .. print its data
            for key, value in data.items():
                print('{}: {}'.format(key, value))

        else:
            print('No review found for given ID, please try again.')

    return {
        'actions': [fetch],
    }


def task_query():
    """
    Queries remote database
    """

    def show_next(text: str = 'Continue? '):
        # Confirm to continue
        return input(text) in [
            '',
            'y', 'yes', 'yo', 'yep', 'sure',
            'j', 'ja', 'jo', 'jepp', 'klar',
        ]


    def query():
        # Initialize object
        ajum = init()

        # Query database
        reviews = ajum.query(
            search_term=get_var('search_term', ''),
            title=get_var('title', ''),
            first_name=get_var('first_name', ''),
            last_name=get_var('last_name', ''),
            illustrator=get_var('illustrator', ''),
            archive=get_var('archive', 'False') == 'True',
            wolgast=get_var('wolgast', 'False') == 'True'
        )

        # Count reviews
        count = len(reviews)

        if count > 0:
            print('We found {} reviews.'.format(str(count)))

            # If confirmed ..
            if show_next('Show results? '):
                # .. loop over reviews ..
                for i, review in enumerate(reviews):
                    # Increase by one for human-readable numbering
                    i += 1

                    # Let user know where we are
                    print('Review {} of {}:'.format(str(i), str(count)))

                    # Print review data
                    for key, value in ajum.get_review(review).items():
                        print('{}: {}'.format(key, value))

                    # Add newline for improved spacing
                    print('\n')

                    # Always remember this: If told to ..
                    if not show_next():
                        # .. stop!
                        break

        else:
            print('Your query did not match any review, please try again.')

    return {
        'actions': [query],
    }

#
# TASKS (END)
###
