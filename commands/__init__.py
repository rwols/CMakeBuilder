from .clear_cache import CmakeClearCacheCommand
from .configure import CmakeConfigureCommand
from .diagnose import CmakeDiagnoseCommand
from .edit_cache import CmakeEditCacheCommand
from .insert_diagnosis import CmakeInsertDiagnosisCommand
from .new_project import CmakeNewProjectCommand
from .open_build_folder import CmakeOpenBuildFolderCommand
from .run_ctest import CmakeRunCtestCommand
from .write_build_targets import CmakeWriteBuildTargetsCommand

__all__ = [
    'CmakeClearCacheCommand'
    , 'CmakeConfigureCommand'
    , 'CmakeDiagnoseCommand'
    , 'CmakeEditCacheCommand'
    , 'CmakeInsertDiagnosisCommand'
    , 'CmakeNewProjectCommand'
    , 'CmakeOpenBuildFolderCommand'
    , 'CmakeRunCtestCommand'
    , 'CmakeWriteBuildTargetsCommand'
]
