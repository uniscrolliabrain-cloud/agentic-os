import re

path = 'src/agentic_os/kernel/ontology/domain_models.py'
with open(path, encoding='utf-8') as f:
    lines = f.readlines()

fixed = []
for line in lines:
    # Si empieza con 8 espacios + @, reducir a 4 espacios
    if line.startswith('        @'):
        fixed.append(line[4:])
    else:
        fixed.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(fixed)

print('FIXED')
