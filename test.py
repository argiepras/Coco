from nation.registrationforms import emailform

w = []
with open('/home/bro/bloc6/nation/dump.sql', 'r') as sql:
    for line in sql:
        a = line.split(',')
        for entry in a:
            if '@' in entry and '.' in entry:
                w.append(entry)

print len(w)
with open('/home/bro/bloc6/nation/newfile', 'w') as sql:
    for e in w:
        sql.write(e)

n = []
for email in w:
    form = emailform({'email': email.strip("'").strip(' ').strip('/').strip('\\')})
    if form.is_valid():
        n.append(email.strip("'").strip(' ').strip('/').strip('\\'))

print len(n)
with open('/home/bro/bloc6/nation/newfile1', 'w') as sql:
    for e in n:
        b = "%s," % e 
        sql.write(str(b))


from django.core.mail import send_mail


send_mail('Cold Conflict account signup', 'msg', "admin@coldconflict.com", ['n00bzalot@gmail.com'])