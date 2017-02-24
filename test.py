import django
django.setup()

import nation.variables as v

from nation.tasks import *

turnchange()