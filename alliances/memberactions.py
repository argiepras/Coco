

def leave(nation):
    if nation.alliance.members.all().count() == 1:
        nation.alliance.delete()
        return "Alliance has been disbanded"
    nation.alliance.kick(nation)
    return result = "You say your goodbyes before being tossed by security."


def withdraw():
    form = withdrawform(nation, request.POST)
            if form.is_valid():
                if form.cleaned_data['empty']:
                    result = "You can't withdraw nothing!"
                else:
                    form.cleaned_data.pop('e mpty')
                    actions = {} #moving to nation
                    withdraws = {} #setting bankstats for limiting
                    withdrawactions = {} #moving from bank
                    for field in form.cleaned_data:
                        actions.update({field: {'action': 'add', 'amount': form.cleaned_data[field]}})
                        withdrawactions.update({field: {'action': 'subtract', 'amount': form.cleaned_data[field]}})
                        withdraws.update({field: F(field) + form.cleaned_data[field]})
                 with transaction.atomic():
                        utils.atomic_transaction(Nation, nation.pk, actions)
                        utils.atomic_transaction(Bank, alliance.bank.pk, withdrawactions)
                        if nation.alliance.bank.limit:
                            if nation.alliance.bank.per_nation:
                                qfilter = {'nation': nation}
                            else:
                                qfilter = {'alliance': nation.alliance}
                            Memberstats.objects.select_for_update().filter(**qfilter).update(**withdraws)
                    banklogging(nation, actions, False)
                    result = "Withdrawal has been made!"
            else:
                result = "You can't withdraw more than your limit!"



def deposit():
    form = depositform(nation, request.POST)
            if form.is_valid():
                if form.cleaned_data['empty']:
                    result = "You can't deposit nothing!"
                else:
                    form.cleaned_data.pop('empty')
                    actions = {}
                    depositactions = {}
                    for field in form.cleaned_data:
                        actions.update({field: {'action': 'subtract', 'amount': form.cleaned_data[field]}})
                        depositactions.update({field: {'action': 'add', 'amount': form.cleaned_data[field]}})
                    utils.atomic_transaction(Nation, nation.pk, actions)
                    utils.atomic_transaction(Bank, alliance.bank.pk, depositactions)
                    banklogging(nation, actions, True)
                    result = "Deposited!"
            else:
                result = "Can't deposit that much!"


def invite(nation, alliance, action):
    try:
        invite = alliance.invites.filter(nation=nation)
    except:
        return "You do not have an invitation from this alliance!"
    if action = "accept":
        return accept_invite(nation, alliance)
    return reject_invite(nation, alliance)


def accept_invite(nation, alliance):
    if alliance.invites.filter(nation=nation).exists()
    

def reject_invite():
    pass