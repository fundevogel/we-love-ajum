from doit import get_var
from src.ajum import Ajum


###
# CONFIG (START)
#

DOIT_CONFIG = {'verbosity': 2}

#
# CONFIG (END)
###


###
# TASKS (START)
#

def task_backup_db():
    """
    Backs up remote database
    """

    def backup_db():
        # Initialize object
        ajum = init()

        # Create backup
        ajum.backup_db(get_var('force', 'False') == 'True')

    return {
        'actions': [backup_db],
    }


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
                    for key, value in ajum.fetch_review(review).items():
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
