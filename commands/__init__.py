from .clear_cache_and_configure import CmakeClearCacheAndConfigureCommand
from .clear_cache import CmakeClearCacheCommand
from .configure import CmakeConfigureCommand
from .diagnose import CmakeDiagnoseCommand
from .insert_diagnosis import CmakeInsertDiagnosisCommand
from .open_build_folder import CmakeOpenBuildFolderCommand
from .run_ctest import CmakeRunCtestCommand
from .write_build_targets import CmakeWriteBuildTargetsCommand

__all__ = [
    'CmakeClearCacheAndConfigureCommand',
    'CmakeClearCacheCommand',
    'CmakeConfigureCommand',
    'CmakeDiagnoseCommand',
    'CmakeInsertDiagnosisCommand',
    'CmakeOpenBuildFolderCommand',
    'CmakeRunCtestCommand',
    'CmakeWriteBuildTargetsCommand'
]

print('CMakeBuilder: Available commands:')
for command in __all__:
    def convert(name):
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        name =  re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        if name.endswith('_command'):
            name = name[:-len('_command')]
        return name
    print('\t{}'.format(convert(command)))

