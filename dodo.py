from doit import get_var
from src.ajum import Ajum


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
