from nation.models import Nation, Actionlog




#takes querysets for actionlogs
#for analysing likeness between turns
def compare_logs(reference, comparer):
    
    if reference.count() == 0 or reference.count() == 0:
        return 0
    a = {}
    b = {}
    for log in reference:
        if log.action in a:
            a[log.action] += 1
        else:
            a[log.action] = 1



def scriptcheck(x, y):
    total = 0
    hits = 0
    for a, b in zip(x, y):
        total += 1
        if a.action == b.action:
            hits += 1

    if int((float(hits)/float(total))*100.0) > 80:
        return True
    return False