import os
import glob

__all__ = []

for file in glob.iglob(os.path.dirname(__file__) + '/*.py'):
    if not os.path.isfile(file): continue
    base = os.path.basename(file)
    if base.startswith('__'): continue
    generator = base[:-3]
    print('\t%s' % generator.replace('_', ' '))
    __all__.append(generator)
