def allianceheaders(request):
    nation = request.user.nation
    options = request.path.split('/')
    headers = []
    active = False
    if not nation.permissions.panel_access():
        return None

    headers.append({
        'name': 'Overview',
        'pageurl': 'alliance:main',
    })

    if nation.permissions.has_permission('invite'):
        headers.append({
            'name': 'Invites',
            'pageurl': 'alliance:invites',
            'badge': nation.alliance.outstanding_invites.count(),
        })
        if 'invites' in options:
            headers[-1].update({'active': True})
            active = True

    if nation.permissions.has_permission('applicants'):
        headers.append({
            'name': 'Applications',
            'pageurl': 'alliance:applications',
            'badge': nation.alliance.applications.count(),
        })
        if 'applications' in options:
            headers[-1].update({'active': True})
            active = True

    if nation.permissions.has_permission('banking'):
        headers.append({
            'name': 'Bank',
            'pageurl': 'alliance:bank',
        })
        if 'bank' in options:
            headers[-1].update({'active': True})
            active = True

    if nation.permissions.panel_access():
        headers.append({
            'name': 'Control panel',
            'pageurl': 'alliance:control_panel',
        })
        if 'control_panel' in options:
            headers[-1].update({'active': True})
            active = True

    if not active:
        headers[0].update({'active': True})

    return headers