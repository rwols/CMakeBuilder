from .build import CmakeBuildCommand
from .clear_cache import CmakeClearCacheCommand
from .configure import CmakeConfigureCommand
from .run_ctest import CmakeRunCtestCommand

__all__ = [
    'CmakeBuildCommand',
    'CmakeClearCacheCommand',
    'CmakeConfigureCommand',
    'CmakeRunCtestCommand'
]

print('CMakeBuilder: Available commands:')
for command in __all__:
    import re
    def convert(name):
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        cmd = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        if cmd.endswith('_command')
            cmd = cmd[:-len('_command')]
        return cmd
    print('\t{}'.format(convert(command)))

